"""
Employee Two-Factor Authentication (2FA) Pages
===============================================
1. Employee 2FA Setup Page (during required login enrollment or self-service)
2. Employee 2FA Verification Page (during login when 2FA is enabled)
"""

import time
import streamlit as st
from services.two_factor_service import (
    generate_totp_secret,
    get_provisioning_uri,
    generate_qr_code_bytes,
    verify_totp_code,
    encrypt_totp_secret,
    decrypt_totp_secret,
    generate_recovery_codes,
    hash_recovery_codes,
    verify_and_consume_recovery_code,
    check_2fa_rate_limit,
    compute_next_2fa_lockout,
)
from services.auth_service import complete_2fa_login, cancel_pending_2fa
from database.queries import (
    get_user_2fa_record,
    save_user_2fa_setup,
    activate_user_2fa,
    disable_user_2fa,
    record_2fa_verification_result,
)


def _init_setup_state(username: str, user_id: str, user_type: str):
    """Initialize or retrieve pending TOTP setup secret & recovery codes in session state."""
    if not st.session_state.get("pending_2fa_setup_secret") or st.session_state.get("pending_2fa_setup_user") != username:
        secret = generate_totp_secret()
        recovery_codes = generate_recovery_codes(8)
        enc_secret = encrypt_totp_secret(secret)
        rec_hashes = hash_recovery_codes(recovery_codes)
        save_user_2fa_setup(username, user_id, user_type, enc_secret, rec_hashes)
        st.session_state["pending_2fa_setup_user"] = username
        st.session_state["pending_2fa_setup_secret"] = secret
        st.session_state["pending_2fa_setup_recovery"] = recovery_codes


def render_employee_2fa_setup_page(user: dict, is_login_flow: bool = False):
    """Employee 2FA Setup Page — QR code, manual key, 6-digit verification, and recovery codes."""
    username = user.get("username", "")
    user_id = user.get("employee_id") or user.get("id") or username
    emp_name = user.get("employee_name") or username.title()

    if is_login_flow:
        st.markdown("<h1 style='text-align: center; color: #2563EB;'>Employee 2FA Setup</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Your administrator requires Two-Factor Authentication. Please configure your authenticator app to continue.</p>", unsafe_allow_html=True)
    else:
        st.subheader("🔐 Employee Two-Factor Authentication (2FA)", divider="blue")
        st.caption(f"Manage authenticator app security for **{emp_name}** (`{username}`)")

    record = get_user_2fa_record(username)
    already_verified = bool(record and record.get("two_fa_enabled") and record.get("setup_verified"))

    # If recovery codes were just generated on activation, show them once before continuing
    if st.session_state.get("emp_2fa_just_activated"):
        codes = st.session_state.get("pending_2fa_setup_recovery", [])
        col1, col2, col3 = st.columns([1, 2, 1]) if is_login_flow else (st.container(), st.container(), st.container())
        target_col = col2 if is_login_flow else st.container()
        with target_col:
            with st.container(border=True):
                st.success("✅ Two-Factor Authentication is now enabled for your account!")
                st.warning("⚠️ **Save your single-use recovery codes now.** They will not be shown again. Store them safely in case you lose access to your authenticator device.")
                st.code("\n".join(codes), language="text")
                st.download_button(
                    "📥 Download Recovery Codes (.txt)",
                    data="\n".join(codes),
                    file_name=f"{username}_2fa_recovery_codes.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
                if st.button("Continue to Application →" if is_login_flow else "Done", type="primary", use_container_width=True):
                    st.session_state.pop("emp_2fa_just_activated", None)
                    st.session_state.pop("pending_2fa_setup_user", None)
                    if is_login_flow:
                        complete_2fa_login(user)
                    st.rerun()
        return

    col_left, col_center, col_right = st.columns([0.8, 2.2, 0.8]) if is_login_flow else (None, None, None)
    wrapper = col_center if is_login_flow else st.container()

    with wrapper:
        if already_verified and not is_login_flow:
            with st.container(border=True):
                st.success("🟢 **2FA Status: Enabled & Verified**")
                if record.get("last_verified_at"):
                    st.caption(f"Last verified: `{record['last_verified_at']}`")
                rem_codes = len(record.get("recovery_codes_hashed") or [])
                st.info(f"Remaining single-use recovery codes: **{rem_codes}**")

                st.divider()
                st.markdown("#### Disable 2FA")
                st.caption("Disabling 2FA removes authenticator verification from your login. You can re-enable it at any time.")
                if st.button("Disable My 2FA", type="secondary", key="btn_disable_own_emp_2fa"):
                    ok, msg = disable_user_2fa(username, username)
                    if ok:
                        st.session_state.pop("pending_2fa_setup_secret", None)
                        st.session_state.pop("pending_2fa_setup_user", None)
                        st.success("Two-Factor Authentication has been disabled for your account.")
                        st.rerun()
                    else:
                        st.error(f"Failed to disable 2FA: {msg}")
            return

        _init_setup_state(username, str(user_id), "employee")
        secret = st.session_state["pending_2fa_setup_secret"]
        uri = get_provisioning_uri(secret, username)
        qr_bytes = generate_qr_code_bytes(uri)

        with st.container(border=True):
            st.markdown("### Configure Authenticator App")
            st.markdown(
                "Use **Google Authenticator**, **Microsoft Authenticator**, **Authy**, or any standard TOTP app."
            )

            qr_col, instr_col = st.columns([1.1, 1.4])
            with qr_col:
                st.image(qr_bytes, caption="Scan QR Code with Authenticator App", width=220)
            with instr_col:
                st.markdown("**Step 1:** Open your authenticator app and tap **+ / Add Account**.")
                st.markdown("**Step 2:** Scan the QR code on the left, **or** enter this manual setup key:")
                st.code(secret, language="text")
                st.caption("Account type: Time-based (TOTP) • 6 digits • 30-second interval")

            st.divider()
            with st.form("emp_2fa_setup_verify_form", border=False):
                code_input = st.text_input(
                    "Step 3: Enter 6-Digit Verification Code",
                    placeholder="123456",
                    max_chars=6,
                    key="emp_2fa_setup_code",
                )
                verify_btn = st.form_submit_button("Verify & Enable 2FA", type="primary", use_container_width=True)

                if verify_btn:
                    is_ok, matched_step, err_msg = verify_totp_code(secret, code_input)
                    if is_ok:
                        ok, db_msg = activate_user_2fa(username, matched_step)
                        if ok:
                            st.session_state["emp_2fa_just_activated"] = True
                            st.rerun()
                        else:
                            st.error(f"Failed to activate 2FA: {db_msg}")
                    else:
                        st.error(err_msg)

            if is_login_flow:
                if st.button("← Back to Login", use_container_width=True, key="emp_setup_back_login"):
                    cancel_pending_2fa()
                    st.rerun()


def render_employee_2fa_verify_page(pending_user: dict):
    """Employee 2FA Verification Page — shown after password verification when 2FA is active."""
    username = pending_user.get("username", "")
    emp_name = pending_user.get("employee_name") or username.title()

    st.markdown("<h1 style='text-align: center; color: #2563EB;'>Employee 2FA Verification</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center;'>Welcome back, <b>{emp_name}</b>. Enter your authenticator code to continue.</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            record = get_user_2fa_record(username)
            if not record or not record.get("encrypted_secret"):
                # Safety redirect to setup if secret is missing
                st.session_state["pending_2fa_mode"] = "setup"
                st.rerun()
                return

            allowed, lock_msg = check_2fa_rate_limit(record)
            if not allowed:
                st.error(f"🚫 {lock_msg}")
                if st.button("← Back to Login", use_container_width=True, key="emp_2fa_locked_back"):
                    cancel_pending_2fa()
                    st.rerun()
                return

            tab_totp, tab_recovery = st.tabs(["📱 Authenticator Code", "🔑 Recovery Code"])

            with tab_totp:
                with st.form("emp_2fa_verify_form", border=False):
                    totp_input = st.text_input(
                        "6-Digit Authenticator Code",
                        placeholder="Enter 6-digit code",
                        max_chars=6,
                        key="emp_2fa_verify_code",
                    )
                    submit_totp = st.form_submit_button("Verify & Sign In", type="primary", use_container_width=True)

                    if submit_totp:
                        secret = decrypt_totp_secret(record["encrypted_secret"])
                        last_step = record.get("last_used_timestep")
                        is_ok, matched_step, err_msg = verify_totp_code(secret, totp_input, last_used_timestep=last_step)

                        if is_ok:
                            record_2fa_verification_result(username, True, matched_step=matched_step)
                            complete_2fa_login(pending_user)
                            st.success("2FA Verified! Redirecting...")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            new_failed, lock_until = compute_next_2fa_lockout(record.get("failed_attempts", 0))
                            record_2fa_verification_result(username, False, failed_attempts=new_failed, locked_until=lock_until)
                            if lock_until:
                                st.error("🚫 Too many failed 2FA attempts. Verification locked for 15 minutes.")
                            else:
                                st.error(f"❌ {err_msg} (Attempt {new_failed}/5)")

            with tab_recovery:
                st.caption("Use one of your single-use backup recovery codes (e.g. `ABCD-EFGH`).")
                with st.form("emp_2fa_recovery_form", border=False):
                    rec_input = st.text_input("Recovery Code", placeholder="XXXX-XXXX", key="emp_2fa_recovery_code")
                    submit_rec = st.form_submit_button("Verify Recovery Code", type="primary", use_container_width=True)

                    if submit_rec:
                        stored_hashes = record.get("recovery_codes_hashed") or []
                        is_ok, remaining = verify_and_consume_recovery_code(rec_input, stored_hashes)
                        if is_ok:
                            record_2fa_verification_result(
                                username,
                                True,
                                recovery_hashes=remaining,
                                used_recovery=True,
                            )
                            complete_2fa_login(pending_user)
                            st.success("Recovery code accepted! Signing in...")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            new_failed, lock_until = compute_next_2fa_lockout(record.get("failed_attempts", 0))
                            record_2fa_verification_result(username, False, failed_attempts=new_failed, locked_until=lock_until)
                            st.error(f"❌ Invalid or already used recovery code. (Attempt {new_failed}/5)")

            st.divider()
            if st.button("← Back to Login", use_container_width=True, key="emp_verify_back_login"):
                cancel_pending_2fa()
                st.rerun()

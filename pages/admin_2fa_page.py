"""
Admin Two-Factor Authentication (2FA) Pages
============================================
1. Admin 2FA Setup & Configuration Page (enable/disable own 2FA, QR + manual key, recovery codes)
2. Admin 2FA Verification Page (separate verification flow for Admin login)
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


def _init_admin_setup_state(username: str, user_id: str):
    """Initialize pending Admin TOTP setup secret and recovery codes."""
    if not st.session_state.get("pending_2fa_setup_secret") or st.session_state.get("pending_2fa_setup_user") != username:
        secret = generate_totp_secret()
        recovery_codes = generate_recovery_codes(8)
        enc_secret = encrypt_totp_secret(secret)
        rec_hashes = hash_recovery_codes(recovery_codes)
        save_user_2fa_setup(username, user_id, "admin", enc_secret, rec_hashes)
        st.session_state["pending_2fa_setup_user"] = username
        st.session_state["pending_2fa_setup_secret"] = secret
        st.session_state["pending_2fa_setup_recovery"] = recovery_codes


def render_admin_2fa_setup_page(user: dict, is_login_flow: bool = False):
    """Admin 2FA Setup & Configuration Page — independent Admin 2FA management."""
    if user.get("role") != "admin":
        st.error("⛔ Access Denied: Administrator privileges required.")
        return

    username = user.get("username", "admin")
    user_id = user.get("employee_id") or user.get("id") or "admin"

    if is_login_flow:
        st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🛡️ Admin 2FA Setup</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center;'>Configure Two-Factor Authentication for your Administrator account.</p>", unsafe_allow_html=True)
    else:
        st.subheader("🛡️ Admin Two-Factor Authentication (2FA)", divider="blue")
        st.caption(f"Independent 2FA configuration for Administrator account **`{username}`**")

    record = get_user_2fa_record(username)
    is_enabled = bool(record and record.get("two_fa_enabled") and record.get("setup_verified"))

    # One-time recovery codes display after activation
    if st.session_state.get("admin_2fa_just_activated"):
        codes = st.session_state.get("pending_2fa_setup_recovery", [])
        with st.container(border=True):
            st.success("✅ Admin Two-Factor Authentication is now active!")
            st.warning("⚠️ **Save your single-use recovery codes immediately.** They will not be displayed again.")
            st.code("\n".join(codes), language="text")
            st.download_button(
                "📥 Download Admin Recovery Codes (.txt)",
                data="\n".join(codes),
                file_name=f"{username}_admin_2fa_recovery_codes.txt",
                mime="text/plain",
                use_container_width=True,
            )
            if st.button("Continue" if is_login_flow else "Done", type="primary", use_container_width=True):
                st.session_state.pop("admin_2fa_just_activated", None)
                st.session_state.pop("pending_2fa_setup_user", None)
                if is_login_flow:
                    complete_2fa_login(user)
                st.rerun()
        return

    if is_enabled and not is_login_flow:
        with st.container(border=True):
            st.success("🟢 **Admin 2FA Status: Enabled & Active**")
            if record.get("last_verified_at"):
                st.caption(f"Last verified: `{record['last_verified_at']}`")
            rem_codes = len(record.get("recovery_codes_hashed") or [])
            st.info(f"Remaining single-use recovery codes: **{rem_codes}**")

            st.divider()
            st.markdown("#### Disable Admin 2FA")
            st.caption("Disabling 2FA reduces account security. You can re-enable it at any time.")
            if st.button("Disable Admin 2FA", type="secondary", key="btn_disable_own_admin_2fa"):
                ok, msg = disable_user_2fa(username, username)
                if ok:
                    st.session_state.pop("pending_2fa_setup_secret", None)
                    st.session_state.pop("pending_2fa_setup_user", None)
                    st.success("Admin 2FA has been disabled.")
                    st.rerun()
                else:
                    st.error(f"Failed to disable 2FA: {msg}")
        return

    # Setup flow
    _init_admin_setup_state(username, str(user_id))
    secret = st.session_state["pending_2fa_setup_secret"]
    uri = get_provisioning_uri(secret, f"{username} (Admin)")
    qr_bytes = generate_qr_code_bytes(uri)

    with st.container(border=True):
        st.info("🔴 **Admin 2FA Status: Disabled** — Scan the QR code below to activate 2FA.")
        qr_col, instr_col = st.columns([1.0, 1.5])
        with qr_col:
            st.image(qr_bytes, caption="Admin Authenticator QR Code", width=220)
        with instr_col:
            st.markdown("**Step 1:** Open Google Authenticator, Microsoft Authenticator, Authy, or any TOTP app.")
            st.markdown("**Step 2:** Scan the QR code or enter this manual setup key:")
            st.code(secret, language="text")
            st.caption("Standard RFC 6238 TOTP • 6 digits • 30-second interval")

        st.divider()
        with st.form("admin_2fa_setup_verify_form", border=False):
            code_input = st.text_input(
                "Step 3: Enter 6-Digit Authenticator Code to Activate",
                placeholder="123456",
                max_chars=6,
                key="admin_2fa_setup_code",
            )
            submit_btn = st.form_submit_button("Verify & Activate Admin 2FA", type="primary", use_container_width=True)

            if submit_btn:
                is_ok, matched_step, err_msg = verify_totp_code(secret, code_input)
                if is_ok:
                    ok, db_msg = activate_user_2fa(username, matched_step)
                    if ok:
                        st.session_state["admin_2fa_just_activated"] = True
                        st.rerun()
                    else:
                        st.error(f"Failed to activate Admin 2FA: {db_msg}")
                else:
                    st.error(err_msg)

        if is_login_flow:
            if st.button("← Back to Login", use_container_width=True, key="admin_setup_back_login"):
                cancel_pending_2fa()
                st.rerun()


def render_admin_2fa_verify_page(pending_user: dict):
    """Separate Admin 2FA Verification Page during Admin login."""
    username = pending_user.get("username", "admin")

    st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>🛡️ Admin 2FA Verification</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center;'>Administrator security check for <b>{username.title()}</b></p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            st.markdown(
                '<div style="background:#EFF6FF;border-left:4px solid #1E3A8A;padding:8px 12px;border-radius:6px;margin-bottom:12px;font-size:13px;color:#1E3A8A;">'
                '<b>Administrator Session Verification</b> — Enter your 6-digit authenticator code to access the Admin Dashboard.'
                '</div>',
                unsafe_allow_html=True,
            )

            record = get_user_2fa_record(username)
            if not record or not record.get("encrypted_secret"):
                st.session_state["pending_2fa_mode"] = "setup"
                st.rerun()
                return

            allowed, lock_msg = check_2fa_rate_limit(record)
            if not allowed:
                st.error(f"🚫 {lock_msg}")
                if st.button("← Back to Login", use_container_width=True, key="admin_2fa_locked_back"):
                    cancel_pending_2fa()
                    st.rerun()
                return

            tab_totp, tab_recovery = st.tabs(["📱 Authenticator Code", "🔑 Recovery Code"])

            with tab_totp:
                with st.form("admin_2fa_verify_form", border=False):
                    totp_input = st.text_input(
                        "6-Digit Admin Authenticator Code",
                        placeholder="Enter 6-digit code",
                        max_chars=6,
                        key="admin_2fa_verify_code",
                    )
                    submit_totp = st.form_submit_button("Verify & Access Admin Dashboard", type="primary", use_container_width=True)

                    if submit_totp:
                        secret = decrypt_totp_secret(record["encrypted_secret"])
                        last_step = record.get("last_used_timestep")
                        is_ok, matched_step, err_msg = verify_totp_code(secret, totp_input, last_used_timestep=last_step)

                        if is_ok:
                            record_2fa_verification_result(username, True, matched_step=matched_step)
                            complete_2fa_login(pending_user)
                            st.success("Admin 2FA Verified! Redirecting...")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            new_failed, lock_until = compute_next_2fa_lockout(record.get("failed_attempts", 0))
                            record_2fa_verification_result(username, False, failed_attempts=new_failed, locked_until=lock_until)
                            if lock_until:
                                st.error("🚫 Too many failed 2FA attempts. Admin verification locked for 15 minutes.")
                            else:
                                st.error(f"❌ {err_msg} (Attempt {new_failed}/5)")

            with tab_recovery:
                st.caption("Use a single-use Admin recovery code (e.g. `ABCD-EFGH`).")
                with st.form("admin_2fa_recovery_form", border=False):
                    rec_input = st.text_input("Admin Recovery Code", placeholder="XXXX-XXXX", key="admin_2fa_recovery_code")
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
                            st.success("Recovery code accepted! Accessing Admin Dashboard...")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            new_failed, lock_until = compute_next_2fa_lockout(record.get("failed_attempts", 0))
                            record_2fa_verification_result(username, False, failed_attempts=new_failed, locked_until=lock_until)
                            st.error(f"❌ Invalid or already used recovery code. (Attempt {new_failed}/5)")

            st.divider()
            if st.button("← Back to Login", use_container_width=True, key="admin_verify_back_login"):
                cancel_pending_2fa()
                st.rerun()

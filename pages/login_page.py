import streamlit as st
import time
from database.queries import get_all_users, get_user_2fa_record
from services.auth_service import login_user, complete_2fa_login


def render_login_page():
    st.markdown("<h1 style='text-align: center; color: #4A90E2;'>Timesheet Portal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Login to manage time entries</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            all_users = get_all_users()
            username_list = ["Select Username"] + (all_users['username'].tolist() if not all_users.empty else ["admin"])

            def on_user_change():
                if "login_password" in st.session_state:
                    st.session_state["login_password"] = ""

            def format_username(uname):
                if uname == "Select Username":
                    return uname
                return uname.title()

            username = st.selectbox(
                "Username",
                username_list,
                format_func=format_username,
                on_change=on_user_change
            )

            with st.form("login_form", border=False):
                password = st.text_input("Password", type="password", key="login_password")
                submit = st.form_submit_button("Sign In", use_container_width=True, type="primary")

                if submit:
                    if username == "Select Username":
                        st.error("Please select a username.")
                    else:
                        res = login_user(username, password)
                        if "error" in res:
                            err_placeholder = st.empty()
                            err_placeholder.error(res["error"])
                            time.sleep(3)
                            err_placeholder.empty()
                            st.rerun()
                        else:
                            # Check if 2FA is enabled/required for this user
                            two_fa_rec = get_user_2fa_record(res.get("username"))
                            if two_fa_rec and two_fa_rec.get("two_fa_enabled"):
                                st.session_state["pending_2fa_user"] = res
                                has_verified_secret = bool(
                                    two_fa_rec.get("setup_verified") and two_fa_rec.get("encrypted_secret")
                                )
                                st.session_state["pending_2fa_mode"] = "verify" if has_verified_secret else "setup"
                                st.rerun()
                            else:
                                complete_2fa_login(res)
                                st.success("Login Successful!")
                                time.sleep(0.5)
                                st.rerun()

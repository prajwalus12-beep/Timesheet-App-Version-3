import streamlit as st
import random
import time
from database.queries import get_all_users
from services.auth_service import login_user
from utils.captcha_generator import generate_captcha_image


def _new_captcha():
    """Generate a new CAPTCHA code and its image, store in session state."""
    chars = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
    code = "".join(random.choices(chars, k=6))
    st.session_state.captcha_code = code
    st.session_state.captcha_image = generate_captcha_image(code)


def render_login_page():
    st.markdown("<h1 style='text-align: center; color: #4A90E2;'>Timesheet Portal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Login to manage time entries</p>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        with st.container(border=True):
            all_users = get_all_users()
            username_list = all_users['username'].tolist() if not all_users.empty else ["admin"]

            def on_user_change():
                if "login_password" in st.session_state:
                    st.session_state["login_password"] = ""

            username = st.selectbox("Username", username_list, on_change=on_user_change)

            # --- Image CAPTCHA ---
            if "captcha_code" not in st.session_state:
                _new_captcha()

            cap_col1, cap_col2 = st.columns([4, 1])
            with cap_col1:
                st.image(st.session_state.captcha_image, width="content")
            with cap_col2:
                if st.button("🔄", help="Refresh Captcha", key="refresh_captcha"):
                    _new_captcha()
                    st.rerun()

            captcha_input = st.text_input("Enter Captcha", placeholder="6-digit code")

            with st.form("login_form", border=False):
                password = st.text_input("Password", type="password", key="login_password")
                submit = st.form_submit_button("Sign In", use_container_width=True)

                if submit:
                    if captcha_input.upper() != st.session_state.captcha_code:
                        st.error("Invalid Captcha.")
                        _new_captcha()
                        time.sleep(2)
                        st.rerun()
                    else:
                        res = login_user(username, password)
                        if "error" in res:
                            _new_captcha()
                            err_placeholder = st.empty()
                            err_placeholder.error(res["error"])
                            time.sleep(8)
                            err_placeholder.empty()
                            st.rerun()
                        else:
                            st.session_state["logged_in"] = True
                            st.session_state["user"] = res
                            if "captcha_code" in st.session_state:
                                del st.session_state["captcha_code"]
                            if "captcha_image" in st.session_state:
                                del st.session_state["captcha_image"]
                            st.success("Login Successful!")
                            time.sleep(1)
                            st.rerun()

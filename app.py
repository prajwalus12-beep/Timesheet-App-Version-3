import streamlit as st
# Reloading...
from database.queries import init_db
from services.auth_service import check_login
from components.navbar import render_navbar
from pages.login_page import render_login_page
from pages.timesheet_page import render_timesheet_page
from pages.projects_page import render_projects_page
from pages.employees_page import render_employees_page
from pages.reports_page import render_reports_page
from pages.import_page import render_import_page
from config.constants import PAGE_CONFIG

# 1. Page Config
st.set_page_config(**PAGE_CONFIG)

# 2. Global Styling
with open("assets/css/style.css", "r") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# 3. Initialize Database
if "db_initialized" not in st.session_state:
    success, msg = init_db()
    if success: st.session_state["db_initialized"] = True
    else: st.error(msg)

# 4. Authentication
user = check_login()

if not user:
    render_login_page()
else:
    # 5. Routing
    if "page" not in st.session_state:
        st.session_state["page"] = "Timesheet Entries"
    
    # Navigation
    render_navbar(user)
    
    # Page Content
    page = st.session_state["page"]
    if page == "Timesheet Entries": render_timesheet_page(user)
    elif page == "Projects": render_projects_page()
    elif page == "Employees": render_employees_page(user)
    elif page == "Reports": render_reports_page(user)
    elif page == "Import Data": render_import_page()

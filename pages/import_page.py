import streamlit as st
import pandas as pd
from database.queries import import_employees, import_projects, import_assignments, import_project_updates
from utils.xlsx_export import build_clean_xlsx

def get_excel_download(df):
    return build_clean_xlsx(df)

def read_excel_or_csv(uploaded_file):
    """Read File depending on extension."""
    na_vals = [
        '#N/A', '#N/A N/A', '#NA', '-1.#IND', '-1.#QNAN', '-NaN', '-nan',
        '1.#IND', '1.#QNAN', '<NA>', 'N/A', 'NULL', 'NaN', 'n/a', 'nan', 'null', ''
    ]
    if uploaded_file.name.endswith('.csv'):
        try:
            return pd.read_csv(uploaded_file, keep_default_na=False, na_values=na_vals)
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, encoding='cp1252', keep_default_na=False, na_values=na_vals)
    else:
        return pd.read_excel(uploaded_file, keep_default_na=False, na_values=na_vals)

def render_import_page():
    st.subheader("Import Data", divider="blue")
    col_emp, col_proj = st.columns(2)
    col_assign, col_update = st.columns(2)
    
    with col_emp:
        st.markdown('<div class="table-container" style="padding: 20px;">', unsafe_allow_html=True)
        st.write("### 👥 Employees")
        uploaded_file = st.file_uploader("Upload Employees File", type=["xls", "xlsx", "csv"], key="emp_csv")
        if uploaded_file:
            df = read_excel_or_csv(uploaded_file)
            if st.button("Import Employees", type="primary"):
                success, msg = import_employees(df)
                st.success(msg) if success else st.error(msg)
        
        sample_emp = pd.DataFrame([["101", "John Doe", "U12345", "john.doe@example.com"]], columns=['a__Serial', 'Name', 'Slack ID', 'Email'])
        st.download_button("📥 Sample Employee Excel", get_excel_download(sample_emp), "sample_employees.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        st.info("Required: 'a__Serial', 'Name', 'Slack ID', 'Email'.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_proj:
        st.markdown('<div class="table-container" style="padding: 20px;">', unsafe_allow_html=True)
        st.write("### 🏗️ Projects")
        uploaded_file = st.file_uploader("Upload Projects File", type=["xls", "xlsx", "csv"], key="proj_csv")
        if uploaded_file:
            df = read_excel_or_csv(uploaded_file)
            if st.button("Import Projects", type="primary"):
                success, msg = import_projects(df)
                st.success(msg) if success else st.error(msg)
        
        sample_proj = pd.DataFrame([["P001", "High", "Website Redesign", "In progress", "Alice", "https://trello.com/b/123"]], columns=['Job No', 'Job Priority', 'Project', 'Status', 'Lead engineer', 'Trello'])
        st.download_button("📥 Sample Project Excel", get_excel_download(sample_proj), "sample_projects.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        st.info("Required: 'Job No', 'Job Priority', 'Project', 'Status', 'Lead engineer', 'Trello'.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_assign:
        st.markdown('<div class="table-container" style="padding: 20px;">', unsafe_allow_html=True)
        st.write("### 🔗 Assignments")
        uploaded_file = st.file_uploader("Upload Assignments File", type=["xls", "xlsx", "csv"], key="assign_csv")
        if uploaded_file:
            df = read_excel_or_csv(uploaded_file)
            if st.button("Import Assignments", type="primary"):
                success, msg = import_assignments(df)
                st.success(msg) if success else st.error(msg)
        
        sample_assign = pd.DataFrame([["101", "P001"]], columns=['Projects_Resources::a_EmployeeID', 'Projects_Resources::a_ProjectID'])
        st.download_button("📥 Sample Assignment Excel", get_excel_download(sample_assign), "sample_assignments.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        st.info("Required: 'Projects_Resources::a_EmployeeID', 'Projects_Resources::a_ProjectID'.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_update:
        st.markdown('<div class="table-container" style="padding: 20px;">', unsafe_allow_html=True)
        st.write("### 🔄 Update Projects")
        uploaded_file = st.file_uploader("Upload Update Projects File", type=["xls", "xlsx", "csv"], key="update_proj_csv")
        if uploaded_file:
            df = read_excel_or_csv(uploaded_file)
            if st.button("Import Update Project", type="primary"):
                success, msg = import_project_updates(df)
                if success:
                    st.success(msg)
                    st.session_state["import_success_msg"] = msg
                else:
                    st.error(msg)
        
        sample_update_proj = pd.DataFrame(
            [[
                "852", "1", "St Paul's College Trip Payment", "Not started", "Kritika Wadhwa", 
                "https://trello.com/...", "https://slack.com/...", "https://figma.com/...", 
                "14-05-2026", "15-05-2026", "Development", "1", "1", "1", "1", "166", "117"
            ]],
            columns=[
                'Job No', 'Job Priority', 'Priority', 'Search_Project', 'Lead engineer', 
                'Trello', 'Slack', 'Prototype', 'Start Date', 'Finish Date', 'Current Phase_g',
                'CheckBoxe BC', 'CheckBoxe Trello', 'CheckBoxe WA', 'CheckBoxe WS',
                'Estimated Days', 'Actual Days'
            ]
        )
        st.download_button("📥 Sample Update Project Excel", get_excel_download(sample_update_proj), "sample_update_projects.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        st.info("Required: 'Job No', 'Job Priority' (numeric), 'Priority' (used as Name if 'Project' is missing), 'Lead engineer'. Supports multiple aliases for Status, Phase, Dates, and Checkboxes (BC, Trello, WA, WS).")
        st.markdown('</div>', unsafe_allow_html=True)

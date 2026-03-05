import streamlit as st
import pandas as pd
from database.queries import import_employees, import_projects, import_assignments

def render_import_page():
    st.subheader("Import Data", divider="blue")
    col_emp, col_proj, col_assign = st.columns(3)
    
    with col_emp:
        st.markdown('<div class="table-container" style="padding: 20px;">', unsafe_allow_html=True)
        st.write("### 👥 Employees")
        uploaded_file = st.file_uploader("Upload Employees CSV", type="csv", key="emp_csv")
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            if st.button("Import Employees", type="primary"):
                success, msg = import_employees(df)
                st.success(msg) if success else st.error(msg)
        
        sample_emp = pd.DataFrame([["101", "John Doe", "U12345"]], columns=['a__Serial', 'Name', 'Slack ID'])
        st.download_button("📥 Sample Employee CSV", sample_emp.to_csv(index=False), "sample_employees.csv", "text/csv", use_container_width=True)
        st.info("Required: 'a__Serial', 'Name', 'Slack ID'.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_proj:
        st.markdown('<div class="table-container" style="padding: 20px;">', unsafe_allow_html=True)
        st.write("### 🏗️ Projects")
        uploaded_file = st.file_uploader("Upload Projects CSV", type="csv", key="proj_csv")
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            if st.button("Import Projects", type="primary"):
                success, msg = import_projects(df)
                st.success(msg) if success else st.error(msg)
        
        sample_proj = pd.DataFrame([["P001", "Website Redesign", "In progress"]], columns=['Job No', 'Project', 'Status'])
        st.download_button("📥 Sample Project CSV", sample_proj.to_csv(index=False), "sample_projects.csv", "text/csv", use_container_width=True)
        st.info("Required: 'Job No', 'Project', 'Status'.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_assign:
        st.markdown('<div class="table-container" style="padding: 20px;">', unsafe_allow_html=True)
        st.write("### 🔗 Assignments")
        uploaded_file = st.file_uploader("Upload Assignments CSV", type="csv", key="assign_csv")
        if uploaded_file:
            df = pd.read_csv(uploaded_file)
            if st.button("Import Assignments", type="primary"):
                success, msg = import_assignments(df)
                st.success(msg) if success else st.error(msg)
        
        sample_assign = pd.DataFrame([["101", "P001"]], columns=['Projects_Resources::a_EmployeeID', 'Projects_Resources::a_ProjectID'])
        st.download_button("📥 Sample Assignment CSV", sample_assign.to_csv(index=False), "sample_assignments.csv", "text/csv", use_container_width=True)
        st.info("Required: 'Projects_Resources::a_EmployeeID', 'Projects_Resources::a_ProjectID'.")
        st.markdown('</div>', unsafe_allow_html=True)

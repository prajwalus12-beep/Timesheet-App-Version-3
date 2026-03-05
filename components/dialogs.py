import streamlit as st
import datetime
import time
from database.queries import get_all_projects, add_timesheet_entry, update_timesheet_entry, verify_user_password, update_user_password
from services.auth_service import is_password_strong, hash_password

@st.dialog("Update Password")
def update_password_dialog(username):
    st.write(f"Update password for **{username}**")
    current_pwd = st.text_input("Current Password", type="password")
    new_pwd = st.text_input("New Password", type="password")
    confirm_pwd = st.text_input("Confirm Password", type="password")
    
    if st.button("Update Password", use_container_width=True):
        if not current_pwd or not new_pwd or not confirm_pwd:
            st.error("All fields are required.")
            return

        if not verify_user_password(username, current_pwd):
            st.error("Incorrect current password.")
            return

        if new_pwd != confirm_pwd:
            st.error("Passwords do not match.")
            return

        is_strong, msg = is_password_strong(new_pwd)
        if not is_strong:
            st.error(msg)
            return

        hashed = hash_password(new_pwd)
        update_user_password(username, hashed)
        st.success("Password updated successfully!")
        time.sleep(1.5)
        st.rerun()

@st.dialog("Add New Entry - TEST")
def entry_form_dialog(user, emp_options, current_emp_id):
    filter_type = st.radio("Project Type", ["Incomplete", "Complete"], horizontal=True, key="entry_filter_type_modal")
    
    with st.form("add_time_form"):
        user_option_key = next((k for k, v in emp_options.items() if v == current_emp_id), None)
        options = list(emp_options.keys())
        default_idx = options.index(user_option_key) if user_option_key in options else 0
        
        entry_emp = st.selectbox("Employee", options, index=default_idx, key="entry_emp_modal")
        today = datetime.date.today()
        end_of_week = today + datetime.timedelta(days=(6 - today.weekday()))
        col_d, col_h = st.columns(2)
        with col_d:
            entry_date = st.date_input("Date", datetime.date.today(), max_value=end_of_week, format="DD-MM-YYYY", key="entry_date_modal")
        with col_h:
            entry_hours = st.number_input("Hours", min_value=0.0, max_value=24.0, step=1.0, key="entry_hours_modal")
        
        all_projects_df = get_all_projects()
        filtered_projs = all_projects_df[all_projects_df['status'] == 'Complete'] if filter_type == "Complete" else all_projects_df[all_projects_df['status'] != 'Complete']
            
        form_proj_options = {f"{r['project_code']} - {r['project_name']}": (r['project_code'], r['project_name'], r.get('status', '')) for _, r in filtered_projs.iterrows()}
        proj_keys = list(form_proj_options.keys())
        entry_proj_key = st.selectbox("Project", ["None"] + proj_keys, key="entry_proj_modal")
        
        entry_phase = st.selectbox("Phase", ["Analysis", "Design", "Development", "Testing", "Deployement"], key="entry_phase_modal")
        submit_entry = st.form_submit_button("Submit Entry", type="primary")
        
        if submit_entry:
            if not entry_date or entry_date > end_of_week:
                st.warning("Cannot submit entry for a future week date.")
            elif entry_hours > 0 and entry_proj_key != "None":
                proj_data = form_proj_options[entry_proj_key]
                e_id = emp_options[entry_emp]
                e_name = entry_emp.split(" (")[0] 
                add_timesheet_entry(e_id, e_name, proj_data[0], proj_data[1], entry_date, entry_hours, entry_phase, proj_data[2])
                st.success("Entry Added!")
                st.rerun()
            elif entry_proj_key == "None": st.warning("Please select a project.")
            else: st.warning("Please enter valid hours.")

@st.dialog("Edit Entry")
def edit_form_dialog(entry_data, emp_options, current_emp_id, user_role):
    current_status = entry_data.get('project_status', '')
    default_filter = "Complete" if current_status == "Complete" else "Incomplete"
    filter_type = st.radio("Project Type", ["Incomplete", "Complete"], index=0 if default_filter == "Incomplete" else 1, horizontal=True, key="edit_filter_type_modal")
    
    with st.form("edit_time_form"):
        current_emp_label = next((k for k, v in emp_options.items() if v == entry_data['emp_id']), None)
        options = list(emp_options.keys())
        default_idx = options.index(current_emp_label) if current_emp_label in options else 0
        entry_emp = st.selectbox("Employee", options, index=default_idx, key="edit_emp_modal")

        today = datetime.date.today()
        end_of_week = today + datetime.timedelta(days=(6 - today.weekday()))
        col_d, col_h = st.columns(2)
        with col_d:
            row_date = entry_data['date']
            if isinstance(row_date, str): row_date = datetime.datetime.strptime(row_date, '%Y-%m-%d').date()
            entry_date = st.date_input("Date", row_date, max_value=end_of_week, format="DD-MM-YYYY", key="edit_date_modal")
        with col_h:
            entry_hours = st.number_input("Hours", min_value=0.0, max_value=24.0, step=1.0, value=float(entry_data['hours']), key="edit_hours_modal")
        
        all_projects_df = get_all_projects()
        filtered_projs = all_projects_df[all_projects_df['status'] == 'Complete'] if filter_type == "Complete" else all_projects_df[all_projects_df['status'] != 'Complete']
            
        form_proj_options = {f"{r['project_code']} - {r['project_name']}": (r['project_code'], r['project_name'], r.get('status', '')) for _, r in filtered_projs.iterrows()}
        proj_keys = list(form_proj_options.keys())
        current_proj_code = entry_data.get('project_code', '')
        default_proj_idx = next((i + 1 for i, pk in enumerate(proj_keys) if form_proj_options[pk][0] == current_proj_code), 0)
                
        entry_proj_key = st.selectbox("Project", ["None"] + proj_keys, index=default_proj_idx, key="edit_proj_modal")
        
        phase_options = ["Analysis", "Design", "Development", "Testing", "Deployement"]
        phase_map = {"Analysis": "1", "Design": "2", "Development": "3", "Testing": "4", "Deployement": "5"}
        rev_phase_map = {v: k for k, v in phase_map.items()}
        current_phase_label = rev_phase_map.get(str(entry_data.get('Phase', '1')), "Analysis")
        default_phase_idx = phase_options.index(current_phase_label) if current_phase_label in phase_options else 0
        entry_phase = st.selectbox("Phase", phase_options, index=default_phase_idx, key="edit_phase_modal")

        submit_update = st.form_submit_button("Update Entry", type="primary")
        if submit_update:
            if not entry_date or entry_date > end_of_week:
                st.warning("Cannot update entry to a future week date.")
            elif entry_hours > 0 and entry_proj_key != "None":
                proj_data = form_proj_options[entry_proj_key]
                e_id = emp_options[entry_emp]
                e_name = entry_emp.split(" (")[0] 
                update_timesheet_entry(entry_data['id'], e_id, e_name, proj_data[0], proj_data[1], entry_date, entry_hours, entry_phase, proj_data[2])
                st.success("Entry Updated!")
                st.rerun()
            elif entry_proj_key == "None": st.warning("Please select a project.")
            else: st.warning("Please enter valid hours.")

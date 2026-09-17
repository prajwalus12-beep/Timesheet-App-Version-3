import streamlit as st
import datetime
import time
import json
import pandas as pd
import streamlit.components.v1 as components
from database.queries import (
    get_all_projects, add_timesheet_entry, update_timesheet_entry, verify_user_password,
    update_user_password, has_leave_for_date, add_leave_entries,
    add_holiday, update_holiday, delete_holiday, import_holidays
)
from services.auth_service import is_password_strong, encrypt_data

def format_proj_key(code, name, max_len=40):
    name_str = str(name)
    trunc_name = name_str[:max_len] + '...' if len(name_str) > max_len else name_str
    return f"{code} - {trunc_name}"


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

        encrypted = encrypt_data(new_pwd)
        update_user_password(username, encrypted)
        st.success("Password updated successfully!")
        time.sleep(1.5)
        st.rerun()


@st.dialog("Add New Entry")
def entry_form_dialog(user, emp_options, current_emp_id):
    # Detect if dialog was just opened (widgets are cleared when dialog is closed)
    if "entry_filter_type_modal" not in st.session_state:
        st.session_state._entry_proj_visible = 20
        st.session_state.pop('_entry_selected_proj_key', None)
        
    def reset_visible():
        st.session_state._entry_proj_visible = 20
        st.session_state.pop('_entry_selected_proj_key', None)

    filter_type = st.radio("Project Status", ["In-Progress", "Complete"], horizontal=True, key="entry_filter_type_modal", on_change=reset_visible, help="Select In-Progress to view active projects (In-testing, In Progress, Not Started, Awaiting Info, To Be Deployed) or Select Complete to view completed projects only on Project Selection list. The project list is synced with the latest status from the Project V1 page.")
    
    # Fetch and filter projects by status
    all_projects_df = get_all_projects()
    if filter_type == "Complete":
        filtered_projs = all_projects_df[all_projects_df['status'] == 'Complete']
    else:
        filtered_projs = all_projects_df[all_projects_df['status'] != 'Complete']
    
    # Build project options dict from ALL filtered projects
    all_proj_options = {format_proj_key(r['project_code'], r['project_name']): (r['project_code'], r['project_name'], r.get('status', '')) for _, r in filtered_projs.iterrows()}
    all_proj_keys = list(all_proj_options.keys())
    # Sort descending numerically by job number (project code)
    def _sort_key(k):
        code = k.split(" - ")[0]
        try: return float(code)
        except ValueError: return 0.0
    all_proj_keys.sort(key=_sort_key, reverse=True)
    
    # Use a container instead of a form so interactive elements (like "Show More") run instantly
    with st.container(border=True):
        user_option_key = next((k for k, v in emp_options.items() if v == current_emp_id), None)
        options = list(emp_options.keys())
        default_idx = options.index(user_option_key) if user_option_key in options else 0
        
        entry_emp = st.selectbox("Employee", options, index=default_idx, disabled=True, key="entry_emp_modal")
        
        today = datetime.date.today()
        end_of_week = today + datetime.timedelta(days=(6 - today.weekday()))
        col_d, col_h = st.columns(2)
        with col_d:
            entry_date = st.date_input("Date", datetime.date.today(), max_value=end_of_week, format="DD-MM-YYYY", key="entry_date_modal")
        with col_h:
            entry_hours = st.number_input("Hours", min_value=0.0, max_value=24.0, value=4.0, step=1.0, key="entry_hours_modal")
        
        # --- Custom Project Picker ---
        st.markdown("**Project Selection**")
        
        search_query = st.text_input("🔍 Search Project (type to filter all)", key="entry_proj_search", placeholder="Type project name or code...")
        
        if search_query:
            q = search_query.lower()
            filtered_keys = [k for k in all_proj_keys if q in k.lower()]
        else:
            filtered_keys = []
            
        total_records = len(filtered_keys)
        
        selected_key = st.session_state.get('_entry_selected_proj_key', 'None')
        if selected_key != "None":
            full_name = f"{all_proj_options[selected_key][0]} - {all_proj_options[selected_key][1]}" if selected_key in all_proj_options else selected_key
            st.info(f"📋 **Selected Project:** {full_name}")
        else:
            st.warning("⚠️ No project selected")
            
        display_keys = filtered_keys[:20]
        
        if not search_query:
            st.caption("Please enter a search query above to find projects.")
        elif total_records == 0:
            st.caption("No projects found.")
        else:
            st.caption(f"Showing 1–{len(display_keys)} of {total_records} projects")
            
        def handle_entry_radio():
            val = st.session_state.entry_radio_modal
            if val is not None:
                st.session_state._entry_selected_proj_key = val
            
        with st.container(border=True, height=250):
            st.markdown(
                """
                <style>
                div[data-testid="stRadio"] label p {
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            if display_keys:
                selected_idx = display_keys.index(selected_key) if selected_key in display_keys else None
                
                st.radio(
                    "Select a project",
                    options=display_keys,
                    index=selected_idx,
                    key="entry_radio_modal",
                    on_change=handle_entry_radio,
                    label_visibility="collapsed"
                )
                
                # Inject JS to add title attribute for tooltips
                tooltip_map = {k: f"{all_proj_options[k][0]} - {all_proj_options[k][1]}" for k in display_keys}
                js_code = f"""
                <script>
                setTimeout(function() {{
                    const parent = window.parent.document;
                    if (!parent) return;
                    const mapping = {json.dumps(tooltip_map)};
                    const labels = parent.querySelectorAll('div[data-testid="stRadio"] label p');
                    labels.forEach(el => {{
                        const txt = el.innerText.trim();
                        if (mapping[txt]) {{
                            el.parentElement.parentElement.setAttribute('title', mapping[txt]);
                        }}
                    }});
                }}, 300);
                </script>
                """
                components.html(js_code, height=0, width=0)
                
        entry_proj_key = selected_key
        # -----------------------------------------------
        
        # Add Entry Form - Comment is mandatory
        entry_comment = st.text_area("Comment", max_chars=400, placeholder="Enter work details, update summary, or notes...", key="entry_comment_modal")
        
        entry_phase = st.selectbox("Phase", ["Analysis", "Design", "Development", "Testing", "Deployement", "Support"], key="entry_phase_modal")
        
        submit_entry = st.button("Submit Entry", type="primary")
        
        if submit_entry:
            # Validation: Comment must not be empty after stripping whitespace
            if not entry_comment.strip():
                st.warning("Comment is required. Please provide details before submitting.")
                st.stop()
            if not entry_date or entry_date > end_of_week:
                st.warning("Cannot submit entry for a future week date.")
            elif has_leave_for_date(emp_options[entry_emp], entry_date):
                st.warning("This date is registered as approved leave. Standard work hours cannot be logged for leave dates.")
            elif entry_hours <= 0:
                st.warning("Please enter valid hours.")
            elif entry_proj_key == "None":
                st.error("⚠️ No project selected — pick one from the list above")
            elif entry_proj_key not in all_proj_options:
                # Key exists in session but doesn't match current filter (e.g. filter changed)
                st.error("⚠️ Selected project is no longer in the current filter. Please re-select the project.")
                st.session_state.pop('_entry_selected_proj_key', None)
                st.stop()
            else:
                with st.spinner("Saving entry..."):
                    proj_data = all_proj_options[entry_proj_key]
                    e_id = emp_options[entry_emp]
                    e_name = entry_emp.split(" (")[0]
                    success, err = add_timesheet_entry(e_id, e_name, proj_data[0], proj_data[1], entry_date, entry_hours, entry_phase, proj_data[2], entry_comment)
                    if success:
                        st.session_state.pop('_entry_selected_proj_key', None)
                        st.toast("✅ Entry added successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to add entry: {err}")

@st.dialog("Add Multiple Entries")
def multiple_entry_dialog(user, emp_labels, current_emp_id):
    """Dialog to add multiple timesheet entries at once.
    The user can specify how many rows to add, then fill each row's fields.
    All rows are submitted in a single batch.
    """
    st.write("## Add Multiple Timesheet Entries")
    num_rows = st.number_input("Number of entries", min_value=1, max_value=20, value=2, step=1)
    entries = []
    for i in range(int(num_rows)):
        st.markdown(f"### Entry {i+1}")
        # Employee selection – same as single entry
        entry_emp = st.selectbox(f"Employee {i+1}", list(emp_labels.keys()), key=f"mult_emp_{i}")
        # Project selection – reuse project picker logic (simplified)
        all_projs = get_all_projects()
        proj_options = {f"{r['project_code']} - {r['project_name']}": (r['project_code'], r['project_name'], r.get('status','')) for _, r in all_projs.iterrows()}
        proj_key = st.selectbox(f"Project {i+1}", list(proj_options.keys()), key=f"mult_proj_{i}")
        # Date, Hours, Phase, Comment
        today = datetime.date.today()
        end_of_week = today + datetime.timedelta(days=(6 - today.weekday()))
        entry_date = st.date_input(f"Date {i+1}", max_value=end_of_week, key=f"mult_date_{i}")
        entry_hours = st.number_input(f"Hours {i+1}", min_value=0.0, max_value=24.0, step=0.5, key=f"mult_hours_{i}")
        phase_options = ["Analysis", "Design", "Development", "Testing", "Deployement", "Support"]
        entry_phase = st.selectbox(f"Phase {i+1}", phase_options, key=f"mult_phase_{i}")
        entry_comment = st.text_area(f"Comment {i+1}", max_chars=400, placeholder="Enter work details...", key=f"mult_comment_{i}")
        entries.append({
            "emp_key": entry_emp,
            "proj_key": proj_key,
            "date": entry_date,
            "hours": entry_hours,
            "phase": entry_phase,
            "comment": entry_comment,
        })
    if st.button("Submit All Entries", type="primary"):
        # Validate all entries
        for idx, e in enumerate(entries):
            if not e["comment"].strip():
                st.warning(f"Entry {idx+1}: Comment is required.")
                st.stop()
            if e["date"] > end_of_week:
                st.warning(f"Entry {idx+1}: Date cannot be in future week.")
                st.stop()
            if has_leave_for_date(emp_labels[e["emp_key"]], e["date"]):
                st.warning(f"Entry {idx+1}: This date is registered as approved leave. Standard work hours cannot be logged for leave dates.")
                st.stop()
            if e["hours"] <= 0:
                st.warning(f"Entry {idx+1}: Hours must be > 0.")
                st.stop()
            if e["proj_key"] == "None":
                st.warning(f"Entry {idx+1}: Project not selected.")
                st.stop()
        # All validations passed – insert rows
        with st.spinner(f"Saving {len(entries)} entries..."):
            all_ok = True
            for e in entries:
                proj_data = proj_options[e["proj_key"]]
                e_id = emp_labels[e["emp_key"]]
                e_name = e["emp_key"].split(" (")[0]
                ok, err = add_timesheet_entry(e_id, e_name, proj_data[0], proj_data[1], e["date"], e["hours"], e["phase"], proj_data[2], e["comment"])
                if not ok:
                    all_ok = False
                    st.error(f"Error adding entry: {err}")
            if all_ok:
                st.toast(f"✅ Added {len(entries)} entries successfully!")
                st.rerun()

@st.dialog("Edit Entry")
def edit_form_dialog(entry_data, emp_options, current_emp_id, user_role):
    if "edit_filter_type_modal" not in st.session_state:
        st.session_state._edit_proj_page = 0
        current_proj_code = entry_data.get('project_code', '')
        current_proj_name = entry_data.get('project_name', '')
        if current_proj_code:
            st.session_state._edit_selected_proj_key = format_proj_key(current_proj_code, current_proj_name)
        else:
            st.session_state._edit_selected_proj_key = 'None'

    def reset_edit_visible():
        st.session_state._edit_proj_page = 0

    current_status = entry_data.get('project_status', '')
    default_filter = "Complete" if current_status == "Complete" else "Inprogress"
    filter_type = st.radio("Project Type", ["Inprogress", "Complete"], index=0 if default_filter == "Inprogress" else 1, horizontal=True, key="edit_filter_type_modal", on_change=reset_edit_visible)
    
    # Fetch and filter projects
    all_projects_df = get_all_projects()
    filtered_projs = all_projects_df[all_projects_df['status'] == 'Complete'] if filter_type == "Complete" else all_projects_df[all_projects_df['status'] != 'Complete']
    
    all_proj_options = {format_proj_key(r['project_code'], r['project_name']): (r['project_code'], r['project_name'], r.get('status', '')) for _, r in filtered_projs.iterrows()}
    
    selected_key = st.session_state.get('_edit_selected_proj_key', 'None')
    if selected_key != 'None' and selected_key not in all_proj_options:
        prev_proj_code = selected_key.split(' - ')[0]
        current_proj_row = all_projects_df[all_projects_df['project_code'] == prev_proj_code]
        if not current_proj_row.empty:
            r = current_proj_row.iloc[0]
            new_key = format_proj_key(r['project_code'], r['project_name'])
            all_proj_options[new_key] = (r['project_code'], r['project_name'], r.get('status', ''))
            if selected_key != new_key:
                st.session_state._edit_selected_proj_key = new_key
                selected_key = new_key
            
    all_proj_keys = list(all_proj_options.keys())
    def _sort_key(k):
        code = k.split(" - ")[0]
        try: return float(code)
        except ValueError: return 0.0
    all_proj_keys.sort(key=_sort_key, reverse=True)
    
    # Convert form to container so pagination buttons work instantly
    with st.container(border=True):
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
        
        # --- Custom Project Picker ---
        st.markdown("**Project Selection**")
        
        search_query = st.text_input("🔍 Search Project (type to filter all)", key="edit_proj_search", placeholder="Type project name or code...")
        
        if search_query:
            q = search_query.lower()
            filtered_keys = [k for k in all_proj_keys if q in k.lower()]
        else:
            filtered_keys = []
            
        total_records = len(filtered_keys)
            
        if selected_key != "None":
            full_name = f"{all_proj_options[selected_key][0]} - {all_proj_options[selected_key][1]}" if selected_key in all_proj_options else selected_key
            st.info(f"📋 **Selected Project:** {full_name}")
        else:
            st.warning("⚠️ No project selected")
            
        display_keys = filtered_keys[:20]
        
        if not search_query:
            st.caption("Please enter a search query above to find projects.")
        elif total_records == 0:
            st.caption("No projects found.")
        else:
            st.caption(f"Showing 1–{len(display_keys)} of {total_records} projects")
            
        def handle_edit_radio():
            val = st.session_state.edit_radio_modal
            if val is not None:
                st.session_state._edit_selected_proj_key = val
                
        with st.container(border=True, height=250):
            st.markdown(
                """
                <style>
                div[data-testid="stRadio"] label p {
                    white-space: nowrap;
                    overflow: hidden;
                    text-overflow: ellipsis;
                }
                </style>
                """,
                unsafe_allow_html=True
            )
            if display_keys:
                selected_idx = display_keys.index(selected_key) if selected_key in display_keys else None
                
                st.radio(
                    "Select a project",
                    options=display_keys,
                    index=selected_idx,
                    key="edit_radio_modal",
                    on_change=handle_edit_radio,
                    label_visibility="collapsed"
                )
                
                # Inject JS to add title attribute for tooltips
                tooltip_map = {k: f"{all_proj_options[k][0]} - {all_proj_options[k][1]}" for k in display_keys}
                js_code = f"""
                <script>
                setTimeout(function() {{
                    const parent = window.parent.document;
                    if (!parent) return;
                    const mapping = {json.dumps(tooltip_map)};
                    const labels = parent.querySelectorAll('div[data-testid="stRadio"] label p');
                    labels.forEach(el => {{
                        const txt = el.innerText.trim();
                        if (mapping[txt]) {{
                            el.parentElement.parentElement.setAttribute('title', mapping[txt]);
                        }}
                    }});
                }}, 300);
                </script>
                """
                components.html(js_code, height=0, width=0)
                
        entry_proj_key = selected_key
        # -----------------------------------------------
        
        current_comment = entry_data.get('comment', '') if pd.notna(entry_data.get('comment', '')) else ''
        
        # Edit Entry Form - Comment is mandatory
        entry_comment = st.text_area("Comment", value=current_comment, max_chars=400, placeholder="Enter work details, update summary, or notes...", key="edit_comment_modal")
        
        phase_options = ["Analysis", "Design", "Development", "Testing", "Deployement", "Support"]
        phase_map = {"Analysis": "1", "Design": "2", "Development": "3", "Testing": "4", "Deployement": "5", "Support": "6"}
        rev_phase_map = {v: k for k, v in phase_map.items()}
        current_phase_label = rev_phase_map.get(str(entry_data.get('Phase', '1')), "Analysis")
        default_phase_idx = phase_options.index(current_phase_label) if current_phase_label in phase_options else 0
        entry_phase = st.selectbox("Phase", phase_options, index=default_phase_idx, key="edit_phase_modal")

        submit_update = st.button("Update Entry", type="primary")
        if submit_update:
            # Validation: Comment must not be empty after stripping whitespace
            if not entry_comment.strip():
                st.warning("Comment is required to update the entry.")
                st.stop()
            if not entry_date or entry_date > end_of_week:
                st.warning("Cannot update entry to a future week date.")
            elif entry_proj_key != "None" and entry_proj_key in all_proj_options and not str(all_proj_options[entry_proj_key][0]).startswith("LEAVE-") and has_leave_for_date(emp_options[entry_emp], entry_date):
                st.warning("This date is registered as approved leave. Standard work hours cannot be logged for leave dates.")
            elif entry_hours <= 0:
                st.warning("Please enter valid hours.")
            elif entry_proj_key == "None":
                st.error("⚠️ No project selected")
            elif entry_proj_key not in all_proj_options:
                # Key exists in session but doesn't match current filter (e.g. filter changed)
                st.error("⚠️ Selected project is no longer in the current filter. Please re-select the project.")
                st.session_state.pop('_edit_selected_proj_key', None)
                st.stop()
            else:
                with st.spinner("Updating entry..."):
                    proj_data = all_proj_options[entry_proj_key]
                    e_id = emp_options[entry_emp]
                    e_name = entry_emp.split(" (")[0]
                    success, err = update_timesheet_entry(entry_data['id'], e_id, e_name, proj_data[0], proj_data[1], entry_date, entry_hours, entry_phase, proj_data[2], entry_comment)
                    if success:
                        st.session_state.pop('_edit_selected_proj_key', None)
                        st.toast("✅ Entry updated successfully!")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to update entry: {err}")

@st.dialog("Add Leave Request")
def add_leave_dialog(user, emp_options, current_emp_id):
    st.markdown("**Excludes date from timesheet log & export**")
    user_option_key = next((k for k, v in emp_options.items() if v == current_emp_id), None)
    options = list(emp_options.keys())
    default_idx = options.index(user_option_key) if user_option_key in options else 0
    
    leave_emp = st.selectbox("Employee Name", options, index=default_idx, disabled=not (user.get("role") == "admin"), key="leave_emp_modal")
    leave_type = st.selectbox("Leave Type", ["Casual Leave", "Sick Leave", "Earned/Paid Leave", "Unpaid Leave"], key="leave_type_modal")
    
    col_start, col_end = st.columns(2)
    with col_start:
        start_date = st.date_input("Start Date", datetime.date.today(), format="DD-MM-YYYY", key="leave_start_modal")
    with col_end:
        end_date = st.date_input("End Date", datetime.date.today(), format="DD-MM-YYYY", key="leave_end_modal")
        
    reason = st.text_area("Reason / Notes", placeholder="e.g. Personal errand / Doctor appointment", key="leave_reason_modal")
    
    st.info("⚙️ **Automatic Exclusions Applied:**\n\n- Date will be locked against regular work time logging.\n- Will be omitted from client billable Excel reports.\n- Suppresses automated 'Timesheet Missing' emails for this date.")
    
    if st.button("Confirm & Add Leave", type="primary", use_container_width=True):
        if end_date < start_date:
            st.error("End Date cannot be before Start Date.")
            st.stop()
        if not reason.strip():
            st.warning("Reason / Notes is required.")
            st.stop()
            
        with st.spinner("Adding leave..."):
            e_id = emp_options[leave_emp]
            e_name = leave_emp.split(" (")[0]
            success, err = add_leave_entries(e_id, e_name, leave_type, start_date, end_date, reason)
            if success:
                st.toast("✅ Leave added successfully!")
                st.rerun()
            else:
                st.error(f"❌ Failed to add leave: {err}")

@st.dialog("Edit Leave Entry")
def edit_leave_dialog(entry_data, emp_options, current_emp_id, user_role):
    st.markdown("**Edit Leave Details**")
    current_emp_label = next((k for k, v in emp_options.items() if v == entry_data.get('emp_id')), None)
    options = list(emp_options.keys())
    default_emp_idx = options.index(current_emp_label) if current_emp_label in options else 0
    leave_emp = st.selectbox("Employee Name", options, index=default_emp_idx, disabled=(user_role != "admin"), key="edit_leave_emp_modal")
    
    code_to_type = {
        "LEAVE-CL": "Casual Leave",
        "LEAVE-SL": "Sick Leave",
        "LEAVE-PL": "Earned/Paid Leave",
        "LEAVE-UL": "Unpaid Leave"
    }
    current_code = str(entry_data.get('project_code', ''))
    default_type = code_to_type.get(current_code, "Casual Leave")
    leave_types = ["Casual Leave", "Sick Leave", "Earned/Paid Leave", "Unpaid Leave"]
    default_type_idx = leave_types.index(default_type) if default_type in leave_types else 0
    leave_type = st.selectbox("Leave Type", leave_types, index=default_type_idx, key="edit_leave_type_modal")
    
    today = datetime.date.today()
    end_of_week = today + datetime.timedelta(days=(6 - today.weekday()))
    col_d, col_h = st.columns(2)
    with col_d:
        row_date = entry_data.get('date')
        if isinstance(row_date, str):
            row_date = datetime.datetime.strptime(row_date, '%Y-%m-%d').date()
        entry_date = st.date_input("Date", row_date, max_value=end_of_week, format="DD-MM-YYYY", key="edit_leave_date_modal")
    with col_h:
        entry_hours = st.number_input("Hours", min_value=0.0, max_value=24.0, step=1.0, value=float(entry_data.get('hours', 8.0)), key="edit_leave_hours_modal")
        
    current_comment = entry_data.get('comment', '') or ''
    reason = st.text_area("Reason / Notes", value=str(current_comment), placeholder="e.g. Personal errand / Doctor appointment", key="edit_leave_reason_modal")
    
    st.info("⚙️ Leave dates are excluded from regular hours & billable Excel exports.")
    
    if st.button("Save Changes", type="primary", use_container_width=True, key="save_leave_edit_btn"):
        if not reason.strip():
            st.warning("Reason / Notes is required.")
            st.stop()
            
        type_to_proj = {
            "Casual Leave": ("LEAVE-CL", "Casual Leave (CL)"),
            "Sick Leave": ("LEAVE-SL", "Sick Leave (SL)"),
            "Earned/Paid Leave": ("LEAVE-PL", "Earned/Paid Leave (PL)"),
            "Unpaid Leave": ("LEAVE-UL", "Unpaid Leave (UL)")
        }
        proj_code, proj_name = type_to_proj.get(leave_type, ("LEAVE-OTHER", f"Leave ({leave_type})"))
        e_id = emp_options[leave_emp]
        e_name = leave_emp.split(" (")[0]
        
        with st.spinner("Updating leave entry..."):
            success, err = update_timesheet_entry(
                entry_id=entry_data['id'],
                emp_id=e_id,
                emp_name=e_name,
                project_code=proj_code,
                project_name=proj_name,
                date=entry_date,
                hours=entry_hours,
                phase="Analysis",
                project_status="Approved Leave",
                comment=reason
            )
            if success:
                st.toast("✅ Leave entry updated successfully!")
                st.rerun()
            else:
                st.error(f"❌ Failed to update leave: {err}")


# ==============================================================================
# Holiday Dialogs
# ==============================================================================

@st.dialog("Add New Holiday")
def add_holiday_dialog(user=None):
    """Dialog for administrative creation of a new holiday."""
    st.markdown("Enter the holiday details below. Configured holidays apply to **all employees**.")
    
    col_d, col_n = st.columns([1.2, 2.0])
    with col_d:
        h_date = st.date_input("Holiday Date", value=datetime.date.today(), format="DD-MM-YYYY", key="add_h_date_input")
    with col_n:
        h_name = st.text_input("Holiday Name", placeholder="e.g. Gandhi Jayanti", max_chars=255, key="add_h_name_input")
        
    st.caption("ℹ️ A unique constraint prevents duplicate holidays on the same date.")
    
    col_save, col_cancel = st.columns(2)
    with col_save:
        if st.button("💾 Save Holiday", type="primary", use_container_width=True, key="save_add_holiday_btn"):
            if not h_name.strip():
                st.error("❌ Holiday Name is required.")
                st.stop()
                
            creator = (user.get('employee_id') or user.get('username', 'admin')) if user else 'admin'
            with st.spinner("Saving holiday..."):
                success, msg = add_holiday(h_date, h_name.strip(), created_by=creator)
                if success:
                    st.toast(f"✅ Holiday '{h_name.strip()}' added successfully!", icon="🏖️")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")


@st.dialog("Edit Holiday")
def edit_holiday_dialog(holiday_data, user=None):
    """Dialog for editing an existing holiday."""
    st.markdown(f"Editing holiday: **{holiday_data.get('holiday_name')}**")
    
    current_date_val = holiday_data.get('holiday_date')
    if isinstance(current_date_val, str):
        try:
            current_date_val = datetime.date.fromisoformat(current_date_val)
        except Exception:
            current_date_val = datetime.date.today()
            
    col_d, col_n = st.columns([1.2, 2.0])
    with col_d:
        new_date = st.date_input("Holiday Date", value=current_date_val, format="DD-MM-YYYY", key=f"edit_h_date_{holiday_data['id']}")
    with col_n:
        new_name = st.text_input("Holiday Name", value=holiday_data.get('holiday_name', ''), max_chars=255, key=f"edit_h_name_{holiday_data['id']}")
        
    col_update, col_cancel = st.columns(2)
    with col_update:
        if st.button("💾 Update Holiday", type="primary", use_container_width=True, key=f"update_h_btn_{holiday_data['id']}"):
            if not new_name.strip():
                st.error("❌ Holiday Name is required.")
                st.stop()
                
            updater = (user.get('employee_id') or user.get('username', 'admin')) if user else 'admin'
            with st.spinner("Updating holiday..."):
                success, msg = update_holiday(holiday_data['id'], new_date, new_name.strip(), updated_by=updater)
                if success:
                    st.toast(f"✅ Holiday updated successfully!", icon="🏖️")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")


@st.dialog("Import Holiday Sheet", width="large")
def import_holiday_dialog(user=None):
    """Dialog for importing a holiday file (.xlsx, .xls, .csv)."""
    st.markdown("Upload an Excel or CSV file containing configured company holidays.")
    st.caption("Required columns: `date` and `holiday name`.")
    
    from utils.xlsx_export import build_clean_xlsx
    
    # Download sample template
    sample_df = pd.DataFrame([
        ["2026-10-02", "Gandhi Jayanti"],
        ["2026-12-25", "Christmas"]
    ], columns=['date', 'holiday name'])
    sample_bytes = build_clean_xlsx(sample_df, sheet_name="Holidays")
    
    col_down, _ = st.columns([1.5, 2.5])
    with col_down:
        st.download_button(
            "📥 Download Sample Template", 
            sample_bytes, 
            "sample_holidays.xlsx", 
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
            use_container_width=True,
            key="dl_sample_holiday_btn"
        )
    
    st.divider()
    
    uploaded_file = st.file_uploader("Choose Holiday Sheet", type=["xlsx", "xls", "csv"], key="import_holiday_uploader")
    
    if uploaded_file:
        from pages.import_page import read_excel_or_csv
        try:
            df = read_excel_or_csv(uploaded_file)
            st.write(f"📄 **File preview:** ({len(df)} rows detected)")
            st.dataframe(df.head(10), use_container_width=True)
            
            if st.button("🚀 Import Holidays", type="primary", use_container_width=True, key="exec_import_holiday_btn"):
                creator = (user.get('employee_id') or user.get('username', 'admin')) if user else 'admin'
                with st.spinner("Validating and importing holidays..."):
                    success, msg, details = import_holidays(df, created_by=creator)
                    if success:
                        st.toast(f"✅ {msg}", icon="🎉")
                        time.sleep(1.0)
                        st.rerun()
                    else:
                        st.error(f"❌ {msg}")
                        if "errors" in details:
                            with st.expander("🔍 View Row-Level Validation Errors", expanded=True):
                                for err in details["errors"]:
                                    st.markdown(f"- {err}")
        except Exception as e:
            st.error(f"❌ Could not read file: {e}")


@st.dialog("Confirm Delete Holiday")
def confirm_delete_holiday_dialog(holiday_data, user=None):
    """Confirmation modal before deleting a holiday."""
    h_name = holiday_data.get('holiday_name')
    h_date = holiday_data.get('holiday_date')
    st.warning(f"Are you sure you want to delete the holiday **{h_name}** on **{h_date}**?")
    st.info("ℹ️ Once deleted, this holiday will no longer appear on employee timesheets. Historical timesheet work logs remain unaffected.")
    
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("🗑️ Yes, Delete", type="primary", use_container_width=True, key=f"confirm_del_h_{holiday_data['id']}"):
            updater = (user.get('employee_id') or user.get('username', 'admin')) if user else 'admin'
            with st.spinner("Deleting holiday..."):
                success, msg = delete_holiday(holiday_data['id'], soft_delete=True, updated_by=updater)
                if success:
                    st.toast(f"✅ Holiday '{h_name}' deleted.", icon="🗑️")
                    st.rerun()
                else:
                    st.error(f"❌ {msg}")
    with col_no:
        if st.button("Cancel", use_container_width=True, key=f"cancel_del_h_{holiday_data['id']}"):
            st.rerun()


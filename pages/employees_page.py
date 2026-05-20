import streamlit as st
from database.queries import get_all_users, add_employee, update_employee
from services.auth_service import decrypt_data
import re

def is_valid_email(email):
    if not email: return True
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def render_employees_page(user):
    st.subheader("Employees", divider="blue")
    
    tab1, tab2, tab3 = st.tabs(["👥 Employee List", "➕ Add Employee", "✏️ Edit Employee"])
    
    users = get_all_users()
    
    with tab1:
        st.write("### Employee Directory")
        search = st.text_input("🔍 Search by Name, Email, or Slack ID")
        
        if not users.empty:
            display_users = users.copy()
            if search:
                search = search.lower()
                display_users = display_users[
                    display_users['employee_name'].fillna('').astype(str).str.lower().str.contains(search, na=False) |
                    display_users['email'].fillna('').astype(str).str.lower().str.contains(search, na=False) |
                    display_users['slack_id'].fillna('').astype(str).str.lower().str.contains(search, na=False)
                ]
            
            # Sort by Name
            display_users = display_users.sort_values(by='employee_name')
            
            st.markdown('<div class="table-container">', unsafe_allow_html=True)
            st.markdown('<div class="table-header"><div style="flex: 2;">Username</div><div style="flex: 3;">Employee Name</div><div style="flex: 3;">Email</div><div style="flex: 2;">Slack ID</div><div style="flex: 2;">Password</div></div>', unsafe_allow_html=True)
            for _, row in display_users.iterrows():
                st.markdown('<div class="table-row">', unsafe_allow_html=True)
                c1, c2, c_email, c_slack, c3 = st.columns([2, 3, 3, 2, 2])
                c1.markdown(f'<div class="table-cell">{row["username"]}</div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="table-cell"><b>{row["employee_name"] if row["employee_name"] else "N/A"}</b></div>', unsafe_allow_html=True)
                c_email.markdown(f'<div class="table-cell">{row["email"] if row.get("email") else "-"}</div>', unsafe_allow_html=True)
                c_slack.markdown(f'<div class="table-cell">{row["slack_id"] if row["slack_id"] else "-"}</div>', unsafe_allow_html=True)
                
                # Show password to admin/system administrator
                is_admin = user["role"] == "admin" or user["username"] == "admin"
                stored_pw = row["password"]
                # Attempt decryption (only works if Fernet-encrypted, not bcrypt hashed)
                pw_display = decrypt_data(stored_pw) if is_admin else "HIDDEN"
                c3.markdown(f'<div class="table-cell"><code>{pw_display}</code></div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("No employees found.")
            
    with tab2:
        st.write("### Create New Employee")
        with st.form("add_employee_form"):
            emp_id = st.text_input("Employee ID / Serial *")
            emp_name = st.text_input("Name *")
            email = st.text_input("Email")
            slack_id = st.text_input("Slack ID")
            
            submitted = st.form_submit_button("Add Employee", type="primary")
            if submitted:
                if not emp_id or not emp_name:
                    st.error("Employee ID and Name are required.")
                elif email and not is_valid_email(email):
                    st.error("Invalid email format.")
                else:
                    success, msg = add_employee(emp_id, emp_name, slack_id, email)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(f"Failed to create: {msg}")
                        
    with tab3:
        st.write("### Update/Edit Employee")
        if not users.empty:
            # Dropdown for selecting employee
            emp_options = {f"{r['employee_name']} ({r['employee_id']})": r['employee_id'] for _, r in users.iterrows()}
            selected_emp_label = st.selectbox("Select Employee to Edit", list(emp_options.keys()))
            selected_emp_id = emp_options[selected_emp_label]
            
            emp_data = users[users['employee_id'] == selected_emp_id].iloc[0]
            
            with st.form("edit_employee_form"):
                e_name = st.text_input("Name *", value=emp_data['employee_name'] or "")
                e_email = st.text_input("Email", value=emp_data.get('email') or "")
                e_slack = st.text_input("Slack ID", value=emp_data['slack_id'] or "")
                
                updated = st.form_submit_button("Save Changes", type="primary")
                if updated:
                    if not e_name:
                        st.error("Name is required.")
                    elif e_email and not is_valid_email(e_email):
                        st.error("Invalid email format.")
                    else:
                        success, msg = update_employee(selected_emp_id, e_name, e_slack, e_email)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(f"Failed to update: {msg}")
        else:
            st.info("No employees available to edit.")

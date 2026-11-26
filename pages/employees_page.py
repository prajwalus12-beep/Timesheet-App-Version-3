import streamlit as st
from database.queries import (
    get_all_users,
    add_employee,
    update_employee,
    get_all_2fa_statuses,
    admin_set_employee_2fa,
    get_2fa_audit_logs,
)
from services.auth_service import decrypt_data
import re

def is_valid_email(email):
    if not email: return True
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def render_employees_page(user):
    st.subheader("Employees", divider="blue")
    
    tab1, tab2, tab3, tab4 = st.tabs(["👥 Employee List", "➕ Add Employee", "✏️ Edit Employee", "🔐 2FA Management"])
    
    users = get_all_users()
    two_fa_statuses = get_all_2fa_statuses()
    
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
            st.markdown('<div class="table-header"><div style="flex: 2;">Username</div><div style="flex: 3;">Employee Name</div><div style="flex: 2.5;">Email</div><div style="flex: 1.5;">Slack ID</div><div style="flex: 1.5;">Status</div><div style="flex: 2;">2FA Status</div><div style="flex: 2;">Password</div></div>', unsafe_allow_html=True)
            for _, row in display_users.iterrows():
                st.markdown('<div class="table-row">', unsafe_allow_html=True)
                c1, c2, c_email, c_slack, c_status, c_2fa, c3 = st.columns([2, 3, 2.5, 1.5, 1.5, 2, 2])
                c1.markdown(f'<div class="table-cell">{row["username"]}</div>', unsafe_allow_html=True)
                c2.markdown(f'<div class="table-cell"><b>{row["employee_name"] if row["employee_name"] else "N/A"}</b><br/><small>{row.get("emp_type", "Full-Time Employee")}</small></div>', unsafe_allow_html=True)
                c_email.markdown(f'<div class="table-cell">{row["email"] if row.get("email") else "-"}</div>', unsafe_allow_html=True)
                c_slack.markdown(f'<div class="table-cell">{row["slack_id"] if row["slack_id"] else "-"}</div>', unsafe_allow_html=True)
                
                status_val = row.get("status", 1)
                if status_val == 1:
                    status_badge = '<span style="background-color: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 12px; font-size: 0.85em; font-weight: bold;">Active</span>'
                else:
                    status_badge = '<span style="background-color: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 12px; font-size: 0.85em; font-weight: bold;">Inactive</span>'
                c_status.markdown(f'<div class="table-cell">{status_badge}</div>', unsafe_allow_html=True)

                tfa = two_fa_statuses.get(str(row["username"]).lower(), {})
                if tfa.get("two_fa_enabled") and tfa.get("setup_verified"):
                    tfa_badge = '<span style="background-color: #dcfce7; color: #166534; padding: 2px 8px; border-radius: 12px; font-size: 0.85em; font-weight: bold;">Enabled</span>'
                elif tfa.get("two_fa_enabled"):
                    tfa_badge = '<span style="background-color: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 12px; font-size: 0.85em; font-weight: bold;">Pending Setup</span>'
                else:
                    tfa_badge = '<span style="background-color: #f1f5f9; color: #475569; padding: 2px 8px; border-radius: 12px; font-size: 0.85em; font-weight: bold;">Disabled</span>'
                c_2fa.markdown(f'<div class="table-cell">{tfa_badge}</div>', unsafe_allow_html=True)
                
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
            emp_type = st.selectbox("Employee Type", ["Full-Time Employee", "Intern"])
            status_sel = st.selectbox("Status", ["Active", "Inactive"])
            
            submitted = st.form_submit_button("Add Employee", type="primary")
            if submitted:
                if not emp_id or not emp_name:
                    st.error("Employee ID and Name are required.")
                elif email and not is_valid_email(email):
                    st.error("Invalid email format.")
                else:
                    status_val = 1 if status_sel == "Active" else 0
                    success, msg = add_employee(emp_id, emp_name, slack_id, email, status=status_val, emp_type=emp_type)
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
            emp_is_active = emp_data.get('status', 1) == 1
            
            if not emp_is_active:
                st.info("ℹ️ This employee is currently inactive. The information is available in read-only mode, but you can change their status to Active.")
            
            with st.form("edit_employee_form"):
                e_name = st.text_input("Name *", value=emp_data['employee_name'] or "", disabled=not emp_is_active)
                e_email = st.text_input("Email", value=emp_data.get('email') or "", disabled=not emp_is_active)
                e_slack = st.text_input("Slack ID", value=emp_data['slack_id'] or "", disabled=not emp_is_active)
                
                emp_type_idx = 0 if emp_data.get('emp_type', 'Full-Time Employee') == 'Full-Time Employee' else 1
                e_emp_type = st.selectbox("Employee Type", ["Full-Time Employee", "Intern"], index=emp_type_idx, disabled=not emp_is_active)

                status_idx = 0 if emp_is_active else 1
                e_status = st.selectbox("Status", ["Active", "Inactive"], index=status_idx)
                
                updated = st.form_submit_button("Save Changes", type="primary")
                if updated:
                    if not e_name:
                        st.error("Name is required.")
                    elif e_email and not is_valid_email(e_email):
                        st.error("Invalid email format.")
                    else:
                        status_val = 1 if e_status == "Active" else 0
                        success, msg = update_employee(selected_emp_id, e_name, e_slack, e_email, status=status_val, emp_type=e_emp_type)
                        if success:
                            st.success(msg)
                            st.rerun()
                        else:
                            st.error(f"Failed to update: {msg}")
        else:
            st.info("No employees available to edit.")

    with tab4:
        st.write("### 🔐 Employee Two-Factor Authentication (2FA) Management")
        st.info(
            "Enable or disable 2FA for individual employees. When enabled, employees who haven't configured an authenticator app yet will be prompted to set up 2FA on their next login. "
            "Employee authenticator secrets are encrypted and never visible here."
        )
        if not users.empty:
            emp_rows = users[users["username"].str.lower() != "admin"].sort_values(by="employee_name")
            search_2fa = st.text_input("🔍 Filter employees for 2FA", key="search_2fa_emp")
            if search_2fa:
                sq = search_2fa.lower()
                emp_rows = emp_rows[
                    emp_rows["employee_name"].fillna("").astype(str).str.lower().str.contains(sq, na=False)
                    | emp_rows["username"].fillna("").astype(str).str.lower().str.contains(sq, na=False)
                ]

            h1, h2, h3, h4 = st.columns([2.5, 2.0, 2.0, 2.0])
            h1.markdown("**Employee**")
            h2.markdown("**Username**")
            h3.markdown("**2FA Status**")
            h4.markdown("**Action**")
            st.divider()

            for _, row in emp_rows.iterrows():
                uname = str(row["username"])
                emp_name = row.get("employee_name") or uname
                emp_id_val = str(row.get("employee_id") or uname)
                tfa = two_fa_statuses.get(uname.lower(), {})
                is_enabled = bool(tfa.get("two_fa_enabled", False))
                is_verified = bool(tfa.get("setup_verified", False))

                c1, c2, c3, c4 = st.columns([2.5, 2.0, 2.0, 2.0])
                c1.write(f"**{emp_name}**")
                c2.code(uname)
                if is_enabled and is_verified:
                    c3.success("Enabled (Verified)")
                elif is_enabled:
                    c3.warning("Enabled (Pending Setup)")
                else:
                    c3.write("Disabled")

                if is_enabled:
                    if c4.button("Disable 2FA", key=f"disable_2fa_{uname}", type="secondary", use_container_width=True):
                        ok, msg = admin_set_employee_2fa(uname, emp_id_val, False, user.get("username", "admin"))
                        if ok:
                            st.success(f"2FA disabled for {emp_name}.")
                            st.rerun()
                        else:
                            st.error(msg)
                else:
                    if c4.button("Enable 2FA", key=f"enable_2fa_{uname}", type="primary", use_container_width=True):
                        ok, msg = admin_set_employee_2fa(uname, emp_id_val, True, user.get("username", "admin"))
                        if ok:
                            st.success(f"2FA enabled for {emp_name}. They will configure their authenticator on next login.")
                            st.rerun()
                        else:
                            st.error(msg)

            with st.expander("📋 Recent 2FA Security Audit Logs"):
                logs = get_2fa_audit_logs(limit=30)
                if logs:
                    import pandas as pd
                    st.dataframe(pd.DataFrame(logs)[["created_at", "event_type", "actor_username", "target_username", "user_type", "details"]], use_container_width=True)
                else:
                    st.caption("No 2FA audit events recorded yet.")
        else:
            st.info("No employees found.")

import streamlit as st
import pandas as pd
import datetime
from database.queries import (
    get_all_users, update_project_update_access, update_add_project_access, get_app_setting, set_app_setting,
    get_all_holidays
)
from utils.lockout_helpers import get_lockout_schedule, save_lockout_schedule
from components.dialogs import (
    add_holiday_dialog, edit_holiday_dialog, import_holiday_dialog, confirm_delete_holiday_dialog
)

def render_settings_page(user=None):
    """Render the administrative settings page for access control and holiday management."""
    if user is None:
        user = st.session_state.get('user', {})
        
    st.subheader("System Settings", divider="blue")
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🗓️ Weekly Lockout Schedule", 
        "👥 Employee Permissions", 
        "📧 Timesheet Reminder Settings",
        "📊 Send Report Settings",
        "🏖️ Holiday Management"
    ])
    
    with tab1:
        # --- Weekly Lockout Schedule ---
        st.write("### 🗓️ Weekly Lockout Schedule")
        st.caption("Select the days of the week when project updates should be automatically disabled for all employees.")

        if "lockout_schedule" not in st.session_state:
            st.session_state.lockout_schedule = get_lockout_schedule()

        days = ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]
        cols = st.columns(7)
        
        # Custom CSS for multiline button alignment
        st.markdown("""
        <style>
        /* Target streamlit buttons to allow multiline and center text */
        div[data-testid="stButton"] > button {
            height: 100px;
            white-space: pre-line;
        }
        div[data-testid="stButton"] > button p {
            text-align: center;
            line-height: 1.5;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)

        for i, day in enumerate(days):
            is_blocked = st.session_state.lockout_schedule.get(day, False)
            
            # Decide label and icon
            icon = "🔒" if is_blocked else "🔓"
            status_text = "BLOCKED" if is_blocked else "OPEN"
            
            button_label = f"{day}\n{icon}\n{status_text}"
            
            with cols[i]:
                if st.button(button_label, key=f"lockout_btn_{day}", use_container_width=True, type="primary" if is_blocked else "secondary"):
                    # Toggle state
                    st.session_state.lockout_schedule[day] = not is_blocked
                    save_lockout_schedule(st.session_state.lockout_schedule)
                    st.rerun()

        # Legend
        st.markdown('''
            <div style="display: flex; justify-content: center; margin-top: 15px; margin-bottom: 40px; gap: 20px; font-size: 14px; color: #555;">
                <div style="display: flex; align-items: center;">
                    <span style="height: 10px; width: 10px; background-color: #ff4b4b; border-radius: 50%; display: inline-block; margin-right: 6px;"></span>
                    Auto-Locked Day
                </div>
                <div style="display: flex; align-items: center;">
                    <span style="height: 10px; width: 10px; background-color: #e0e0e0; border-radius: 50%; display: inline-block; margin-right: 6px;"></span>
                    Editable Day
                </div>
            </div>
        ''', unsafe_allow_html=True)

    with tab2:
        # --- Employee Permissions ---
        st.write("### 👥 Employee Permissions")
        st.caption("Override standard access for specific employees. (Note: Weekly lockout takes precedence).")

        # Fetch all users with their current project update access
        users_df = get_all_users()
        
        if users_df.empty:
            st.info("No users found to manage.")
        else:
            # Filter out admin (admin always has access, no need to toggle)
            manageable_users = users_df[users_df['username'] != 'admin'].copy()
            
            if manageable_users.empty:
                st.info("No non-admin users found to manage.")
            else:
                # Display users in a clean list with toggles
                st.markdown("""
                <style>
                .settings-row {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 12px 16px;
                    background: rgba(128, 128, 128, 0.05);
                    border-radius: 8px;
                    margin-bottom: 8px;
                }
                .user-details {
                    display: flex;
                    flex-direction: column;
                }
                .user-name {
                    font-weight: 600;
                    font-size: 15px;
                }
                .user-username {
                    font-size: 13px;
                    opacity: 0.7;
                }
                </style>
                """, unsafe_allow_html=True)

                changes_made = False
                
                # Header row for permission columns
                h_col1, h_col2, h_col3 = st.columns([3, 1.2, 1.5])
                with h_col1:
                    st.markdown("<span style='font-size: 0.8rem; font-weight: 700; color: #64748b; text-transform: uppercase;'>Employee</span>", unsafe_allow_html=True)
                with h_col2:
                    st.markdown("<span style='font-size: 0.8rem; font-weight: 700; color: #64748b; text-transform: uppercase;'>Project Update</span>", unsafe_allow_html=True)
                with h_col3:
                    st.markdown("<span style='font-size: 0.8rem; font-weight: 700; color: #64748b; text-transform: uppercase;'>Add Project</span>", unsafe_allow_html=True)

                for idx, row in manageable_users.iterrows():
                    col1, col2, col3 = st.columns([3, 1.2, 1.5])
                    
                    with col1:
                        st.markdown(f"""
                        <div class="user-details">
                            <div class="user-name">{row['employee_name']}</div>
                            <div class="user-username">@{row['username']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with col2:
                        current_access = bool(row['project_update_access'])
                        new_access = st.checkbox(
                            "Allow Edit", 
                            value=current_access, 
                            key=f"access_{row['employee_id']}"
                        )
                        
                        if new_access != current_access:
                            success, msg = update_project_update_access(row['employee_id'], new_access)
                            if success:
                                st.toast(f"✅ Edit access updated for {row['employee_name']}", icon="🔒")
                                changes_made = True
                            else:
                                st.error(f"Error: {msg}")

                    with col3:
                        current_add_access = bool(row.get('allow_add_project', False))
                        new_add_access = st.checkbox(
                            "Allow to Add Project",
                            value=current_add_access,
                            key=f"add_project_access_{row['employee_id']}"
                        )

                        if new_add_access != current_add_access:
                            success, msg = update_add_project_access(row['employee_id'], new_add_access)
                            if success:
                                st.toast(f"✅ 'Allow to Add Project' updated for {row['employee_name']}", icon="➕")
                                changes_made = True
                            else:
                                st.error(f"Error: {msg}")

                if changes_made:
                    st.rerun()

                st.divider()
                st.info("💡 **Tip:** Administrators always have full access to all modules and cannot be restricted.")

    with tab3:
        # --- Timesheet Reminder Settings (Admin-only) ---
        st.write("### 📧 Timesheet Reminder Settings")
        st.caption("Configure automated weekly timesheet reminders sent to employees with incomplete timesheets.")

        # Load current settings from DB
        reminder_enabled_str = get_app_setting('timesheet_reminder_enabled', 'false')
        reminder_days_str = get_app_setting('timesheet_reminder_days', 'thu')
        reminder_time_str = get_app_setting('timesheet_reminder_time', '10:00')

        current_enabled = reminder_enabled_str.lower() == 'true'
        
        # Map DB values (mon, tue, wed, thu, fri, sat, sun) to UI labels
        DAY_MAP = {
            'mon': 'Monday', 'tue': 'Tuesday', 'wed': 'Wednesday', 
            'thu': 'Thursday', 'fri': 'Friday', 'sat': 'Saturday', 'sun': 'Sunday'
        }
        INV_DAY_MAP = {v: k for k, v in DAY_MAP.items()}
        ALL_DAYS = list(DAY_MAP.values())
        
        current_days = [d.strip() for d in reminder_days_str.split(',') if d.strip()]
        if not current_days:
            current_days = ['thu']
        current_days_labels = [DAY_MAP.get(d, 'Thursday') for d in current_days]

        try:
            parts = reminder_time_str.strip().split(':')
            current_time = datetime.time(int(parts[0]), int(parts[1]))
        except (ValueError, IndexError):
            current_time = datetime.time(10, 0)

        with st.container(border=True):
            new_enabled = st.toggle(
                "Enable Timesheet Reminder Cron",
                value=current_enabled,
                key="ts_reminder_enabled_toggle",
                help="When enabled, reminder emails are sent on the selected days at the configured time."
            )

            r_col1, r_col2 = st.columns([1, 1])

            with r_col1:
                new_days_labels = st.multiselect(
                    "Reminder Days",
                    options=ALL_DAYS,
                    default=current_days_labels,
                    key="ts_reminder_days_input",
                    help="Select the day(s) to send the automated reminder."
                )

            with r_col2:
                new_time = st.time_input(
                    "Reminder Time",
                    value=current_time,
                    key="ts_reminder_time_input",
                    help="The time when the automated reminder runs on the selected days."
                )

            # Status display
            status_col1, status_col2 = st.columns(2)
            with status_col1:
                if new_enabled:
                    st.markdown("**Status:** :green[✅ Enabled]")
                else:
                    st.markdown("**Status:** :red[❌ Disabled]")
            with status_col2:
                try:
                    from services.scheduler_service import get_next_run_time
                    next_run = get_next_run_time()
                    if next_run:
                        st.markdown(f"**Next run:** {next_run.strftime('%A, %d-%m-%Y at %H:%M')}")
                    else:
                        st.markdown("**Next run:** —")
                except Exception:
                    st.markdown("**Next run:** —")

            # Save button
            if st.button("💾 Save Reminder Settings", key="save_reminder_settings", type="primary"):
                if not new_days_labels:
                    st.error("❌ Please select at least one reminder day.")
                    st.stop()

                new_time_str = new_time.strftime('%H:%M')
                new_days_str = ",".join([INV_DAY_MAP[d] for d in new_days_labels])

                # Validate time
                try:
                    h, m = int(new_time_str.split(':')[0]), int(new_time_str.split(':')[1])
                    if not (0 <= h <= 23 and 0 <= m <= 59):
                        raise ValueError("Invalid time")
                except (ValueError, IndexError):
                    st.error("❌ Invalid time value. Please enter a valid time.")
                    st.stop()

                # Save to DB
                ok1, msg1 = set_app_setting('timesheet_reminder_enabled', str(new_enabled).lower())
                ok2, msg2 = set_app_setting('timesheet_reminder_days', new_days_str)
                ok3, msg3 = set_app_setting('timesheet_reminder_time', new_time_str)

                if ok1 and ok2 and ok3:
                    # Update the scheduler
                    try:
                        from services.scheduler_service import update_reminder_schedule
                        update_reminder_schedule(new_enabled, new_days_str, new_time_str)
                    except Exception as sched_err:
                        st.warning(f"⚠️ Settings saved but scheduler update failed: {sched_err}")

                    if new_enabled:
                        days_display = ", ".join(new_days_labels)
                        st.toast(f"✅ Reminder settings saved successfully for {days_display} at {new_time_str}", icon="📧")
                    else:
                        st.toast("✅ Reminder settings saved successfully! (Currently disabled)", icon="📧")
                    st.rerun()
                else:
                    errors = []
                    if not ok1: errors.append(msg1)
                    if not ok2: errors.append(msg2)
                    if not ok3: errors.append(msg3)
                    st.error(f"❌ Failed to save settings: {'; '.join(errors)}")

        # --- Automatic Log Cleanup Notice (read-only, system-managed) ---
        st.divider()
        st.info(
            "🗑️ **Automatic Log Cleanup**\n\n"
            "Timesheet reminder logs older than **4 weeks** are automatically deleted "
            "every 4 weeks during nighttime hours (02:00). "
            "This setting is managed by the system and cannot be changed."
        )

    with tab4:
        # --- Send Report Settings (Admin-only) ---
        from database.queries import get_report_email_settings, update_report_email_settings
        from services.email_service import send_test_report_email
        import re
        
        st.write("### 📊 Send Report Settings")
        st.caption("Configure automated weekly timesheet report emails with charts and analytics.")
        
        # Load current settings
        report_settings = get_report_email_settings()
        current_enabled = report_settings.get('enabled', False)
        current_recipients = report_settings.get('recipients', [])
        current_day = report_settings.get('day', 'fri')
        current_time_str = report_settings.get('time', '17:00')
        current_timezone = report_settings.get('timezone', 'UTC')
        last_sent = report_settings.get('last_sent', '')
        
        # Day mapping
        REPORT_DAY_MAP = {
            'mon': 'Monday', 'tue': 'Tuesday', 'wed': 'Wednesday',
            'thu': 'Thursday', 'fri': 'Friday', 'sat': 'Saturday', 'sun': 'Sunday'
        }
        INV_REPORT_DAY_MAP = {v: k for k, v in REPORT_DAY_MAP.items()}
        
        try:
            parts = current_time_str.strip().split(':')
            current_time = datetime.time(int(parts[0]), int(parts[1]))
        except (ValueError, IndexError):
            current_time = datetime.time(17, 0)
        
        with st.container(border=True):
            # Enable/Disable toggle
            new_enabled = st.toggle(
                "Enable Automatic Weekly Reports",
                value=current_enabled,
                key="report_email_enabled_toggle",
                help="When enabled, weekly reports are automatically sent on the selected day at the configured time."
            )
            
            st.markdown("---")
            
            # Email Recipients
            st.markdown("**📧 Email Recipients**")
            st.caption("Add one or more email addresses to receive weekly reports. Press Enter after each email.")
            
            # Display current recipients
            if current_recipients:
                st.markdown(f"**Current Recipients ({len(current_recipients)}):**")
                for idx, email in enumerate(current_recipients):
                    col_e, col_x = st.columns([5, 1])
                    with col_e:
                        st.code(email, language=None)
                    with col_x:
                        if st.button("🗑️", key=f"remove_recipient_{idx}", help="Remove this recipient"):
                            current_recipients.pop(idx)
                            update_report_email_settings(recipients=current_recipients)
                            st.toast(f"✅ Removed {email}", icon="🗑️")
                            st.rerun()
            else:
                st.info("ℹ️ No recipients configured. Add email addresses below.")
            
            # Add new recipient
            new_email = st.text_input(
                "Add Recipient Email",
                placeholder="email@example.com",
                key="new_recipient_email_input",
                help="Enter a valid email address and click Add"
            )
            
            if st.button("➕ Add Recipient", key="add_recipient_btn"):
                if not new_email:
                    st.error("❌ Please enter an email address")
                elif not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', new_email):
                    st.error("❌ Please enter a valid email address")
                elif new_email in current_recipients:
                    st.warning("⚠️ This email is already in the recipient list")
                else:
                    current_recipients.append(new_email)
                    update_report_email_settings(recipients=current_recipients)
                    st.toast(f"✅ Added {new_email}", icon="📧")
                    st.rerun()
            
            st.markdown("---")
            
            # Schedule settings
            st.markdown("**📅 Report Schedule**")
            col_day, col_time, col_tz = st.columns(3)
            
            with col_day:
                current_day_label = REPORT_DAY_MAP.get(current_day, 'Friday')
                new_day_label = st.selectbox(
                    "Day of Week",
                    options=list(REPORT_DAY_MAP.values()),
                    index=list(REPORT_DAY_MAP.values()).index(current_day_label),
                    key="report_day_select"
                )
            
            with col_time:
                new_time = st.time_input(
                    "Time",
                    value=current_time,
                    key="report_time_input",
                    help="Time when the report is automatically sent"
                )
            
            with col_tz:
                # Common timezones
                timezones = ['UTC', 'America/New_York', 'America/Chicago', 'America/Los_Angeles', 
                            'Europe/London', 'Europe/Paris', 'Asia/Kolkata', 'Asia/Tokyo', 
                            'Australia/Sydney']
                try:
                    tz_index = timezones.index(current_timezone)
                except ValueError:
                    tz_index = 0
                    
                new_timezone = st.selectbox(
                    "Time Zone",
                    options=timezones,
                    index=tz_index,
                    key="report_timezone_select"
                )
            
            st.markdown("---")
            
            # Status display
            status_col1, status_col2 = st.columns(2)
            with status_col1:
                if new_enabled:
                    st.markdown("**Status:** :green[✅ Enabled]")
                else:
                    st.markdown("**Status:** :red[❌ Disabled]")
            
            with status_col2:
                if last_sent:
                    try:
                        last_sent_dt = datetime.datetime.fromisoformat(last_sent)
                        st.markdown(f"**Last sent:** {last_sent_dt.strftime('%d-%m-%Y %H:%M')}")
                    except Exception:
                        st.markdown("**Last sent:** —")
                else:
                    st.markdown("**Last sent:** Never")
            
            # Next run time
            try:
                from services.scheduler_service import get_weekly_report_next_run_time
                next_run = get_weekly_report_next_run_time()
                if next_run:
                    st.markdown(f"**Next scheduled run:** {next_run.strftime('%A, %d-%m-%Y at %H:%M')}")
                else:
                    st.markdown("**Next scheduled run:** —")
            except Exception:
                pass
            
            st.markdown("---")
            
            # Action buttons
            btn_col1, btn_col2 = st.columns(2)
            
            with btn_col1:
                if st.button("💾 Save Settings", key="save_report_settings_btn", type="primary", use_container_width=True):
                    if new_enabled and not current_recipients:
                        st.error("❌ Please add at least one recipient email address before enabling automatic reports")
                        st.stop()
                    
                    new_time_str = new_time.strftime('%H:%M')
                    new_day = INV_REPORT_DAY_MAP[new_day_label]
                    
                    # Save settings
                    success, msg = update_report_email_settings(
                        enabled=new_enabled,
                        recipients=current_recipients,
                        day=new_day,
                        time=new_time_str,
                        timezone=new_timezone
                    )
                    
                    if success:
                        # Update scheduler
                        try:
                            from services.scheduler_service import update_weekly_report_schedule
                            update_weekly_report_schedule(new_enabled, new_day, new_time_str)
                        except Exception as sched_err:
                            st.warning(f"⚠️ Settings saved but scheduler update failed: {sched_err}")
                        
                        if new_enabled:
                            st.toast(f"✅ Report settings saved! Reports will be sent every {new_day_label} at {new_time_str}", icon="📊")
                        else:
                            st.toast("✅ Report settings saved! (Currently disabled)", icon="📊")
                        st.rerun()
                    else:
                        st.error(f"❌ Failed to save settings: {msg}")
            
            with btn_col2:
                if st.button("📧 Send Test Email", key="send_test_report_email_btn", use_container_width=True, disabled=not current_recipients):
                    if current_recipients:
                        test_recipient = current_recipients[0]
                        with st.spinner(f"Sending test email to {test_recipient}..."):
                            success, msg = send_test_report_email(test_recipient)
                        if success:
                            st.success(f"✅ {msg}")
                        else:
                            st.error(f"❌ {msg}")
                    else:
                        st.error("❌ Please add at least one recipient first")
        
        st.markdown("---")
        st.info(
            "**📌 Report Content**\n\n"
            "The weekly report includes:\n"
            "- Summary of timesheet submissions and employee statistics\n"
            "- Project breakdown with codes and names\n"
            "- Combined PDF with both pie chart and bar chart\n"
            "- Reporting period and effort metrics (hours/days)\n\n"
            "You can also send reports manually from the Report page."
        )

    with tab5:
        # --- Holiday Management (Admin-only) ---
        st.write("### 🏖️ Holiday Management")
        st.caption("Configure company-wide holidays applicable to all employees. Add manually or import via Excel/CSV.")

        curr_year = datetime.date.today().year
        year_options = ["All", str(curr_year - 1), str(curr_year), str(curr_year + 1), str(curr_year + 2)]
        
        col_y, col_space, col_add, col_imp = st.columns([1.5, 3.2, 1.6, 1.7])
        with col_y:
            sel_year = st.selectbox("Filter by Year", year_options, index=2, key="holiday_year_filter")
        with col_add:
            st.write("")
            st.write("")
            if st.button("➕ Add Holiday", type="primary", use_container_width=True, key="open_add_holiday_btn"):
                add_holiday_dialog(user)
        with col_imp:
            st.write("")
            st.write("")
            if st.button("📥 Import Holidays", type="secondary", use_container_width=True, key="open_import_holiday_btn"):
                import_holiday_dialog(user)

        filter_year = None if sel_year == "All" else int(sel_year)
        holidays_df = get_all_holidays(year=filter_year)

        if holidays_df.empty:
            st.info("ℹ️ No holidays configured for the selected filter. Click **'Add Holiday'** or **'Import Holidays'** to configure dates.")
        else:
            st.markdown(f"**Total Holidays:** {len(holidays_df)}")
            
            st.markdown("""
            <style>
            .holiday-card {
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 12px 16px;
                background: rgba(128, 128, 128, 0.05);
                border-left: 4px solid #8b5cf6;
                border-radius: 8px;
                margin-bottom: 8px;
            }
            .holiday-date-badge {
                font-weight: 700;
                font-size: 15px;
                color: #2563eb;
            }
            .holiday-day-label {
                font-size: 12px;
                color: #64748b;
                margin-left: 6px;
            }
            .holiday-name-text {
                font-size: 15px;
                font-weight: 600;
                margin-top: 2px;
            }
            .holiday-audit-text {
                font-size: 12px;
                color: #94a3b8;
                margin-top: 2px;
            }
            </style>
            """, unsafe_allow_html=True)

            for _, h_row in holidays_df.iterrows():
                h_date_raw = h_row['holiday_date']
                if isinstance(h_date_raw, str):
                    try:
                        h_date_obj = datetime.date.fromisoformat(h_date_raw)
                    except Exception:
                        h_date_obj = h_date_raw
                else:
                    h_date_obj = h_date_raw

                date_str = h_date_obj.strftime("%d-%m-%Y") if hasattr(h_date_obj, 'strftime') else str(h_date_obj)
                day_str = h_date_obj.strftime("%A") if hasattr(h_date_obj, 'strftime') else ""

                card_col, action_col = st.columns([5.5, 1.5])
                with card_col:
                    st.markdown(f"""
                    <div class="holiday-card">
                        <div>
                            <div>
                                <span class="holiday-date-badge">📅 {date_str}</span>
                                <span class="holiday-day-label">({day_str})</span>
                            </div>
                            <div class="holiday-name-text">🎉 {h_row['holiday_name']}</div>
                            <div class="holiday-audit-text">Configured by: @{h_row.get('created_by') or 'admin'}</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                with action_col:
                    st.write("")
                    act_c1, act_c2 = st.columns(2)
                    with act_c1:
                        if st.button(":material/edit:", key=f"edit_h_btn_{h_row['id']}", help="Edit Holiday"):
                            edit_holiday_dialog(h_row.to_dict(), user)
                    with act_c2:
                        if st.button(":material/delete:", key=f"del_h_btn_{h_row['id']}", help="Delete Holiday"):
                            confirm_delete_holiday_dialog(h_row.to_dict(), user)



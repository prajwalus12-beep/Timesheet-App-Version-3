import streamlit as st
import pandas as pd
import datetime
from database.queries import get_all_users, update_project_update_access, get_app_setting, set_app_setting
from utils.lockout_helpers import get_lockout_schedule, save_lockout_schedule

def render_settings_page():
    """Render the administrative settings page for access control."""
    st.subheader("System Settings", divider="blue")
    tab1, tab2, tab3 = st.tabs([
        "🗓️ Weekly Lockout Schedule", 
        "👥 Employee Permissions", 
        "📧 Timesheet Reminder Settings"
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
                
                for idx, row in manageable_users.iterrows():
                    col1, col2 = st.columns([4, 1])
                    
                    with col1:
                        st.markdown(f"""
                        <div class="user-details">
                            <div class="user-name">{row['employee_name']}</div>
                            <div class="user-username">@{row['username']}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with col2:
                        current_access = bool(row['project_update_access'])
                        # Using checkbox as requested
                        new_access = st.checkbox(
                            "Allow Edit", 
                            value=current_access, 
                            key=f"access_{row['employee_id']}"
                        )
                        
                        if new_access != current_access:
                            success, msg = update_project_update_access(row['employee_id'], new_access)
                            if success:
                                st.toast(f"✅ Access updated for {row['employee_name']}", icon="🔒")
                                changes_made = True
                            else:
                                st.error(f"Error: {msg}")

                if changes_made:
                    # Note: In a real app we might want to force a refresh of the user's session if they are logged in.
                    # For now, this updates the DB immediately.
                    pass

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


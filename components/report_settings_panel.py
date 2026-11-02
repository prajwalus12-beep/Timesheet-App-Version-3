"""
Report Settings Panel Component
================================
Reusable component for automatic report configuration with date range filters.
Used in settings_page.py
"""

import streamlit as st
import datetime
import re
from database.queries import get_report_email_settings, update_report_email_settings
from services.email_service import send_test_report_email
from utils.date_helpers import calculate_report_date_range, get_date_range_display_name


def render_report_settings_panel():
    """
    Render the complete report settings panel with automatic scheduling and date range filters.
    
    Includes:
    - Enable/disable toggle
    - Email recipients management
    - Date range filter selection (with custom date picker)
    - Schedule configuration (day and time)
    - Status display
    - Action buttons (save, test, clear)
    """
    
    from database.queries import get_report_email_settings, update_report_email_settings
    import datetime
    
    st.write("### 📊 Automatic Report Settings")
    st.caption("Configure automated weekly timesheet reports with flexible date range filters.")
    
    # Load current settings
    report_settings = get_report_email_settings()
    current_enabled = report_settings.get('enabled', False)
    current_recipients = report_settings.get('recipients', [])
    current_day = report_settings.get('day', 'fri')
    current_time_str = report_settings.get('time', '17:00')
    current_timezone = report_settings.get('timezone', 'UTC')
    current_date_range_filter = report_settings.get('date_range_filter', 'last_week')
    current_custom_start = report_settings.get('custom_start_date', '')
    current_custom_end = report_settings.get('custom_end_date', '')
    last_sent = report_settings.get('last_sent', '')
    
    # Day mapping
    REPORT_DAY_MAP = {
        'mon': 'Monday', 'tue': 'Tuesday', 'wed': 'Wednesday',
        'thu': 'Thursday', 'fri': 'Friday', 'sat': 'Saturday', 'sun': 'Sunday'
    }
    INV_REPORT_DAY_MAP = {v: k for k, v in REPORT_DAY_MAP.items()}
    
    # Date range filter options
    DATE_RANGE_OPTIONS = {
        'this_week': 'This Week',
        'last_week': 'Last Week',
        'current_cycle': 'Current 4-Week Cycle',
        'previous_cycle': 'Previous 4-Week Cycle',
        'custom': 'Custom Date Range'
    }
    
    try:
        parts = current_time_str.strip().split(':')
        current_time = datetime.time(int(parts[0]), int(parts[1]))
    except (ValueError, IndexError):
        current_time = datetime.time(17, 0)
    
    # Parse custom dates
    custom_start_date = None
    custom_end_date = None
    if current_custom_start:
        try:
            custom_start_date = datetime.datetime.strptime(current_custom_start, '%Y-%m-%d').date()
        except ValueError:
            pass
    if current_custom_end:
        try:
            custom_end_date = datetime.datetime.strptime(current_custom_end, '%Y-%m-%d').date()
        except ValueError:
            pass
    
    with st.container(border=True):
        # Enable/Disable toggle
        new_enabled = st.toggle(
            "Enable Automatic Reports",
            value=current_enabled,
            key="report_email_enabled_toggle",
            help="When enabled, reports are automatically sent on the selected day at the configured time with data from the selected date range."
        )
        
        st.markdown("---")
        
        # ========================================
        # DATE RANGE FILTER SECTION
        # ========================================
        st.markdown("**📅 Date Range Filter**")
        st.caption("Select which period's data should be included in each report")
        
        # Date range filter selection
        current_filter_label = DATE_RANGE_OPTIONS.get(current_date_range_filter, 'Last Week')
        new_filter_label = st.selectbox(
            "Report Data Period",
            options=list(DATE_RANGE_OPTIONS.values()),
            index=list(DATE_RANGE_OPTIONS.values()).index(current_filter_label),
            key="report_date_range_filter_select",
            help="Choose which period's timesheet data to include in the report"
        )
        
        # Convert back to filter key
        new_filter_type = [k for k, v in DATE_RANGE_OPTIONS.items() if v == new_filter_label][0]
        
        # Show date pickers for custom range
        new_custom_start = custom_start_date
        new_custom_end = custom_end_date
        
        if new_filter_type == 'custom':
            col1, col2 = st.columns(2)
            with col1:
                new_custom_start = st.date_input(
                    "Start Date",
                    value=custom_start_date or datetime.date.today() - datetime.timedelta(days=7),
                    key="report_custom_start_date"
                )
            with col2:
                new_custom_end = st.date_input(
                    "End Date",
                    value=custom_end_date or datetime.date.today(),
                    key="report_custom_end_date"
                )
            
            # Validate custom dates
            if new_custom_start and new_custom_end:
                if new_custom_start > new_custom_end:
                    st.error("❌ Start date must be before end date")
                else:
                    days_diff = (new_custom_end - new_custom_start).days + 1
                    st.info(f"ℹ️ Report will cover {days_diff} days of timesheet data")
        else:
            # Show preview of date range
            try:
                preview_start, preview_end = calculate_report_date_range(new_filter_type)
                st.info(f"ℹ️ Report will cover: {preview_start.strftime('%d-%m-%Y')} to {preview_end.strftime('%d-%m-%Y')}")
            except Exception:
                pass
        
        st.markdown("---")
        
        # ========================================
        # EMAIL RECIPIENTS SECTION
        # ========================================
        st.markdown("**📧 Email Recipients**")
        st.caption("Add one or more email addresses to receive the automated reports")
        
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
            help="Enter a valid email address"
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
        
        # ========================================
        # SCHEDULE SETTINGS SECTION
        # ========================================
        st.markdown("**🕒 Report Schedule**")
        st.caption("Select when the report should be sent automatically")
        
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
                help="Time when the report is automatically sent (24-hour format)"
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
        
        # ========================================
        # STATUS & INFO SECTION
        # ========================================
        st.markdown("**📋 Status**")
        status_col1, status_col2, status_col3 = st.columns(3)
        
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
        
        with status_col3:
            range_display = get_date_range_display_name(new_filter_type, new_custom_start, new_custom_end)
            st.markdown(f"**Data Period:** {range_display}")
        
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
        
        # ========================================
        # ACTION BUTTONS SECTION
        # ========================================
        st.markdown("**⚡ Actions**")
        
        btn_col1, btn_col2, btn_col3 = st.columns(3)
        
        with btn_col1:
            if st.button("💾 Save Settings", key="save_report_settings_btn", type="primary", use_container_width=True):
                if new_enabled and not current_recipients:
                    st.error("❌ Please add at least one recipient email address before enabling automatic reports")
                    st.stop()
                
                if new_enabled and new_filter_type == 'custom' and (not new_custom_start or not new_custom_end):
                    st.error("❌ Please select both start and end dates for custom date range")
                    st.stop()
                
                new_time_str = new_time.strftime('%H:%M')
                new_day = INV_REPORT_DAY_MAP[new_day_label]
                
                # Save settings with date range filter
                success, msg = update_report_email_settings(
                    enabled=new_enabled,
                    recipients=current_recipients,
                    day=new_day,
                    time=new_time_str,
                    timezone=new_timezone,
                    date_range_filter=new_filter_type,
                    custom_start_date=new_custom_start if new_filter_type == 'custom' else None,
                    custom_end_date=new_custom_end if new_filter_type == 'custom' else None
                )
                
                if success:
                    # Update scheduler
                    try:
                        from services.scheduler_service import update_weekly_report_schedule
                        update_weekly_report_schedule(new_enabled, new_day, new_time_str)
                    except Exception as sched_err:
                        st.warning(f"⚠️ Settings saved but scheduler update failed: {sched_err}")
                    
                    if new_enabled:
                        range_name = get_date_range_display_name(new_filter_type, new_custom_start, new_custom_end)
                        st.toast(f"✅ Reports enabled! {new_day_label} at {new_time_str} ({range_name})", icon="📊")
                    else:
                        st.toast("✅ Automatic reports disabled", icon="📊")
                    st.rerun()
                else:
                    st.error(f"❌ Failed to save settings: {msg}")
        
        with btn_col2:
            if st.button("📧 Send Test Email", key="send_test_report_email_btn", use_container_width=True, 
                        disabled=not current_recipients):
                if current_recipients:
                    test_recipient = current_recipients[0]
                    with st.spinner(f"Sending test email to {test_recipient}..."):
                        success, msg = send_test_report_email(test_recipient)
                    if success:
                        st.success(f"✅ {msg}")
                    else:
                        st.error(f"❌ {msg}")
        
        with btn_col3:
            if st.button("🔍 Preview", key="preview_report_settings_btn", use_container_width=True):
                preview_time_str = new_time.strftime('%H:%M')
                st.info(f"""
                **Report Preview:**
                - 📧 Recipients: {len(current_recipients)} configured
                - 📅 Date Range: {get_date_range_display_name(new_filter_type, new_custom_start, new_custom_end)}
                - 🕒 Schedule: Every {new_day_label} at {preview_time_str} ({new_timezone})
                - 📊 Status: {'✅ Enabled' if new_enabled else '❌ Disabled'}
                """)

import streamlit as st
import pandas as pd
from database.queries import get_all_users, update_project_update_access
from utils.lockout_helpers import get_lockout_schedule, save_lockout_schedule

def render_settings_page():
    """Render the administrative settings page for access control."""
    st.subheader("System Settings", divider="blue")
    
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

    # --- Employee Permissions ---
    st.write("### 👥 Employee Permissions")
    st.caption("Override standard access for specific employees. (Note: Weekly lockout takes precedence).")

    # Fetch all users with their current project update access
    users_df = get_all_users()
    
    if users_df.empty:
        st.info("No users found to manage.")
        return

    # Filter out admin (admin always has access, no need to toggle)
    manageable_users = users_df[users_df['username'] != 'admin'].copy()
    
    if manageable_users.empty:
        st.info("No non-admin users found to manage.")
        return

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

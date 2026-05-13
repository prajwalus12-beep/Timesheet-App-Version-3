"""Project Update 2 — React-based Project Attributes page."""
import streamlit as st
import pandas as pd
import io
import datetime
from openpyxl.styles import PatternFill
from database.queries import get_project_reports, save_project_updates, get_all_employees
from components.project_update_react import project_update_component


def _generate_excel_buffer(df, highlight_updated=False):
    """Generate an Excel buffer for the given DataFrame, highlighting updated cells."""
    export_cols_map = {
        'project_code': 'Job No',
        'priority': 'Job Priority',
        'project_name': 'Project',
        'status': 'Status',
        'lead_engineer': 'Lead engineer',
        'trello_link': 'Trello',
        'start_date': 'Start Date',
        'end_date': 'End Date',
        'phase': 'Phase',
        'prototype_link': 'Prototype',
        'slack_link': 'Slack',
        'estimated_days': 'Estimated Days',
        'checkbox_bc': 'CheckBoxe BC',
        'checkbox_trello': 'CheckBoxe Trello',
        'checkbox_wa': 'CheckBoxe WA',
        'checkbox_ws': 'CheckBoxe WS'
    }
    clean_df = df.copy()
    
    # Format 'priority' for export (e.g. 1.0 -> 1)
    if 'priority' in clean_df.columns:
        def _fmt_priority(v):
            if pd.isna(v): return v
            try:
                f_val = float(v)
                if f_val == int(f_val):
                    return int(f_val)
                return f_val
            except (ValueError, TypeError):
                return v
        clean_df['priority'] = clean_df['priority'].apply(_fmt_priority)

    # Filter only available columns mapped for export
    export_cols_keys = [k for k in export_cols_map.keys() if k in clean_df.columns]
    renamed_df = clean_df[export_cols_keys].rename(columns=export_cols_map)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        renamed_df.to_excel(writer, index=False, sheet_name='Updated Projects')
        
        if highlight_updated:
            worksheet = writer.sheets['Updated Projects']
            yellow_fill = PatternFill(start_color='FFFF00', end_color='FFFF00', fill_type='solid')
            
            # Apply highlight to specific updated cells
            for row_idx in range(len(clean_df)):
                for col_idx, key in enumerate(export_cols_keys):
                    flag_col = f"{key}_updated"
                    if flag_col in clean_df.columns and clean_df.iloc[row_idx][flag_col] == True:
                        # Row + 2 (1 for header, 1 for 0-index), Col + 1
                        cell = worksheet.cell(row=row_idx + 2, column=col_idx + 1)
                        cell.fill = yellow_fill
    
    return buffer.getvalue()


@st.dialog("Export Data")
def export_dialog(df):
    """Streamlit dialog to handle exporting projects."""
    st.write("Select which records you would like to export:")
    st.write("") # Spacing
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### Export All")
        st.caption(f"Export all {len(df)} projects")
        buffer_all = _generate_excel_buffer(df)
        st.download_button(
            "📥 Download All",
            data=buffer_all,
            file_name=f"projects_all_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
    with col2:
        st.markdown("#### Export Updated Only")
        # Find updated records based on _updated boolean columns
        updated_cols = [c for c in df.columns if c.endswith('_updated')]
        if updated_cols:
            updated_mask = df[updated_cols].any(axis=1)
            updated_df = df[updated_mask].reset_index(drop=True)
        else:
            updated_df = pd.DataFrame(columns=df.columns)
            
        st.caption(f"Export only the {len(updated_df)} modified projects")
        
        # If there are no updated records, disable the button
        buffer_updated = _generate_excel_buffer(updated_df, highlight_updated=True) if not updated_df.empty else b""
        st.download_button(
            "📥 Download Updated",
            data=buffer_updated,
            file_name=f"projects_updated_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            disabled=updated_df.empty,
            use_container_width=True
        )


from utils.lockout_helpers import get_lockout_schedule

def render_project_update_page_v2(user):
    """Render the React-based Project Update page."""
    st.subheader("Project Update", divider="blue")

    # Show persistent success message from import if it exists
    if "import_success_msg" in st.session_state:
        st.success(st.session_state["import_success_msg"])
        # We don't delete it immediately so the user can see it on the page they just landed on
        # But we'll clear it after the next rerun or if they stay here.
        # Actually, let's clear it now so it only shows once.
        del st.session_state["import_success_msg"]

    # Determine read-only status: Admins always edit, employees edit only if granted access
    is_admin = user.get("role") == "admin"
    has_edit_access = user.get("project_update_access", False)
    read_only = not (is_admin or has_edit_access)

    # --- Weekly Lockout Logic ---
    lockout_schedule = get_lockout_schedule()
    current_day = datetime.datetime.now().strftime("%a").upper()
    
    if not is_admin:
        if lockout_schedule.get(current_day, False):
            read_only = True
            st.error(f"🔒 **Updates are locked for today ({current_day}).** According to the Weekly Lockout Schedule, you cannot make changes today.")
    # ----------------------------

    if read_only and not (not is_admin and lockout_schedule.get(current_day, False)):
        st.info("ℹ️ View-only mode. You do not have permission to edit project attributes.")

    # 1. Fetch Master Data
    df = get_project_reports()

    # Calculate Last Modified Time from updated_at column
    last_mod_str = "Unknown"
    if not df.empty and 'updated_at' in df.columns:
        try:
            max_updated = pd.to_datetime(df['updated_at']).max()
            if pd.notna(max_updated):
                # Format: 13-05-2026 18:30
                last_mod_str = max_updated.strftime("%d-%m-%Y %H:%M")
        except Exception:
            pass
    
    # Display the timestamp with consistent styling
    st.markdown(f"<p style='color: #6B7280; font-size: 0.92rem; margin-top: -15px; margin-bottom: 20px;'>Last Modified: <span style='color: #2563EB; font-weight: 600;'>{last_mod_str}</span></p>", unsafe_allow_html=True)

    all_emps = get_all_employees()
    valid_emp_names = set(str(n).strip() for n in all_emps['employee_name'].dropna())

    if df.empty:
        st.info("No projects found in project_reports. Please upload via 'Import Data' → 'Update Projects'.")
        return

    # 2. Filter data to only include projects with valid lead engineers
    # Projects with leads not in the employee table are treated as non-relevant
    # We strip whitespace to handle potential data entry issues
    df['lead_engineer_clean'] = df['lead_engineer'].fillna('').str.strip()
    df = df[df['lead_engineer_clean'].isin(valid_emp_names)]

    if df.empty:
        st.info("No relevant projects found (Lead Engineer must be a valid employee).")
        return

    # Prepare data for the React component
    # Convert DataFrame to list of dicts, handling NaN/NaT
    projects_list = []
    for _, row in df.iterrows():
        record = {}
        for col in df.columns:
            if col == 'lead_engineer_clean': continue
            val = row[col]
            if pd.isna(val) or str(val).strip().lower() in ('nan', 'none', 'nat', ''):
                record[col] = None
            elif hasattr(val, 'isoformat'):
                record[col] = val.isoformat()
            elif col in ['start_date', 'end_date']:
                # Ensure date strings are in YYYY-MM-DD for the HTML5 date input
                try:
                    record[col] = pd.to_datetime(val).date().isoformat()
                except Exception:
                    record[col] = str(val)
            elif isinstance(val, bool):
                record[col] = val
            else:
                # Format Priority to remove .0 from whole numbers (e.g. 1.0 -> 1)
                if col == 'priority' and val is not None:
                    try:
                        f_val = float(val)
                        if f_val == int(f_val):
                            record[col] = str(int(f_val))
                        else:
                            record[col] = str(val)
                    except (ValueError, TypeError):
                        record[col] = str(val)
                else:
                    record[col] = str(val) if val is not None else None
        projects_list.append(record)

    # Extract unique lead engineers (already filtered by valid_emp_names above)
    lead_engineers = sorted(set(
        str(e).strip() for e in df['lead_engineer'].dropna().unique() 
        if str(e).strip() and str(e).strip().lower() != 'nan'
    ))
    
    # Use fixed status options from the provided screenshot
    status_options = [
        "Not started", "Awaiting Info", "At Beta", "In progress",
        "In testing", "Complete", "To be deployed", "Duplicate - Closed", "Ongoing"
    ]

    # Extract unique phases dynamically, preserving defaults if missing
    phase_options = sorted(set(
        str(e) for e in df['phase'].dropna().unique() if str(e).strip()
    ))
    for p in ["Analysis", "Design", "Development", "Testing", "Deployment", "Support"]:
        if p not in phase_options:
            phase_options.append(p)
    phase_options = sorted(set(phase_options))

    # Render the React component (height scales with content)
    result = project_update_component(
        projects=projects_list,
        lead_engineers=lead_engineers,
        phase_options=phase_options,
        status_options=status_options,
        read_only=read_only,
        key=f"pu_react_{st.session_state.get('pu_react_refresh', 0)}"
    )

    # Handle actions from the React component
    if result is not None:
        action = result.get("action")

        if action == "save":
            edits = result.get("edits", {})
            if edits:
                # Directly update via Supabase
                from database.connection import get_supabase_client
                supabase = get_supabase_client()
                
                save_count = 0
                for proj_code, changes in edits.items():
                    update_payload = {}
                    for col, new_val in changes.items():
                        update_payload[col] = new_val
                        flag_col = f"{col}_updated"
                        # We use the original df to check for column existence
                        if flag_col in df.columns:
                            update_payload[flag_col] = True
                    
                    if update_payload:
                        try:
                            supabase.table('project_reports').update(update_payload).eq('project_code', proj_code).execute()
                            save_count += 1
                        except Exception as e:
                            st.error(f"Error saving project {proj_code}: {e}")
                
                if save_count > 0:
                    st.success(f"✅ Successfully saved {save_count} project(s).")
                    # Refresh key to reload component with new data
                    st.session_state['pu_react_refresh'] = st.session_state.get('pu_react_refresh', 0) + 1
                    st.rerun()

        elif action == "open_export_modal":
            export_dialog(df)

"""Project Update 2 — React-based Project Attributes page."""
import streamlit as st
import pandas as pd
import io
import datetime
from openpyxl.styles import PatternFill
from database.queries import get_project_reports, save_project_updates, get_all_employees
from components.project_update_react import project_update_component


# ─────────────────────────────────────────────────────────────────────────────
# Cached data fetchers – avoid re-hitting Supabase on every interaction
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=30, show_spinner=False)
def _cached_project_reports():
    """Fetch project reports with a 30-second cache to reduce DB round-trips."""
    return get_project_reports()


@st.cache_data(ttl=120, show_spinner=False)
def _cached_employees():
    """Fetch employees with a 2-minute cache."""
    return get_all_employees()


def _invalidate_project_cache():
    """Clear the project reports cache after a save so fresh data loads."""
    _cached_project_reports.clear()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _round_actual_days(v):
    """Round actual_days: >=0.5 decimal rounds up, <0.5 rounds down."""
    if v is None or (hasattr(v, '__class__') and v.__class__.__name__ in ('float', 'int') and pd.isna(v)):
        return v
    try:
        import math
        f = float(v)
        frac = f - math.floor(f)
        return math.ceil(f) if frac >= 0.5 else math.floor(f)
    except (ValueError, TypeError):
        return v

def _generate_excel_buffer(df, highlight_updated=False, only_updated_values=False):
    """Generate an Excel buffer for the given DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Source data including ``*_updated`` flag columns.
    highlight_updated : bool
        If True, updated cells get a yellow background in the Excel file.
    only_updated_values : bool
        Deprecated. Kept for backwards compatibility but ignored to ensure
        all existing project fields/data are fully preserved and exported.
    """
    export_cols_map = {
        'project_code': 'Job No',
        'priority': 'Job Priority',
        'project_name': 'Project',
        'status': 'Status',
        'lead_engineer': 'Lead engineer',
        'trello_link': 'Trello',
        'start_date': 'Start Date',
        'end_date': 'End Date',
        'prototype_link': 'Prototype',
        'slack_link': 'Slack',
        'estimated_days': 'Estimated Days',
        'actual_days': 'Actual Days',
        'checkbox_bc': 'CheckBoxe BC',
        'checkbox_trello': 'CheckBoxe Trello',
        'checkbox_wa': 'CheckBoxe WA',
        'checkbox_ws': 'CheckBoxe WS'
    }

    # Columns whose values are always preserved (row identifiers)
    _always_keep = {'project_code'}

    clean_df = df.copy()
    
    if 'priority' in clean_df.columns:
        def _fmt_priority(v):
            if pd.isna(v): return v
            try:
                f_val = float(v)
                return int(f_val) if f_val == int(f_val) else f_val
            except (ValueError, TypeError):
                return v
        clean_df['priority'] = clean_df['priority'].apply(_fmt_priority)

    # Apply rounding to actual_days before export
    if 'actual_days' in clean_df.columns:
        clean_df['actual_days'] = clean_df['actual_days'].apply(_round_actual_days)

    # ── Map Lead Engineer name to Employee ID ────────────────────────────────
    all_emps = _cached_employees()
    name_to_id = {}
    if not all_emps.empty:
        name_to_id = {
            str(row['employee_name']).strip().lower(): str(row['employee_id']).strip()
            for _, row in all_emps.iterrows()
            if pd.notna(row['employee_name']) and pd.notna(row['employee_id'])
        }

    if 'lead_engineer' in clean_df.columns:
        def _map_lead_engineer(v):
            if pd.isna(v) or not v or str(v).strip().lower() in ('nan', 'none', 'nat', ''):
                return ''
            s = str(v).strip().lower()
            return name_to_id.get(s, v)
        clean_df['lead_engineer'] = clean_df['lead_engineer'].apply(_map_lead_engineer)

    # ── Standardise Date Formats to dd/mm/yy ─────────────────────────────────
    def _format_date_to_ddmmyy(v):
        if pd.isna(v) or not v or str(v).strip().lower() in ('nan', 'none', 'nat', ''):
            return ''
        try:
            if hasattr(v, 'strftime'):
                return v.strftime('%d/%m/%y')
            dt = pd.to_datetime(v)
            if pd.notna(dt):
                return dt.strftime('%d/%m/%y')
        except Exception:
            pass
        return str(v)

    if 'start_date' in clean_df.columns:
        clean_df['start_date'] = clean_df['start_date'].apply(_format_date_to_ddmmyy)
    if 'end_date' in clean_df.columns:
        clean_df['end_date'] = clean_df['end_date'].apply(_format_date_to_ddmmyy)

    # ── Convert Job No and Lead Engineer to numeric where possible ───────────
    def _to_numeric_where_possible(v):
        if pd.isna(v) or v is None:
            return v
        s = str(v).strip()
        if s.lower() in ('nan', 'none', 'nat', ''):
            return None
        try:
            f_val = float(s)
            if f_val == int(f_val):
                return int(f_val)
            return f_val
        except (ValueError, TypeError):
            return v

    if 'project_code' in clean_df.columns:
        clean_df['project_code'] = clean_df['project_code'].apply(_to_numeric_where_possible)
    if 'lead_engineer' in clean_df.columns:
        clean_df['lead_engineer'] = clean_df['lead_engineer'].apply(_to_numeric_where_possible)

    export_cols_keys = [k for k in export_cols_map.keys() if k in clean_df.columns]

    renamed_df = clean_df[export_cols_keys].rename(columns=export_cols_map)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        renamed_df.to_excel(writer, index=False, sheet_name='Updated Projects')
        
        if highlight_updated:
            worksheet = writer.sheets['Updated Projects']
            yellow_fill = PatternFill(start_color='FFFF00', end_color='FFFF00', fill_type='solid')
            for row_idx in range(len(clean_df)):
                for col_idx, key in enumerate(export_cols_keys):
                    flag_col = f"{key}_updated"
                    if flag_col in clean_df.columns and clean_df.iloc[row_idx][flag_col] == True:
                        cell = worksheet.cell(row=row_idx + 2, column=col_idx + 1)
                        cell.fill = yellow_fill
    
    return buffer.getvalue()


@st.dialog("Export Data")
def export_dialog(df):
    """Streamlit dialog to handle exporting projects."""
    st.write("Select which records you would like to export:")
    st.write("")
    
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
        updated_cols = [c for c in df.columns if c.endswith('_updated')]
        if updated_cols:
            updated_mask = df[updated_cols].any(axis=1)
            updated_df = df[updated_mask].reset_index(drop=True)
        else:
            updated_df = pd.DataFrame(columns=df.columns)
            
        st.caption(f"Export only the {len(updated_df)} modified projects")
        buffer_updated = _generate_excel_buffer(updated_df, highlight_updated=True, only_updated_values=True) if not updated_df.empty else b""
        st.download_button(
            "📥 Download Updated",
            data=buffer_updated,
            file_name=f"projects_updated_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            disabled=updated_df.empty,
            use_container_width=True
        )


@st.dialog("Send Reminders", width="medium")
def reminder_dialog(all_emps, df, displayed_project_codes):
    """Streamlit dialog to handle sending reminders."""
    st.write("Select the employees you want to send validation reminders to. The system will compile all validation errors for projects they are assigned as Lead Engineer.")
    st.write("")
    
    if displayed_project_codes is None:
        st.info("No projects are visible to send reminders for.")
        return
        
    # Find unique lead engineers from displayed projects
    displayed_str_codes = [str(c) for c in displayed_project_codes]
    displayed_df = df[df['project_code'].astype(str).isin(displayed_str_codes)]
    
    active_leads = set(displayed_df['lead_engineer'].dropna().str.strip().str.lower())
    
    # Filter all_emps to only those active lead engineers
    filtered_emps = []
    if not all_emps.empty:
        raw_list = all_emps.to_dict(orient='records')
        for r in raw_list:
            emp_name = str(r.get('employee_name', '')).strip().lower()
            if emp_name in active_leads:
                filtered_emps.append(r)
                
    if not filtered_emps:
        st.info("No employees found for visible projects.")
        return
        
    options = []
    emp_map = {}
    for emp in filtered_emps:
        name = emp.get('employee_name')
        email = emp.get('email')
        emp_id = emp.get('employee_id')
        if email and str(email).strip():
            display = f"{name} ({email})"
            options.append(display)
            emp_map[display] = emp
        else:
            display = f"⚠️ {name} (No Email configured)"
            options.append(display)
            emp_map[display] = emp
            
    # Let's show Select All checkbox to easily toggle selection
    select_all = st.checkbox("Select All Employees", value=True)
    default_selection = options if select_all else []
    
    selected_displays = st.multiselect(
        "Select Employees",
        options=options,
        default=default_selection,
        label_visibility="collapsed"
    )
    
    st.write("")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Cancel", use_container_width=True):
            st.rerun()
    with col2:
        valid_selected = [emp_map[d] for d in selected_displays if emp_map[d].get('email') and str(emp_map[d].get('email')).strip()]
        
        if st.button("Send Email", type="primary", use_container_width=True, disabled=not valid_selected):
            success_count = 0
            skipped_count = 0
            error_messages = []
            
            from services.email_service import send_reminder_email
            
            with st.spinner("Sending emails..."):
                for emp in valid_selected:
                    emp_id = emp.get('employee_id')
                    emp_name = emp.get('employee_name')
                    emp_email = emp.get('email')
                    
                    # Filter projects led by this employee and displayed
                    emp_projects_df = displayed_df[displayed_df['lead_engineer'].fillna('').str.strip().str.lower() == str(emp_name).strip().lower()]
                    
                    emp_projects_with_issues = []
                    for _, proj_row in emp_projects_df.iterrows():
                        issues = []
                        start = proj_row.get('start_date')
                        end = proj_row.get('end_date')
                        status = proj_row.get('status')
                        
                        if not start or pd.isna(start):
                            issues.append("Missing Start Date")
                        if not end or pd.isna(end):
                            issues.append("Missing End Date")
                            
                        if start and end and not pd.isna(start) and not pd.isna(end):
                            try:
                                s_dt = pd.to_datetime(start).date()
                                e_dt = pd.to_datetime(end).date()
                                if s_dt > e_dt:
                                    issues.append("Start Date is after End Date")
                            except:
                                pass
                                
                        validate_past_date_statuses = ["Not started", "Ongoing", "In testing", "Awaiting Info", "At Beta", "In progress"]
                        if status in validate_past_date_statuses and end and not pd.isna(end):
                            try:
                                e_dt = pd.to_datetime(end).date()
                                if e_dt < datetime.date.today():
                                    issues.append("Past date is not allowed.")
                            except:
                                pass
                                
                        if not proj_row.get('trello_link') or not str(proj_row.get('trello_link')).strip():
                            issues.append("Missing Trello Link")
                        if not proj_row.get('slack_link') or not str(proj_row.get('slack_link')).strip():
                            issues.append("Missing Slack Link")
                            
                        est = proj_row.get('estimated_days')
                        if est is None or pd.isna(est) or str(est).strip() == "" or str(est) == "0":
                            issues.append("Missing estimates")
                            
                        actual = proj_row.get('actual_days')
                        try:
                            actual_val = float(actual) if actual is not None and not pd.isna(actual) else 0.0
                            if actual_val > 1.0 and status == "Not started":
                                issues.append("Please check the status. The actual says more than one but the status is not started")
                        except:
                            pass
                            
                        bc = proj_row.get('checkbox_bc')
                        if bc == 1 or str(bc) == '1' or str(bc) == '1.0':
                            issues.append("Please check the BRD check box is not checked")
                            
                        trello_cb = proj_row.get('checkbox_trello')
                        if trello_cb == 1 or str(trello_cb) == '1' or str(trello_cb) == '1.0':
                            issues.append("Please check the Trello checkbox is not checked")
                            
                        wa = proj_row.get('checkbox_wa')
                        if wa == 1 or str(wa) == '1' or str(wa) == '1.0':
                            issues.append("Please check the WA check box is not checked")
                            
                        ws = proj_row.get('checkbox_ws')
                        if ws == 1 or str(ws) == '1' or str(ws) == '1.0':
                            issues.append("Please check that the WS checkbox is not checked")
                            
                        if issues:
                            emp_projects_with_issues.append({
                                "projectCode": str(proj_row.get('project_code', '')),
                                "projectName": str(proj_row.get('project_name', '')),
                                "issues": issues
                            })
                            
                    if not emp_projects_with_issues:
                        skipped_count += 1
                        continue
                        
                    success, msg = send_reminder_email(emp_id, emp_email, emp_name, emp_projects_with_issues)
                    if success:
                        success_count += 1
                    else:
                        error_messages.append(f"Failed to send email to {emp_name}: {msg}")
            
            if success_count > 0:
                st.toast(f"📨 Successfully sent reminder emails to {success_count} employee(s).", icon="✉️")
            if error_messages:
                for err in error_messages:
                    st.error(err)
            
            # Reset the component state by incrementing refresh key
            st.session_state['pu_react_refresh'] = st.session_state.get('pu_react_refresh', 0) + 1
            
            # small delay and rerun
            import time
            time.sleep(1)
            st.rerun()


def _prepare_projects_list(df):
    """Convert DataFrame rows to JSON-serialisable dicts for the React component."""
    projects_list = []
    for _, row in df.iterrows():
        record = {}
        for col in df.columns:
            if col == 'lead_engineer_clean':
                continue
            val = row[col]
            if pd.isna(val) or str(val).strip().lower() in ('nan', 'none', 'nat', ''):
                record[col] = None
            elif hasattr(val, 'isoformat'):
                record[col] = val.isoformat()
            elif col in ['start_date', 'end_date']:
                try:
                    record[col] = pd.to_datetime(val).date().isoformat()
                except Exception:
                    record[col] = str(val)
            elif isinstance(val, bool):
                record[col] = val
            else:
                if col == 'priority' and val is not None:
                    try:
                        f_val = float(val)
                        record[col] = str(int(f_val)) if f_val == int(f_val) else str(val)
                    except (ValueError, TypeError):
                        record[col] = str(val)
                else:
                    record[col] = str(val) if val is not None else None
        projects_list.append(record)
    return projects_list


# ─────────────────────────────────────────────────────────────────────────────
# Isolated save handler — uses @st.fragment to avoid full-page rerun on save
# ─────────────────────────────────────────────────────────────────────────────

@st.fragment
def _render_react_component(projects_list, lead_engineers, phase_options, status_options,
                             read_only, user, df, all_emps):
    """Render the React component inside a fragment so saves don't reload the full page."""
    refresh_key = st.session_state.get('pu_react_refresh', 0)

    # Convert all_emps DataFrame to records dict, handling NaN values safely
    employees_list = []
    if not all_emps.empty:
        raw_list = all_emps.to_dict(orient='records')
        for r in raw_list:
            clean_r = {}
            for k, v in r.items():
                if pd.isna(v) or str(v).strip().lower() in ('nan', 'none', 'nat'):
                    clean_r[k] = None
                else:
                    clean_r[k] = v
            employees_list.append(clean_r)

    result = project_update_component(
        projects=projects_list,
        lead_engineers=lead_engineers,
        employees=employees_list,
        current_user=user.get("employee_name", ""),
        user_role=user.get("role", "employee"),
        phase_options=phase_options,
        status_options=status_options,
        read_only=read_only,
        key=f"pu_react_{refresh_key}"
    )

    if result is None:
        return

    action = result.get("action")

    if action == "save":
        edits = result.get("edits", {})
        if edits:
            from database.connection import get_supabase_client
            supabase = get_supabase_client()
            save_count = 0

            with st.spinner("Saving changes…"):
                for proj_code, changes in edits.items():
                    update_payload = {}
                    for col, new_val in changes.items():
                        update_payload[col] = new_val
                        flag_col = f"{col}_updated"
                        if flag_col in df.columns:
                            update_payload[flag_col] = True

                    if update_payload:
                        try:
                            supabase.table('project_reports').update(update_payload).eq('project_code', proj_code).execute()
                            save_count += 1
                        except Exception as e:
                            st.error(f"Error saving project {proj_code}: {e}")

            if save_count > 0:
                _invalidate_project_cache()
                st.success(f"✅ Successfully saved {save_count} project(s).")
                st.session_state['pu_react_refresh'] = refresh_key + 1
                st.rerun()

    elif action == "open_export_modal":
        export_dialog(df)

    elif action == "open_reminder_modal":
        payload = result.get("payload", {})
        displayed_project_codes = payload.get("displayedProjectCodes", [])
        reminder_dialog(all_emps, df, displayed_project_codes)


# ─────────────────────────────────────────────────────────────────────────────
# Main page renderer
# ─────────────────────────────────────────────────────────────────────────────

from utils.lockout_helpers import get_lockout_schedule

def render_project_update_page_v2(user):
    """Render the React-based Project Update page."""
    st.subheader("Project Update", divider="blue")

    if "import_success_msg" in st.session_state:
        st.success(st.session_state.pop("import_success_msg"))

    is_admin = user.get("role") == "admin"
    has_edit_access = user.get("project_update_access", False)
    read_only = not (is_admin or has_edit_access)

    # Weekly Lockout Logic
    lockout_schedule = get_lockout_schedule()
    current_day = datetime.datetime.now().strftime("%a").upper()
    if not is_admin and lockout_schedule.get(current_day, False):
        read_only = True
        st.error(f"🔒 **Updates are locked for today ({current_day}).** According to the Weekly Lockout Schedule, you cannot make changes today.")

    if read_only and not (not is_admin and lockout_schedule.get(current_day, False)):
        st.info("ℹ️ View-only mode. You do not have permission to edit project attributes.")

    # ── Fetch data (cached) ──────────────────────────────────────────────────
    with st.spinner("Loading project data…"):
        df = _cached_project_reports()
        all_emps = _cached_employees()

    # Last Modified timestamp
    last_mod_str = "Unknown"
    if not df.empty and 'updated_at' in df.columns:
        try:
            max_updated = pd.to_datetime(df['updated_at']).max()
            if pd.notna(max_updated):
                last_mod_str = max_updated.strftime("%d-%m-%Y %H:%M")
        except Exception:
            pass

    st.markdown(
        f"<p style='color: #6B7280; font-size: 0.92rem; margin-top: -15px; margin-bottom: 20px;'>"
        f"Last Modified: <span style='color: #2563EB; font-weight: 600;'>{last_mod_str}</span></p>",
        unsafe_allow_html=True
    )

    valid_emp_names = set(str(n).strip() for n in all_emps['employee_name'].dropna())

    if df.empty:
        st.info("No projects found in project_reports. Please upload via 'Import Data' → 'Update Projects'.")
        return

    df['lead_engineer_clean'] = df['lead_engineer'].fillna('').str.strip()
    df = df[df['lead_engineer_clean'].isin(valid_emp_names)]

    if df.empty:
        st.info("No relevant projects found (Lead Engineer must be a valid employee).")
        return

    # ── Prepare component data ───────────────────────────────────────────────
    projects_list = _prepare_projects_list(df)

    lead_engineers = sorted(set(
        str(e).strip() for e in df['lead_engineer'].dropna().unique()
        if str(e).strip() and str(e).strip().lower() != 'nan'
    ))

    status_options = [
        "Not started", "Awaiting Info", "At Beta", "In progress",
        "In testing", "Complete", "To be deployed", "Duplicate - Closed", "Ongoing"
    ]

    phase_options = sorted(set(str(e) for e in df['phase'].dropna().unique() if str(e).strip()))
    for p in ["Analysis", "Design", "Development", "Testing", "Deployment", "Support"]:
        if p not in phase_options:
            phase_options.append(p)
    phase_options = sorted(set(phase_options))

    # ── Render React component inside a fragment ──────────────────────────────
    _render_react_component(
        projects_list, lead_engineers, phase_options, status_options,
        read_only, user, df, all_emps
    )

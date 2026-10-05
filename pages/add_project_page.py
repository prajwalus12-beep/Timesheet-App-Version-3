"""Add Project — Standalone page for registering new projects destined for FMP import.

Design reference: project_update_page_v2.py
Permissions:
  - All logged-in users can view and add/edit rows.
  - Admin-only: Export to Import FMP, Export to Import TS, Mark Added in FMP.
"""
import io
import datetime
import streamlit as st
import pandas as pd

from database.queries import (
    get_add_projects,
    create_add_project,
    update_add_project,
    mark_fmp_added,
    delete_add_project,
    delete_add_projects_bulk,
    check_project_code_exists,
    get_all_employees,
    is_employee_active
)

from components.add_project_react import project_update_component


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

STATUS_OPTIONS = [
    "Not started", "Awaiting Info", "At Beta", "In progress",
    "In testing", "Complete", "To be deployed", "Duplicate - Closed", "Ongoing",
]

PHASE_OPTIONS = [
    "Analysis", "Design", "Development", "Testing", "Deployment", "Support",
]

PRIORITY_OPTIONS = ["1", "2", "3", "4", "5", "High", "Medium", "Low", ""]


# ─────────────────────────────────────────────────────────────────────────────
# Cached helpers
# ─────────────────────────────────────────────────────────────────────────────

@st.cache_data(ttl=30, show_spinner=False)
def _cached_add_projects():
    return get_add_projects()


@st.cache_data(ttl=120, show_spinner=False)
def _cached_employees_ap():
    return get_all_employees()


def _invalidate_cache():
    _cached_add_projects.clear()


# ─────────────────────────────────────────────────────────────────────────────
# Excel export helpers
# ─────────────────────────────────────────────────────────────────────────────

def _safe_date(v):
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(v, 'date'):
        return v.date()
    if hasattr(v, 'year'):
        return v
    s = str(v).strip()
    if not s or s.lower() in ('nan', 'none', 'nat', ''):
        return None
    try:
        return pd.to_datetime(s, dayfirst=True).date()
    except Exception:
        return None


def _format_cb(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return 'TRUE'
    s = str(v).strip()
    if s in ('1', '1.0'):
        return 'FALSE'
    return 'TRUE'


def _generate_fmp_excel(df: pd.DataFrame) -> bytes:
    from utils.xlsx_export import sanitise_dataframe, deep_clean_worksheet, apply_column_widths
    from openpyxl.styles import PatternFill

    col_map = {
        'project_code':   'Job No',
        'priority':       'Job Priority',
        'project_name':   'Project',
        'status':         'Status',
        'lead_engineer':  'Lead engineer',
        'trello_link':    'Trello',
        'start_date':     'Start Date',
        'end_date':       'End Date',
        'prototype_link': 'Prototype',
        'slack_link':     'Slack',
        'estimated_days': 'Estimated Days',
        'actual_days':    'Actual Days',
        'checkbox_bc':    'CheckBoxe BC',
        'checkbox_trello':'CheckBoxe Trello',
        'checkbox_wa':    'CheckBoxe WA',
        'checkbox_ws':    'CheckBoxe WS',
        'notes':          'Notes',
    }

    clean = df.copy()

    all_emps = _cached_employees_ap()
    name_to_id = {}
    if not all_emps.empty:
        name_to_id = {
            str(r['employee_name']).strip().lower(): str(r['employee_id']).strip()
            for _, r in all_emps.iterrows()
            if pd.notna(r['employee_name']) and pd.notna(r['employee_id'])
        }
    if 'lead_engineer' in clean.columns:
        clean['lead_engineer'] = clean['lead_engineer'].apply(
            lambda v: name_to_id.get(str(v).strip().lower(), v) if pd.notna(v) and str(v).strip() else ''
        )

    if 'start_date' in clean.columns:
        clean['start_date'] = clean['start_date'].apply(_safe_date)
    if 'end_date' in clean.columns:
        clean['end_date'] = clean['end_date'].apply(_safe_date)

    for cb in ['checkbox_bc', 'checkbox_trello', 'checkbox_wa', 'checkbox_ws']:
        if cb in clean.columns:
            clean[cb] = clean[cb].apply(_format_cb)

    def _to_num(v):
        if pd.isna(v) or v is None:
            return v
        try:
            f = float(str(v).strip())
            return int(f) if f == int(f) else f
        except Exception:
            return v

    if 'project_code' in clean.columns:
        clean['project_code'] = clean['project_code'].apply(_to_num)
    if 'lead_engineer' in clean.columns:
        clean['lead_engineer'] = clean['lead_engineer'].apply(_to_num)
    if 'priority' in clean.columns:
        clean['priority'] = clean['priority'].apply(_to_num)

    export_keys = [k for k in col_map if k in clean.columns]
    renamed = clean[export_keys].rename(columns=col_map)
    renamed = sanitise_dataframe(renamed)

    date_col_indices = [
        i + 1 for i, c in enumerate(renamed.columns) if c in ('Start Date', 'End Date')
    ]
    n_rows = len(renamed) + 1
    n_cols = len(renamed.columns)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl', date_format='DD-MM-YYYY', datetime_format='DD-MM-YYYY') as writer:
        renamed.to_excel(writer, index=False, sheet_name='Add Projects')
        ws = writer.sheets['Add Projects']
        for ci in date_col_indices:
            for ri in range(2, n_rows + 1):
                cell = ws.cell(row=ri, column=ci)
                if cell.value is not None:
                    cell.number_format = 'DD-MM-YYYY'
        apply_column_widths(ws, n_rows, n_cols, comment_col_name='Notes')
        deep_clean_worksheet(ws, n_rows, n_cols)

    return buf.getvalue()


def _generate_ts_excel(df: pd.DataFrame) -> bytes:
    from utils.xlsx_export import sanitise_dataframe, deep_clean_worksheet, apply_column_widths

    col_map = {
        'project_code':  'Job No',
        'project_name':  'Project',
        'status':        'Status',
        'lead_engineer': 'Lead engineer',
        'phase':         'Phase',
        'start_date':    'Start Date',
        'end_date':      'End Date',
        'estimated_days':'Estimated Days',
        'actual_days':   'Actual Days',
    }

    clean = df.copy()
    if 'start_date' in clean.columns:
        clean['start_date'] = clean['start_date'].apply(_safe_date)
    if 'end_date' in clean.columns:
        clean['end_date'] = clean['end_date'].apply(_safe_date)
    if 'project_code' in clean.columns:
        clean['project_code'] = clean['project_code'].apply(
            lambda v: (lambda s: int(float(s)) if s.replace('.', '', 1).isdigit() else s)(str(v).strip())
            if pd.notna(v) else v
        )

    export_keys = [k for k in col_map if k in clean.columns]
    renamed = clean[export_keys].rename(columns=col_map)
    renamed = sanitise_dataframe(renamed)

    date_col_indices = [
        i + 1 for i, c in enumerate(renamed.columns) if c in ('Start Date', 'End Date')
    ]
    n_rows = len(renamed) + 1
    n_cols = len(renamed.columns)

    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine='openpyxl', date_format='DD-MM-YYYY', datetime_format='DD-MM-YYYY') as writer:
        renamed.to_excel(writer, index=False, sheet_name='TS Import')
        ws = writer.sheets['TS Import']
        for ci in date_col_indices:
            for ri in range(2, n_rows + 1):
                cell = ws.cell(row=ri, column=ci)
                if cell.value is not None:
                    cell.number_format = 'DD-MM-YYYY'
        apply_column_widths(ws, n_rows, n_cols, comment_col_name='None')
        deep_clean_worksheet(ws, n_rows, n_cols)

    return buf.getvalue()


@st.dialog("Export Add Projects")
def export_dialog(df):
    st.write("Select the export format:")
    
    ts_now = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    c1, c2 = st.columns(2)
    with c1:
        fmp_buf = _generate_fmp_excel(df)
        st.download_button(
            "📥 Export → FMP",
            data=fmp_buf,
            file_name=f"add_project_fmp_{ts_now}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with c2:
        ts_buf = _generate_ts_excel(df)
        st.download_button(
            "📥 Export → TS",
            data=ts_buf,
            file_name=f"add_project_ts_{ts_now}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )


def _prepare_projects_list(df):
    """Convert DataFrame rows to JSON-serialisable dicts for the React component."""
    projects_list = []
    for _, row in df.iterrows():
        record = {}
        for col in df.columns:
            val = row[col]
            if pd.isna(val) or str(val).strip().lower() in ('nan', 'none', 'nat', ''):
                record[col] = None
            elif hasattr(val, 'isoformat'):
                record[col] = val.isoformat()
            elif col in ['start_date', 'end_date', 'created_at', 'updated_at']:
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


@st.fragment
def _render_react_component(projects_list, lead_engineers, phase_options, status_options, read_only, user, df, all_emps):
    refresh_key = st.session_state.get('ap_react_refresh', 0)
    
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
        is_add_mode=True,
        key=f"ap_react_{refresh_key}"
    )

    if result is None:
        return

    action = result.get("action")

    if action == "save":
        is_admin = user.get("role") == "admin"
        if not is_admin and not is_employee_active(user.get("employee_id")):
            st.error("Employee is inactive. This action is not available for inactive employees.")
            return

        edits = result.get("edits", {})
        if edits:
            save_count = 0
            with st.spinner("Saving changes…"):
                for proj_code, changes in edits.items():
                    if changes.get("_isNew"):
                        payload = {}
                        for col, new_val in changes.items():
                            if col != "_isNew":
                                payload[col] = new_val
                        
                        # Backend duplicate project code check
                        new_code = str(payload.get("project_code", "")).strip()
                        if new_code and check_project_code_exists(new_code):
                            st.error(f"❌ Project Code **{new_code}** already exists. Please use a unique project code.")
                            continue
                                
                        # Handle checkbox encoding back to Python (True/False -> None/1)
                        # The React component handles them as True/False or string "True"/"False"
                        # We must map them for DB
                        def parse_bool(v):
                            if str(v).lower() in ("true", "1"): return True
                            return False
                        for cb in ['checkbox_bc', 'checkbox_trello', 'checkbox_wa', 'checkbox_ws']:
                            if cb in payload:
                                payload[cb] = None if parse_bool(payload[cb]) else 1
                                
                        ok, msg, _ = create_add_project(payload, user.get("employee_id"), user.get("employee_name"))
                        if ok: save_count += 1
                        else: st.error(f"Error saving new project {proj_code}: {msg}")
                    else:
                        row = df[df['project_code'] == proj_code]
                        if row.empty:
                            continue
                        record_id = row.iloc[0]['id']
                        
                        update_payload = {}
                        for col, new_val in changes.items():
                            update_payload[col] = new_val
                            
                        # Handle checkbox encoding
                        def parse_bool(v):
                            if str(v).lower() in ("true", "1"): return True
                            return False
                        for cb in ['checkbox_bc', 'checkbox_trello', 'checkbox_wa', 'checkbox_ws']:
                            if cb in update_payload:
                                update_payload[cb] = None if parse_bool(update_payload[cb]) else 1

                        if update_payload:
                            ok, msg = update_add_project(record_id, update_payload, user.get("employee_id"), user.get("employee_name"))
                            if ok: save_count += 1
                            else: st.error(f"Error updating project {proj_code}: {msg}")

            if save_count > 0:
                _invalidate_cache()
                st.success(f"✅ Successfully saved {save_count} project(s).")
                st.session_state['ap_react_refresh'] = refresh_key + 1
                st.rerun()

    elif action == "delete_projects":
        # Single or multi-delete
        record_ids = result.get("record_ids", [])
        if record_ids:
            with st.spinner("Deleting project(s)…"):
                ok, msg = delete_add_projects_bulk(record_ids)
            if ok:
                _invalidate_cache()
                st.success(f"✅ {msg}")
                st.session_state['ap_react_refresh'] = refresh_key + 1
                st.rerun()
            else:
                st.error(f"❌ Error deleting: {msg}")

    elif action == "check_project_code":
        # Frontend requests a duplicate-code check
        code = result.get("project_code", "")
        exclude_id = result.get("exclude_id")  # None for new, int for existing
        exists = check_project_code_exists(code, exclude_id)
        # We can't easily push back to React, so store in session state;
        # the React component will use the server-side save validation instead.
        st.session_state[f"code_exists_{code}"] = exists

    elif action == "open_export_modal":
        export_dialog(df)


def render_add_project_page(user):
    st.subheader("Add Project", divider="blue")

    is_admin = user.get("role") == "admin"
    is_active = is_employee_active(user.get("employee_id")) if not is_admin else True
    read_only = not (is_admin or is_active)

    with st.spinner("Loading projects…"):
        df = _cached_add_projects()
        all_emps = _cached_employees_ap()

    lead_engineers = sorted(all_emps['employee_name'].dropna().unique().tolist()) if not all_emps.empty else []
    
    if df.empty:
        df = pd.DataFrame(columns=[
            "id", "project_code", "project_name", "priority", "status", "lead_engineer",
            "phase", "trello_link", "prototype_link", "slack_link", "estimated_days", "actual_days",
            "start_date", "end_date", "checkbox_bc", "checkbox_trello", "checkbox_wa", "checkbox_ws", "notes",
            "created_at", "updated_at"
        ])

    projects_list = _prepare_projects_list(df)

    _render_react_component(
        projects_list=projects_list,
        lead_engineers=lead_engineers,
        phase_options=PHASE_OPTIONS,
        status_options=STATUS_OPTIONS,
        read_only=read_only,
        user=user,
        df=df,
        all_emps=all_emps
    )

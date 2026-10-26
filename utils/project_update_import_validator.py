"""Helper module for validating project updates before importing sheets.

Identifies manually updated/marked fields in existing projects, compares them
with incoming sheet data, and generates structured comparison records and styling.
"""
import pandas as pd
import math
from database.connection import get_supabase_client
from database.queries import _normalize_code, _parse_priority, _parse_date_value, _parse_checkbox_value, _parse_int_value

# Human-readable labels for database fields
FIELD_LABELS = {
    'project_name': 'Project Name',
    'priority': 'Job Priority',
    'status': 'Project Status',
    'lead_engineer': 'Lead Engineer',
    'trello_link': 'Trello Link',
    'start_date': 'Start Date',
    'end_date': 'End Date',
    'phase': 'Phase',
    'prototype_link': 'Prototype Link',
    'slack_link': 'Slack Link',
    'estimated_days': 'Estimated Days',
    'actual_days': 'Actual Days',
    'checkbox_bc': 'BRD Checkbox (BC)',
    'checkbox_trello': 'Trello Checkbox',
    'checkbox_wa': 'WA Checkbox',
    'checkbox_ws': 'WS Checkbox',
    'notes': 'Notes',
}

# Aliases used in incoming sheets
FIELD_ALIASES = {
    'project_name': ['Project', 'Project Name', 'Project_Name', 'Priority'],
    'priority': ['Job Priority', 'Priority Level', 'Job_Priority', 'Priority_Level', 'Job Priority Level', 'Priority', 'priority'],
    'status': ['Status', 'Project Status', 'Search_Project'],
    'lead_engineer': ['Lead engineer', 'Lead Engineer', 'Lead'],
    'trello_link': ['Trello', 'Trello Link', 'Trello_Link'],
    'start_date': ['Start Date', 'Date Start', 'Date_Start', 'Start'],
    'end_date': ['End Date', 'Date End', 'Finish Date', 'Date Finish', 'Finish', 'Date_Finish', 'End'],
    'phase': ['Phase', 'Project Phase', 'Current Phase_g'],
    'prototype_link': ['Prototype', 'Prototype Link', 'Prototype_Link'],
    'slack_link': ['Slack', 'Slack Link', 'Slack URL', 'Slack_Link'],
    'estimated_days': ['Estimated Days', 'Estimate Days', 'Days'],
    'actual_days': ['Actual Days', 'Actual_Days', 'ActualDays'],
    'checkbox_bc': ['CheckBoxe BC', 'CheckBoxe_BC', 'BRD'],
    'checkbox_trello': ['CheckBoxe Trello', 'CheckBoxe_Trello', 'Trello Check'],
    'checkbox_wa': ['CheckBoxe WA', 'CheckBoxe_WA', 'WA'],
    'checkbox_ws': ['CheckBoxe WS', 'CheckBoxe_WS', 'WS'],
    'notes': ['Notes', 'Note', 'Comments', 'Comment', 'notes'],
}


def _normalize_cmp(v):
    """Normalize values for robust equality comparison."""
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except (TypeError, ValueError):
        pass
    try:
        f_v = float(v)
        if math.isnan(f_v):
            return None
        if f_v == int(f_v):
            return str(int(f_v))
        return str(f_v)
    except (ValueError, TypeError):
        s = str(v).strip()
        if s.lower() in ('nan', 'none', 'nat', 'null', ''):
            return None
        return s


def _format_display_value(v, db_field=None):
    """Format raw or parsed values cleanly for UI table presentation."""
    if v is None:
        return "(empty)"
    try:
        if pd.isna(v):
            return "(empty)"
    except (TypeError, ValueError):
        pass
    if db_field in ('checkbox_bc', 'checkbox_trello', 'checkbox_wa', 'checkbox_ws'):
        # In DB: 1 means Unchecked, None means Checked
        s = str(v).strip().lower()
        if s in ('1', '1.0', 'true', 'x', 'yes', 'checked'):
            return "Unchecked"
        if s in ('none', '(empty)', '', '0', '0.0', 'false'):
            return "Checked"
    s = str(v).strip()
    return s if s and s.lower() not in ('nan', 'none', 'nat', 'null') else "(empty)"


def get_column_mapping(df_columns):
    """Match uploaded sheet columns against known field aliases."""
    col_mapping = {}
    df_cols_lower = {str(c).strip().lower(): str(c).strip() for c in df_columns}
    for db_f, aliases in FIELD_ALIASES.items():
        found = False
        for a in aliases:
            if a in df_columns:
                col_mapping[db_f] = a
                found = True
                break
            if a.lower() in df_cols_lower:
                col_mapping[db_f] = df_cols_lower[a.lower()]
                found = True
                break
        if not found:
            col_mapping[db_f] = None
    return col_mapping


def validate_project_updates_import(df):
    """Analyze incoming sheet against existing project_reports in DB.

    Returns:
        dict with:
            - has_conflicts: bool (True if any manually updated field differs)
            - has_manual_updates: bool (True if any affected project had updated fields)
            - mismatches_count: int
            - affected_projects_count: int
            - comparison_rows: list of dicts for the warning table
            - project_comparisons: dict mapping project_code -> list of field diffs
            - missing_in_sheet: list of field names that exist in project but missing from sheet
            - unrecognised_columns: list of columns in sheet that don't map to any project field
    """
    supabase = get_supabase_client()
    if not supabase:
        return {
            "error": "Configuration error: database connection not available.",
            "has_conflicts": False,
            "has_manual_updates": False,
            "mismatches_count": 0,
            "affected_projects_count": 0,
            "comparison_rows": [],
            "project_comparisons": {},
            "missing_in_sheet": [],
            "unrecognised_columns": []
        }

    # Fetch employees for lead engineer mapping
    emp_res = supabase.table('employee').select('employee_id, employee_name').execute()
    emp_data = emp_res.data or []
    id_to_name = {}
    name_to_name = {}
    for emp in emp_data:
        eid = emp.get('employee_id')
        ename = emp.get('employee_name')
        if eid and ename:
            id_to_name[_normalize_code(eid).strip().lower()] = ename
        if ename:
            name_to_name[ename.strip().lower()] = ename

    def _parse_lead_engineer(val):
        if pd.isna(val) or val is None:
            return ""
        s_val = str(val).strip()
        if s_val.lower() in ('nan', 'none', 'nat', ''):
            return ""
        norm_val = _normalize_code(s_val).strip().lower()
        if norm_val in id_to_name:
            return id_to_name[norm_val]
        if norm_val in name_to_name:
            return name_to_name[norm_val]
        lower_val = s_val.lower()
        if lower_val in name_to_name:
            return name_to_name[lower_val]
        return s_val

    # Fetch existing project_reports
    existing_res = supabase.table('project_reports').select('*').execute()
    existing_map = {str(r.get('project_code', '')).strip(): r for r in (existing_res.data or []) if r.get('project_code')}

    col_mapping = get_column_mapping(df.columns)

    # Detect unrecognised columns in the sheet
    known_sheet_cols = {c for c in col_mapping.values() if c is not None}
    # Add Job No / Project Code columns as known
    code_aliases = {'job no', 'project code', 'job_no', 'project_code', 'code'}
    unrecognised_columns = [
        c for c in df.columns
        if str(c).strip() not in known_sheet_cols and str(c).strip().lower() not in code_aliases
    ]

    # Detect fields in project that are missing from imported sheet
    missing_in_sheet = [
        FIELD_LABELS.get(f, f)
        for f, mapped_col in col_mapping.items()
        if mapped_col is None
    ]

    # Data fields to process: (db_f, parser, default)
    data_fields = [
        ('project_name', lambda x: str(x).strip() if pd.notna(x) else "", ""),
        ('priority', _parse_priority, None),
        ('status', lambda x: str(x).strip() if pd.notna(x) else 'In progress', 'In progress'),
        ('lead_engineer', _parse_lead_engineer, ""),
        ('trello_link', lambda x: str(x).strip() if pd.notna(x) and str(x).strip().lower() not in ('nan', 'none', 'nat', '') else None, None),
        ('start_date', _parse_date_value, None),
        ('end_date', _parse_date_value, None),
        ('phase', lambda x: str(x).strip() if pd.notna(x) else 'Analysis', 'Analysis'),
        ('prototype_link', lambda x: str(x).strip() if pd.notna(x) and str(x).strip().lower() not in ('nan', 'none', 'nat', '') else None, None),
        ('slack_link', lambda x: str(x).strip() if pd.notna(x) and str(x).strip().lower() not in ('nan', 'none', 'nat', '') else None, None),
        ('estimated_days', _parse_int_value, None),
        ('actual_days', lambda x: round(float(x)) if x is not None and pd.notna(x) and str(x).strip() not in ('', 'nan', 'none') else None, None),
        ('checkbox_bc', _parse_checkbox_value, None),
        ('checkbox_trello', _parse_checkbox_value, None),
        ('checkbox_wa', _parse_checkbox_value, None),
        ('checkbox_ws', _parse_checkbox_value, None),
        ('notes', lambda x: str(x).strip() if pd.notna(x) and str(x).strip().lower() not in ('nan', 'none', 'nat', '') else None, None),
    ]

    comparison_rows = []
    project_comparisons = {}
    mismatches_count = 0
    affected_projects = set()
    has_manual_updates = False

    for _, row in df.iterrows():
        raw_code = row.get('Job No') or row.get('Project Code') or row.get('Job_No') or row.get('Project_Code') or ''
        code = _normalize_code(raw_code)
        if not code or code.lower() == 'nan':
            continue

        if code not in existing_map:
            # New project being added — no overwrite risk of existing manual updates
            continue

        existing = existing_map[code]
        p_name = existing.get('project_name') or code

        # Resolve project_name for incoming sheet if needed
        proj_col = col_mapping.get('project_name')
        raw_proj = row.get(proj_col) if proj_col else None
        if pd.isna(raw_proj) or str(raw_proj).strip() == "":
            for alt_alias in FIELD_ALIASES['project_name']:
                if alt_alias in df.columns:
                    alt_val = row.get(alt_alias)
                    if pd.notna(alt_val) and str(alt_val).strip() != "":
                        raw_proj = alt_val
                        break

        proj_diffs = []

        for db_f, parser, default in data_fields:
            flag_col = f"{db_f}_updated"
            is_manually_updated = bool(existing.get(flag_col, False))

            excel_f = col_mapping.get(db_f)
            is_mapped = excel_f is not None

            if db_f == 'project_name':
                imp_val = str(raw_proj).strip() if pd.notna(raw_proj) else default
            else:
                raw_val = row.get(excel_f) if is_mapped else None
                imp_val = parser(raw_val) if (raw_val is not None and is_mapped) else default

            db_val = existing.get(db_f)

            if not is_mapped:
                status_str = "⚠ Missing in Sheet"
                is_match = False
                imp_display = "(not in sheet)"
            else:
                imp_display = _format_display_value(imp_val, db_f)
                if _normalize_cmp(imp_val) == _normalize_cmp(db_val):
                    status_str = "✓ Match"
                    is_match = True
                else:
                    status_str = "⚠ Mismatch"
                    is_match = False

            curr_display = _format_display_value(db_val, db_f)

            # Record if this field was manually updated, or if it differs
            if is_manually_updated:
                has_manual_updates = True
                affected_projects.add(code)
                if not is_match:
                    mismatches_count += 1

                comparison_rows.append({
                    "Project Code": code,
                    "Project Name": p_name,
                    "Field": FIELD_LABELS.get(db_f, db_f),
                    "db_field": db_f,
                    "Current Project Value": curr_display,
                    "Imported Sheet Value": imp_display,
                    "Status": status_str,
                    "is_mismatch": not is_match,
                    "is_manually_updated": True
                })

            proj_diffs.append({
                "field": db_f,
                "label": FIELD_LABELS.get(db_f, db_f),
                "current_val": curr_display,
                "imported_val": imp_display,
                "is_match": is_match,
                "is_manually_updated": is_manually_updated
            })

        project_comparisons[code] = proj_diffs

    return {
        "has_conflicts": mismatches_count > 0,
        "has_manual_updates": has_manual_updates,
        "mismatches_count": mismatches_count,
        "affected_projects_count": len(affected_projects),
        "comparison_rows": comparison_rows,
        "project_comparisons": project_comparisons,
        "missing_in_sheet": missing_in_sheet,
        "unrecognised_columns": unrecognised_columns
    }

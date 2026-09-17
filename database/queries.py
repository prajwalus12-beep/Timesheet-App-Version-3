import pandas as pd
from database.connection import get_supabase_client
from services.auth_service import hash_password, encrypt_data, decrypt_data

print(f"DEBUG: Loading queries.py from {__file__}")

def get_all_employees(exclude_admin=False):
    """Fetch all employees using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame(columns=['employee_id', 'employee_name', 'slack_id', 'email', 'status'])
    
    # Try fetching with email and status columns
    try:
        query = supabase.table('employee').select('employee_id, employee_name, slack_id, email, status')
        if exclude_admin:
            query = query.neq('employee_id', 'admin')
        res = query.order('employee_name').execute()
        data = res.data or []
        df = pd.DataFrame(data, columns=['employee_id', 'employee_name', 'slack_id', 'email', 'status'])
        df['status'] = df['status'].fillna(1).astype(int)
        return df
    except Exception:
        # Fallback if email or status column isn't accessible
        query = supabase.table('employee').select('employee_id, employee_name, slack_id')
        if exclude_admin:
            query = query.neq('employee_id', 'admin')
        res = query.order('employee_name').execute()
        data = res.data or []
        df = pd.DataFrame(data, columns=['employee_id', 'employee_name', 'slack_id'])
        df['email'] = None
        df['status'] = 1
        return df

def is_employee_active(emp_id):
    """Check if an employee is active (status = 1). Admins are assumed active."""
    if not emp_id: return False
    if str(emp_id).lower() == 'admin': return True
    supabase = get_supabase_client()
    if not supabase: return False
    try:
        res = supabase.table('employee').select('status').eq('employee_id', emp_id).execute()
        if res.data:
            return res.data[0].get('status', 1) == 1
    except Exception:
        pass
    return False

def get_all_projects(include_leave=False):
    """Fetch all projects using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame(columns=['project_code', 'project_name', 'status', 'priority', 'lead_engineer', 'trello_link'])
    
    res = supabase.table('project').select('project_code, project_name, status, priority, lead_engineer, trello_link').order('project_code', desc=True).execute()
    data = res.data or []
    
    # Decrypt project names
    decrypted_res = [[r['project_code'], decrypt_data(r['project_name']), r['status'], r.get('priority'), r.get('lead_engineer'), r.get('trello_link')] for r in data]
    df = pd.DataFrame(decrypted_res, columns=['project_code', 'project_name', 'status', 'priority', 'lead_engineer', 'trello_link'])
    if not include_leave and not df.empty:
        df = df[~df['project_code'].astype(str).str.startswith('LEAVE-')].reset_index(drop=True)
    return df

def get_user_by_username(username):
    """Fetch user details using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return None
    
    try:
        # Try fetching with employee details
        res = supabase.table('users').select('id, employee_id, username, password, failed_attempts, locked_until, employee:employee(employee_name, project_update_access)').eq('username', username).execute()
    except Exception:
        # Fallback if employee table join fails or schema differs
        res = supabase.table('users').select('id, employee_id, username, password, failed_attempts, locked_until').eq('username', username).execute()
        
    data = res.data
    if data:
        u = data[0]
        emp = u.get('employee') or {}
        return (u['id'], u['employee_id'], u['username'], u['password'], u['failed_attempts'], u['locked_until'], emp.get('project_update_access', False), emp.get('employee_name'))
    return None

def update_user_lockout(username, failed_attempts, locked_until=None):
    """Update failed login attempts and lockout timestamp using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    try:
        supabase.table('users').update({
            'failed_attempts': failed_attempts, 
            'locked_until': locked_until.isoformat() if locked_until else None
        }).eq('username', username).execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def get_all_users():
    """Fetch all users with their details using Supabase SDK join-like approach."""
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame(columns=['id', 'username', 'employee_name', 'slack_id', 'password', 'project_update_access', 'employee_id', 'email', 'status'])
    
    try:
        # Try fetching with the new columns
        res = supabase.table('users').select('id, username, employee_id, password, employee:employee(employee_name, slack_id, project_update_access, email, status)').order('username').execute()
    except Exception:
        # Fallback if columns don't exist yet
        res = supabase.table('users').select('id, username, employee_id, password, employee:employee(employee_name, slack_id)').order('username').execute()
    
    data = res.data or []
    rows = []
    for r in data:
        emp = r.get('employee') or {}
        rows.append([
            r['id'],
            r['username'],
            emp.get('employee_name'),
            emp.get('slack_id'),
            r['password'],
            emp.get('project_update_access', False), # Defaults to False if missing
            r['employee_id'],
            emp.get('email'),
            emp.get('status', 1)
        ])
    
    return pd.DataFrame(rows, columns=['id', 'username', 'employee_name', 'slack_id', 'password', 'project_update_access', 'employee_id', 'email', 'status'])

def get_employee_by_id(emp_id):
    """Fetch single employee details using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return None
    
    res = supabase.table('employee').select('*').eq('employee_id', emp_id).execute()
    return res.data[0] if res.data else None

def add_timesheet_entry(emp_id, emp_name, project_code, project_name, date, hours, phase, project_status="Not started", comment=""):
    """Insert a new timesheet entry using Supabase SDK."""
    if not is_employee_active(emp_id):
        return False, "Employee is inactive. This action is not available for inactive employees."
        
    date_str = date.isoformat() if hasattr(date, 'isoformat') else date
    if not str(project_code).startswith("LEAVE-") and has_leave_for_date(emp_id, date_str):
        return False, "This date is registered as approved leave. Standard work hours cannot be logged for leave dates."

    if not str(project_code).startswith("LEAVE-") and not str(project_code).startswith("HOLIDAY"):
        is_holiday, h_info = has_active_holiday_for_date(emp_id, date_str)
        if is_holiday:
            return False, f"This date ({date_str}) is configured as a Holiday ('{h_info['holiday_name']}'). If you worked on this day, please remove the holiday entry from your timesheet first."

    if str(project_code).startswith("LEAVE-"):
        ensure_leave_projects_exist()

    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    phase_map = {"Analysis": "1", "Design": "2", "Development": "3", "Testing": "4", "Deployement": "5", "Support": "6"}
    phase_code = phase_map.get(phase, phase)
    
    data = {
        "emp_id": emp_id,
        "emp_name": emp_name,
        "project_code": project_code,
        "project_name": encrypt_data(project_name),
        "date": date.isoformat() if hasattr(date, 'isoformat') else date,
        "hours": float(hours),
        "Phase": phase_code,
        "project_status": project_status,
        "comment": str(comment).strip()[:400] if pd.notna(comment) and str(comment).strip() else None
    }
    
    try:
        supabase.table('timesheet').insert(data).execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def has_leave_for_date(emp_id, date):
    """Check if the employee has any leave registered on the given date."""
    supabase = get_supabase_client()
    if not supabase: return False
    date_str = date.isoformat() if hasattr(date, 'isoformat') else date
    try:
        # Fetch entries for this employee and date
        res = supabase.table('timesheet').select('project_code').eq('emp_id', emp_id).eq('date', date_str).execute()
        data = res.data or []
        for row in data:
            if str(row.get('project_code', '')).startswith('LEAVE-'):
                return True
        return False
    except Exception:
        return False

LEAVE_PROJECT_TYPES = {
    "Casual Leave": ("LEAVE-CL", "Casual Leave (CL)"),
    "Sick Leave": ("LEAVE-SL", "Sick Leave (SL)"),
    "Earned/Paid Leave": ("LEAVE-PL", "Earned/Paid Leave (PL)"),
    "Unpaid Leave": ("LEAVE-UL", "Unpaid Leave (UL)")
}

def ensure_leave_projects_exist():
    """Ensure standard leave project records exist in the project table to satisfy foreign key constraints."""
    supabase = get_supabase_client()
    if not supabase:
        return
    try:
        leave_records = [
            {"project_code": "LEAVE-CL", "project_name": encrypt_data("Casual Leave (CL)"), "status": "Leave"},
            {"project_code": "LEAVE-SL", "project_name": encrypt_data("Sick Leave (SL)"), "status": "Leave"},
            {"project_code": "LEAVE-PL", "project_name": encrypt_data("Earned/Paid Leave (PL)"), "status": "Leave"},
            {"project_code": "LEAVE-UL", "project_name": encrypt_data("Unpaid Leave (UL)"), "status": "Leave"},
            {"project_code": "LEAVE-OTHER", "project_name": encrypt_data("Leave (Other)"), "status": "Leave"},
        ]
        supabase.table('project').upsert(leave_records, on_conflict='project_code').execute()
    except Exception:
        pass

def add_leave_entries(emp_id, emp_name, leave_type_str, start_date, end_date, reason):
    """Insert one or more leave entries for a date range."""
    import datetime
    
    # Ensure leave project entries exist in project table to satisfy timesheet foreign key constraint
    ensure_leave_projects_exist()
    
    project_code, project_name = LEAVE_PROJECT_TYPES.get(leave_type_str, ("LEAVE-OTHER", f"Leave ({leave_type_str})"))
    
    # In case project_code is custom or not in the standard list, ensure it's in project table
    try:
        supabase = get_supabase_client()
        if supabase:
            supabase.table('project').upsert([{
                "project_code": project_code,
                "project_name": encrypt_data(project_name),
                "status": "Leave"
            }], on_conflict='project_code').execute()
    except Exception:
        pass
    
    current_date = start_date
    success_count = 0
    errors = []
    
    while current_date <= end_date:
        ok, err = add_timesheet_entry(
            emp_id=emp_id,
            emp_name=emp_name,
            project_code=project_code,
            project_name=project_name,
            date=current_date,
            hours=8.0,
            phase="Analysis", # Dummy phase
            project_status="Approved Leave",
            comment=reason
        )
        if ok:
            success_count += 1
        else:
            errors.append(f"{current_date}: {err}")
            
        current_date += datetime.timedelta(days=1)
        
    if errors:
        return False, "; ".join(errors)
    return True, f"Successfully added {success_count} leave days."

def get_timesheets(start_date=None, end_date=None, emp_id=None, project_code=None, include_holidays=True):
    """Fetch timesheet entries with optional filters using Supabase SDK, dynamically merging holidays."""
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()
    
    query = supabase.table('timesheet').select('id, emp_id, emp_name, project_code, project_name, date, hours, Phase, project_status, comment')
    
    if start_date: query = query.gte('date', start_date.isoformat() if hasattr(start_date, 'isoformat') else start_date)
    if end_date: query = query.lte('date', end_date.isoformat() if hasattr(end_date, 'isoformat') else end_date)
    if emp_id: query = query.eq('emp_id', emp_id)
    if project_code: query = query.eq('project_code', project_code)
    
    res = query.order('date', desc=True).execute()
    data = res.data or []
    
    cols = ['id', 'emp_id', 'emp_name', 'project_code', 'project_name', 'date', 'hours', 'Phase', 'project_status', 'comment']
    rows = []
    
    logged_dates_by_emp = {}
    for r in data:
        eid = str(r['emp_id'])
        d_val = str(r['date'])
        if eid not in logged_dates_by_emp: logged_dates_by_emp[eid] = set()
        logged_dates_by_emp[eid].add(d_val)
        
        rows.append([
            r['id'],
            r['emp_id'],
            r['emp_name'],
            r['project_code'],
            decrypt_data(r['project_name']),
            r['date'],
            r['hours'],
            r['Phase'],
            r['project_status'],
            r.get('comment', '')
        ])
    
    # Dynamically inject holidays if requested.
    # Only skip if project_code filter is set to a specific non-holiday project (not a LEAVE/HOLIDAY prefix).
    _pc_str = str(project_code) if project_code is not None else ''
    _is_non_holiday_filter = project_code is not None and not _pc_str.startswith('HOLIDAY') and not _pc_str.startswith('LEAVE-')
    if include_holidays and not _is_non_holiday_filter:
        try:
            h_query = supabase.table('holidays').select('id, holiday_date, holiday_name').is_('deleted_at', 'null')
            if start_date: h_query = h_query.gte('holiday_date', start_date.isoformat() if hasattr(start_date, 'isoformat') else start_date)
            if end_date: h_query = h_query.lte('holiday_date', end_date.isoformat() if hasattr(end_date, 'isoformat') else end_date)
            h_res = h_query.execute()
            holidays = h_res.data or []
            
            if holidays:
                if emp_id:
                    emp_row = get_employee_by_id(emp_id)
                    emp_name = emp_row.get('employee_name', str(emp_id)) if emp_row else str(emp_id)
                    emp_list = [{'employee_id': str(emp_id), 'employee_name': emp_name}]
                else:
                    emp_df = get_all_employees(exclude_admin=True)
                    # Only synthesize holidays for ACTIVE employees (status == 1)
                    if 'status' in emp_df.columns:
                        emp_df = emp_df[emp_df['status'].astype(int) == 1]
                    emp_list = emp_df[['employee_id', 'employee_name']].to_dict('records') if not emp_df.empty else []
                    
                holiday_ids = [h['id'] for h in holidays]
                ex_res = supabase.table('employee_holiday_exclusions').select('employee_id, holiday_id').in_('holiday_id', holiday_ids).execute()
                exclusions_set = {(str(r['employee_id']), int(r['holiday_id'])) for r in (ex_res.data or [])}
                
                for h in holidays:
                    h_id = int(h['id'])
                    h_date = str(h['holiday_date'])
                    h_name = str(h['holiday_name'])
                    
                    for emp in emp_list:
                        e_id = str(emp['employee_id'])
                        if e_id == 'admin': continue
                        
                        if (e_id, h_id) in exclusions_set:
                            continue
                            
                        # If employee already has a real entry on this date, skip holiday
                        if e_id in logged_dates_by_emp and h_date in logged_dates_by_emp[e_id]:
                            continue
                            
                        rows.append([
                            f"HOLIDAY-{h_id}-{e_id}",
                            e_id,
                            emp['employee_name'],
                            f"HOLIDAY-{h_id}",
                            h_name,
                            h_date,
                            8.0,
                            "Holiday",
                            "Holiday",
                            "Company Holiday"
                        ])
        except Exception as ex:
            print(f"Error synthesizing holiday entries: {ex}")
            
    return pd.DataFrame(rows, columns=cols)

def delete_timesheet_entry(entry_id):
    """Delete a timesheet entry using Supabase SDK, supporting holiday exclusion."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    # Handle virtual holiday deletion (employee self-service override)
    if str(entry_id).startswith("HOLIDAY-"):
        try:
            parts = str(entry_id).split("-")
            h_id = int(parts[1])
            e_id = parts[2] if len(parts) > 2 else None
            return exclude_holiday_for_employee(e_id, h_id)
        except Exception as e:
            return False, str(e)
            
    try:
        res = supabase.table('timesheet').select('emp_id').eq('id', entry_id).execute()
        if res.data:
            emp_id = res.data[0].get('emp_id')
            if not is_employee_active(emp_id):
                return False, "Employee is inactive. This action is not available for inactive employees."
    except Exception:
        pass
    
    try:
        supabase.table('timesheet').delete().eq('id', entry_id).execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def update_timesheet_entry(entry_id, emp_id, emp_name, project_code, project_name, date, hours, phase, project_status, comment=""):
    """Update a timesheet entry using Supabase SDK."""
    if not is_employee_active(emp_id):
        return False, "Employee is inactive. This action is not available for inactive employees."
        
    date_str = date.isoformat() if hasattr(date, 'isoformat') else date
    
    # We only block if the project being updated IS NOT a leave entry itself
    if not str(project_code).startswith("LEAVE-") and has_leave_for_date(emp_id, date_str):
        return False, "This date is registered as approved leave. Standard work hours cannot be logged for leave dates."

    if not str(project_code).startswith("LEAVE-") and not str(project_code).startswith("HOLIDAY"):
        is_holiday, h_info = has_active_holiday_for_date(emp_id, date_str)
        if is_holiday:
            return False, f"This date ({date_str}) is configured as a Holiday ('{h_info['holiday_name']}'). If you worked on this day, please remove the holiday entry from your timesheet first."

    if str(project_code).startswith("LEAVE-"):
        ensure_leave_projects_exist()

    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    phase_map = {"Analysis": "1", "Design": "2", "Development": "3", "Testing": "4", "Deployement": "5", "Support": "6"}
    phase_code = phase_map.get(phase, phase)
    
    data = {
        "emp_id": emp_id,
        "emp_name": emp_name,
        "project_code": project_code,
        "project_name": encrypt_data(project_name),
        "date": date.isoformat() if hasattr(date, 'isoformat') else date,
        "hours": float(hours),
        "Phase": phase_code,
        "project_status": project_status,
        "comment": str(comment).strip()[:400] if pd.notna(comment) and str(comment).strip() else None
    }
    
    try:
        supabase.table('timesheet').update(data).eq('id', entry_id).execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def update_user_password(username, hashed_password):
    """Update a user's password using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    try:
        supabase.table('users').update({'password': hashed_password}).eq('username', username).execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def verify_user_password(username, password):
    """Verify if the provided password matches the one in DB using Supabase SDK."""
    from services.auth_service import verify_password
    user = get_user_by_username(username)
    if user:
        # user tuple order: (id, employee_id, username, password, failed_attempts, locked_until)
        return verify_password(password, user[3])
    return False

def assign_project(emp_id, project_code):
    """Assign a project to an employee using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    try:
        supabase.table('project_employee').upsert({'employee_id': emp_id, 'project_code': project_code}).execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def revoke_project(emp_id, project_code):
    """Remove a project assignment using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    try:
        supabase.table('project_employee').delete().match({'employee_id': emp_id, 'project_code': project_code}).execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def get_projects_by_employee(emp_id):
    """Fetch projects assigned to a specific employee using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()
    
    # Get project codes joined with project details
    res = supabase.table('project_employee').select('project!inner(project_code, project_name, status)').eq('employee_id', emp_id).execute()
    data = res.data or []
    
    rows = []
    for r in data:
        p = r.get('project') or {}
        rows.append([
            p['project_code'],
            decrypt_data(p['project_name']),
            p['status']
        ])
    
    return pd.DataFrame(rows, columns=['project_code', 'project_name', 'status'])

def get_all_assignments():
    """Fetch all project assignments using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()
    
    res = supabase.table('project_employee').select('employee_id, employee:employee(employee_name), project_code, project:project(project_name)').execute()
    data = res.data or []
    
    rows = []
    for r in data:
        emp = r.get('employee') or {}
        proj = r.get('project') or {}
        rows.append([
            r['employee_id'],
            emp.get('employee_name'),
            r['project_code'],
            decrypt_data(proj.get('project_name', ''))
        ])
    
    return pd.DataFrame(rows, columns=['employee_id', 'employee_name', 'project_code', 'project_name'])

def check_assignment(emp_id, project_code):
    """Check if an employee is assigned to a project using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return False
    
    res = supabase.table('project_employee').select('1').match({'employee_id': emp_id, 'project_code': project_code}).execute()
    return len(res.data) > 0

def _sanitize_dict(d):
    """Replace any NaN/NaT values with None so they serialize as JSON null."""
    return {k: (None if pd.isna(v) else v) if not isinstance(v, str) else v
            for k, v in d.items()}

def _normalize_code(code):
    """Normalize project code by removing .0 suffixes (Excel artifact)."""
    s = str(code).strip()
    if s.endswith('.0'):
        return s[:-2]
    return s

def import_projects(df):
    """Import projects using Supabase SDK. Updates existing projects by Job No."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    try:
        # Fetch existing project codes to determine new vs updated
        existing_res = supabase.table('project').select('project_code').execute()
        existing_codes = {r['project_code'] for r in (existing_res.data or [])}
        
        # Fetch all employees from database to build ID-to-Name mapping
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
        
        data = []
        updated_count = 0
        new_count = 0
        for _, row in df.iterrows():
            code = _normalize_code(row.get('Job No') or row.get('Project Code') or '')
            record = {
                "project_code": code,
                "project_name": encrypt_data(str(row.get('Project', ''))),
                "status": row.get('Status', 'In progress'),
                "priority": row.get('Job Priority'),
                "lead_engineer": _parse_lead_engineer(row.get('Lead engineer')),
                "trello_link": row.get('Trello')
            }
            data.append(_sanitize_dict(record))
            if code in existing_codes:
                updated_count += 1
            else:
                new_count += 1
        
        if data:
            supabase.table('project').upsert(data, on_conflict='project_code').execute()
        return True, f"Successfully imported {len(df)} projects ({new_count} new, {updated_count} updated)."
    except Exception as e:
        return False, str(e)

def import_employees(df):
    """Import employees and create users using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    try:
        from services.auth_service import FIXED_PASSWORD
        emp_data = []
        user_data = []
        
        # Normalize and validate required columns case-insensitively
        col_map = {str(c).strip().lower(): c for c in df.columns}
        required = ['a__serial', 'name', 'slack id', 'email']
        for r in required:
            if r not in col_map:
                disp_names = {
                    'a__serial': 'a__Serial',
                    'name': 'Name',
                    'slack id': 'Slack ID',
                    'email': 'Email'
                }
                return False, f"Missing required column: '{disp_names[r]}'"
                
        for _, row in df.iterrows():
            emp_id_val = row[col_map['a__serial']]
            if pd.isna(emp_id_val) or str(emp_id_val).strip() == "":
                continue
            emp_id = str(emp_id_val).strip()
            
            emp_name = row[col_map['name']]
            emp_name = str(emp_name).strip() if not pd.isna(emp_name) else ""
            if not emp_name:
                return False, f"Employee ID {emp_id} is missing 'Name'."
                
            slack_id = row[col_map['slack id']]
            slack_id = str(slack_id).strip() if not pd.isna(slack_id) else ""
            if not slack_id:
                return False, f"Employee {emp_name} (ID {emp_id}) is missing 'Slack ID'."
                
            email = row[col_map['email']]
            email = str(email).strip() if not pd.isna(email) else ""
            if not email:
                return False, f"Employee {emp_name} (ID {emp_id}) is missing 'Email'."
            
            # Simple format validation
            import re
            if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
                return False, f"Invalid email format for employee {emp_name}: {email}"
            
            emp_data.append(_sanitize_dict({
                "employee_id": emp_id,
                "employee_name": emp_name,
                "slack_id": slack_id,
                "email": email
            }))
            
            username = " ".join(emp_name.strip().lower().split())
            enc_pwd = encrypt_data(FIXED_PASSWORD)
            user_data.append(_sanitize_dict({
                "employee_id": emp_id,
                "username": username,
                "password": enc_pwd
            }))
            
        # Validate uniqueness of emails in this batch and against DB
        if emp_data:
            emails_in_batch = {}
            for e in emp_data:
                em = e.get('email')
                if em:
                    if em in emails_in_batch and emails_in_batch[em] != e['employee_id']:
                        return False, f"Duplicate email {em} found in import file."
                    emails_in_batch[em] = e['employee_id']
                    
            if emails_in_batch:
                # Check DB for these emails
                res = supabase.table('employee').select('employee_id, email').in_('email', list(emails_in_batch.keys())).execute()
                if res.data:
                    for r in res.data:
                        # If email belongs to a different employee, it's a conflict
                        if str(r['employee_id']) != str(emails_in_batch[r['email']]):
                            return False, f"Email {r['email']} is already assigned to a different employee in the system."
                            
            supabase.table('employee').upsert(emp_data).execute()
        if user_data:
            supabase.table('users').upsert(user_data, on_conflict='employee_id').execute()
            
        return True, f"Successfully imported {len(df)} employees."
    except Exception as e:
        return False, str(e)

def import_assignments(df):
    """Import assignments using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    try:
        data = []
        for _, row in df.iterrows():
            emp_code = str(row.get('Projects_Resources::a_EmployeeID', ''))
            proj_code = str(row.get('Projects_Resources::a_ProjectID', ''))
            if emp_code and proj_code:
                data.append(_sanitize_dict({
                    "employee_id": emp_code,
                    "project_code": proj_code
                }))
        
        if data:
            supabase.table('project_employee').upsert(data).execute()
        return True, f"Successfully imported {len(df)} assignments."
    except Exception as e:
        return False, str(e)

def get_project_reports():
    """Fetch all data from project_reports table."""
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame()
    
    res = supabase.table('project_reports').select('*').order('project_code', desc=True).execute()
    data = res.data or []
    if not data:
        return pd.DataFrame()
    return pd.DataFrame(data)

def _parse_date_value(val):
    """Convert an Excel date cell value to an ISO date string, or None if blank."""
    if val is None:
        return None
    # pandas NaT / numpy NaN
    try:
        if pd.isna(val):
            return None
    except (TypeError, ValueError):
        pass

    # Check if the value is an Excel serial number (numeric or string representation of numeric)
    # Excel date serial numbers are usually between 10000 (1927) and 99999 (2173)
    try:
        f_val = float(val)
        if 10000 <= f_val <= 99999:
            return pd.to_datetime(f_val, unit='D', origin='1899-12-30').date().isoformat()
    except (ValueError, TypeError):
        pass

    # pandas Timestamp or datetime.datetime / datetime.date
    if hasattr(val, 'date'):
        try:
            return val.date().isoformat()
        except Exception:
            pass
    if hasattr(val, 'isoformat'):
        return val.isoformat()
    # Plain string
    s = str(val).strip()
    if not s or s.lower() in ('nat', 'none', 'nan', ''):
        return None
    # Try to parse a string date so it is normalised to YYYY-MM-DD
    try:
        # If it starts with a 4-digit year, parse it year-first (to avoid dayfirst swapped month/day)
        s_clean = s.replace('/', '-').replace(' ', '')
        import re
        if re.match(r'^\d{4}-\d{2}-\d{2}', s_clean):
            try:
                return pd.to_datetime(s_clean).date().isoformat()
            except Exception:
                pass
        # Use dayfirst=True and mixed format for robust parsing for other cases (e.g. DD-MM-YYYY)
        return pd.to_datetime(s, format='mixed', dayfirst=True).date().isoformat()
    except Exception:
        return s  # return as-is if unparseable


def _parse_checkbox_value(val):
    """Convert Excel checkbox values to DB representation:
    - Unchecked in Excel (1, TRUE, '1', 'x', 'yes', 'checked') maps to DB Unchecked: 1
    - Checked in Excel (blank/NaN, 0, FALSE) maps to DB Checked: None
    """
    if pd.isna(val):
        return None  # Blank in Excel -> Checked (None)
    s = str(val).strip().lower()
    if s in ('1', '1.0', 'true', 'x', 'yes', 'checked'):
        return 1  # Unchecked in Excel -> Unchecked (1)
    if s in ('0', '0.0', 'false', 'no', 'unchecked', ''):
        return None  # Checked in Excel -> Checked (None)
    return 1  # Default to Unchecked

def _parse_int_value(val):
    """Safely convert Excel numeric values to int or None."""
    if pd.isna(val):
        return None
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None

def import_project_updates(df):
    """Import project updates into project_reports using Supabase SDK.
    
    If a field has its '*_updated' flag set to True (meaning it was manually edited in the UI),
    this function will only overwrite it if the imported value matches the current DB value.
    Otherwise, it preserves the manual edit and keeps the highlight.
    """
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    # Fetch all employees from database to build ID-to-Name mapping
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

    def _normalize_for_cmp(v):
        if v is None: return None
        # Handle pandas NaN / NaT
        try:
            if pd.isna(v):
                return None
        except (TypeError, ValueError):
            pass
        try:
            # If it's a number, convert 9.0 -> 9
            f_v = float(v)
            import math
            if math.isnan(f_v):
                return None
            if f_v == int(f_v): return str(int(f_v))
            return str(f_v)
        except (ValueError, TypeError):
            s = str(v).strip()
            if s.lower() in ('nan', 'none', 'nat', ''):
                return None
            return s

    try:
        # Fetch existing records for comparison
        existing_res = supabase.table('project_reports').select('*').execute()
        existing_map = {r['project_code']: r for r in (existing_res.data or [])}
        
        def _parse_priority(val):
            if pd.isna(val): return None
            try:
                # Handle numeric priority (e.g. 1.0 -> "1")
                f_val = float(val)
                if f_val == int(f_val): return str(int(f_val))
                return str(f_val)
            except (ValueError, TypeError):
                # Handle text priority (e.g. "High")
                s = str(val).strip()
                return s if s.lower() not in ('nan', 'none', 'nat', '') else None

        # Map DB fields to potential Excel column aliases for robust matching
        field_aliases = {
            'project_name': ['Project', 'Project Name', 'Project_Name', 'Priority'],
            'priority': ['Job Priority', 'Priority', 'Job_Priority'],
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
            'checkbox_ws': ['CheckBoxe WS', 'CheckBoxe_WS', 'WS']
        }

        # Pre-resolve which column name to use for each DB field based on the uploaded DataFrame columns
        col_mapping = {}
        df_cols_lower = {str(c).strip().lower(): str(c).strip() for c in df.columns}
        
        for db_f, aliases in field_aliases.items():
            found = False
            for a in aliases:
                # Direct match
                if a in df.columns:
                    col_mapping[db_f] = a
                    found = True
                    break
                # Case-insensitive match
                if a.lower() in df_cols_lower:
                    col_mapping[db_f] = df_cols_lower[a.lower()]
                    found = True
                    break
            if not found:
                col_mapping[db_f] = None

        to_insert = []
        to_update = []
        new_count = 0
        updated_count = 0
        preserved_count = 0
        cleared_count = 0

        # Data fields to process: (DB Field, Parser, Default)
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
        ]

        for _, row in df.iterrows():
            code = _normalize_code(row.get('Job No') or row.get('Project Code') or row.get('Job_No') or row.get('Project_Code') or '')
            if not code or code.lower() == 'nan':
                continue

            record = {"project_code": code}
            
            # Special check for project_name fallback: 
            # If 'Project' is empty but 'Priority' contains the name (as in some exports)
            # we already handle it by having 'Priority' in field_aliases['project_name'].
            # However, if BOTH exist and 'Project' is empty, we might want to prefer 'Priority'.
            # Let's adjust the parser for project_name.
            proj_col = col_mapping.get('project_name')
            raw_proj = row.get(proj_col) if proj_col else None
            
            # If the primary name column is empty, check other aliases
            if pd.isna(raw_proj) or str(raw_proj).strip() == "":
                for alt_alias in field_aliases['project_name']:
                    if alt_alias in df.columns:
                        alt_val = row.get(alt_alias)
                        if pd.notna(alt_val) and str(alt_val).strip() != "":
                            raw_proj = alt_val
                            break
            
            if code in existing_map:
                existing = existing_map[code]
                record["id"] = existing["id"]
                row_changed = False
                row_preserved = False
                
                for db_f, parser, default in data_fields:
                    if db_f == 'project_name':
                        imp_val = str(raw_proj).strip() if pd.notna(raw_proj) else default
                    else:
                        excel_f = col_mapping.get(db_f)
                        raw_val = row.get(excel_f) if excel_f else None
                        imp_val = parser(raw_val) if raw_val is not None else default
                    
                    flag_col = f"{db_f}_updated"
                    is_updated = existing.get(flag_col, False)
                    db_val = existing.get(db_f)
                    
                    if is_updated:
                        # Case: Field was manually edited (*_updated = TRUE)
                        if _normalize_for_cmp(imp_val) == _normalize_for_cmp(db_val):
                            # Sub-case: Imported data matches current edited value
                            record[db_f] = imp_val
                            record[flag_col] = False
                            cleared_count += 1
                            row_changed = True
                        else:
                            # Sub-case: Imported sheet data does not match manually edited field
                            record[db_f] = db_val
                            record[flag_col] = True
                            row_preserved = True
                    else:
                        # Case: Field was NOT manually edited (*_updated = FALSE)
                        if _normalize_for_cmp(imp_val) != _normalize_for_cmp(db_val):
                            # Sub-case: Imported sheet data is different
                            record[db_f] = imp_val
                            record[flag_col] = False
                            row_changed = True
                        else:
                            # Sub-case: Values match, ensure flag stays FALSE
                            record[db_f] = db_val
                            record[flag_col] = False
                
                if row_changed or row_preserved:
                    if "project_code_updated" in existing:
                        record["project_code_updated"] = False
                    to_update.append(_sanitize_dict(record))
                    if row_changed: updated_count += 1
                    if row_preserved: preserved_count += 1
            else:
                # New record: Set all flags to FALSE
                for db_f, parser, default in data_fields:
                    excel_f = col_mapping.get(db_f)
                    raw_val = row.get(excel_f) if excel_f else None
                    record[db_f] = parser(raw_val) if raw_val is not None else default
                    record[f"{db_f}_updated"] = False
                
                record["project_code_updated"] = False
                to_insert.append(_sanitize_dict(record))
                new_count += 1

        if to_insert:
            supabase.table('project_reports').insert(to_insert).execute()
        if to_update:
            supabase.table('project_reports').upsert(to_update).execute()
             
        msg = f"Import complete: {new_count} new projects added."
        if updated_count: msg += f" {updated_count} projects updated."
        if preserved_count: msg += f" {preserved_count} manual edits preserved."
        if cleared_count: msg += f" {cleared_count} highlights cleared."
        
        return True, msg
    except Exception as e:
        return False, str(e)

def save_project_updates(edited_rows_dict, current_df, user_emp_id=None):
    """Process st.data_editor changes and save to project_reports, updating flags."""
    if user_emp_id and not is_employee_active(user_emp_id):
        return False, "Employee is inactive. This action is not available for inactive employees."
        
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    try:
        updated_records = []
        for row_idx, changes in edited_rows_dict.items():
            # Get original row using index
            orig_row = current_df.iloc[int(row_idx)]
            proj_code = orig_row['project_code']
            
            update_payload = {"project_code": proj_code}
            
            for col, new_val in changes.items():
                update_payload[col] = new_val
                # Set the updated flag to true if a corresponding column exists
                flag_col = f"{col}_updated"
                if flag_col in current_df.columns:
                    update_payload[flag_col] = True
            
            if len(update_payload) > 1: # More than just project_code
                updated_records.append(update_payload)
                
        for record in updated_records:
            supabase.table('project_reports').update(record).eq('project_code', record['project_code']).execute()
            
        return True, f"Successfully updated {len(updated_records)} projects."
    except Exception as e:
        return False, str(e)

def update_project_update_access(employee_id, has_access):
    """Update an employee's access to the project update page."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    try:
        supabase.table('employee').update({'project_update_access': has_access}).eq('employee_id', employee_id).execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)

def init_db():
    """Initialize system admin if missing using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    try:
        from services.auth_service import FIXED_PASSWORD
        enc_pwd = encrypt_data(FIXED_PASSWORD)
        
        # 1. UPSERT admin employee (admins always have access)
        supabase.table('employee').upsert({
            "employee_id": "admin", 
            "employee_name": "System Administrator",
            "project_update_access": True
        }).execute()
        
        # 2. UPSERT admin user
        supabase.table('users').upsert({
            "employee_id": "admin", 
            "username": "admin", 
            "password": enc_pwd
        }, on_conflict='username').execute()
        
        return True, "Database references initialized (System Admin created)"
    except Exception as e:
        return False, str(e)

def add_employee(emp_id, emp_name, slack_id, email=None, status=1):
    """Add a new employee and their user account."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    # Check unique email
    if email and str(email).strip():
        res = supabase.table('employee').select('employee_id').eq('email', email).execute()
        if res.data: return False, "Email already exists"
        
    try:
        from services.auth_service import FIXED_PASSWORD, encrypt_data
        
        supabase.table('employee').insert({
            "employee_id": emp_id,
            "employee_name": emp_name,
            "slack_id": slack_id,
            "email": email if str(email).strip() else None,
            "status": int(status)
        }).execute()
        
        username = " ".join(emp_name.strip().lower().split())
        enc_pwd = encrypt_data(FIXED_PASSWORD)
        supabase.table('users').insert({
            "employee_id": emp_id,
            "username": username,
            "password": enc_pwd
        }).execute()
        
        return True, "Employee created successfully"
    except Exception as e:
        return False, str(e)

def update_employee(emp_id, emp_name, slack_id, email=None, status=1):
    """Update an existing employee."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    # Check unique email
    if email and str(email).strip():
        res = supabase.table('employee').select('employee_id').eq('email', email).neq('employee_id', emp_id).execute()
        if res.data: return False, "Email already exists"
        
    try:
        supabase.table('employee').update({
            "employee_name": emp_name,
            "slack_id": slack_id,
            "email": email if str(email).strip() else None,
            "status": int(status)
        }).eq('employee_id', emp_id).execute()
        
        return True, "Employee updated successfully"
    except Exception as e:
        return False, str(e)

def create_reminder_log(employee_id, recipient_email, project_ids, email_subject, email_body):
    """Insert initial pending log record for a project update reminder."""
    supabase = get_supabase_client()
    if not supabase: return None
    
    try:
        try:
            emp_id_int = int(employee_id)
        except ValueError:
            emp_id_int = 0
            
        data = {
            "employee_id": emp_id_int,
            "recipient_email": recipient_email,
            "project_ids": project_ids,
            "email_subject": email_subject,
            "email_body": email_body,
            "status": 0
        }
        res = supabase.table('project_update_reminder_logs').insert(data).execute()
        if res.data:
            return res.data[0].get('id')
    except Exception as e:
        print("Error creating reminder log:", e)
    return None

def update_reminder_log(log_id, status, error_message=None):
    """Update status, error message, and sent_at for reminder log."""
    supabase = get_supabase_client()
    if not supabase or log_id is None: return False
    
    import datetime
    try:
        data = {
            "status": status,
            "error_message": error_message
        }
        if status == 1:
            data["sent_at"] = datetime.datetime.now().isoformat()
            
        supabase.table('project_update_reminder_logs').update(data).eq('id', log_id).execute()
        return True
    except Exception as e:
        print("Error updating reminder log:", e)
    return False

# ============================================================
# App Settings (key-value store in app_settings table)
# ============================================================

def get_app_setting(key, default=None):
    """Fetch a single application setting by key."""
    supabase = get_supabase_client()
    if not supabase:
        return default
    try:
        res = supabase.table('app_settings').select('value').eq('key', key).execute()
        if res.data:
            return res.data[0]['value']
    except Exception as e:
        print(f"Error reading app setting '{key}': {e}")
    return default

def set_app_setting(key, value):
    """Upsert an application setting."""
    supabase = get_supabase_client()
    if not supabase:
        return False, "Configuration error"
    try:
        supabase.table('app_settings').upsert({
            'key': key,
            'value': str(value)
        }, on_conflict='key').execute()
        return True, "Success"
    except Exception as e:
        return False, str(e)

# ============================================================
# Timesheet Reminder Queries
# ============================================================

def get_active_employees_with_email():
    """Fetch all non-admin employees who have a valid email address."""
    supabase = get_supabase_client()
    if not supabase:
        return []
    try:
        res = (supabase.table('employee')
               .select('employee_id, employee_name, email')
               .neq('employee_id', 'admin')
               .not_.is_('email', 'null')
               .eq('status', 1)
               .order('employee_name')
               .execute())
        employees = []
        for r in (res.data or []):
            email = r.get('email', '')
            if email and str(email).strip():
                employees.append({
                    'employee_id': r['employee_id'],
                    'employee_name': r['employee_name'],
                    'email': str(email).strip()
                })
        return employees
    except Exception as e:
        print(f"Error fetching active employees with email: {e}")
        return []

def get_timesheet_dates_for_employee(emp_id, start_date, end_date):
    """Return the set of dates (as date objects) for which the employee has timesheet entries."""
    supabase = get_supabase_client()
    if not supabase:
        return set()
    try:
        res = (supabase.table('timesheet')
               .select('date')
               .eq('emp_id', emp_id)
               .gte('date', start_date.isoformat())
               .lte('date', end_date.isoformat())
               .execute())
        dates = set()
        for r in (res.data or []):
            d = r.get('date')
            if d:
                if isinstance(d, str):
                    import datetime as _dt
                    dates.add(_dt.date.fromisoformat(d))
                else:
                    dates.add(d)
        return dates
    except Exception as e:
        print(f"Error fetching timesheet dates for {emp_id}: {e}")
        return set()

def create_ts_reminder_log(employee_id, employee_email, week_start_date,
                           reminder_type, missing_days=None):
    """Insert a pending timesheet reminder log record. Returns the log id or None."""
    supabase = get_supabase_client()
    if not supabase:
        return None
    try:
        import json as _json
        data = {
            'employee_id': str(employee_id),
            'employee_email': employee_email,
            'week_start_date': week_start_date.isoformat(),
            'reminder_type': reminder_type,
            'missing_days': _json.dumps([d.isoformat() for d in missing_days]) if missing_days else None,
            'status': 0
        }
        res = supabase.table('timesheet_reminder_logs').insert(data).execute()
        if res.data:
            return res.data[0].get('id')
    except Exception as e:
        print(f"Error creating ts reminder log: {e}")
    return None

def update_ts_reminder_log(log_id, status, error_message=None):
    """Update status and sent_at for a timesheet reminder log entry."""
    supabase = get_supabase_client()
    if not supabase or log_id is None:
        return False
    import datetime as _dt
    try:
        data = {'status': status, 'error_message': error_message}
        if status == 1:
            data['sent_at'] = _dt.datetime.now().isoformat()
        supabase.table('timesheet_reminder_logs').update(data).eq('id', log_id).execute()
        return True
    except Exception as e:
        print(f"Error updating ts reminder log {log_id}: {e}")
    return False

def check_ts_reminder_exists(employee_id, week_start_date, status=1):
    """Check if a successful reminder already exists for this employee and week."""
    supabase = get_supabase_client()
    if not supabase:
        return False
    try:
        res = (supabase.table('timesheet_reminder_logs')
               .select('id')
               .eq('employee_id', str(employee_id))
               .eq('week_start_date', week_start_date.isoformat())
               .eq('status', status)
               .limit(1)
               .execute())
        return len(res.data or []) > 0
    except Exception as e:
        print(f"Error checking ts reminder existence: {e}")
    return False

_REMINDER_LOG_RETENTION_DAYS = 28  # 4 weeks — not user-configurable

def cleanup_old_reminder_logs():
    """Delete timesheet reminder logs older than 4 weeks (28 days).

    The retention window is system-managed and hardcoded to
    ``_REMINDER_LOG_RETENTION_DAYS``.  Do NOT expose this value as a
    user-configurable setting.

    Returns
    -------
    int
        Number of records deleted, or 0 on error.
    """
    supabase = get_supabase_client()
    if not supabase:
        return 0
    import datetime as _dt
    try:
        cutoff = (_dt.datetime.now() - _dt.timedelta(days=_REMINDER_LOG_RETENTION_DAYS)).isoformat()
        res = supabase.table('timesheet_reminder_logs').delete().lt('created_at', cutoff).execute()
        count = len(res.data or [])
        return count
    except Exception as e:
        print(f"Error cleaning up old ts reminder logs: {e}")
    return 0


# ==============================================================================
# Holiday Management & Employee Holiday Exclusion Functions
# ==============================================================================

def get_all_holidays(year=None, include_inactive=False):
    """Fetch configured holidays using Supabase SDK."""
    supabase = get_supabase_client()
    if not supabase: return pd.DataFrame(columns=['id', 'holiday_date', 'holiday_name', 'created_at', 'created_by'])
    
    try:
        query = supabase.table('holidays').select('id, holiday_date, holiday_name, is_active, created_at, created_by, deleted_at')
        if not include_inactive:
            query = query.is_('deleted_at', 'null')
        if year and str(year).strip().lower() != 'all':
            query = query.gte('holiday_date', f"{year}-01-01").lte('holiday_date', f"{year}-12-31")
            
        res = query.order('holiday_date', desc=False).execute()
        data = res.data or []
        return pd.DataFrame(data)
    except Exception as e:
        print(f"Error fetching holidays: {e}")
        return pd.DataFrame(columns=['id', 'holiday_date', 'holiday_name', 'created_at', 'created_by'])

def ensure_holiday_project_exists(holiday_id, holiday_name):
    """Ensure a HOLIDAY-{id} project record exists in the project table (needed as FK for timesheet)."""
    supabase = get_supabase_client()
    if not supabase: return
    project_code = f"HOLIDAY-{holiday_id}"
    try:
        supabase.table('project').upsert([{
            "project_code": project_code,
            "project_name": encrypt_data(str(holiday_name)),
            "status": "Holiday"
        }], on_conflict='project_code').execute()
    except Exception as e:
        print(f"ensure_holiday_project_exists error: {e}")

def create_holiday_timesheet_entries(holiday_date, holiday_name, holiday_id, created_by='admin'):
    """
    Physically insert a timesheet row in the `timesheet` table for every active employee
    who does not already have any entry on `holiday_date`.
    Returns (created_count, skipped_count).
    """
    supabase = get_supabase_client()
    if not supabase: return 0, 0

    date_str = holiday_date.isoformat() if hasattr(holiday_date, 'isoformat') else str(holiday_date)
    project_code = f"HOLIDAY-{holiday_id}"

    # Guarantee project FK exists
    ensure_holiday_project_exists(holiday_id, holiday_name)

    # Fetch all active employees (excludes admin row)
    emp_df = get_all_employees(exclude_admin=True)
    if 'status' in emp_df.columns:
        emp_df = emp_df[emp_df['status'].astype(int) == 1]
    if emp_df.empty:
        return 0, 0

    # Find employees who already have ANY entry on this date
    try:
        existing_res = supabase.table('timesheet').select('emp_id').eq('date', date_str).execute()
        existing_emps = {str(r['emp_id']) for r in (existing_res.data or [])}
    except Exception:
        existing_emps = set()

    records = []
    skipped = 0
    for _, emp_row in emp_df.iterrows():
        e_id = str(emp_row['employee_id'])
        if e_id in existing_emps:
            skipped += 1
            continue
        records.append({
            "emp_id": e_id,
            "emp_name": emp_row['employee_name'],
            "project_code": project_code,
            "project_name": encrypt_data(str(holiday_name)),
            "date": date_str,
            "hours": 8.0,
            "Phase": "Holiday",
            "project_status": "Holiday",
            "comment": "Company Holiday"
        })

    if records:
        try:
            supabase.table('timesheet').insert(records).execute()
            print(f"create_holiday_timesheet_entries: inserted {len(records)} rows for '{holiday_name}' on {date_str}")
        except Exception as e:
            print(f"create_holiday_timesheet_entries insert error: {e}")
            return 0, skipped

    return len(records), skipped

def add_holiday(holiday_date, holiday_name, created_by='admin'):
    """Add a new holiday. Enforces date uniqueness for active holidays."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    date_str = holiday_date.isoformat() if hasattr(holiday_date, 'isoformat') else str(holiday_date).strip()
    name_str = str(holiday_name).strip()
    
    if not date_str:
        return False, "Holiday date is required."
    if not name_str:
        return False, "Holiday name is required."
    if len(name_str) > 255:
        return False, "Holiday name cannot exceed 255 characters."
        
    try:
        res = supabase.table('holidays').select('id, holiday_name').eq('holiday_date', date_str).is_('deleted_at', 'null').execute()
        if res.data:
            existing = res.data[0]
            return False, f"A holiday ('{existing['holiday_name']}') already exists on {date_str}."
            
        data = {
            "holiday_date": date_str,
            "holiday_name": name_str,
            "is_active": True,
            "created_by": created_by
        }
        insert_result = supabase.table('holidays').insert(data).execute()
        h_id = insert_result.data[0]['id'] if insert_result.data else None
        msg = "Holiday added successfully."
        if h_id:
            created_cnt, skipped_cnt = create_holiday_timesheet_entries(date_str, name_str, h_id, created_by)
            msg = f"Holiday added. Timesheet entries created for {created_cnt} employee(s) ({skipped_cnt} already had entries for this date)."
        return True, msg
    except Exception as e:
        return False, str(e)

def update_holiday(holiday_id, holiday_date, holiday_name, updated_by='admin'):
    """Update an existing holiday date and name."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    
    date_str = holiday_date.isoformat() if hasattr(holiday_date, 'isoformat') else str(holiday_date).strip()
    name_str = str(holiday_name).strip()
    
    if not date_str: return False, "Holiday date is required."
    if not name_str: return False, "Holiday name is required."
    if len(name_str) > 255: return False, "Holiday name cannot exceed 255 characters."
    
    try:
        res = supabase.table('holidays').select('id').eq('holiday_date', date_str).neq('id', holiday_id).is_('deleted_at', 'null').execute()
        if res.data:
            return False, f"Another holiday already exists on {date_str}."
            
        data = {
            "holiday_date": date_str,
            "holiday_name": name_str,
            "updated_by": updated_by
        }
        supabase.table('holidays').update(data).eq('id', holiday_id).execute()
        return True, "Holiday updated successfully."
    except Exception as e:
        return False, str(e)

def delete_holiday(holiday_id, soft_delete=True, updated_by='admin'):
    """Delete a holiday. Soft-deletes by default to preserve historical integrity.
    Also removes the physical timesheet rows that were created for this holiday.
    """
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"

    project_code = f"HOLIDAY-{holiday_id}"

    try:
        # Remove physical timesheet entries for this holiday from the timesheet table
        try:
            supabase.table('timesheet').delete().eq('project_code', project_code).execute()
        except Exception as ts_err:
            print(f"delete_holiday: could not remove timesheet rows for {project_code}: {ts_err}")

        if soft_delete:
            import datetime as _dt
            now_iso = _dt.datetime.now(_dt.timezone.utc).isoformat()
            supabase.table('holidays').update({
                'is_active': False,
                'deleted_at': now_iso,
                'updated_by': updated_by
            }).eq('id', holiday_id).execute()
        else:
            supabase.table('holidays').delete().eq('id', holiday_id).execute()
        return True, "Holiday deleted successfully."
    except Exception as e:
        return False, str(e)

def import_holidays(df, created_by='admin'):
    """Import holidays from DataFrame with columns 'date' and 'holiday name'."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error", {}
    
    col_map = {str(c).strip().lower(): c for c in df.columns}
    required = ['date', 'holiday name']
    for r in required:
        if r not in col_map:
            return False, f"Missing required column: '{r}'. Expected 'date' and 'holiday name'.", {}
            
    valid_records = []
    seen_dates = set()
    errors = []
    
    for idx, row in df.iterrows():
        row_num = idx + 2
        raw_date = row[col_map['date']]
        raw_name = row[col_map['holiday name']]
        
        if (pd.isna(raw_date) or str(raw_date).strip() == "") and (pd.isna(raw_name) or str(raw_name).strip() == ""):
            continue
            
        parsed_date = _parse_date_value(raw_date)
        is_valid_date = False
        if parsed_date:
            try:
                import datetime as _dt
                _dt.date.fromisoformat(str(parsed_date))
                is_valid_date = True
            except Exception:
                is_valid_date = False
                
        if not is_valid_date:
            errors.append(f"Row {row_num}: Invalid or missing date '{raw_date}'.")
            continue
            
        name_str = str(raw_name).strip() if pd.notna(raw_name) else ""
        if not name_str:
            errors.append(f"Row {row_num}: Missing holiday name.")
            continue
        if len(name_str) > 255:
            errors.append(f"Row {row_num}: Holiday name exceeds 255 characters.")
            continue
            
        if parsed_date in seen_dates:
            errors.append(f"Row {row_num}: Duplicate date '{parsed_date}' within uploaded file.")
            continue
        seen_dates.add(parsed_date)
        
        valid_records.append({
            "holiday_date": parsed_date,
            "holiday_name": name_str,
            "is_active": True,
            "created_by": created_by
        })
        
    if errors:
        return False, f"Validation failed with {len(errors)} error(s).", {"errors": errors, "valid_count": len(valid_records)}
        
    if not valid_records:
        return False, "No valid holiday records found in file.", {}
        
    dates_to_check = [r['holiday_date'] for r in valid_records]
    try:
        existing_res = supabase.table('holidays').select('holiday_date, holiday_name').in_('holiday_date', dates_to_check).is_('deleted_at', 'null').execute()
        if existing_res.data:
            db_conflicts = [f"{r['holiday_date']} ({r['holiday_name']})" for r in existing_res.data]
            return False, f"Import rejected: {len(db_conflicts)} date(s) already exist in system: {', '.join(db_conflicts[:5])}{'...' if len(db_conflicts) > 5 else ''}", {"conflicts": db_conflicts}
            
        insert_result = supabase.table('holidays').insert(valid_records).execute()
        inserted_holidays = insert_result.data or []

        # Physically create timesheet rows for every active employee for each inserted holiday
        total_ts_created = 0
        for h in inserted_holidays:
            h_id = h.get('id')
            h_date = h.get('holiday_date')
            h_name = h.get('holiday_name')
            if h_id and h_date and h_name:
                cnt, _ = create_holiday_timesheet_entries(h_date, h_name, h_id, created_by)
                total_ts_created += cnt

        # Fallback: if Supabase didn't return inserted rows, fetch by dates
        if not inserted_holidays:
            fallback_res = supabase.table('holidays').select('id, holiday_date, holiday_name').in_('holiday_date', dates_to_check).is_('deleted_at', 'null').execute()
            for h in (fallback_res.data or []):
                h_id = h.get('id')
                h_date = h.get('holiday_date')
                h_name = h.get('holiday_name')
                if h_id and h_date and h_name:
                    cnt, _ = create_holiday_timesheet_entries(h_date, h_name, h_id, created_by)
                    total_ts_created += cnt

        return True, f"Successfully imported {len(valid_records)} holiday(s). Timesheet entries created for {total_ts_created} employee-holiday combinations.", {"imported_count": len(valid_records), "ts_created": total_ts_created}
    except Exception as e:
        return False, f"Database error during import: {str(e)}", {}

def get_employee_holiday_exclusions(emp_id):
    """Fetch all holiday_ids excluded by employee."""
    supabase = get_supabase_client()
    if not supabase or not emp_id: return set()
    
    try:
        res = supabase.table('employee_holiday_exclusions').select('holiday_id').eq('employee_id', str(emp_id)).execute()
        return {int(r['holiday_id']) for r in (res.data or [])}
    except Exception:
        return set()

def exclude_holiday_for_employee(emp_id, holiday_id, created_by=None):
    """Exclude a holiday for an employee so they can record work hours."""
    supabase = get_supabase_client()
    if not supabase: return False, "Configuration error"
    if not emp_id or not holiday_id: return False, "Employee ID and Holiday ID are required."
    
    try:
        supabase.table('employee_holiday_exclusions').upsert({
            "employee_id": str(emp_id),
            "holiday_id": int(holiday_id),
            "created_by": str(created_by or emp_id)
        }, on_conflict='employee_id, holiday_id').execute()
        return True, "Holiday entry removed from your timesheet. You may now log your work hours."
    except Exception as e:
        return False, str(e)

def has_active_holiday_for_date(emp_id, date):
    """Check if a date has an active un-excluded holiday for this employee."""
    supabase = get_supabase_client()
    if not supabase: return False, None
    date_str = date.isoformat() if hasattr(date, 'isoformat') else str(date)
    
    try:
        res = supabase.table('holidays').select('id, holiday_name').eq('holiday_date', date_str).is_('deleted_at', 'null').execute()
        if not res.data:
            return False, None
        holiday = res.data[0]
        
        if emp_id:
            ex_res = supabase.table('employee_holiday_exclusions').select('id').eq('employee_id', str(emp_id)).eq('holiday_id', holiday['id']).execute()
            if ex_res.data:
                return False, None
                
        return True, holiday
    except Exception:
        return False, None


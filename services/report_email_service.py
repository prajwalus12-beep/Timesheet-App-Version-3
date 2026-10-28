"""
Report Email Service
====================
Handles generation and delivery of weekly timesheet reports.
"""
import datetime
import pandas as pd
from utils.date_helpers import get_curr_cycle_dates
from utils.chart_helpers import (
    build_pie_pdf_report, 
    build_bar_pdf_report,
    convert_hours_to_days, 
    format_days_display,
    format_date_short,
    clean_bar_project_title,
    wrap_project_name,
    build_project_metadata_text,
)
from services.email_service import send_weekly_report_email
from database.queries import get_timesheets, get_all_employees, get_all_projects


def format_initials(emp_names):
    """Format employee names as comma-separated initials (max 3)."""
    if not emp_names:
        return ""
    initials = []
    for name in emp_names[:3]:  # Max 3 initials
        if isinstance(name, str) and name.strip():
            initials.append(''.join([w[0].upper() for w in name.split() if w]))
    return ', '.join(initials)


def get_report_week_dates():
    """Calculate the reporting period for the current week (Monday to Sunday)."""
    today = datetime.date.today()
    # Get Monday of current week
    start_of_week = today - datetime.timedelta(days=today.weekday())
    # Get Sunday of current week
    end_of_week = start_of_week + datetime.timedelta(days=6)
    return start_of_week, end_of_week


def generate_report_data(start_date, end_date):
    """
    Generate report data and metrics for the specified period.
    
    Returns:
    --------
    dict : Report metrics and data
    pd.DataFrame : Pie chart data
    float : Total days for pie chart
    pd.DataFrame : Bar chart data
    """
    # Fetch timesheet data
    ts_data = get_timesheets(start_date, end_date, None, None)
    
    # Exclude LEAVE and HOLIDAY codes
    if not ts_data.empty:
        chart_data = ts_data[
            ~ts_data['project_code'].astype(str).str.startswith(('LEAVE-', 'HOLIDAY'))
        ].copy()
        chart_data['hours'] = pd.to_numeric(chart_data['hours'], errors='coerce').fillna(0)
    else:
        chart_data = pd.DataFrame()
    
    # Calculate metrics
    if not chart_data.empty:
        submitted_count = chart_data['emp_id'].nunique()
        total_entries = len(chart_data)
        project_count = chart_data['project_code'].nunique()
        total_hours = chart_data['hours'].sum()
        total_days = convert_hours_to_days(total_hours)
        
        # Count submission status
        all_employees = get_all_employees(exclude_admin=True)
        if 'status' in all_employees.columns:
            all_employees = all_employees[all_employees['status'].astype(int) == 1]
        if 'emp_type' in all_employees.columns:
            all_employees = all_employees[all_employees['emp_type'] != 'Intern']
        
        total_active_employees = len(all_employees)
        completed_count = submitted_count
        uncompleted_count = total_active_employees - completed_count
        
        status_summary = f"{completed_count} completed, {uncompleted_count} incomplete out of {total_active_employees} employees"
    else:
        submitted_count = 0
        total_entries = 0
        project_count = 0
        total_hours = 0.0
        total_days = 0.0
        status_summary = "No timesheet data available"
    
    # Prepare chart data (similar to reports_page.py logic)
    project_records = []
    if not chart_data.empty:
        for p_name, group in chart_data.groupby('project_name'):
            h = group['hours'].sum()
            if h <= 0:
                continue
            days = convert_hours_to_days(h)
            codes = [str(c).strip() for c in group['project_code'].dropna().unique() if str(c).strip()]
            p_code = codes[0] if codes else ""
            emp_names = group['emp_name'].dropna().unique().tolist()
            ts_statuses = [str(s).strip() for s in group['project_status'].dropna().unique() if str(s).strip() and str(s).strip().lower() not in ('nan', 'none', '_', '')]
            ts_status = ts_statuses[-1] if ts_statuses else ""
            
            project_records.append({
                'project_name': p_name,
                'project_code': p_code,
                'hours': h,
                'days': days,
                'emp_names': emp_names,
                'ts_status': ts_status,
            })
    
    sorted_proj_records = sorted(project_records, key=lambda x: x['days'], reverse=True)
    total_project_days = sum(p['days'] for p in sorted_proj_records)
    
    # Fetch project metadata for enhanced info
    all_projs = get_all_projects()
    pr_map = {}
    if not all_projs.empty:
        for _, pr_r in all_projs.iterrows():
            c = str(pr_r.get('project_code', '')).strip()
            if c:
                pr_map[c] = pr_r.to_dict()
    
    # Prepare pie chart data
    pie_rows = []
    for idx, p in enumerate(sorted_proj_records):
        pct = (p['days'] / total_project_days * 100) if total_project_days > 0 else 0
        
        # Get project status from project map
        p_code = p['project_code']
        pr_rec = pr_map.get(p_code, {})
        status = (pr_rec.get('status') if pr_rec and pd.notna(pr_rec.get('status')) else None) or p['ts_status']
        
        pie_rows.append({
            'project_name': p['project_name'],
            'project_code': p['project_code'],
            'display_name_with_code': f"[{p['project_code']}] {p['project_name']}" if p['project_code'] else p['project_name'],
            'days': p['days'],
            'pct': pct,
            'initials': format_initials(p['emp_names']),
            'status': status,
        })
    
    pie_df = pd.DataFrame(pie_rows) if pie_rows else pd.DataFrame()
    
    # Prepare bar chart data with all necessary columns
    bar_top_projects = sorted_proj_records[:30] if len(sorted_proj_records) > 30 else sorted_proj_records
    bar_rows = []
    for p in bar_top_projects:
        p_code = p['project_code']
        pr_rec = pr_map.get(p_code, {})
        
        # Get status - prefer project table status, fall back to timesheet status
        status = (pr_rec.get('status') if pr_rec and pd.notna(pr_rec.get('status')) else None) or p['ts_status']
        
        # Get project dates
        start_date_obj = pr_rec.get('start_date') if pr_rec else None
        end_date_obj = pr_rec.get('end_date') if pr_rec else None
        start_str = format_date_short(start_date_obj)
        end_str = format_date_short(end_date_obj)
        
        # Format initials
        initials = format_initials(p['emp_names'])
        
        # Build metadata text
        pct = (p['days'] / sum([x['days'] for x in bar_top_projects]) * 100) if bar_top_projects else 0
        metadata_text = build_project_metadata_text(p['days'], pct, initials, start_str, end_str, status)
        
        # Clean project name and wrap
        clean_name = clean_bar_project_title(p['project_name'])
        display_name_with_code = f"[{p_code}] {clean_name}" if p_code else clean_name
        wrapped_name = wrap_project_name(display_name_with_code, width=30, html=True)
        
        bar_rows.append({
            'project_name': p['project_name'],
            'project_code': p_code,
            'display_name_with_code': display_name_with_code,
            'wrapped_name': wrapped_name,
            'days': p['days'],
            'hours': p['hours'],
            'pct': pct,
            'initials': initials,
            'start_str': start_str,
            'end_str': end_str,
            'status': status,
            'metadata_text': metadata_text,
        })
    
    bar_df = pd.DataFrame(bar_rows) if bar_rows else pd.DataFrame()
    
    # Report data dictionary
    report_data = {
        'period_start': start_date,
        'period_end': end_date,
        'submitted_count': submitted_count,
        'total_entries': total_entries,
        'project_count': project_count,
        'total_days': total_days,
        'total_hours': total_hours,
        'status_summary': status_summary,
    }
    
    return report_data, pie_df, total_project_days, bar_df


def generate_and_send_weekly_report(recipients, trigger_type='manual', sent_by=None, 
                                    start_date=None, end_date=None):
    """
    Generate weekly timesheet report and send to configured recipients.
    Creates a single PDF file for the bar chart.
    
    Parameters:
    -----------
    recipients : list
        List of recipient email addresses
    trigger_type : str
        'manual' or 'scheduled'
    sent_by : str
        Employee ID or 'system'
    start_date : date, optional
        Start of reporting period (defaults to current week Monday)
    end_date : date, optional
        End of reporting period (defaults to current week Sunday)
        
    Returns:
    --------
    tuple : (success: bool, message: str)
    """
    try:
        from utils.chart_helpers import build_bar_pdf_report
        
        # Determine reporting period
        if start_date is None or end_date is None:
            start_date, end_date = get_report_week_dates()
        
        # Generate report data and charts
        report_data, pie_df, total_pie_days, bar_df = generate_report_data(start_date, end_date)
        
        # Check if there's data to report
        if bar_df.empty:
            return False, "No timesheet data available for the selected period"
        
        # Generate bar chart PDF only
        bar_pdf_bytes = build_bar_pdf_report(
            r_start=start_date,
            r_end=end_date,
            bar_df=bar_df
        )
        
        # Send email with bar chart PDF
        success, message, log_id = send_weekly_report_email(
            recipients=recipients,
            report_data=report_data,
            bar_pdf_bytes=bar_pdf_bytes,
            trigger_type=trigger_type,
            sent_by=sent_by
        )
        
        return success, message
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error generating/sending weekly report: {error_details}")
        return False, f"Error: {str(e)}"

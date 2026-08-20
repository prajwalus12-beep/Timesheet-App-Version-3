"""
Timesheet Reminder Service
===========================
Central business logic for identifying employees with incomplete timesheets
and sending reminder emails. Used by both the automated cron job and the
manual Admin "Send Reminder" button.
"""
import datetime
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# Date helpers
# ------------------------------------------------------------------

def get_current_week_range(reference_date=None):
    """Return (monday, friday) of the week containing *reference_date*.

    If *reference_date* is ``None``, today's date is used.
    """
    if reference_date is None:
        reference_date = datetime.date.today()
    monday = reference_date - datetime.timedelta(days=reference_date.weekday())
    friday = monday + datetime.timedelta(days=4)
    return monday, friday


def get_applicable_days(reference_date=None):
    """Return the list of working-day dates (Mon–Fri) that should be checked."""
    if reference_date is None:
        reference_date = datetime.date.today()
    monday, friday = get_current_week_range(reference_date)
    days = []
    for i in range(5):  # Mon=0 … Fri=4
        day = monday + datetime.timedelta(days=i)
        days.append(day)
    return days


# ------------------------------------------------------------------
# Employee analysis
# ------------------------------------------------------------------

def get_employees_with_missing_timesheets(reference_date=None):
    """Scan all active employees and return those who have missing timesheets.

    Returns a list of dicts::

        [
            {
                "employee_id": "123",
                "employee_name": "John Doe",
                "email": "john@example.com",
                "missing_days": [datetime.date(2026, 8, 18), ...],
            },
            ...
        ]
    """
    from database.queries import (
        get_active_employees_with_email,
        get_timesheet_dates_for_employee,
    )

    if reference_date is None:
        reference_date = datetime.date.today()

    applicable_days = get_applicable_days(reference_date)
    if not applicable_days:
        logger.info("No applicable working days to check.")
        return []

    monday, friday = get_current_week_range(reference_date)
    employees = get_active_employees_with_email()
    logger.info("Checking %d employees for week %s – %s", len(employees),
                monday.isoformat(), friday.isoformat())

    results = []
    for emp in employees:
        filled_dates = get_timesheet_dates_for_employee(
            emp['employee_id'], monday, friday
        )
        missing = [d for d in applicable_days if d not in filled_dates]
        if missing:
            results.append({
                'employee_id': emp['employee_id'],
                'employee_name': emp['employee_name'],
                'email': emp['email'],
                'missing_days': missing,
            })

    logger.info("%d employees have incomplete timesheets.", len(results))
    return results


# ------------------------------------------------------------------
# Email
# ------------------------------------------------------------------

def _get_smtp_config():
    """Read SMTP credentials from Streamlit secrets (non-UI context safe)."""
    try:
        import streamlit as st
        smtp_host = st.secrets["SMTP_HOST"]
        smtp_port = int(st.secrets["SMTP_PORT"])
        smtp_user = st.secrets["SMTP_USER"]
        smtp_pass = st.secrets["SMTP_PASS"]
        smtp_encryption = st.secrets.get("SMTP_ENCRYPTION", "starttls").lower()
        return smtp_host, smtp_port, smtp_user, smtp_pass, smtp_encryption
    except Exception as e:
        logger.error("Failed to read SMTP config: %s", e)
        return None


def _build_reminder_email(employee_name, week_start, week_end, missing_days):
    """Build the subject and HTML body for the reminder email."""
    subject = "Action Required: Missing Timesheet Entry"

    missing_list_html = "".join(
        f"<li style='margin-bottom: 5px;'>{d.strftime('%d/%m/%Y')}</li>" for d in missing_days
    )
    
    start_str = week_start.strftime('%d %B %Y')
    end_str = week_end.strftime('%d %B %Y')

    body = f"""\
<html>
<body style="font-family: Arial, sans-serif; background-color: #f4f5f7; margin: 0; padding: 40px 20px; color: #333333;">
<div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 4px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
    
    <!-- Header -->
    <div style="background-color: #ea4335; padding: 25px 20px; text-align: center;">
        <h2 style="margin: 0; color: #ffffff; font-size: 22px; font-weight: normal;">Action Required: Missing Timesheet Entry</h2>
    </div>
    
    <!-- Body -->
    <div style="padding: 30px 40px;">
        <p style="font-size: 16px; margin-top: 0; color: #333333;">Dear <strong>{employee_name}</strong>,</p>
        
        <p style="font-size: 16px; line-height: 1.5; color: #4a5568;">
            Our system indicates that your timesheet has not been submitted for the following date(s) in the current week (<strong>{start_str} – {end_str}</strong>):
        </p>
        
        <!-- Missing Dates Box -->
        <div style="background-color: #fdf5f5; border-left: 4px solid #ea4335; padding: 20px; margin: 25px 0;">
            <p style="margin-top: 0; margin-bottom: 15px; font-size: 16px; color: #4a5568;">Missing Date(s):</p>
            <ul style="margin: 0; padding-left: 20px; color: #c5221f; font-weight: bold; font-size: 16px;">
                {missing_list_html}
            </ul>
        </div>
        
        <p style="font-size: 16px; line-height: 1.5; color: #4a5568; margin-bottom: 30px;">
            Please complete and submit the missing timesheet entries at the earliest to ensure accurate processing.
        </p>
        
        <!-- Button -->
        <div style="text-align: center; margin-bottom: 40px;">
            <a href="https://ustimesheetapps.streamlit.app/" style="display: inline-block; background-color: #1a73e8; color: #ffffff; text-decoration: none; padding: 14px 30px; font-size: 16px; font-weight: bold; border-radius: 6px;">Go to Timesheet Portal</a>
        </div>
        
        <!-- Footer text -->
        <p style="font-size: 14px; font-style: italic; color: #718096; margin-bottom: 0;">
            If you have already completed these entries in the last few minutes, please ignore this email.
        </p>
    </div>
</div>
</body>
</html>"""

    return subject, body


def send_single_reminder_email(employee, week_start, week_end, missing_days,
                               smtp_config=None):
    """Send a single reminder email. Returns (success: bool, error_msg: str|None)."""
    if smtp_config is None:
        smtp_config = _get_smtp_config()
        if smtp_config is None:
            return False, "SMTP configuration unavailable"

    smtp_host, smtp_port, smtp_user, smtp_pass, smtp_encryption = smtp_config
    subject, body = _build_reminder_email(
        employee['employee_name'], week_start, week_end, missing_days
    )

    msg = MIMEMultipart("alternative")
    msg['From'] = f"Timesheet Admin <{smtp_user}>"
    msg['To'] = employee['email']
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'html'))

    try:
        if smtp_encryption in ("ssl", "ssl/tls"):
            server = smtplib.SMTP_SSL(smtp_host, smtp_port)
        else:
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.ehlo()
            if smtp_encryption in ("starttls", "tls"):
                server.starttls()
                server.ehlo()

        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, employee['email'], msg.as_string())
        server.close()
        return True, None
    except Exception as e:
        logger.error("Email send failed for %s (%s): %s",
                      employee['employee_name'], employee['email'], e)
        return False, str(e)


# ------------------------------------------------------------------
# Main orchestrator
# ------------------------------------------------------------------

def process_timesheet_reminders(reminder_type="cron", force_resend=False,
                                 reference_date=None):
    """Run the full reminder pipeline.

    Parameters
    ----------
    reminder_type : str
        ``"cron"`` for scheduled or ``"manual"`` for admin-triggered.
    force_resend : bool
        If ``True``, skip duplicate-check and resend even if already sent this week.
    reference_date : datetime.date | None
        Override for today's date (useful for testing).

    Returns
    -------
    dict
        ``{"sent": int, "failed": int, "skipped": int, "total": int,
           "details": [...]}``
    """
    from database.queries import (
        create_ts_reminder_log,
        update_ts_reminder_log,
        check_ts_reminder_exists,
    )

    if reference_date is None:
        reference_date = datetime.date.today()

    monday, friday = get_current_week_range(reference_date)
    logger.info("Starting timesheet reminder process (%s) for week %s – %s",
                reminder_type, monday.isoformat(), friday.isoformat())

    employees_missing = get_employees_with_missing_timesheets(reference_date)

    result = {
        "sent": 0,
        "failed": 0,
        "skipped": 0,
        "total": len(employees_missing),
        "details": [],
    }

    if not employees_missing:
        logger.info("No employees require reminders.")
        return result

    # Pre-fetch SMTP config once for the batch
    smtp_config = _get_smtp_config()
    if smtp_config is None:
        logger.error("SMTP config unavailable — aborting reminder batch.")
        result["failed"] = result["total"]
        return result

    for emp in employees_missing:
        # Duplicate check
        if not force_resend and check_ts_reminder_exists(emp['employee_id'], monday):
            logger.info("Skipping %s — reminder already sent this week.",
                        emp['employee_name'])
            result["skipped"] += 1
            result["details"].append({
                "employee": emp['employee_name'],
                "status": "skipped",
                "reason": "already sent this week",
            })
            continue

        # Create pending log
        log_id = create_ts_reminder_log(
            employee_id=emp['employee_id'],
            employee_email=emp['email'],
            week_start_date=monday,
            reminder_type=reminder_type,
            missing_days=emp['missing_days'],
        )

        # Send email
        success, err = send_single_reminder_email(
            emp, monday, friday, emp['missing_days'], smtp_config
        )

        if success:
            update_ts_reminder_log(log_id, status=1)
            result["sent"] += 1
            result["details"].append({
                "employee": emp['employee_name'],
                "status": "sent",
            })
            logger.info("Reminder sent to %s (%s).", emp['employee_name'], emp['email'])
        else:
            update_ts_reminder_log(log_id, status=-1, error_message=err)
            result["failed"] += 1
            result["details"].append({
                "employee": emp['employee_name'],
                "status": "failed",
                "error": err,
            })
            logger.error("Reminder failed for %s: %s", emp['employee_name'], err)

    logger.info("Reminder process complete: %d sent, %d failed, %d skipped.",
                result["sent"], result["failed"], result["skipped"])
    return result

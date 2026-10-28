import os
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import streamlit as st

def generate_validation_pdf(employee_name, projects):
    """
    Generate a professional PDF with validation errors using ReportLab.
    Returns the PDF content as bytes.
    """
    import io
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter,
                            rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    story = []
    
    styles = getSampleStyleSheet()
    
    # Custom Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        textColor=colors.HexColor('#1e3a8a'), # Premium Dark Blue
        spaceAfter=15
    )
    
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#475569'),
        spaceAfter=20
    )
    
    issue_style = ParagraphStyle(
        'IssueItem',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9.5,
        leading=13,
        textColor=colors.HexColor('#b91c1c'), # Premium Dark Red/Crimson
    )
    
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#334155'),
        spaceAfter=10
    )

    # Document Header
    story.append(Paragraph("Timesheet Application - Validation Reminder", title_style))
    story.append(Paragraph(f"<b>Recipient:</b> {employee_name}<br/><b>Date Generated:</b> {datetime.datetime.now().strftime('%d-%m-%Y %H:%M')}", subtitle_style))
    story.append(Spacer(1, 10))
    
    story.append(Paragraph("Hello,", body_style))
    story.append(Paragraph("Please review the validation errors flagged below in the Project Update module and take action at the earliest.", body_style))
    story.append(Spacer(1, 10))
    
    # Table data
    table_data = [[
        Paragraph("<b>Project Details</b>", body_style),
        Paragraph("<b>Validation Issues Needing Attention</b>", body_style)
    ]]
    
    for proj in projects:
        proj_details = f"<b>Project Code:</b> {proj['projectCode']}<br/><b>Name:</b> {proj['projectName']}"
        
        issues_html = ""
        for issue in proj['issues']:
            issues_html += f"• {issue}<br/>"
        
        table_data.append([
            Paragraph(proj_details, body_style),
            Paragraph(issues_html, issue_style)
        ])
        
    # Create Table
    t = Table(table_data, colWidths=[200, 320])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#f1f5f9')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
    ]))
    
    story.append(t)
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Regards,<br/>Time Sheet Admin", body_style))
    
    doc.build(story)
    pdf_data = buffer.getvalue()
    buffer.close()
    return pdf_data

def send_reminder_email(employee_id, recipient_email, employee_name, projects):
    """
    Send validation reminder email to an employee, attach PDF report, and log to the database.
    """
    from database.queries import create_reminder_log, update_reminder_log

    try:
        smtp_host = st.secrets["SMTP_HOST"]
        smtp_port = st.secrets["SMTP_PORT"]
        smtp_user = st.secrets["SMTP_USER"]
        smtp_pass = st.secrets["SMTP_PASS"]
        smtp_encryption = st.secrets.get("SMTP_ENCRYPTION", "starttls").lower()
    except KeyError as e:
        return False, f"Missing {e.args[0]} in Streamlit secrets."

    try:
        smtp_port = int(smtp_port)
    except ValueError:
        return False, "Invalid SMTP_PORT in Streamlit secrets."

    # Construct Email Content
    subject = "Action Required: to fill project status for missing field"
    
    body = f"Hello {employee_name},\n\n"
    body += "Please review these validations flagged in the Project Update module of the Timesheet application and take action at the earliest.\n\n"
    body += "This item need to be attention please check attach pdf\n\n"
    body += "Please confirm to Sandeep once the action has been taken.\n\n"
    body += "Regards,\nTime Sheet Admin"

    # Create Initial Pending Log
    project_ids = [str(proj['projectCode']) for proj in projects]
    log_id = create_reminder_log(
        employee_id=employee_id,
        recipient_email=recipient_email,
        project_ids=project_ids,
        email_subject=subject,
        email_body=body
    )

    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = recipient_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # Generate and attach PDF
    try:
        pdf_data = generate_validation_pdf(employee_name, projects)
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(pdf_data)
        encoders.encode_base64(part)
        safe_name = employee_name.replace(" ", "_")
        part.add_header(
            'Content-Disposition',
            f'attachment; filename="Validation_Report_{safe_name}.pdf"'
        )
        msg.attach(part)
    except Exception as pdf_err:
        import traceback
        error_details = traceback.format_exc()
        print("Failed to generate/attach PDF:", error_details)
        return False, f"Failed to generate/attach PDF: {pdf_err}. Details: {error_details}"


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
        server.sendmail(smtp_user, recipient_email, msg.as_string())
        server.close()
        
        # Log success
        if log_id is not None:
            update_reminder_log(log_id, status=1)
            
        return True, "Email sent successfully."
    except Exception as e:
        # Log failure
        if log_id is not None:
            update_reminder_log(log_id, status=-1, error_message=str(e))
            
        return False, str(e)





def send_weekly_report_email(recipients, report_data, bar_pdf_bytes, trigger_type='manual', sent_by=None):
    """
    Send weekly timesheet report email with bar chart PDF attachment.
    
    Parameters:
    -----------
    recipients : list
        List of recipient email addresses
    report_data : dict
        Dictionary containing report metrics and period info
    bar_pdf_bytes : bytes
        Bar chart PDF content
    trigger_type : str
        'manual' or 'scheduled'
    sent_by : str
        Employee ID or 'system'
        
    Returns:
    --------
    tuple : (success: bool, message: str, log_id: int or None)
    """
    from database.queries import create_report_email_log, update_report_email_log
    import traceback
    
    if not recipients:
        return False, "No recipients configured", None
    
    # Validate email configuration
    try:
        smtp_host = st.secrets["SMTP_HOST"]
        smtp_port = st.secrets["SMTP_PORT"]
        smtp_user = st.secrets["SMTP_USER"]
        smtp_pass = st.secrets["SMTP_PASS"]
        smtp_encryption = st.secrets.get("SMTP_ENCRYPTION", "starttls").lower()
    except KeyError as e:
        return False, f"Missing {e.args[0]} in Streamlit secrets", None
    
    try:
        smtp_port = int(smtp_port)
    except ValueError:
        return False, "Invalid SMTP_PORT in Streamlit secrets", None
    
    # Extract report data
    period_start = report_data.get('period_start')
    period_end = report_data.get('period_end')
    submitted_count = report_data.get('submitted_count', 0)
    total_entries = report_data.get('total_entries', 0)
    project_count = report_data.get('project_count', 0)
    total_days = report_data.get('total_days', 0.0)
    total_hours = report_data.get('total_hours', 0.0)
    status_summary = report_data.get('status_summary', 'N/A')
    
    # Format dates for display
    start_str = period_start.strftime('%d %b %Y') if hasattr(period_start, 'strftime') else str(period_start)
    end_str = period_end.strftime('%d %b %Y') if hasattr(period_end, 'strftime') else str(period_end)
    
    # Email subject
    subject = f"Weekly Timesheet Report | {start_str} – {end_str}"
    
    # Create professional HTML email body
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
                line-height: 1.6;
                color: #1e293b;
                background-color: #f8fafc;
            }}
            .email-container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-top: 4px solid #3b82f6;
            }}
            .header {{
                background-color: #ffffff;
                padding: 32px 24px;
                border-bottom: 1px solid #e2e8f0;
            }}
            .header h1 {{
                font-size: 24px;
                font-weight: 600;
                color: #0f172a;
                margin-bottom: 8px;
            }}
            .period-info {{
                font-size: 14px;
                color: #64748b;
            }}
            .content {{
                padding: 32px 24px;
            }}
            .greeting {{
                font-size: 16px;
                color: #1e293b;
                margin-bottom: 24px;
            }}
            .section {{
                margin-bottom: 28px;
            }}
            .section-title {{
                font-size: 16px;
                font-weight: 600;
                color: #0f172a;
                margin-bottom: 16px;
                padding-bottom: 8px;
                border-bottom: 2px solid #e2e8f0;
            }}
            .summary-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 16px;
                margin-bottom: 20px;
            }}
            .summary-item {{
                background-color: #f1f5f9;
                padding: 16px;
                border-radius: 6px;
                border-left: 3px solid #3b82f6;
            }}
            .summary-label {{
                font-size: 12px;
                color: #64748b;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                margin-bottom: 4px;
            }}
            .summary-value {{
                font-size: 20px;
                font-weight: 700;
                color: #0f172a;
            }}
            .description {{
                font-size: 14px;
                color: #475569;
                line-height: 1.6;
                margin-bottom: 16px;
            }}
            .attachments-section {{
                background-color: #f0f9ff;
                border: 1px solid #bfdbfe;
                border-radius: 6px;
                padding: 16px;
                margin-top: 20px;
            }}
            .attachments-title {{
                font-size: 14px;
                font-weight: 600;
                color: #1e40af;
                margin-bottom: 12px;
            }}
            .attachment-item {{
                font-size: 14px;
                color: #1e40af;
                margin-bottom: 8px;
                display: flex;
                align-items: flex-start;
            }}
            .attachment-item:last-child {{
                margin-bottom: 0;
            }}
            .attachment-icon {{
                margin-right: 8px;
                font-weight: bold;
            }}
            .footer {{
                background-color: #f8fafc;
                padding: 24px;
                border-top: 1px solid #e2e8f0;
                text-align: center;
            }}
            .footer-text {{
                font-size: 12px;
                color: #64748b;
                line-height: 1.6;
            }}
            .divider {{
                border: none;
                border-top: 1px solid #e2e8f0;
                margin: 20px 0;
            }}
            .regards {{
                font-size: 14px;
                color: #1e293b;
                margin-top: 20px;
            }}
            .regards-name {{
                font-weight: 600;
                margin-top: 4px;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <!-- Header -->
            <div class="header">
                <h1>Weekly Timesheet Report</h1>
                <div class="period-info">Period: {start_str} to {end_str}</div>
            </div>
            
            <!-- Content -->
            <div class="content">
                <!-- Greeting -->
                <div class="greeting">Hello Team,</div>
                
                <!-- Weekly Summary Section -->
                <div class="section">
                    <div class="section-title">📊 Weekly Summary</div>
                    <div class="summary-grid">
                        <div class="summary-item">
                            <div class="summary-label">Employees Submitted</div>
                            <div class="summary-value">{submitted_count}</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-label">Entries</div>
                            <div class="summary-value">{total_entries}</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-label">Projects Covered</div>
                            <div class="summary-value">{project_count}</div>
                        </div>
                        <div class="summary-item">
                            <div class="summary-label">Total Effort</div>
                            <div class="summary-value">{total_days:.1f}d</div>
                        </div>
                    </div>
                    <div class="description">
                        <strong>Status:</strong> {status_summary}
                    </div>
                </div>
                
                <!-- Project Overview Section -->
                <div class="section">
                    <div class="section-title">📈 Project Overview</div>
                    <div class="description">
                        This report summarizes employee timesheet submissions, project codes and names, actual effort logged, and current project statuses.
                    </div>
                </div>
                
                <!-- Attachments Section -->
                <div class="attachments-section">
                    <div class="attachments-title">📎 Attached Reports</div>
                    <div class="attachment-item">
                        <span class="attachment-icon">📊</span>
                        <span><strong>bar_chart.pdf</strong> — Horizontal bar chart with project details and timelines</span>
                    </div>
                </div>
                
                <!-- Regards -->
                <div class="regards">
                    Best regards,
                    <div class="regards-name">Timesheet Reporting System</div>
                </div>
            </div>
            
            <!-- Footer -->
            <div class="footer">
                <hr class="divider">
                <div class="footer-text">
                    This is an automated report. Please do not reply to this email.
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Create initial log entry
    log_id = create_report_email_log(
        recipient_emails=recipients,
        period_start=period_start,
        period_end=period_end,
        trigger_type=trigger_type,
        sent_by=sent_by,
        email_subject=subject,
        total_employees=submitted_count,
        total_entries=total_entries,
        total_projects=project_count,
        total_days=total_days
    )
    
    # Create email message
    msg = MIMEMultipart()
    
    # Set sender with display name: "Timesheet Admin <remotedesktopnyati@gmail.com>"
    msg['From'] = 'Timesheet Admin <remotedesktopnyati@gmail.com>'
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = subject
    
    # Create alternative part for plain text + HTML
    msg_alternative = MIMEMultipart('alternative')
    msg.attach(msg_alternative)
    
    # Attach HTML version (preferred)
    msg_alternative.attach(MIMEText(html_body, 'html'))
    
    # Attach Bar Chart PDF
    try:
        bar_part = MIMEBase('application', 'pdf')
        bar_part.set_payload(bar_pdf_bytes)
        encoders.encode_base64(bar_part)
        bar_filename = f"bar_chart_{period_start.strftime('%d%m%Y')}_{period_end.strftime('%d%m%Y')}.pdf"
        bar_part.add_header('Content-Disposition', f'attachment; filename="{bar_filename}"')
        msg.attach(bar_part)
    except Exception as bar_err:
        error_msg = f"Failed to attach bar chart PDF: {bar_err}"
        if log_id:
            update_report_email_log(log_id, status=-1, error_message=error_msg)
        return False, error_msg, log_id
    
    # Send email
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
        server.sendmail(smtp_user, recipients, msg.as_string())
        server.close()
        
        # Update log as successful
        if log_id:
            update_report_email_log(log_id, status=1)
        
        return True, "Report email sent successfully", log_id
        
    except Exception as e:
        error_details = traceback.format_exc()
        error_msg = f"Failed to send email: {str(e)}"
        print(f"Email send error: {error_details}")
        
        # Update log as failed
        if log_id:
            update_report_email_log(log_id, status=-1, error_message=error_msg)
        
        return False, error_msg, log_id


def send_test_report_email(recipient):
    """Send a test email to verify configuration."""
    try:
        smtp_host = st.secrets["SMTP_HOST"]
        smtp_port = st.secrets["SMTP_PORT"]
        smtp_user = st.secrets["SMTP_USER"]
        smtp_pass = st.secrets["SMTP_PASS"]
        smtp_encryption = st.secrets.get("SMTP_ENCRYPTION", "starttls").lower()
    except KeyError as e:
        return False, f"Missing {e.args[0]} in Streamlit secrets"
    
    try:
        smtp_port = int(smtp_port)
    except ValueError:
        return False, "Invalid SMTP_PORT in Streamlit secrets"
    
    subject = "Test Email - Timesheet Report Configuration"
    body = f"""Hello,

This is a test email from the Timesheet Reporting System.

Your email configuration is working correctly!

Sent at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Regards,
Timesheet Reporting System
"""
    
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = recipient
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
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
        server.sendmail(smtp_user, [recipient], msg.as_string())
        server.close()
        
        return True, "Test email sent successfully"
    except Exception as e:
        return False, f"Failed to send test email: {str(e)}"

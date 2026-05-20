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
        print("Failed to generate/attach PDF:", pdf_err)

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



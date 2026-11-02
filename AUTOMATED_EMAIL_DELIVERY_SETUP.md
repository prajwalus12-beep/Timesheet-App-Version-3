# Automated Email Delivery System Setup Guide

## Overview

This guide covers the complete setup for automated email delivery in the Timesheet Application. The system sends scheduled emails **independently of Streamlit**, ensuring 24/7 reliability.

### What Gets Sent

1. **Weekly Report Emails** (Friday 5:00 PM)
   - Bar chart PDF with project analytics
   - Summary statistics
   - Recipients: Configured team leads/managers

2. **Timesheet Reminder Emails** (Thursday 10:00 AM)
   - Reminders to employees with incomplete timesheets
   - Recipients: Auto-identified based on completion status

3. **Automatic Cleanup** (Sunday 2:00 AM)
   - Removes logs older than 4 weeks
   - Keeps database clean and optimized

---

## System Architecture

### Before (Problem)
```
Streamlit ← APScheduler (embedded)
   ↓
   └─ Only runs while Streamlit is running
   └─ Dies on restart/crash
   └─ No emails at night
```

### After (Solution)
```
Streamlit ← Manual button + Settings UI
   ↓
Database ← Stored configuration
   ↓
Standalone Scheduler (runs 24/7)
   ├─ Windows Task Scheduler / Linux Cron
   ├─ Independent of Streamlit
   ├─ Reads settings from same database
   └─ Sends emails automatically
```

---

## Files Created

### 1. Core Scheduler
```
services/automated_scheduler.py
├─ ScheduledEmailService class
├─ send_weekly_report_email()
├─ send_timesheet_reminders()
├─ cleanup_old_logs()
└─ run_all_tasks()
```

### 2. Setup Scripts
```
scripts/setup_windows_scheduler.ps1
├─ PowerShell script for Windows
├─ Creates 3 scheduled tasks
└─ Admin only

scripts/setup_linux_scheduler.sh
├─ Bash script for Linux/macOS
├─ Creates 3 cron jobs
└─ Root recommended
```

---

## Setup Instructions

### Option A: Windows Setup (Recommended if on Windows)

#### Step 1: Verify Python Installation

Open PowerShell and run:
```powershell
python --version
```

You should see: `Python 3.x.x`

#### Step 2: Find Python Path

```powershell
where python
```

Example output:
```
C:\Users\prajw\AppData\Local\Programs\Python\Python314\python.exe
```

#### Step 3: Edit Setup Script

Open `scripts/setup_windows_scheduler.ps1` in your editor.

Update these variables:
```powershell
$APP_ROOT = "c:\FMP TS\update project include project updatation page\Timesheet-App-Version-3"
$PYTHON_EXE = "C:\Users\prajw\AppData\Local\Programs\Python\Python314\python.exe"
```

#### Step 4: Run Setup Script

**IMPORTANT: Run as Administrator**

```powershell
# Option 1: Right-click the file → "Run with PowerShell"

# Option 2: PowerShell as Administrator, then:
cd "c:\FMP TS\update project include project updatation page\Timesheet-App-Version-3"
powershell -ExecutionPolicy Bypass -File scripts/setup_windows_scheduler.ps1
```

Expected output:
```
✅ Configuration verified
✅ Log directory ready
✅ Task created successfully (x3)
✅ Setup completed successfully!
```

#### Step 5: Verify Tasks

1. Open **Task Scheduler** (Windows+R → `taskschd.msc`)
2. Look for:
   - `Timesheet-WeeklyReport`
   - `Timesheet-Reminders`
   - `Timesheet-LogCleanup`
3. Right-click → **Properties** to view details

#### Step 6: Test Tasks

Right-click any task → **Run** to test immediately.

Check logs:
```
c:\FMP TS\update project include project updatation page\Timesheet-App-Version-3\logs\scheduler\
```

---

### Option B: Linux/macOS Setup

#### Step 1: Make Script Executable

```bash
chmod +x scripts/setup_linux_scheduler.sh
```

#### Step 2: Edit Setup Script

```bash
nano scripts/setup_linux_scheduler.sh
```

Update these variables:
```bash
APP_ROOT="/path/to/Timesheet-App-Version-3"
PYTHON_EXE="python3"
```

#### Step 3: Run Setup Script

```bash
./scripts/setup_linux_scheduler.sh
```

Or with sudo:
```bash
sudo ./scripts/setup_linux_scheduler.sh
```

Expected output:
```
✅ Configuration verified
✅ Log directory ready
✅ Cron jobs installed successfully!
✅ Setup completed successfully!
```

#### Step 4: Verify Cron Jobs

```bash
crontab -l
```

You should see 3 lines for Timesheet tasks.

#### Step 5: Test Jobs

```bash
python3 /path/to/services/automated_scheduler.py weekly-report
python3 /path/to/services/automated_scheduler.py reminders
python3 /path/to/services/automated_scheduler.py cleanup
```

Check logs:
```bash
tail -f /path/to/logs/scheduler/scheduler_*.log
```

---

### Option C: Docker Setup (Advanced)

If running in Docker, add to your Dockerfile:

```dockerfile
# Install cron
RUN apt-get update && apt-get install -y cron

# Copy cron setup
COPY scripts/setup_linux_scheduler.sh /app/scripts/
RUN chmod +x /app/scripts/setup_linux_scheduler.sh

# Run setup during build
RUN /app/scripts/setup_linux_scheduler.sh

# Keep cron running
CMD ["cron", "-f"]
```

---

### Option D: Cloud Deployment

#### AWS Lambda + EventBridge

1. Create Lambda function with `services/automated_scheduler.py`
2. Set environment variables for database connection
3. Create EventBridge rules:
   - Weekly Report: `cron(0 17 ? * FRI *)`
   - Reminders: `cron(0 10 ? * THU *)`
   - Cleanup: `cron(0 2 ? * SUN *)`

#### Azure Functions

```csharp
[FunctionName("TimesheetScheduler")]
public static async Task Run(
    [TimerTrigger("0 0 17 * * FRI")] TimerInfo myTimer
)
{
    // Call Python script or trigger via HTTP
}
```

#### Google Cloud Scheduler

```bash
gcloud scheduler jobs create app-engine weekly-report \
  --schedule "0 17 * * FRI" \
  --http-method POST \
  --uri "https://your-app.com/api/run-scheduler" \
  --time-zone "America/New_York"
```

---

## Configuration Management

### Changing Schedule in Streamlit UI

1. Go to **Settings** → **📊 Send Report Settings**
2. Adjust:
   - Enable/Disable toggle
   - Recipients
   - Day and Time
3. Click **💾 Save Settings**

The scheduler picks up these changes automatically.

### Manual Testing

#### Test Weekly Report
```bash
# Windows
python services/automated_scheduler.py weekly-report

# Linux
python3 services/automated_scheduler.py weekly-report
```

#### Test Reminders
```bash
python services/automated_scheduler.py reminders
```

#### Test All Tasks
```bash
python services/automated_scheduler.py all
```

#### Test Cleanup
```bash
python services/automated_scheduler.py cleanup
```

---

## Monitoring & Logs

### Log Location

```
logs/scheduler/
├── scheduler_20261024.log     (daily logs)
├── weekly_report.log           (Linux only)
├── reminders.log               (Linux only)
└── cleanup.log                 (Linux only)
```

### View Logs

#### Windows
```powershell
# Real-time view
Get-Content logs\scheduler\scheduler_*.log -Wait

# View Task History
Get-EventLog -LogName System -Source TaskScheduler | Where-Object {$_.Message -like "*Timesheet*"}
```

#### Linux
```bash
# Real-time view
tail -f logs/scheduler/scheduler_*.log

# Search for errors
grep ERROR logs/scheduler/*.log

# Check specific task
crontab -l | grep TIMESHEET
```

### Log Format

```
2026-10-24 17:00:05 | INFO     | ============================================================
2026-10-24 17:00:05 | INFO     | Starting: Weekly Report Email
2026-10-24 17:00:05 | INFO     | Recipients: john@company.com, sarah@company.com
2026-10-24 17:00:15 | INFO     | ✅ Weekly Report Email SUCCESS: Report email sent successfully
2026-10-24 17:00:15 | INFO     | Completed: Weekly Report Email
```

---

## Troubleshooting

### Issue: Task Not Running

**Windows:**
1. Open Task Scheduler
2. Right-click task → **Properties**
3. Check:
   - Enabled ☑
   - Trigger is set correctly
   - Action points to correct Python/script
4. Check logs for errors

**Linux:**
```bash
# Verify cron is running
sudo service cron status

# Check syslog
grep CRON /var/log/syslog

# Run manually to test
python3 services/automated_scheduler.py weekly-report
```

### Issue: "Python Not Found"

**Windows:**
Update `setup_windows_scheduler.ps1`:
```powershell
$PYTHON_EXE = "C:\Full\Path\To\python.exe"
```

**Linux:**
Update `setup_linux_scheduler.sh`:
```bash
PYTHON_EXE="/usr/bin/python3"
# or full path
PYTHON_EXE="/usr/local/bin/python3"
```

### Issue: Database Connection Error

Check:
1. `.env` file exists and has correct `SUPABASE_*` vars
2. Supabase credentials are valid
3. VPN/Network access if needed
4. Database is online

### Issue: Email Not Sent

Check logs for:
1. `recipients` is empty (add in Settings UI)
2. `enabled` is False (toggle in Settings UI)
3. SMTP credentials in `.env` are correct
4. Recipient emails are valid

### Issue: Permissions Denied

**Windows:**
Run PowerShell as Administrator

**Linux:**
```bash
# Check file permissions
ls -la services/automated_scheduler.py

# Make executable
chmod +x services/automated_scheduler.py

# Run with proper permissions
sudo python3 services/automated_scheduler.py weekly-report
```

---

## Monitoring Best Practices

### 1. Set Up Log Rotation

**Windows (automatic):**
Task Scheduler handles this.

**Linux:**
```bash
# Install logrotate if needed
sudo apt-get install logrotate

# Create /etc/logrotate.d/timesheet-scheduler
/path/to/logs/scheduler/*.log {
    daily
    rotate 7
    compress
    delaycompress
    notifempty
    missingok
}
```

### 2. Alert on Failures

**Windows:**
Task Scheduler can send email on failure (Advanced Settings)

**Linux:**
Add to crontab:
```bash
MAILTO=admin@company.com
```

### 3. Regular Health Checks

Add a weekly test:
```bash
# Every Monday at 9:00 AM
0 9 * * MON python3 services/automated_scheduler.py all
```

---

## Security Considerations

### 1. Environment Variables

Never commit `.env` to git:
```bash
echo ".env" >> .gitignore
```

### 2. Task Credentials

**Windows:**
- Use SYSTEM account (recommended)
- Or specific service account with minimal permissions

**Linux:**
- Don't run as root unless necessary
- Use dedicated service user

### 3. Log Files

Ensure logs don't contain sensitive info:
- Passwords: Never logged ✓
- Email addresses: Logged for audit ✓
- Recipient count: Logged for audit ✓

### 4. Database Access

Use environment variables for credentials:
```bash
SUPABASE_URL=your_url
SUPABASE_KEY=your_key
SMTP_USER=your_email
SMTP_PASS=your_password
```

---

## Maintenance

### Weekly

- [ ] Check logs for errors
- [ ] Verify tasks ran at expected times
- [ ] Test manual email button in Streamlit

### Monthly

- [ ] Review log file sizes
- [ ] Verify database cleanup completed
- [ ] Test each scheduled task manually

### Quarterly

- [ ] Update Python dependencies
- [ ] Review and update SMTP credentials
- [ ] Test disaster recovery (full app restart)

---

## Uninstall Instructions

### Windows

1. Open Task Scheduler
2. Find each `Timesheet-*` task
3. Right-click → **Delete**

### Linux

```bash
crontab -e

# Remove all lines containing TIMESHEET_AUTO_EMAILS
# Save and exit
```

---

## Support & Debugging

### Enable Debug Logging

Edit `services/automated_scheduler.py`:
```python
logging.basicConfig(level=logging.DEBUG)  # Change from INFO to DEBUG
```

### Collect Diagnostic Information

```bash
# Windows
Get-Content logs\scheduler\scheduler_*.log | Select-String "ERROR|Exception"

# Linux
grep "ERROR\|Exception" logs/scheduler/*.log
```

### Get Help

Include in bug report:
1. Relevant log entries
2. Python version: `python --version`
3. OS and version
4. Database connection status
5. SMTP configuration (no passwords)

---

## Next Steps

1. ✅ Deploy scheduler using appropriate setup script
2. ✅ Configure email recipients in Streamlit UI
3. ✅ Test all three tasks manually
4. ✅ Monitor logs for first 24 hours
5. ✅ Set up log rotation and alerts
6. ✅ Document in your team wiki/confluence

---

## Summary

| Component | Location | Purpose |
|-----------|----------|---------|
| **Scheduler Service** | `services/automated_scheduler.py` | Core scheduling logic |
| **Windows Setup** | `scripts/setup_windows_scheduler.ps1` | Task Scheduler registration |
| **Linux Setup** | `scripts/setup_linux_scheduler.sh` | Cron job registration |
| **Logs** | `logs/scheduler/` | Execution logs & debugging |
| **Config** | Streamlit UI → Settings | Schedule times & recipients |

---

**Version:** 1.0  
**Last Updated:** October 2026  
**Status:** Production Ready

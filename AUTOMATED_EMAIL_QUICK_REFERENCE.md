# Automated Email Delivery - Quick Reference

## TL;DR Setup (Windows)

```powershell
# 1. Run as Administrator
# 2. Edit paths in setup script
# 3. Run:
powershell -ExecutionPolicy Bypass -File scripts/setup_windows_scheduler.ps1
# 4. Done! Tasks run automatically
```

## TL;DR Setup (Linux)

```bash
chmod +x scripts/setup_linux_scheduler.sh
./scripts/setup_linux_scheduler.sh
# Done! Cron jobs run automatically
```

---

## Manual Test Commands

### Windows
```powershell
# Weekly Report
python services/automated_scheduler.py weekly-report

# Timesheet Reminders
python services/automated_scheduler.py reminders

# All Tasks
python services/automated_scheduler.py all
```

### Linux
```bash
python3 services/automated_scheduler.py weekly-report
python3 services/automated_scheduler.py reminders
python3 services/automated_scheduler.py all
```

---

## Scheduled Times

| Task | Day | Time | Timezone |
|------|-----|------|----------|
| Weekly Report | Friday | 17:00 (5:00 PM) | Server Local |
| Reminders | Thursday | 10:00 (10:00 AM) | Server Local |
| Cleanup | Sunday | 02:00 (2:00 AM) | Server Local |

---

## Change Schedule

1. Go to Streamlit → **Settings** → **📊 Send Report Settings**
2. Adjust day/time
3. Click **💾 Save Settings**
4. System picks up changes automatically ✓

---

## View Logs

### Windows
```powershell
Get-Content logs\scheduler\scheduler_*.log -Wait
```

### Linux
```bash
tail -f logs/scheduler/scheduler_*.log
```

---

## Check Status

### Windows
```powershell
# View Tasks
Get-ScheduledTask -TaskName "Timesheet-*"

# View Next Run
(Get-ScheduledTask -TaskName "Timesheet-WeeklyReport").Triggers
```

### Linux
```bash
# View Cron Jobs
crontab -l

# View Last Execution
grep CRON /var/log/syslog | tail -10
```

---

## Troubleshoot

### Task Not Running

**Windows:**
1. Task Scheduler → find task
2. Right-click → Run
3. Check if status changes to "Running"
4. View logs: `logs/scheduler/scheduler_*.log`

**Linux:**
```bash
python3 services/automated_scheduler.py weekly-report
# Check for errors
```

### Email Not Sent

1. Check recipients configured:
   - Streamlit → Settings → Add Recipients
2. Check enabled:
   - Streamlit → Settings → Toggle "Enable Automatic..."
3. Check logs for errors
4. Test manually (commands above)

### Python Not Found

**Windows:**
```powershell
# Find Python
where python

# Edit setup script with full path
$PYTHON_EXE = "C:\full\path\to\python.exe"
```

**Linux:**
```bash
# Find Python
which python3

# Edit setup script with full path
PYTHON_EXE="/full/path/to/python3"
```

---

## Files Overview

```
services/automated_scheduler.py
├─ ScheduledEmailService class
├─ send_weekly_report_email()
├─ send_timesheet_reminders()
├─ cleanup_old_logs()
└─ run_all_tasks()

scripts/
├─ setup_windows_scheduler.ps1  (Windows)
└─ setup_linux_scheduler.sh     (Linux)

logs/scheduler/
└─ scheduler_YYYYMMDD.log
```

---

## Key Features

✅ Runs **24/7** independently  
✅ **Survives restarts** and crashes  
✅ Reads settings from **same database**  
✅ Settings changes picked up **automatically**  
✅ Comprehensive **logging** and error handling  
✅ No **Streamlit dependency**  
✅ Works on **Windows, Linux, macOS**  
✅ Cloud-ready (**AWS, Azure, GCP**)  

---

## Environment Variables

Must be set in `.env`:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password
SMTP_ENCRYPTION=starttls
```

---

## Common Issues & Fixes

| Issue | Fix |
|-------|-----|
| Python not found | Update `$PYTHON_EXE` / `PYTHON_EXE` path |
| Task not running | Check Task Scheduler / crontab, run manually |
| Email not sent | Add recipients in Streamlit UI, enable toggle |
| Permission denied | Run as Administrator (Windows) / sudo (Linux) |
| Database error | Check .env file, verify Supabase credentials |
| Logs not showing | Check `logs/scheduler/` directory exists |

---

## Support

### Debug Mode

Edit `services/automated_scheduler.py`:
```python
logging.basicConfig(level=logging.DEBUG)  # INFO → DEBUG
```

### Check System Time

Tasks use server timezone. Verify:
```powershell
# Windows
Get-Date

# Linux
date
```

### Restart Service

```powershell
# Windows - Restart Task Scheduler
Restart-Service -Name "Schedule"

# Linux - Restart cron
sudo service cron restart
```

---

## Production Checklist

- [ ] Setup script ran without errors
- [ ] All 3 tasks created and visible
- [ ] Recipients configured in Streamlit
- [ ] Manual test of each task passed
- [ ] Logs directory created and writable
- [ ] First scheduled run completed successfully
- [ ] Email received by recipients
- [ ] Log rotation configured (optional)
- [ ] Alerts configured (optional)
- [ ] Documented in team wiki

---

**Version:** 1.0 | **Updated:** Oct 2026 | **Status:** Ready for Production

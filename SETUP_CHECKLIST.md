# Automated Email Delivery - Setup Checklist

## Pre-Setup (5 minutes)

### Prerequisites Verification
- [ ] Python 3.8+ installed: `python --version`
- [ ] `.env` file exists and is configured
- [ ] Supabase credentials valid (test in Streamlit)
- [ ] SMTP credentials working (test email sends manually)
- [ ] Internet connection stable
- [ ] Administrator access (Windows) / sudo access (Linux)

### File Check
- [ ] `services/automated_scheduler.py` exists
- [ ] `scripts/setup_windows_scheduler.ps1` exists (Windows)
- [ ] `scripts/setup_linux_scheduler.sh` exists (Linux)
- [ ] `scripts/verify_scheduler_setup.py` exists
- [ ] Documentation files exist

---

## Windows Setup (20 minutes)

### Step 1: Preparation (5 min)
- [ ] Open Notepad
- [ ] Edit `scripts/setup_windows_scheduler.ps1`
- [ ] Verify `$APP_ROOT` path is correct
- [ ] Verify `$PYTHON_EXE` path is correct
  - Run `where python` to find it
- [ ] Save file

### Step 2: Execution (10 min)
- [ ] Open PowerShell as Administrator
- [ ] Navigate to app directory:
  ```powershell
  cd "C:\FMP TS\update project include project updatation page\Timesheet-App-Version-3"
  ```
- [ ] Run setup script:
  ```powershell
  powershell -ExecutionPolicy Bypass -File scripts/setup_windows_scheduler.ps1
  ```
- [ ] Script completes without errors
- [ ] See success messages for 3 tasks created

### Step 3: Verification (5 min)
- [ ] Open Task Scheduler (Windows + R → taskschd.msc)
- [ ] Find `Timesheet-WeeklyReport` task
  - [ ] Status: Enabled
  - [ ] Trigger: Weekly on Friday at 17:00
  - [ ] Action: Python script
- [ ] Find `Timesheet-Reminders` task
  - [ ] Status: Enabled
  - [ ] Trigger: Weekly on Thursday at 10:00
- [ ] Find `Timesheet-LogCleanup` task
  - [ ] Status: Enabled
  - [ ] Trigger: Weekly on Sunday at 02:00
- [ ] Right-click each task → Properties → verify details

---

## Linux/macOS Setup (20 minutes)

### Step 1: Preparation (5 min)
- [ ] Open text editor
- [ ] Edit `scripts/setup_linux_scheduler.sh`
- [ ] Verify `APP_ROOT` path is correct
- [ ] Verify `PYTHON_EXE` path is correct
  - Run `which python3` to find it
- [ ] Save file

### Step 2: Execution (10 min)
- [ ] Make script executable:
  ```bash
  chmod +x scripts/setup_linux_scheduler.sh
  ```
- [ ] Run setup script with sudo:
  ```bash
  sudo ./scripts/setup_linux_scheduler.sh
  ```
- [ ] Script completes without errors
- [ ] See success messages

### Step 3: Verification (5 min)
- [ ] View cron jobs:
  ```bash
  crontab -l
  ```
- [ ] Verify you see 3 lines containing `TIMESHEET_AUTO_EMAILS`:
  - [ ] Friday 17:00 weekly-report
  - [ ] Thursday 10:00 reminders
  - [ ] Sunday 02:00 cleanup

---

## Configuration in Streamlit (10 minutes)

### Step 1: Access Settings
- [ ] Open Streamlit app
- [ ] Login with admin account
- [ ] Go to Settings page
- [ ] Scroll to "📊 Send Report Settings" tab

### Step 2: Add Recipients
- [ ] Check current recipients list
- [ ] Click "Add Recipient" button
- [ ] Enter first email address
- [ ] Click "Add"
- [ ] Repeat for all recipients
- [ ] Verify recipients appear in list

### Step 3: Configure Schedule
- [ ] Day selector: Select "Friday" (or preferred day)
- [ ] Time picker: Select 17:00 (or preferred time)
- [ ] Timezone: Select your timezone
- [ ] Enable toggle: Check "Enable Automatic Weekly Reports"

### Step 4: Save Settings
- [ ] Click "💾 Save Settings" button
- [ ] Wait for confirmation message
- [ ] Verify "✅ Settings saved" toast appears
- [ ] Verify "Next scheduled run" displays correct date/time

---

## Verification (15 minutes)

### Step 1: Run Verification Script
- [ ] Execute verification script:
  ```bash
  python scripts/verify_scheduler_setup.py
  ```
- [ ] All checks show green ✅
- [ ] Summary shows "ALL CHECKS PASSED"

### Step 2: Manual Test - All Tasks
- [ ] Run all tasks:
  ```bash
  python services/automated_scheduler.py all
  ```
- [ ] Check output for:
  - [ ] "Starting: Weekly Report Email"
  - [ ] "✅ Weekly Report Email SUCCESS"
  - [ ] "Starting: Timesheet Reminder Emails"
  - [ ] "✅ Timesheet Reminder Emails COMPLETE"
  - [ ] "Starting: Log Cleanup"
  - [ ] "✅ Log Cleanup SUCCESS"
- [ ] No error messages displayed

### Step 3: Check Logs
- [ ] Navigate to logs directory:
  ```bash
  cd logs/scheduler
  ```
- [ ] List files:
  ```bash
  ls -la scheduler_*.log
  ```
- [ ] Open latest log file
- [ ] Verify contains success messages
- [ ] No ERROR lines present

### Step 4: Email Test (Optional)
- [ ] Streamlit → Settings → Test Email button
- [ ] Check first recipient's email
- [ ] Verify test email received
- [ ] Confirm no spam folder

---

## First Week Monitoring (Daily)

### Daily Checklist (5 minutes each)
- [ ] Check logs for errors
- [ ] Verify no tasks failed
- [ ] No undeliverable emails

### Day 1 (Setup Day)
- [ ] ✅ Setup complete
- [ ] ✅ Configuration saved
- [ ] ✅ Verification passed
- [ ] ✅ Manual tests successful

### Day 2-6 (Before Thursday)
- [ ] Monitor logs daily
- [ ] No errors appearing
- [ ] System running smoothly

### Day 7 (Thursday - Reminder Test)
- [ ] Wait for 10:00 AM
- [ ] Check logs:
  ```bash
  tail -f logs/scheduler/*.log
  ```
- [ ] Verify task ran
- [ ] Check recipient emails for reminders
- [ ] Confirm emails delivered successfully

### Day 8 (Friday - Report Test)
- [ ] Wait for 17:00 (5:00 PM)
- [ ] Check logs:
  ```bash
  tail -f logs/scheduler/*.log
  ```
- [ ] Verify task ran
- [ ] Check recipient emails for report
- [ ] Open attached PDF charts
- [ ] Confirm data accuracy
- [ ] Verify email formatting

---

## Troubleshooting (If Issues Arise)

### Issue: Setup Script Failed

**Windows:**
- [ ] Verify running as Administrator
- [ ] Check Python path is correct
- [ ] Check app path exists
- [ ] Run: `python -m py_compile services/automated_scheduler.py`
- [ ] Re-run setup script

**Linux:**
- [ ] Check script is executable: `ls -la scripts/setup_linux_scheduler.sh`
- [ ] Verify Python path: `which python3`
- [ ] Run with verbose: `bash -x scripts/setup_linux_scheduler.sh`
- [ ] Try with sudo: `sudo ./scripts/setup_linux_scheduler.sh`

### Issue: Verification Fails

- [ ] Run verification again: `python scripts/verify_scheduler_setup.py`
- [ ] Read error messages carefully
- [ ] Fix indicated issues:
  - [ ] Install missing packages: `pip install supabase python-dotenv`
  - [ ] Fix .env file: verify credentials
  - [ ] Check database: test connection manually
- [ ] Re-run verification

### Issue: Task Doesn't Run

**Windows:**
- [ ] Open Task Scheduler
- [ ] Find task
- [ ] Right-click → Run
- [ ] Check "Last Run Result"
- [ ] If failed, check "Actions" tab for errors
- [ ] Check logs: `logs/scheduler/*.log`

**Linux:**
- [ ] Check crontab: `crontab -l`
- [ ] Verify correct syntax
- [ ] Check syslog: `grep CRON /var/log/syslog`
- [ ] Test manually: `python3 services/automated_scheduler.py weekly-report`
- [ ] Check logs: `logs/scheduler/*.log`

### Issue: Email Not Sent

- [ ] Check recipients configured in Streamlit
- [ ] Check "Enable Automatic" toggle is ON
- [ ] Check SMTP credentials in .env
- [ ] Test manually: `python services/automated_scheduler.py weekly-report`
- [ ] Check logs for SMTP errors
- [ ] Verify recipient email is valid

### Issue: Wrong Time/Day

**Windows:**
- [ ] Task Scheduler → Find task
- [ ] Right-click → Properties
- [ ] Check Triggers tab
- [ ] Verify day and time are correct
- [ ] Check server timezone: `Get-Date`

**Linux:**
- [ ] View crontab: `crontab -l`
- [ ] Verify correct day/time format
- [ ] Check server timezone: `date`
- [ ] Edit crontab: `crontab -e`

---

## Final Sign-Off

### System Ready Checklist
- [ ] All setup steps completed
- [ ] All verification checks passed
- [ ] First manual test successful
- [ ] Logs are being created correctly
- [ ] Scheduled tasks/cron jobs are registered
- [ ] Recipients have received test emails
- [ ] No errors in logs

### Documentation Complete
- [ ] Quick reference bookmarked: `AUTOMATED_EMAIL_QUICK_REFERENCE.md`
- [ ] Full guide available: `AUTOMATED_EMAIL_DELIVERY_SETUP.md`
- [ ] Troubleshooting guide reviewed
- [ ] Team informed of new system

### Production Ready
- [ ] ✅ System is operational
- [ ] ✅ Monitoring in place
- [ ] ✅ Backup procedures documented
- [ ] ✅ Support contact identified
- [ ] ✅ Ready for 24/7 operation

---

## Go-Live Date

**Setup Date:** _________________

**Verification Date:** _________________

**Go-Live Date:** _________________

**Signed Off By:** _________________

**Date:** _________________

---

## Ongoing Maintenance

### Daily (Automated)
- ✅ Tasks run at scheduled times (no action needed)
- ✅ Logs created automatically
- ✅ Emails sent automatically

### Weekly
- [ ] Monday: Review logs for issues
- [ ] Monday: Verify no error emails
- [ ] Friday: After report emails, confirm delivery

### Monthly
- [ ] First Monday: Check log file sizes
- [ ] First Monday: Verify database cleanup ran
- [ ] Review any error patterns

### Quarterly
- [ ] Update documentation if changed
- [ ] Test complete restart procedure
- [ ] Review and update credentials if needed

---

## Emergency Procedures

### If Emails Stop Coming

1. [ ] Check if system is running:
   ```bash
   python scripts/verify_scheduler_setup.py
   ```

2. [ ] Check logs for errors:
   ```bash
   tail -100 logs/scheduler/*.log
   ```

3. [ ] Run manual test:
   ```bash
   python services/automated_scheduler.py all
   ```

4. [ ] Verify tasks registered:
   - Windows: Task Scheduler
   - Linux: `crontab -l`

5. [ ] If unresolved: contact support with:
   - [ ] Log files (last 24 hours)
   - [ ] Verification script output
   - [ ] Manual test output

### If SMTP Fails

- [ ] Test .env credentials manually
- [ ] Check SMTP provider status
- [ ] Verify IP whitelist (if applicable)
- [ ] Check app password (Gmail)
- [ ] Update credentials if expired

---

**Checklist Version:** 1.0  
**Last Updated:** October 2026  
**Status:** Ready to Use

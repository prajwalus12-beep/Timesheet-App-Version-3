# Quick Scheduler Setup Guide

## ⚠️ Current Problem

**Your scheduler is NOT working because:**
- APScheduler only runs while Streamlit is running
- When you close Streamlit, the scheduler stops
- Emails won't send automatically

**Solution:** Set up Windows Task Scheduler for 24/7 automatic emails

---

## 🚀 Quick Setup (5 Minutes)

### Step 1: Open PowerShell as Administrator

1. Press `Windows + X`
2. Click **"Windows PowerShell (Admin)"** or **"Terminal (Admin)"**
3. Click **"Yes"** when asked for permission

### Step 2: Navigate to Your Project

```powershell
cd "c:\FMP TS\update project include project updatation page\Timesheet-App-Version-3"
```

### Step 3: Run the Setup Script

```powershell
powershell -ExecutionPolicy Bypass -File scripts/setup_windows_scheduler.ps1
```

**Wait for:** You should see "✅ Setup completed successfully!"

### Step 4: Verify It Worked

```powershell
Get-ScheduledTask -TaskName "Timesheet-*"
```

**Expected output:**
```
TaskName                TaskPath    State
--------                --------    -----
Timesheet-WeeklyReport  \           Ready
Timesheet-Reminders     \           Ready
Timesheet-LogCleanup    \           Ready
```

---

## 🔍 Troubleshooting

### Issue: Script doesn't exist

**Solution:** Check if file exists:
```powershell
Test-Path scripts/setup_windows_scheduler.ps1
```

If it says `False`, the file is missing. Let me know and I'll recreate it.

### Issue: Python path error

**Solution:** Update the `$PYTHON_EXE` variable in the script:

1. Find your Python path:
```powershell
where python
```

2. Edit the script:
```powershell
notepad scripts/setup_windows_scheduler.ps1
```

3. Update this line with your Python path:
```powershell
$PYTHON_EXE = "C:\Full\Path\To\python.exe"
```

### Issue: Permission denied

**Solution:** Make sure you're running PowerShell **as Administrator**.

---

## ✅ After Setup

Once setup is complete:

1. **Automatic emails will send even when Streamlit is closed**
2. **Check status in Task Scheduler:**
   - Press `Windows + R`
   - Type `taskschd.msc`
   - Look for tasks starting with "Timesheet-"

3. **View logs:**
   ```
   c:\FMP TS\update project include project updatation page\Timesheet-App-Version-3\logs\scheduler\
   ```

4. **Test manually:**
   ```powershell
   python services/automated_scheduler.py weekly-report
   ```

---

## 📋 What Gets Created

| Task Name | Schedule | What It Does |
|-----------|----------|--------------|
| **Timesheet-WeeklyReport** | Monday 12:00 | Sends weekly report with configured date range |
| **Timesheet-Reminders** | Thursday 10:00 | Sends reminders to employees |
| **Timesheet-LogCleanup** | Sunday 02:00 | Cleans old logs |

---

## ⏰ Changing the Schedule

**Method 1: Via Streamlit (Recommended)**
1. Go to **Settings → Automatic Report Settings**
2. Change day/time
3. Click **Save Settings**
4. The scheduler updates automatically

**Method 2: Via Task Scheduler**
1. Open Task Scheduler (`taskschd.msc`)
2. Find "Timesheet-WeeklyReport"
3. Right-click → **Properties**
4. Go to **Triggers** tab
5. Edit the schedule

---

## 🆘 Still Not Working?

### Quick Test:

```powershell
# Test if the script works
python services/automated_scheduler.py weekly-report

# Check if email was sent (look for success message)
```

### Check Logs:

```powershell
Get-Content logs\scheduler\*.log -Tail 50
```

### Verify Settings:

1. Go to Streamlit → **Settings**
2. Check:
   - ✅ "Enable Automatic Reports" is **ON**
   - ✅ Recipients are configured
   - ✅ Date Range is selected (e.g., "Last Week")
   - ✅ Schedule day/time is set

---

## 💡 Why This Matters

**Without Windows Task Scheduler:**
- ❌ Streamlit must be running 24/7
- ❌ Emails stop if you restart computer
- ❌ Emails stop if Streamlit crashes
- ❌ Unreliable

**With Windows Task Scheduler:**
- ✅ Emails send even when Streamlit is closed
- ✅ Survives restarts
- ✅ Runs 24/7 automatically
- ✅ Reliable production solution

---

## 📞 Need Help?

If setup fails, provide:
1. Error message from setup script
2. Output of: `python --version`
3. Output of: `where python`
4. Screenshot of error (if any)

---

**Ready?** Run the setup script now to get automatic emails working! 🚀

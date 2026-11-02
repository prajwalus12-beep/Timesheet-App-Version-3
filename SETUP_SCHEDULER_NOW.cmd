@echo off
REM Quick Setup for Windows Task Scheduler
REM Run this file as Administrator to set up automatic emails

echo ========================================
echo Timesheet Automatic Email Setup
echo ========================================
echo.
echo This will set up Windows Task Scheduler so emails
echo send automatically 24/7, even when Streamlit is closed.
echo.
echo Press any key to continue, or Ctrl+C to cancel...
pause > nul

cd /d "c:\FMP TS\update project include project updatation page\Timesheet-App-Version-3"

echo.
echo Running setup script...
echo.

powershell -ExecutionPolicy Bypass -File scripts/setup_windows_scheduler.ps1

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Check Task Scheduler (taskschd.msc)
echo 2. Look for tasks starting with "Timesheet-"
echo 3. Verify "Next scheduled run" in Settings page
echo.
echo Press any key to exit...
pause > nul

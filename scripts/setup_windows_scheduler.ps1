# Windows Task Scheduler Setup Script
# ========================================
# This PowerShell script sets up automated email delivery tasks in Windows Task Scheduler.
# 
# Prerequisites:
# - Run as Administrator
# - Python 3.8+ installed
# - Update paths as needed
#
# Usage:
# - Right-click and "Run with PowerShell"
# - OR: powershell -ExecutionPolicy Bypass -File setup_windows_scheduler.ps1
#
# After setup, scheduled tasks will run automatically at configured times.

# ========================================
# CONFIGURATION
# ========================================

# Path to your Timesheet App
$APP_ROOT = "c:\FMP TS\update project include project updatation page\Timesheet-App-Version-3"

# Path to Python executable
$PYTHON_EXE = "C:\Users\prajw\AppData\Local\Programs\Python\Python314\python.exe"
# Alternative: "python"  (if Python is in PATH)

# Script to run
$SCHEDULER_SCRIPT = "$APP_ROOT\services\automated_scheduler.py"

# Log directory
$LOG_DIR = "$APP_ROOT\logs\scheduler"

# Task details
$TASK_USER = "SYSTEM"  # or your Windows username
$TASK_PASSWORD = ""    # Leave empty if using SYSTEM account


# ========================================
# FUNCTION: Create Task
# ========================================

function Create-ScheduledTask {
    param(
        [string]$TaskName,
        [string]$TaskDescription,
        [string]$Schedule,
        [string]$Time,
        [string]$Arguments
    )
    
    Write-Host "Creating task: $TaskName" -ForegroundColor Cyan
    
    # Check if task exists
    $existingTask = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    
    if ($existingTask) {
        Write-Host "  ⚠️  Task already exists. Removing..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false | Out-Null
    }
    
    # Create trigger
    switch ($Schedule) {
        "weekly" {
            # Day and time based
            $day, $hour, $minute = $Time.Split(":")
            $trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek $day -At "$hour`:$minute"
        }
        default {
            Write-Host "  ❌ Unknown schedule type: $Schedule" -ForegroundColor Red
            return $false
        }
    }
    
    # Create action
    $action = New-ScheduledTaskAction -Execute $PYTHON_EXE -Argument $Arguments
    
    # Create task settings
    $settings = New-ScheduledTaskSettingsSet `
        -StartWhenAvailable `
        -RunOnlyIfNetworkAvailable `
        -AllowStartIfOnBatteries:$false `
        -DontStopIfGoingOnBatteries `
        -MultipleInstances Parallel
    
    # Register task
    try {
        Register-ScheduledTask -TaskName $TaskName `
            -Trigger $trigger `
            -Action $action `
            -Settings $settings `
            -Description $TaskDescription `
            -User $TASK_USER `
            -RunLevel Highest `
            -Force | Out-Null
        
        Write-Host "  ✅ Task created successfully" -ForegroundColor Green
        return $true
    }
    catch {
        Write-Host "  ❌ Failed to create task: $_" -ForegroundColor Red
        return $false
    }
}


# ========================================
# MAIN SCRIPT
# ========================================

Write-Host "`n" -ForegroundColor Cyan
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   Windows Task Scheduler Setup - Timesheet Auto Emails     ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host "`n"

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")

if (-not $isAdmin) {
    Write-Host "❌ ERROR: This script must be run as Administrator" -ForegroundColor Red
    Write-Host "   Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Red
    exit 1
}

# Verify paths exist
if (-not (Test-Path $APP_ROOT)) {
    Write-Host "❌ ERROR: App root path not found: $APP_ROOT" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $PYTHON_EXE)) {
    Write-Host "❌ ERROR: Python executable not found: $PYTHON_EXE" -ForegroundColor Red
    Write-Host "   Update `$PYTHON_EXE in this script to point to your Python installation" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $SCHEDULER_SCRIPT)) {
    Write-Host "❌ ERROR: Scheduler script not found: $SCHEDULER_SCRIPT" -ForegroundColor Red
    exit 1
}

Write-Host "Configuration:" -ForegroundColor Green
Write-Host "  App Root: $APP_ROOT"
Write-Host "  Python: $PYTHON_EXE"
Write-Host "  Script: $SCHEDULER_SCRIPT"
Write-Host "  Log Dir: $LOG_DIR"
Write-Host "`n"

# Create log directory
if (-not (Test-Path $LOG_DIR)) {
    New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null
    Write-Host "✅ Created log directory: $LOG_DIR" -ForegroundColor Green
}

Write-Host "Creating scheduled tasks...`n" -ForegroundColor Cyan

# ========================================
# Task 1: Weekly Report Email
# ========================================

$weeklyReportTask = Create-ScheduledTask `
    -TaskName "Timesheet-WeeklyReport" `
    -TaskDescription "Send automated weekly timesheet report emails every Friday at 5:00 PM" `
    -Schedule "weekly" `
    -Time "Friday:17:00" `
    -Arguments "`"$SCHEDULER_SCRIPT`" weekly-report"

# ========================================
# Task 2: Timesheet Reminders
# ========================================

$remindersTask = Create-ScheduledTask `
    -TaskName "Timesheet-Reminders" `
    -TaskDescription "Send timesheet reminder emails every Thursday at 10:00 AM" `
    -Schedule "weekly" `
    -Time "Thursday:10:00" `
    -Arguments "`"$SCHEDULER_SCRIPT`" reminders"

# ========================================
# Task 3: Log Cleanup
# ========================================

$cleanupTask = Create-ScheduledTask `
    -TaskName "Timesheet-LogCleanup" `
    -TaskDescription "Clean up old timesheet logs (runs every 28 days)" `
    -Schedule "weekly" `
    -Time "Sunday:02:00" `
    -Arguments "`"$SCHEDULER_SCRIPT`" cleanup"

# ========================================
# Summary
# ========================================

Write-Host "`n" -ForegroundColor Cyan
Write-Host "╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║                      SETUP COMPLETE                        ║" -ForegroundColor Cyan
Write-Host "╚════════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host "`n"

Write-Host "Scheduled Tasks Created:" -ForegroundColor Green
Write-Host "  1. Timesheet-WeeklyReport  → Friday 17:00 (5:00 PM)" -ForegroundColor Green
Write-Host "  2. Timesheet-Reminders     → Thursday 10:00 (10:00 AM)" -ForegroundColor Green
Write-Host "  3. Timesheet-LogCleanup    → Sunday 02:00 (2:00 AM)" -ForegroundColor Green

Write-Host "`nView and Manage Tasks:" -ForegroundColor Cyan
Write-Host "  1. Open Task Scheduler (Press Windows+R, type 'taskschd.msc')" -ForegroundColor Cyan
Write-Host "  2. Look for tasks starting with 'Timesheet-'" -ForegroundColor Cyan
Write-Host "  3. Right-click any task to run, disable, or view logs" -ForegroundColor Cyan

Write-Host "`nTest Tasks:" -ForegroundColor Yellow
Write-Host "  Run immediately: powershell -Command `"& '$PYTHON_EXE' '$SCHEDULER_SCRIPT' weekly-report`"" -ForegroundColor Yellow

Write-Host "`nLogs Location:" -ForegroundColor Magenta
Write-Host "  $LOG_DIR" -ForegroundColor Magenta

Write-Host "`n✅ Setup completed successfully!" -ForegroundColor Green
Write-Host ""

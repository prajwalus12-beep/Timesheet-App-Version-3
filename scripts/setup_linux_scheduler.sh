#!/bin/bash
# Linux/Unix Scheduler Setup Script
# ==================================
# This script sets up automated email delivery using cron jobs.
#
# Supports:
# - Linux distributions (Ubuntu, Debian, CentOS, etc.)
# - macOS
# - Any Unix-like system with cron
#
# Usage:
# - chmod +x setup_linux_scheduler.sh
# - ./setup_linux_scheduler.sh
#

# ========================================
# CONFIGURATION
# ========================================

# Path to your Timesheet App
APP_ROOT="/path/to/Timesheet-App-Version-3"

# Path to Python executable
PYTHON_EXE="python3"
# Alternative: "/usr/bin/python3" or full path

# Script to run
SCHEDULER_SCRIPT="$APP_ROOT/services/automated_scheduler.py"

# Log directory
LOG_DIR="$APP_ROOT/logs/scheduler"

# Cron job identifier (must be unique)
CRON_IDENTIFIER="TIMESHEET_AUTO_EMAILS"


# ========================================
# FUNCTIONS
# ========================================

# Print colored output
print_info() {
    echo -e "\033[0;36m$1\033[0m"  # Cyan
}

print_success() {
    echo -e "\033[0;32m$1\033[0m"  # Green
}

print_error() {
    echo -e "\033[0;31m$1\033[0m"  # Red
}

print_warning() {
    echo -e "\033[0;33m$1\033[0m"  # Yellow
}

# ========================================
# MAIN SCRIPT
# ========================================

clear
echo ""
print_info "╔════════════════════════════════════════════════════════════╗"
print_info "║    Linux/Unix Cron Setup - Timesheet Auto Emails          ║"
print_info "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if running as root (optional but recommended)
if [[ $EUID -ne 0 ]]; then
    print_warning "⚠️  This script is not running as root."
    print_warning "   Some operations may require 'sudo' or may fail."
    print_warning "   Continue? (y/n): "
    read -r response
    if [[ "$response" != "y" ]]; then
        exit 1
    fi
fi

# Verify paths exist
if [ ! -d "$APP_ROOT" ]; then
    print_error "❌ ERROR: App root path not found: $APP_ROOT"
    exit 1
fi

if ! command -v $PYTHON_EXE &> /dev/null; then
    print_error "❌ ERROR: Python not found: $PYTHON_EXE"
    print_error "   Update PYTHON_EXE in this script or ensure Python is in PATH"
    exit 1
fi

if [ ! -f "$SCHEDULER_SCRIPT" ]; then
    print_error "❌ ERROR: Scheduler script not found: $SCHEDULER_SCRIPT"
    exit 1
fi

print_success "✅ Configuration verified:"
echo "   App Root: $APP_ROOT"
echo "   Python: $PYTHON_EXE"
echo "   Script: $SCHEDULER_SCRIPT"
echo "   Log Dir: $LOG_DIR"
echo ""

# Create log directory
mkdir -p "$LOG_DIR"
print_success "✅ Log directory ready: $LOG_DIR"
echo ""

# ========================================
# INSTALL CRON JOBS
# ========================================

print_info "Installing cron jobs..."
echo ""

# Get current crontab (or create empty)
crontab -l 2>/dev/null > /tmp/crontab.bak || true

# Remove existing Timesheet cron jobs
grep -v "$CRON_IDENTIFIER" /tmp/crontab.bak > /tmp/crontab.new || true

# Add new cron jobs
{
    # Weekly Report Email - Friday at 5:00 PM
    echo "# $CRON_IDENTIFIER"
    echo "# Weekly Report Email - Fridays at 17:00 (5:00 PM)"
    echo "0 17 * * FRI $PYTHON_EXE $SCHEDULER_SCRIPT weekly-report >> $LOG_DIR/weekly_report.log 2>&1"
    echo ""
    
    # Timesheet Reminders - Thursday at 10:00 AM
    echo "# Timesheet Reminder Emails - Thursdays at 10:00 AM"
    echo "0 10 * * THU $PYTHON_EXE $SCHEDULER_SCRIPT reminders >> $LOG_DIR/reminders.log 2>&1"
    echo ""
    
    # Log Cleanup - Every 28 days at 2:00 AM (approximated as every 4 weeks on Sunday)
    echo "# Log Cleanup - Sundays at 02:00 AM"
    echo "0 2 * * SUN $PYTHON_EXE $SCHEDULER_SCRIPT cleanup >> $LOG_DIR/cleanup.log 2>&1"
    
} >> /tmp/crontab.new

# Install new crontab
crontab /tmp/crontab.new
crontab_status=$?

# Cleanup temp files
rm -f /tmp/crontab.bak /tmp/crontab.new

if [ $crontab_status -eq 0 ]; then
    print_success "✅ Cron jobs installed successfully!"
else
    print_error "❌ Failed to install cron jobs"
    exit 1
fi

echo ""

# ========================================
# SUMMARY
# ========================================

print_info "╔════════════════════════════════════════════════════════════╗"
print_info "║                      SETUP COMPLETE                        ║"
print_info "╚════════════════════════════════════════════════════════════╝"
echo ""

print_success "Scheduled Jobs Created:"
echo "  1. Weekly Report Email  → Friday 17:00 (5:00 PM)"
echo "  2. Timesheet Reminders  → Thursday 10:00 (10:00 AM)"
echo "  3. Log Cleanup          → Sunday 02:00 (2:00 AM)"
echo ""

print_info "View Installed Cron Jobs:"
echo "  crontab -l"
echo ""

print_info "Edit Cron Jobs:"
echo "  crontab -e"
echo ""

print_info "Logs Location:"
echo "  $LOG_DIR/"
echo ""

print_info "Test Commands (run manually):"
echo "  $PYTHON_EXE $SCHEDULER_SCRIPT weekly-report"
echo "  $PYTHON_EXE $SCHEDULER_SCRIPT reminders"
echo "  $PYTHON_EXE $SCHEDULER_SCRIPT cleanup"
echo ""

print_success "✅ Setup completed successfully!"
echo ""

# Verify installation
echo ""
print_warning "Verifying installation..."
crontab -l | grep -q "$CRON_IDENTIFIER"
if [ $? -eq 0 ]; then
    print_success "✅ Cron jobs verified"
else
    print_error "❌ Cron jobs verification failed"
fi

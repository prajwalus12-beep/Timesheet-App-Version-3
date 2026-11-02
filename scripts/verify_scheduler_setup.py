#!/usr/bin/env python3
"""
Scheduler Setup Verification Script
====================================
Verifies that the automated email scheduler is correctly configured and ready.

Usage:
------
python scripts/verify_scheduler_setup.py
python3 scripts/verify_scheduler_setup.py
"""

import sys
import os
import subprocess
import datetime
from pathlib import Path

# ANSI Colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'
    
    @staticmethod
    def disable():
        Colors.HEADER = Colors.BLUE = Colors.CYAN = ''
        Colors.GREEN = Colors.YELLOW = Colors.RED = ''
        Colors.END = Colors.BOLD = ''


def print_header(text):
    """Print formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.END}\n")


def print_success(text):
    """Print success message."""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text):
    """Print error message."""
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text):
    """Print warning message."""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_info(text):
    """Print info message."""
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")


def check_python_version():
    """Check Python version."""
    print_header("1. Python Version")
    
    version = sys.version_info
    version_str = f"{version.major}.{version.minor}.{version.micro}"
    
    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python {version_str} (Supported)")
        return True
    else:
        print_error(f"Python {version_str} (Need 3.8+)")
        return False


def check_required_packages():
    """Check if required packages are installed."""
    print_header("2. Required Packages")
    
    required_packages = {
        'supabase': 'Supabase client',
        'python-dotenv': 'Environment variables',
        'apscheduler': 'Scheduler (optional for standalone)',
        'smtplib': 'Email (built-in)',
        'logging': 'Logging (built-in)',
    }
    
    all_ok = True
    for package, description in required_packages.items():
        try:
            if package in ['smtplib', 'logging']:
                # Built-in modules
                __import__(package)
                print_success(f"{package}: {description} (built-in)")
            else:
                __import__(package)
                print_success(f"{package}: {description} ✓")
        except ImportError:
            if package in ['supabase', 'python-dotenv', 'apscheduler']:
                print_error(f"{package}: {description} - MISSING")
                all_ok = False
            else:
                print_warning(f"{package}: {description} - Not found")
    
    return all_ok


def check_files_exist():
    """Check if required files exist."""
    print_header("3. Required Files")
    
    base_path = Path(__file__).parent.parent
    
    required_files = {
        'services/automated_scheduler.py': 'Core scheduler service',
        'services/email_service.py': 'Email sending service',
        'services/report_email_service.py': 'Report generation',
        'database/queries.py': 'Database queries',
        'scripts/setup_windows_scheduler.ps1': 'Windows setup script',
        'scripts/setup_linux_scheduler.sh': 'Linux setup script',
        '.env': 'Environment configuration',
    }
    
    all_ok = True
    for file_path, description in required_files.items():
        full_path = base_path / file_path
        if full_path.exists():
            print_success(f"{file_path}: {description}")
        else:
            if file_path == '.env':
                print_warning(f"{file_path}: {description} - NOT FOUND (create it)")
                all_ok = False
            else:
                print_error(f"{file_path}: {description} - NOT FOUND")
                all_ok = False
    
    return all_ok


def check_environment_config():
    """Check environment configuration."""
    print_header("4. Environment Configuration")
    
    base_path = Path(__file__).parent.parent
    env_file = base_path / '.env'
    
    if not env_file.exists():
        print_error(".env file not found - Cannot verify configuration")
        return False
    
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_KEY',
        'SMTP_HOST',
        'SMTP_PORT',
        'SMTP_USER',
        'SMTP_PASS',
    ]
    
    try:
        from dotenv import load_dotenv
        load_dotenv(env_file)
        
        all_ok = True
        for var in required_vars:
            value = os.getenv(var)
            if value:
                masked_value = value[:5] + "***" if len(value) > 5 else "***"
                print_success(f"{var}: {masked_value}")
            else:
                print_error(f"{var}: NOT SET")
                all_ok = False
        
        return all_ok
        
    except Exception as e:
        print_error(f"Error reading .env file: {e}")
        return False


def check_database_connection():
    """Check database connection."""
    print_header("5. Database Connection")
    
    try:
        from database.connection import get_supabase_client
        
        client = get_supabase_client()
        
        # Try a simple query
        from database.queries import get_app_setting
        result = get_app_setting('timesheet_reminder_enabled', 'false')
        
        print_success("Database connection successful")
        print_info(f"Timesheet reminder setting: {result}")
        return True
        
    except Exception as e:
        print_error(f"Database connection failed: {str(e)}")
        return False


def check_scheduler_script():
    """Check scheduler script can be imported."""
    print_header("6. Scheduler Script")
    
    try:
        from services.automated_scheduler import ScheduledEmailService
        
        service = ScheduledEmailService()
        print_success("Scheduler service imported successfully")
        print_info(f"Service: {service.service_name}")
        return True
        
    except Exception as e:
        print_error(f"Failed to import scheduler: {str(e)}")
        return False


def check_log_directory():
    """Check log directory."""
    print_header("7. Log Directory")
    
    base_path = Path(__file__).parent.parent
    log_dir = base_path / 'logs' / 'scheduler'
    
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        print_success(f"Log directory ready: {log_dir}")
        
        # Check if writable
        test_file = log_dir / '.test'
        test_file.touch()
        test_file.unlink()
        
        print_success("Log directory is writable")
        return True
        
    except Exception as e:
        print_error(f"Log directory issue: {str(e)}")
        return False


def check_scheduler_tasks():
    """Check if scheduler tasks are registered."""
    print_header("8. Scheduled Tasks")
    
    system = sys.platform
    
    if system == 'win32':
        # Windows Task Scheduler
        try:
            result = subprocess.run(
                ['powershell', '-Command', 'Get-ScheduledTask | Where-Object {$_.TaskName -like "Timesheet-*"} | Select-Object -ExpandProperty TaskName'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            tasks = [t.strip() for t in result.stdout.strip().split('\n') if t.strip()]
            
            if tasks:
                print_success(f"Found {len(tasks)} scheduled task(s):")
                for task in tasks:
                    print_info(f"  - {task}")
                return len(tasks) == 3
            else:
                print_warning("No Timesheet scheduled tasks found")
                print_info("Run: scripts/setup_windows_scheduler.ps1")
                return False
                
        except Exception as e:
            print_warning(f"Could not check Windows tasks: {str(e)}")
            return False
    
    elif system in ['linux', 'darwin']:  # Linux or macOS
        try:
            result = subprocess.run(
                ['crontab', '-l'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            cron_lines = [l for l in result.stdout.split('\n') if 'TIMESHEET_AUTO_EMAILS' in l]
            
            if cron_lines:
                print_success(f"Found {len(cron_lines)} cron job(s):")
                for line in cron_lines:
                    print_info(f"  {line}")
                return len(cron_lines) >= 3
            else:
                print_warning("No cron jobs found")
                print_info("Run: bash scripts/setup_linux_scheduler.sh")
                return False
                
        except subprocess.CalledProcessError:
            print_warning("No crontab configured yet")
            return False
        except Exception as e:
            print_warning(f"Could not check cron jobs: {str(e)}")
            return False
    
    else:
        print_warning(f"Unknown system: {system}")
        return False


def test_scheduler_execution():
    """Test scheduler execution."""
    print_header("9. Scheduler Execution Test")
    
    try:
        from services.automated_scheduler import ScheduledEmailService
        
        service = ScheduledEmailService()
        
        print_info("Testing scheduler components...")
        
        # Test settings retrieval
        from database.queries import get_report_email_settings, get_app_setting
        
        report_settings = get_report_email_settings()
        print_success(f"Report settings retrieved: Enabled={report_settings.get('enabled')}")
        
        reminder_enabled = get_app_setting('timesheet_reminder_enabled', 'false')
        print_success(f"Reminder settings retrieved: Enabled={reminder_enabled}")
        
        print_success("Scheduler components tested successfully")
        return True
        
    except Exception as e:
        print_error(f"Scheduler test failed: {str(e)}")
        return False


def print_summary(results):
    """Print summary of all checks."""
    print_header("VERIFICATION SUMMARY")
    
    total = len(results)
    passed = sum(1 for v in results.values() if v)
    failed = total - passed
    
    print(f"Total Checks: {total}")
    print(f"{Colors.GREEN}✅ Passed: {passed}{Colors.END}")
    if failed > 0:
        print(f"{Colors.RED}❌ Failed: {failed}{Colors.END}")
    
    if failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ ALL CHECKS PASSED!{Colors.END}")
        print("\nYour scheduler is ready for deployment. Next steps:")
        print("1. Configure recipients in Streamlit UI (Settings → 📊 Send Report Settings)")
        print("2. Adjust schedule day/time if needed")
        print("3. Click 'Save Settings'")
        print("4. Wait for scheduled time or run manual test:")
        print("   python services/automated_scheduler.py weekly-report")
        return True
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ SOME CHECKS FAILED{Colors.END}")
        print("\nFix the issues above and run this script again.")
        return False


def main():
    """Run all verification checks."""
    print(f"\n{Colors.BOLD}Scheduler Setup Verification{Colors.END}")
    print(f"Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    results['Python Version'] = check_python_version()
    results['Required Packages'] = check_required_packages()
    results['Required Files'] = check_files_exist()
    results['Environment Config'] = check_environment_config()
    results['Database Connection'] = check_database_connection()
    results['Scheduler Script'] = check_scheduler_script()
    results['Log Directory'] = check_log_directory()
    results['Scheduled Tasks'] = check_scheduler_tasks()
    results['Scheduler Execution'] = test_scheduler_execution()
    
    success = print_summary(results)
    
    print(f"\nCompleted: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Verification interrupted by user{Colors.END}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n{Colors.RED}Unexpected error: {str(e)}{Colors.END}\n")
        sys.exit(1)

"""
Automated Scheduler Service
============================
Standalone scheduled tasks for sending emails without Streamlit dependency.
Can run as Windows Service, Cron job, or via Task Scheduler.

This module handles:
- Weekly report email delivery
- Timesheet reminder email delivery
- Automatic log cleanup
- Error handling and logging
"""
import logging
import sys
import os
import datetime
from pathlib import Path

# Configure logging
LOG_DIR = Path(__file__).parent.parent / 'logs' / 'scheduler'
LOG_DIR.mkdir(parents=True, exist_ok=True)

log_file = LOG_DIR / f'scheduler_{datetime.datetime.now().strftime("%Y%m%d")}.log'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class ScheduledEmailService:
    """Handles all automated email delivery tasks."""
    
    def __init__(self):
        """Initialize the service."""
        self.service_name = "Timesheet Automated Email Service"
        logger.info(f"Initializing {self.service_name}")
        
    def send_weekly_report_email(self):
        """
        Send weekly timesheet report emails using configured date range filter.
        
        Retrieves settings from database including date range filter and sends reports 
        to configured recipients with data matching the selected date range.
        Logs results and handles errors gracefully.
        
        Returns:
        --------
        dict : {
            'success': bool,
            'message': str,
            'recipients_count': int,
            'date_range': str,
            'timestamp': str
        }
        """
        task_name = "Weekly Report Email"
        logger.info(f"{'='*60}")
        logger.info(f"Starting: {task_name}")
        logger.info(f"{'='*60}")
        
        try:
            from database.queries import get_report_email_settings
            from services.report_email_service import generate_and_send_weekly_report
            
            # Fetch settings
            settings = get_report_email_settings()
            enabled = settings.get('enabled', False)
            recipients = settings.get('recipients', [])
            date_range_filter = settings.get('date_range_filter', 'last_week')
            custom_start = settings.get('custom_start_date', '')
            custom_end = settings.get('custom_end_date', '')
            
            if not enabled:
                msg = f"{task_name}: Disabled in settings - Skipping"
                logger.info(msg)
                return {
                    'success': True,
                    'message': msg,
                    'recipients_count': 0,
                    'date_range': 'N/A',
                    'timestamp': datetime.datetime.now().isoformat()
                }
            
            if not recipients:
                msg = f"{task_name}: No recipients configured - Skipping"
                logger.warning(msg)
                return {
                    'success': False,
                    'message': msg,
                    'recipients_count': 0,
                    'date_range': date_range_filter,
                    'timestamp': datetime.datetime.now().isoformat()
                }
            
            logger.info(f"Recipients: {', '.join(recipients)}")
            logger.info(f"Date Range Filter: {date_range_filter}")
            
            # Generate and send report with date range filter
            success, message = generate_and_send_weekly_report(
                recipients=recipients,
                trigger_type='scheduled',
                sent_by='system',
                date_range_filter=date_range_filter,
                custom_start_date=custom_start if custom_start else None,
                custom_end_date=custom_end if custom_end else None
            )
            
            if success:
                logger.info(f"✅ {task_name} SUCCESS: {message}")
            else:
                logger.error(f"❌ {task_name} FAILED: {message}")
            
            return {
                'success': success,
                'message': message,
                'recipients_count': len(recipients),
                'date_range': date_range_filter,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"❌ {task_name} EXCEPTION: {str(e)}"
            logger.exception(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'recipients_count': 0,
                'date_range': 'unknown',
                'timestamp': datetime.datetime.now().isoformat()
            }
        finally:
            logger.info(f"Completed: {task_name}\n")
    
    
    def send_timesheet_reminders(self):
        """
        Send timesheet reminder emails to employees with incomplete entries.
        
        Retrieves settings and identifies incomplete timesheets, then sends reminders.
        Logs results and handles errors gracefully.
        
        Returns:
        --------
        dict : {
            'success': bool,
            'message': str,
            'sent': int,
            'failed': int,
            'timestamp': str
        }
        """
        task_name = "Timesheet Reminder Emails"
        logger.info(f"{'='*60}")
        logger.info(f"Starting: {task_name}")
        logger.info(f"{'='*60}")
        
        try:
            from database.queries import get_app_setting
            from services.timesheet_reminder_service import process_timesheet_reminders
            
            # Check if enabled
            enabled_str = get_app_setting('timesheet_reminder_enabled', 'false')
            enabled = enabled_str.lower() == 'true'
            
            if not enabled:
                msg = f"{task_name}: Disabled in settings - Skipping"
                logger.info(msg)
                return {
                    'success': True,
                    'message': msg,
                    'sent': 0,
                    'failed': 0,
                    'timestamp': datetime.datetime.now().isoformat()
                }
            
            logger.info(f"{task_name}: Processing reminders...")
            
            # Process reminders
            result = process_timesheet_reminders(
                reminder_type="cron",
                force_resend=False
            )
            
            sent = result.get('sent', 0)
            failed = result.get('failed', 0)
            skipped = result.get('skipped', 0)
            total = result.get('total', 0)
            
            logger.info(f"✅ {task_name} COMPLETE:")
            logger.info(f"   - Sent: {sent}")
            logger.info(f"   - Failed: {failed}")
            logger.info(f"   - Skipped: {skipped}")
            logger.info(f"   - Total: {total}")
            
            success = failed == 0
            message = f"Sent: {sent}, Failed: {failed}, Skipped: {skipped}, Total: {total}"
            
            return {
                'success': success,
                'message': message,
                'sent': sent,
                'failed': failed,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"❌ {task_name} EXCEPTION: {str(e)}"
            logger.exception(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'sent': 0,
                'failed': 0,
                'timestamp': datetime.datetime.now().isoformat()
            }
        finally:
            logger.info(f"Completed: {task_name}\n")
    
    
    def cleanup_old_logs(self):
        """
        Clean up old timesheet reminder logs (retention: 4 weeks).
        
        Automatically removes logs older than configured retention period.
        Logs results and handles errors gracefully.
        
        Returns:
        --------
        dict : {
            'success': bool,
            'message': str,
            'deleted_count': int,
            'timestamp': str
        }
        """
        task_name = "Log Cleanup"
        logger.info(f"{'='*60}")
        logger.info(f"Starting: {task_name}")
        logger.info(f"{'='*60}")
        
        try:
            from database.queries import cleanup_old_reminder_logs
            
            logger.info(f"{task_name}: Removing logs older than 4 weeks...")
            
            count = cleanup_old_reminder_logs()
            
            logger.info(f"✅ {task_name} SUCCESS: Deleted {count} log records")
            
            return {
                'success': True,
                'message': f"Deleted {count} old log records",
                'deleted_count': count,
                'timestamp': datetime.datetime.now().isoformat()
            }
            
        except Exception as e:
            error_msg = f"❌ {task_name} EXCEPTION: {str(e)}"
            logger.exception(error_msg)
            return {
                'success': False,
                'message': error_msg,
                'deleted_count': 0,
                'timestamp': datetime.datetime.now().isoformat()
            }
        finally:
            logger.info(f"Completed: {task_name}\n")
    
    
    def run_all_tasks(self):
        """
        Run all scheduled tasks in sequence.
        
        Executes all email delivery and maintenance tasks.
        Suitable for comprehensive scheduled execution.
        
        Returns:
        --------
        dict : Summary of all task results
        """
        logger.info(f"\n{'#'*60}")
        logger.info(f"# {self.service_name}")
        logger.info(f"# Started: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"{'#'*60}\n")
        
        results = {
            'timestamp': datetime.datetime.now().isoformat(),
            'tasks': {}
        }
        
        # Run all tasks
        results['tasks']['weekly_report'] = self.send_weekly_report_email()
        results['tasks']['reminders'] = self.send_timesheet_reminders()
        results['tasks']['cleanup'] = self.cleanup_old_logs()
        
        # Summary
        logger.info(f"\n{'='*60}")
        logger.info(f"SUMMARY")
        logger.info(f"{'='*60}")
        for task_name, task_result in results['tasks'].items():
            status = "✅ SUCCESS" if task_result['success'] else "❌ FAILED"
            logger.info(f"{task_name.upper()}: {status}")
            logger.info(f"  Message: {task_result['message']}")
        
        logger.info(f"\nCompleted at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        return results


def main():
    """
    Main entry point for the scheduler service.
    
    Usage:
    ------
    python services/automated_scheduler.py [task]
    
    Tasks:
    ------
    - weekly-report  : Send weekly report emails
    - reminders      : Send timesheet reminder emails
    - cleanup        : Clean up old logs
    - all            : Run all tasks (default)
    
    Examples:
    ---------
    python services/automated_scheduler.py weekly-report
    python services/automated_scheduler.py reminders
    python services/automated_scheduler.py cleanup
    python services/automated_scheduler.py all
    python services/automated_scheduler.py  # Runs 'all' by default
    """
    try:
        service = ScheduledEmailService()
        
        # Get task from command line
        task = sys.argv[1].lower() if len(sys.argv) > 1 else 'all'
        
        if task == 'weekly-report':
            result = service.send_weekly_report_email()
        elif task == 'reminders':
            result = service.send_timesheet_reminders()
        elif task == 'cleanup':
            result = service.cleanup_old_logs()
        elif task == 'all':
            result = service.run_all_tasks()
        else:
            logger.error(f"Unknown task: {task}")
            logger.info("Valid tasks: weekly-report, reminders, cleanup, all")
            sys.exit(1)
        
        # Exit with appropriate code
        sys.exit(0 if result.get('success', False) or task == 'all' else 1)
        
    except Exception as e:
        logger.exception(f"Fatal error in main: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()

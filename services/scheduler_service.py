"""
Scheduler Service
==================
Manages the APScheduler BackgroundScheduler for automated timesheet reminders.
Runs in a background thread alongside the Streamlit server.

Provides functions to:
- Initialize the scheduler on app startup
- Update the reminder schedule when admin changes settings
- Safely prevent duplicate jobs
"""
import logging
import threading
import datetime

logger = logging.getLogger(__name__)

# Module-level singleton — shared across all Streamlit sessions
_scheduler = None
_lock = threading.Lock()

JOB_ID = "timesheet_reminder_cron"


def _get_scheduler():
    """Lazily create and start the BackgroundScheduler singleton."""
    global _scheduler
    if _scheduler is not None:
        return _scheduler

    with _lock:
        # Double-check after acquiring the lock
        if _scheduler is not None:
            return _scheduler

        from apscheduler.schedulers.background import BackgroundScheduler
        _scheduler = BackgroundScheduler(daemon=True)
        _scheduler.start()
        logger.info("APScheduler BackgroundScheduler started.")
    return _scheduler


def _reminder_job():
    """Callback executed by the scheduler at the configured time."""
    from database.queries import get_app_setting

    logger.info("Cron job triggered at %s", datetime.datetime.now().isoformat())

    # Double-check enabled flag (admin may have disabled between schedule creation)
    enabled = get_app_setting('timesheet_reminder_enabled', 'false')
    if enabled.lower() != 'true':
        logger.info("Timesheet reminder cron is disabled — skipping.")
        return

    from services.timesheet_reminder_service import process_timesheet_reminders
    result = process_timesheet_reminders(reminder_type="cron", force_resend=False)

    logger.info(
        "Cron reminder complete: %d sent, %d failed, %d skipped out of %d total.",
        result['sent'], result['failed'], result['skipped'], result['total']
    )


def _parse_time(time_str):
    """Parse a time string like '10:00' or '14:30' into (hour, minute)."""
    try:
        parts = time_str.strip().split(':')
        hour = int(parts[0])
        minute = int(parts[1]) if len(parts) > 1 else 0
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError(f"Invalid time: {time_str}")
        return hour, minute
    except (ValueError, IndexError) as e:
        logger.warning("Invalid reminder time '%s', defaulting to 10:00. Error: %s",
                        time_str, e)
        return 10, 0


def update_reminder_schedule(enabled, days_str, time_str):
    """Update (or remove) the scheduled reminder job.

    Called when admin saves reminder settings. Safe to call repeatedly —
    always removes the old job first to prevent duplicates.

    Parameters
    ----------
    enabled : bool
        Whether the cron should be active.
    days_str : str
        Comma-separated days of week, e.g. ``"mon,tue,wed"``.
    time_str : str
        Time in 24-hour format, e.g. ``"10:00"``.
    """
    scheduler = _get_scheduler()

    with _lock:
        # Always remove existing job first
        if scheduler.get_job(JOB_ID):
            scheduler.remove_job(JOB_ID)
            logger.info("Removed existing reminder job '%s'.", JOB_ID)

        if not enabled:
            logger.info("Timesheet reminder cron is disabled.")
            return

        hour, minute = _parse_time(time_str)

        from apscheduler.triggers.cron import CronTrigger
        trigger = CronTrigger(day_of_week=days_str, hour=hour, minute=minute)

        scheduler.add_job(
            _reminder_job,
            trigger=trigger,
            id=JOB_ID,
            name="Timesheet Reminder",
            replace_existing=True,
        )
        logger.info("Scheduled timesheet reminder: days=%s at %02d:%02d.",
                     days_str, hour, minute)


def initialize_scheduler():
    """Read settings from DB and set up the initial schedule.

    Called once on app startup. Safe if called multiple times.
    """
    from database.queries import get_app_setting

    enabled_str = get_app_setting('timesheet_reminder_enabled', 'false')
    days_str = get_app_setting('timesheet_reminder_days', 'thu')
    time_str = get_app_setting('timesheet_reminder_time', '10:00')

    enabled = enabled_str.lower() == 'true'
    update_reminder_schedule(enabled, days_str, time_str)
    logger.info("Scheduler initialized. Enabled=%s, Days=%s, Time=%s", enabled, days_str, time_str)


def get_next_run_time():
    """Return the next scheduled run time as a datetime, or None if not scheduled."""
    scheduler = _get_scheduler()
    job = scheduler.get_job(JOB_ID)
    if job and job.next_run_time:
        return job.next_run_time
    return None


def is_job_scheduled():
    """Return True if the reminder job is currently scheduled."""
    scheduler = _get_scheduler()
    return scheduler.get_job(JOB_ID) is not None

import unittest
from unittest.mock import patch, MagicMock
import datetime

# Mock Streamlit to avoid issues when importing modules that use st.secrets
import sys
mock_st = MagicMock()
mock_st.secrets = {
    "SMTP_HOST": "test.com",
    "SMTP_PORT": "587",
    "SMTP_USER": "test@test.com",
    "SMTP_PASS": "pass",
    "SMTP_ENCRYPTION": "tls"
}
sys.modules['streamlit'] = mock_st

from services.timesheet_reminder_service import (
    get_current_week_range,
    get_applicable_days,
    get_employees_with_missing_timesheets,
    process_timesheet_reminders
)

class TestTimesheetReminderService(unittest.TestCase):

    def test_get_current_week_range(self):
        # A Tuesday
        ref_date = datetime.date(2023, 10, 17)
        monday, friday = get_current_week_range(ref_date)
        self.assertEqual(monday, datetime.date(2023, 10, 16))
        self.assertEqual(friday, datetime.date(2023, 10, 20))

    def test_get_applicable_days_on_thursday(self):
        # A Thursday — get_applicable_days always returns the full Mon-Fri week (5 days).
        ref_date = datetime.date(2023, 10, 19)
        days = get_applicable_days(ref_date)
        self.assertEqual(len(days), 5)  # Mon, Tue, Wed, Thu, Fri
        self.assertIn(datetime.date(2023, 10, 20), days)   # Friday IS included
        self.assertIn(datetime.date(2023, 10, 16), days)   # Monday is included

    def test_get_applicable_days_on_friday(self):
        # A Friday
        ref_date = datetime.date(2023, 10, 20)
        days = get_applicable_days(ref_date)
        self.assertEqual(len(days), 5) # Mon, Tue, Wed, Thu, Fri

    def test_get_applicable_days_on_weekend(self):
        # A Sunday
        ref_date = datetime.date(2023, 10, 22)
        days = get_applicable_days(ref_date)
        # Should be max 5 days (Mon-Fri)
        self.assertEqual(len(days), 5)

    @patch('database.queries.get_active_employees_with_email')
    @patch('database.queries.get_timesheet_dates_for_employee')
    def test_get_employees_with_missing_timesheets(self, mock_get_dates, mock_get_emps):
        mock_get_emps.return_value = [
            {'employee_id': '1', 'employee_name': 'Alice', 'email': 'alice@test.com'},
            {'employee_id': '2', 'employee_name': 'Bob', 'email': 'bob@test.com'}
        ]

        # Thursday — get_applicable_days returns all 5 days of the week (Mon-Fri)
        ref_date = datetime.date(2023, 10, 19)
        all_five_days = [
            datetime.date(2023, 10, 16),  # Mon
            datetime.date(2023, 10, 17),  # Tue
            datetime.date(2023, 10, 18),  # Wed
            datetime.date(2023, 10, 19),  # Thu
            datetime.date(2023, 10, 20),  # Fri
        ]

        # Alice has filled ALL 5 days → no missing entries
        # Bob filled only Mon/Tue → missing Wed, Thu, Fri
        def side_effect(emp_id, start, end):
            if emp_id == '1':
                return set(all_five_days)
            elif emp_id == '2':
                return {datetime.date(2023, 10, 16), datetime.date(2023, 10, 17)}
            return set()

        mock_get_dates.side_effect = side_effect

        missing = get_employees_with_missing_timesheets(ref_date)

        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]['employee_id'], '2')
        self.assertEqual(len(missing[0]['missing_days']), 3)  # Wed, Thu, Fri
        self.assertIn(datetime.date(2023, 10, 18), missing[0]['missing_days'])  # Wed
        self.assertIn(datetime.date(2023, 10, 19), missing[0]['missing_days'])  # Thu
        self.assertIn(datetime.date(2023, 10, 20), missing[0]['missing_days'])  # Fri

    @patch('services.timesheet_reminder_service.get_employees_with_missing_timesheets')
    @patch('database.queries.check_ts_reminder_exists')
    @patch('database.queries.create_ts_reminder_log')
    @patch('services.timesheet_reminder_service.send_single_reminder_email')
    @patch('database.queries.update_ts_reminder_log')
    @patch('services.timesheet_reminder_service._get_smtp_config')
    def test_process_timesheet_reminders(
        self, mock_get_smtp, mock_update_log, mock_send_email,
        mock_create_log, mock_check_exists, mock_get_missing
    ):
        mock_get_smtp.return_value = ('host', 587, 'user', 'pass', 'tls')
        mock_get_missing.return_value = [
            {'employee_id': '1', 'employee_name': 'Alice', 'email': 'a@test.com', 'missing_days': []},
            {'employee_id': '2', 'employee_name': 'Bob', 'email': 'b@test.com', 'missing_days': []}
        ]
        
        # Alice already had a reminder, Bob didn't
        mock_check_exists.side_effect = lambda emp_id, week_start: emp_id == '1'
        mock_create_log.return_value = 123
        mock_send_email.return_value = (True, None) # Success
        
        ref_date = datetime.date(2023, 10, 19)
        result = process_timesheet_reminders("cron", force_resend=False, reference_date=ref_date)
        
        self.assertEqual(result['total'], 2)
        self.assertEqual(result['skipped'], 1) # Alice
        self.assertEqual(result['sent'], 1)    # Bob
        self.assertEqual(result['failed'], 0)
        
        # Verify Bob got the email
        mock_send_email.assert_called_once()
        args, _ = mock_send_email.call_args
        self.assertEqual(args[0]['employee_id'], '2')


# ===========================================================================
# Cleanup Job Tests
# ===========================================================================

class TestCleanupJob(unittest.TestCase):
    """Tests for the automatic timesheet reminder log cleanup feature."""

    # ------------------------------------------------------------------
    # 1. database.queries.cleanup_old_reminder_logs
    # ------------------------------------------------------------------

    @patch('database.queries.get_supabase_client')
    def test_cleanup_uses_28_day_cutoff(self, mock_get_client):
        """cleanup_old_reminder_logs must delete on 'created_at' with a cutoff ~28 days ago.

        Because datetime is imported *inside* the function we cannot patch it at
        module level.  Instead we capture the actual cutoff string passed to .lt()
        and assert that it is between 27 and 29 days in the past.
        """
        from database.queries import cleanup_old_reminder_logs

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.delete.return_value.lt.return_value.execute.return_value.data = []

        before_call = datetime.datetime.now()
        cleanup_old_reminder_logs()
        after_call = datetime.datetime.now()

        lt_args = mock_client.table.return_value.delete.return_value.lt.call_args
        self.assertIsNotNone(lt_args, ".lt() was not called")

        # First positional arg must be the column name
        self.assertEqual(lt_args[0][0], 'created_at')

        # Second positional arg is the ISO-format cutoff string
        cutoff_str = lt_args[0][1]
        cutoff_dt = datetime.datetime.fromisoformat(cutoff_str)

        # Verify the cutoff is within [27, 29] days before the call
        low  = before_call - datetime.timedelta(days=29)
        high = after_call  - datetime.timedelta(days=27)
        self.assertGreaterEqual(cutoff_dt, low,  f"Cutoff {cutoff_dt} is more than 29 days ago")
        self.assertLessEqual   (cutoff_dt, high, f"Cutoff {cutoff_dt} is less than 27 days ago")

    @patch('database.queries.get_supabase_client')
    def test_cleanup_retains_recent_logs(self, mock_get_client):
        """The delete filter must NOT match records newer than 28 days."""
        from database.queries import cleanup_old_reminder_logs

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_execute = MagicMock()
        mock_execute.return_value.data = []
        mock_client.table.return_value.delete.return_value.lt.return_value.execute = mock_execute

        cleanup_old_reminder_logs()

        # Verify `lt` was used (less-than), not `lte` or `gt`
        self.assertTrue(mock_client.table.return_value.delete.return_value.lt.called)
        # Verify `gt` (greater-than) was NOT called — no recent records should be touched
        self.assertFalse(mock_client.table.return_value.delete.return_value.gt.called)

    @patch('database.queries.get_supabase_client')
    def test_cleanup_returns_count_of_deleted_records(self, mock_get_client):
        """cleanup_old_reminder_logs must return the exact number of deleted rows."""
        from database.queries import cleanup_old_reminder_logs

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        # Simulate Supabase returning 3 deleted rows
        mock_client.table.return_value.delete.return_value.lt.return_value.execute.return_value.data = [
            {'id': 1}, {'id': 2}, {'id': 3}
        ]

        count = cleanup_old_reminder_logs()
        self.assertEqual(count, 3)

    @patch('database.queries.get_supabase_client')
    def test_cleanup_is_idempotent(self, mock_get_client):
        """Calling cleanup twice with no new old logs must return 0 on the second call."""
        from database.queries import cleanup_old_reminder_logs

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # First call: 2 rows deleted
        first_execute = MagicMock(return_value=MagicMock(data=[{'id': 10}, {'id': 11}]))
        # Second call: nothing to delete
        second_execute = MagicMock(return_value=MagicMock(data=[]))

        mock_client.table.return_value.delete.return_value.lt.return_value.execute = first_execute
        first_count = cleanup_old_reminder_logs()

        mock_client.table.return_value.delete.return_value.lt.return_value.execute = second_execute
        second_count = cleanup_old_reminder_logs()

        self.assertEqual(first_count, 2)
        self.assertEqual(second_count, 0)

    @patch('database.queries.get_supabase_client')
    def test_cleanup_returns_zero_on_error(self, mock_get_client):
        """cleanup_old_reminder_logs must return 0 (not raise) on database error."""
        from database.queries import cleanup_old_reminder_logs

        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        mock_client.table.return_value.delete.return_value.lt.return_value.execute.side_effect = Exception("DB error")

        count = cleanup_old_reminder_logs()
        self.assertEqual(count, 0)

    # ------------------------------------------------------------------
    # 2. services.scheduler_service — cleanup job registration
    # ------------------------------------------------------------------

    def test_cleanup_job_is_registered_after_initialize(self):
        """After initialize_scheduler(), CLEANUP_JOB_ID must exist in the scheduler."""
        from services import scheduler_service

        mock_scheduler = MagicMock()
        mock_scheduler.get_job.return_value = None  # No existing job

        with patch('services.scheduler_service._get_scheduler', return_value=mock_scheduler), \
             patch('services.scheduler_service.update_reminder_schedule'), \
             patch('database.queries.get_app_setting', return_value='false'):
            scheduler_service.initialize_scheduler()

        # add_job must have been called at least once for the cleanup job
        calls = [str(c) for c in mock_scheduler.add_job.call_args_list]
        cleanup_registered = any(scheduler_service.CLEANUP_JOB_ID in c for c in calls)
        self.assertTrue(cleanup_registered,
                        "CLEANUP_JOB_ID was not found in scheduler.add_job calls")

    def test_cleanup_job_uses_28_day_interval(self):
        """_schedule_cleanup_job must create an IntervalTrigger with days=28."""
        from services import scheduler_service
        from apscheduler.triggers.interval import IntervalTrigger

        mock_scheduler = MagicMock()
        mock_scheduler.get_job.return_value = None

        captured_trigger = {}

        def capture_add_job(fn, trigger, **kwargs):
            if kwargs.get('id') == scheduler_service.CLEANUP_JOB_ID:
                captured_trigger['trigger'] = trigger

        mock_scheduler.add_job.side_effect = capture_add_job

        with patch('services.scheduler_service._lock'):
            scheduler_service._schedule_cleanup_job(mock_scheduler)

        trigger = captured_trigger.get('trigger')
        self.assertIsNotNone(trigger, "_schedule_cleanup_job did not register a trigger")
        self.assertIsInstance(trigger, IntervalTrigger)
        # IntervalTrigger stores interval as a timedelta
        self.assertEqual(trigger.interval.days, scheduler_service._CLEANUP_INTERVAL_DAYS)

    def test_cleanup_job_starts_at_nighttime_hour(self):
        """_schedule_cleanup_job start_date hour must equal _CLEANUP_HOUR (02:00)."""
        from services import scheduler_service
        from apscheduler.triggers.interval import IntervalTrigger

        mock_scheduler = MagicMock()
        mock_scheduler.get_job.return_value = None

        captured_trigger = {}

        def capture_add_job(fn, trigger, **kwargs):
            if kwargs.get('id') == scheduler_service.CLEANUP_JOB_ID:
                captured_trigger['trigger'] = trigger

        mock_scheduler.add_job.side_effect = capture_add_job

        with patch('services.scheduler_service._lock'):
            scheduler_service._schedule_cleanup_job(mock_scheduler)

        trigger = captured_trigger.get('trigger')
        self.assertIsNotNone(trigger)
        # start_date is an aware or naive datetime; check its hour
        self.assertEqual(trigger.start_date.hour, scheduler_service._CLEANUP_HOUR)

    # ------------------------------------------------------------------
    # 3. UI — settings_page.py
    # ------------------------------------------------------------------

    def test_ui_displays_cleanup_info_box(self):
        """The settings page source must contain the automatic cleanup notice text.

        We inspect the source rather than executing render_settings_page() because
        executing it requires a full Streamlit session context that is unavailable
        in unit tests.  Source inspection is reliable and sufficient to confirm the
        notice text is present.
        """
        import inspect
        from pages import settings_page

        source = inspect.getsource(settings_page)

        self.assertIn('Automatic Log Cleanup', source,
                      "'Automatic Log Cleanup' heading not found in settings_page source")
        self.assertIn('4 weeks', source,
                      "'4 weeks' retention text not found in settings_page source")
        self.assertIn('02:00', source,
                      "Nighttime hour '02:00' not found in settings_page source")
        self.assertIn('st.info', source,
                      "st.info() call not found — notice must be rendered as an info box")

    def test_ui_has_no_cleanup_controls(self):
        """The settings page source must not contain cleanup-related input controls."""
        import inspect
        from pages import settings_page

        source = inspect.getsource(settings_page)

        # These widget names would indicate configurable controls were added — they must NOT appear
        # in the context of cleanup settings
        forbidden_patterns = [
            'cleanup_retention',
            'cleanup_interval',
            'cleanup_enabled',
            'cleanup_days_input',
        ]
        for pat in forbidden_patterns:
            self.assertNotIn(pat, source,
                             f"Found forbidden configurable cleanup widget key: '{pat}'")


if __name__ == '__main__':
    unittest.main()

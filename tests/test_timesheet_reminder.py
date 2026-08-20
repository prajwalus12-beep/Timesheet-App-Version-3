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
        # A Thursday
        ref_date = datetime.date(2023, 10, 19)
        days = get_applicable_days(ref_date)
        self.assertEqual(len(days), 4) # Mon, Tue, Wed, Thu
        self.assertNotIn(datetime.date(2023, 10, 20), days) # Friday should not be included

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
        
        # Thursday
        ref_date = datetime.date(2023, 10, 19)
        applicable_days = [
            datetime.date(2023, 10, 16),
            datetime.date(2023, 10, 17),
            datetime.date(2023, 10, 18),
            datetime.date(2023, 10, 19)
        ]
        
        # Alice has filled all days
        # Bob missed Wednesday and Thursday
        def side_effect(emp_id, start, end):
            if emp_id == '1':
                return applicable_days
            elif emp_id == '2':
                return [datetime.date(2023, 10, 16), datetime.date(2023, 10, 17)]
            return []
            
        mock_get_dates.side_effect = side_effect
        
        missing = get_employees_with_missing_timesheets(ref_date)
        
        self.assertEqual(len(missing), 1)
        self.assertEqual(missing[0]['employee_id'], '2')
        self.assertEqual(len(missing[0]['missing_days']), 2)
        self.assertIn(datetime.date(2023, 10, 18), missing[0]['missing_days'])

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

if __name__ == '__main__':
    unittest.main()

"""
tests/test_holiday_management.py
================================
Unit and regression tests for the Holiday Management feature:
  - Holiday CRUD operations & duplicate validations
  - Batch import parsing, validation, and error reporting
  - Dynamic timesheet synthesis with holiday entries
  - Employee holiday self-service exclusion
  - Export filtering (excluding HOLIDAY entries)
  - Timesheet reminder service holiday exclusion
"""

import unittest
from unittest.mock import MagicMock, patch
import datetime
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database.queries import (
    add_holiday, update_holiday, delete_holiday, get_all_holidays,
    import_holidays, exclude_holiday_for_employee, get_employee_holiday_exclusions,
    has_active_holiday_for_date, get_timesheets, add_timesheet_entry
)
from services.timesheet_reminder_service import get_applicable_days


class TestHolidayCRUD(unittest.TestCase):
    """Test holiday creation, update, deletion, and constraints."""

    @patch('database.queries.get_supabase_client')
    def test_add_holiday_success(self, mock_get_client):
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase
        # No existing duplicate
        mock_supabase.table().select().eq().is_().execute.return_value.data = []

        ok, msg = add_holiday("2026-10-02", "Gandhi Jayanti", created_by="admin")
        self.assertTrue(ok)
        self.assertIn("successfully", msg.lower())
        mock_supabase.table('holidays').insert.assert_called()

    @patch('database.queries.get_supabase_client')
    def test_add_holiday_duplicate_date_rejected(self, mock_get_client):
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase
        # Existing holiday on that date
        mock_supabase.table().select().eq().is_().execute.return_value.data = [
            {"id": 1, "holiday_name": "Gandhi Jayanti"}
        ]

        ok, msg = add_holiday("2026-10-02", "New Holiday", created_by="admin")
        self.assertFalse(ok)
        self.assertIn("already exists", msg)

    def test_add_holiday_validation_empty_fields(self):
        ok, msg = add_holiday("", "Some Name")
        self.assertFalse(ok)
        self.assertIn("date is required", msg.lower())

        ok, msg = add_holiday("2026-10-02", "   ")
        self.assertFalse(ok)
        self.assertIn("name is required", msg.lower())

    @patch('database.queries.get_supabase_client')
    def test_update_holiday_success(self, mock_get_client):
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase
        mock_supabase.table().select().eq().neq().is_().execute.return_value.data = []

        ok, msg = update_holiday(1, "2026-10-02", "Gandhi Jayanti Updated", updated_by="admin")
        self.assertTrue(ok)
        mock_supabase.table('holidays').update.assert_called()

    @patch('database.queries.get_supabase_client')
    def test_delete_holiday_soft_delete(self, mock_get_client):
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase

        ok, msg = delete_holiday(1, soft_delete=True, updated_by="admin")
        self.assertTrue(ok)
        # Should update is_active=False and deleted_at
        mock_supabase.table('holidays').update.assert_called()


class TestHolidayImport(unittest.TestCase):
    """Test import parsing, validation, and batch insertion."""

    @patch('database.queries.get_supabase_client')
    def test_import_holidays_success(self, mock_get_client):
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase
        mock_supabase.table().select().in_().is_().execute.return_value.data = []

        df = pd.DataFrame([
            ["2026-10-02", "Gandhi Jayanti"],
            ["2026-12-25", "Christmas"]
        ], columns=['date', 'holiday name'])

        ok, msg, details = import_holidays(df, created_by="admin")
        self.assertTrue(ok)
        self.assertEqual(details.get("imported_count"), 2)

    def test_import_holidays_missing_column(self):
        df = pd.DataFrame([["2026-10-02"]], columns=['date'])
        ok, msg, _ = import_holidays(df, created_by="admin")
        self.assertFalse(ok)
        self.assertIn("Missing required column", msg)

    def test_import_holidays_invalid_date(self):
        df = pd.DataFrame([
            ["not-a-date", "Holiday Name"]
        ], columns=['date', 'holiday name'])

        ok, msg, details = import_holidays(df, created_by="admin")
        self.assertFalse(ok)
        self.assertIn("Validation failed", msg)
        self.assertTrue(any("Invalid or missing date" in err for err in details.get("errors", [])))

    def test_import_holidays_duplicate_in_file(self):
        df = pd.DataFrame([
            ["2026-10-02", "Holiday One"],
            ["2026-10-02", "Holiday Two"]
        ], columns=['date', 'holiday name'])

        ok, msg, details = import_holidays(df, created_by="admin")
        self.assertFalse(ok)
        self.assertTrue(any("Duplicate date" in err for err in details.get("errors", [])))


class TestTimesheetIntegrationAndExclusion(unittest.TestCase):
    """Test dynamic holiday synthesis and employee exclusion."""

    @patch('database.queries.get_employee_by_id')
    @patch('database.queries.get_supabase_client')
    def test_get_timesheets_dynamic_holiday_merge(self, mock_get_client, mock_get_emp):
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase
        mock_get_emp.return_value = {'employee_id': '101', 'employee_name': 'John Doe'}

        # Return empty normal timesheet entries
        mock_timesheet_table = MagicMock()
        mock_timesheet_table.select.return_value.gte.return_value.lte.return_value.eq.return_value.order.return_value.execute.return_value.data = []
        
        # Return 1 active holiday in range
        mock_holiday_table = MagicMock()
        mock_holiday_table.select.return_value.is_.return_value.gte.return_value.lte.return_value.execute.return_value.data = [
            {'id': 10, 'holiday_date': '2026-10-02', 'holiday_name': 'Gandhi Jayanti'}
        ]
        
        # Return 0 exclusions
        mock_ex_table = MagicMock()
        mock_ex_table.select.return_value.in_.return_value.execute.return_value.data = []

        def table_side_effect(table_name):
            if table_name == 'timesheet':
                return mock_timesheet_table
            elif table_name == 'holidays':
                return mock_holiday_table
            elif table_name == 'employee_holiday_exclusions':
                return mock_ex_table
            return MagicMock()

        mock_supabase.table.side_effect = table_side_effect

        df = get_timesheets(
            start_date=datetime.date(2026, 10, 1),
            end_date=datetime.date(2026, 10, 7),
            emp_id='101'
        )

        self.assertFalse(df.empty)
        holiday_rows = df[df['project_code'] == 'HOLIDAY-10']
        self.assertEqual(len(holiday_rows), 1)
        self.assertEqual(holiday_rows.iloc[0]['project_name'], 'Gandhi Jayanti')
        self.assertEqual(holiday_rows.iloc[0]['hours'], 8.0)

    @patch('database.queries.get_employee_by_id')
    @patch('database.queries.get_supabase_client')
    def test_employee_exclusion_hides_holiday(self, mock_get_client, mock_get_emp):
        mock_supabase = MagicMock()
        mock_get_client.return_value = mock_supabase
        mock_get_emp.return_value = {'employee_id': '101', 'employee_name': 'John Doe'}

        mock_timesheet_table = MagicMock()
        mock_timesheet_table.select.return_value.gte.return_value.lte.return_value.eq.return_value.order.return_value.execute.return_value.data = []
        
        mock_holiday_table = MagicMock()
        mock_holiday_table.select.return_value.is_.return_value.gte.return_value.lte.return_value.execute.return_value.data = [
            {'id': 10, 'holiday_date': '2026-10-02', 'holiday_name': 'Gandhi Jayanti'}
        ]
        
        # Employee 101 excluded holiday 10!
        mock_ex_table = MagicMock()
        mock_ex_table.select.return_value.in_.return_value.execute.return_value.data = [
            {'employee_id': '101', 'holiday_id': 10}
        ]

        def table_side_effect(table_name):
            if table_name == 'timesheet':
                return mock_timesheet_table
            elif table_name == 'holidays':
                return mock_holiday_table
            elif table_name == 'employee_holiday_exclusions':
                return mock_ex_table
            return MagicMock()

        mock_supabase.table.side_effect = table_side_effect

        df = get_timesheets(
            start_date=datetime.date(2026, 10, 1),
            end_date=datetime.date(2026, 10, 7),
            emp_id='101'
        )

        # Excluded holiday must not appear
        self.assertTrue(df.empty)

    @patch('database.queries.is_employee_active', return_value=True)
    @patch('database.queries.has_leave_for_date', return_value=False)
    @patch('database.queries.has_active_holiday_for_date')
    def test_add_timesheet_entry_blocked_by_active_holiday(self, mock_has_holiday, mock_has_leave, mock_active):
        mock_has_holiday.return_value = (True, {'holiday_name': 'Gandhi Jayanti'})

        ok, msg = add_timesheet_entry(
            emp_id='101',
            emp_name='John Doe',
            project_code='P101',
            project_name='Design Work',
            date=datetime.date(2026, 10, 2),
            hours=8.0,
            phase='Development'
        )
        self.assertFalse(ok)
        self.assertIn("configured as a Holiday", msg)
        self.assertIn("remove the holiday entry from your timesheet first", msg)


class TestExportAndReminderFiltering(unittest.TestCase):
    """Test export exclusion and reminder service integration."""

    def test_export_dataframe_excludes_holiday(self):
        # Sample dataset containing regular, leave, and holiday records
        data = pd.DataFrame([
            {'project_code': 'P101', 'emp_id': '101', 'emp_name': 'John', 'project_name': 'Project A', 'date': '2026-10-01', 'hours': 8.0, 'Phase': '1', 'project_status': 'In progress', 'comment': ''},
            {'project_code': 'LEAVE-CL', 'emp_id': '101', 'emp_name': 'John', 'project_name': 'Leave', 'date': '2026-10-03', 'hours': 8.0, 'Phase': '1', 'project_status': 'Approved', 'comment': ''},
            {'project_code': 'HOLIDAY-10', 'emp_id': '101', 'emp_name': 'John', 'project_name': 'Gandhi Jayanti', 'date': '2026-10-02', 'hours': 8.0, 'Phase': 'Holiday', 'project_status': 'Holiday', 'comment': ''},
        ])

        # Test filter logic used in timesheet_page and reports_page
        export_df = data[~data['project_code'].astype(str).str.startswith(('LEAVE-', 'HOLIDAY'))].copy()

        self.assertEqual(len(export_df), 1)
        self.assertEqual(export_df.iloc[0]['project_code'], 'P101')

    @patch('database.queries.get_all_holidays')
    def test_reminder_service_excludes_holidays(self, mock_get_holidays):
        # Reference date: Monday 2026-09-28 to Friday 2026-10-02
        ref_date = datetime.date(2026, 9, 30) # Wednesday
        # Holiday on Friday 2026-10-02
        mock_get_holidays.return_value = pd.DataFrame([
            {'holiday_date': '2026-10-02', 'holiday_name': 'Gandhi Jayanti'}
        ])

        days = get_applicable_days(ref_date)
        # Mon-Fri is 5 days, minus 1 holiday = 4 applicable working days
        self.assertEqual(len(days), 4)
        self.assertNotIn(datetime.date(2026, 10, 2), days)


if __name__ == '__main__':
    unittest.main()

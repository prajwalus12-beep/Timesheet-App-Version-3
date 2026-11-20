# Admin Guide 5 — Timesheet Administration

> [!IMPORTANT]
> Admins have **unrestricted access** to view and manage timesheets for **all employees**, with no weekly lock restrictions.

---

## Overview

The Timesheet Administration module allows admins to:
- View all employees' timesheets in one place
- Filter by employee, project, and date range
- Add timesheet entries on behalf of any employee
- Edit or delete any timesheet entry
- Export timesheet data to Excel
- Send manual reminders to employees

**Navigation:** Sidebar → 🗒️ **Timesheet**

---

## 1. Viewing Timesheets

### Default View

On opening the Timesheet module, all entries for the **current 4-week cycle** are shown by default.

### Date Range Presets

Use the **Date Range** selector to quickly jump to a predefined period:

| Preset | Period Covered |
|--------|---------------|
| This Week | Current Mon–Sun |
| Last Week | Previous Mon–Sun |
| Current 4-Week Cycle | Current 4-week billing period |
| Previous 4-Week Cycle | Last 4-week billing period |
| Custom Range | Pick any start and end date |

### Filtering

| Filter | Description |
|--------|-------------|
| Employee | Select one or more employees to show only their entries |
| Project | Filter by project code or project name |

### Sorting

Entries are sorted by:
1. **Date** (primary — ascending)
2. **Project Code** (secondary)
3. **Project Name** (tertiary)

Columns are sortable by clicking the column header.

---

## 2. Timesheet Table Columns

| Column | Description |
|--------|-------------|
| Date | Date of the timesheet entry |
| Employee | Employee name |
| Project Code | Project identifier |
| Project Name | Full project name |
| Activity | Task or activity category |
| Hours | Hours logged (decimal, e.g., `7.5`) |
| Description | Notes or comments for the entry |
| Actions | Edit / Delete buttons |

---

## 3. Adding a Timesheet Entry (For Any Employee)

As an admin, you can add timesheet entries on behalf of any employee.

### How to Add

1. Click the **"+ Add Entry"** button.
2. A dialog box opens.
3. Fill in the fields:

| Field | Required | Description | Validation |
|-------|----------|-------------|------------|
| Employee | ✅ Yes | Select the employee | Must select from dropdown |
| Project | ✅ Yes | Select the project | Search by code or name; select from results |
| Activity | ✅ Yes | Task or activity type | Select from dropdown |
| Date | ✅ Yes | Date of work | Cannot be in future; must be within allowed range |
| Hours | ✅ Yes | Hours worked | Must be between 0.5 and 24 |
| Description | No | Notes about the work | Free text |

4. Click **Save**.

### Success Toast
> ✅ "Timesheet entry added successfully."

---

## 4. Editing a Timesheet Entry

### How to Edit

1. Find the entry in the table.
2. Click the **Edit** button (pencil icon) in the Actions column.
3. The edit dialog opens pre-filled.
4. Make changes.
5. Click **Save**.

> [!NOTE]
> Admins can edit entries from **any week** — including past weeks — without restriction. The weekly lock that applies to employees does **not** apply to admins.

---

## 5. Deleting a Timesheet Entry

1. Find the entry.
2. Click the **Delete** button (trash icon) in the Actions column.
3. Confirm deletion.

> [!CAUTION]
> Deleted timesheet entries are **permanently removed**. This affects employee hour totals and reports. Use with caution.

---

## 6. Adding Leave Entries

Admins can add leave entries for any employee.

### How to Add Leave

1. Click the **"⛱️ Add Leave"** button.
2. A dialog opens.
3. Fill in:

| Field | Required | Description |
|-------|----------|-------------|
| Employee | ✅ Yes | Select the employee |
| Leave Type | ✅ Yes | Annual / Sick / Unpaid / Other / Holiday |
| Start Date | ✅ Yes | First day of leave |
| End Date | ✅ Yes | Last day of leave (must be ≥ Start Date) |
| Reason | ✅ Yes | Reason for the leave |

4. Click **Save**.

> [!NOTE]
> Leave entries are **excluded** from billable reports and timesheet reminder emails automatically.

---

## 7. Exporting Timesheets to Excel

1. Apply desired filters (employee, project, date range).
2. Click the **"Export to Excel"** button.
3. An `.xlsx` file downloads with the filtered data.

The export includes all visible columns in the current filtered view.

---

## 8. Sending Timesheet Reminders

1. Click the **"Send Reminder"** button.
2. A reminder email is sent to employees who have missing timesheet entries.

### Force Resend Option

Check the **"Force Resend"** checkbox before clicking Send Reminder to send reminders even to employees who have already received one for the current cycle.

> [!NOTE]
> Reminder settings (recipients, schedule, SMTP) are configured in [Settings → Reminder Settings](./08-system-settings.md).

---

## 9. Timesheet Week Boundaries

Timesheets follow a **Monday–Sunday** week structure.

- Week 1: Mon to Sun
- Entries are grouped visually by week in reports
- The 4-week cycle aligns with the company billing calendar

---

## 10. Common Admin Timesheet Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "Hours must be between 0.5 and 24" | Invalid hours entered | Enter a value between 0.5 and 24 |
| "Date cannot be in the future" | Future date selected | Select today or a past date |
| "Project not found" | Invalid project code/name | Search and select from the dropdown |
| "Activity is required" | No activity selected | Select an activity from the dropdown |

# Admin Guide 8 — System Settings

> [!IMPORTANT]
> This module is accessible to **Admins only**.

---

## Overview

The Settings module contains 5 configuration tabs that control system-wide behavior including lockout schedules, employee permissions, reminders, automated reports, and holiday management.

**Navigation:** Sidebar → ⚙️ **Settings**

---

## Tab 1: Lockout Schedule

### What It Does

Controls which days of the week employees are **allowed** or **blocked** from submitting timesheet entries.

### Configuration

The schedule shows 7 toggles — one for each day of the week (Monday through Sunday).

| Toggle State | Meaning |
|-------------|---------|
| **OPEN** | Employees can submit timesheets on this day |
| **BLOCKED** | Employees cannot submit timesheets on this day |

### How to Change

1. Go to **Settings → Lockout Schedule** tab.
2. Click the toggle for the day you want to change.
3. The change takes effect immediately.

> [!WARNING]
> When a day is set to **BLOCKED**, employees who attempt to log timesheets on that day will see a lockout message and cannot save entries. Admins are **not affected** by the lockout schedule.

> [!NOTE]
> This lockout is about **submission days**, not the timesheet dates themselves. For example, blocking Sunday means employees cannot submit timesheets on Sunday, but they can still log hours for Sunday on other days.

---

## Tab 2: Employee Permissions

### What It Does

Controls which employees have access to restricted modules beyond the default employee view.

### Available Permissions

| Permission Flag | Module Unlocked |
|----------------|-----------------|
| `project_update_access` | Project Updates V2 — employee can **edit** the grid (otherwise view-only) |
| `allow_add_project` | Add Project Portal — employee can access and create staged projects |

### How to Toggle Permissions

1. Go to **Settings → Employee Permissions** tab.
2. Find the employee in the list.
3. Toggle the desired permission on or off.
4. Changes take effect immediately.

> [!NOTE]
> The **Lockout Schedule takes precedence** over individual permissions. Even if an employee has `project_update_access`, they cannot submit anything during a lockout period.

---

## Tab 3: Timesheet Reminder Settings

### What It Does

Configures automatic timesheet reminder emails sent to employees who have incomplete or missing timesheet entries.

### Configuration Options

| Setting | Description |
|---------|-------------|
| SMTP Server | Email server hostname (e.g., `smtp.gmail.com`) |
| SMTP Port | Port number (typically `587` for TLS) |
| Sender Email | The "From" email address used to send reminders |
| Sender Password | App password or SMTP credentials |
| Reminder Days | Which days of the week to send reminders |
| Reminder Times | What times of day to send reminders |
| Recipient List | Additional email addresses to always CC |

### How to Configure

1. Go to **Settings → Reminder Settings** tab.
2. Enter SMTP credentials and email configuration.
3. Select reminder schedule (days and times).
4. Click **Save**.

> [!CAUTION]
> Incorrect SMTP credentials will cause reminders to fail silently. Test by clicking **Send Reminder** in the Timesheet module after saving settings.

---

## Tab 4: Send Report Settings

### What It Does

Configures **automated management reports** sent on a schedule.

### Configuration Options

| Setting | Description |
|---------|-------------|
| Report Recipients | Email addresses that receive automated reports |
| Report Schedule | When reports are generated and sent |
| Report Type | Which data is included in the report |

### How to Configure

1. Go to **Settings → Send Report Settings** tab.
2. Configure recipient emails, schedule, and report type.
3. Click **Save**.

---

## Tab 5: Holiday Management

### What It Does

Manages the official holiday calendar. Employees marked as on holiday are excluded from timesheet reminders and billable reports.

### Viewing Holidays

The tab shows a list of all configured holidays with:
- Date
- Holiday name
- Applicable employees (or all employees if no exclusions)

### Adding a Holiday

1. Click **"+ Add Holiday"**.
2. Fill in:
   - **Date** — the holiday date
   - **Name** — the holiday name
3. Optionally, specify which employees this holiday applies to.
4. Click **Save**.

### Editing a Holiday

1. Click the **Edit** button next to the holiday.
2. Modify date or name.
3. Click **Save**.

### Deleting a Holiday

1. Click the **Delete** button next to the holiday.
2. Confirm deletion.

### Importing Holidays

1. Click **"Import Holidays"** (or use the Import Data module).
2. Upload an Excel file with holiday dates.
3. See [Import Holidays](./07-data-import-export.md#5-import-holidays) for column requirements.

### Employee Exclusions

Some holidays may not apply to all employees. When adding a holiday, you can specify **employee exclusions** — these employees will not be treated as on holiday for that date.

---

## Common Settings Errors

| Error | Cause | Fix |
|-------|-------|-----|
| Reminder emails not sent | Incorrect SMTP credentials | Verify SMTP server, port, email, and password |
| Lockout applies to admin | — | It doesn't. Admins bypass the lockout schedule. |
| "Holiday already exists for this date" | Duplicate holiday | Edit the existing holiday instead of adding a new one |
| "Invalid email format" in recipient list | Malformed email address | Correct the email address |

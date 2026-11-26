# Admin Guide 2 — Employee Management

> [!IMPORTANT]
> This module is accessible to **Admins only**.

---

## Overview

The Employee Management module allows admins to:
- View the full employee directory
- Add new employee accounts
- Edit existing employee details

**Navigation:** Sidebar → 👥 **Employees**

---

## 1. The Employee Directory (Tab: Directory)

The Directory tab lists all registered employees with their key details.

### Columns Displayed

| Column | Description |
|--------|-------------|
| Employee ID | Unique numeric identifier |
| Name | Full employee name |
| Username | Auto-generated login username |
| Email | Work email address |
| Slack ID | Slack workspace handle |
| Employment Type | Full-Time / Part-Time / Contractor / Intern |
| Status | Active / Inactive |
| 2FA Status | `Enabled`, `Pending Setup`, or `Disabled` |
| Password | Shown decrypted for admin reference |

### Searching Employees

Use the **search bar** at the top of the directory to filter employees by:
- Name
- Email
- Slack ID

Type any part of the value — results filter in real time.

---

## 2. Adding a New Employee (Tab: Add Employee)

### How to Add an Employee

1. Click the **"Add Employee"** tab.
2. Fill in all required fields (marked below).
3. Click **Save** (or the submit button).

### Fields

| Field | Required | Description | Validation |
|-------|----------|-------------|------------|
| Employee ID | ✅ Yes | Numeric unique ID | Must be unique; numbers only |
| Full Name | ✅ Yes | Employee's full name | Cannot be blank |
| Email | ✅ Yes | Work email address | Must be valid email format (e.g., `name@domain.com`) |
| Slack ID | ✅ Yes | Slack handle | Cannot be blank |
| Employment Type | ✅ Yes | Select from dropdown | Must be one of: Full-Time, Part-Time, Contractor, Intern |
| Status | ✅ Yes | Active or Inactive | Must be Active or Inactive |
| Password | ✅ Yes | Initial login password | Must meet password strength rules |

### Auto-Generated Username

The system **automatically creates** a username from the employee's name.

Example:
- Name: `John Doe` → Username: `john.doe`
- Username is shown after saving.

### Password Requirements for New Accounts

| Rule | Requirement |
|------|-------------|
| Minimum length | 8 characters |
| Uppercase | At least 1 uppercase letter |
| Lowercase | At least 1 lowercase letter |
| Digit | At least 1 number |
| Special character | At least 1 special character |

### Success Message

> ✅ "Employee added successfully."

The new employee can now log in using their username and the password you set.

---

## 3. Editing an Employee (Tab: Edit Employee)

### How to Edit an Employee

1. Click the **"Edit Employee"** tab.
2. Use the search or dropdown to select the employee you want to edit.
3. The form pre-fills with current values.
4. Modify the fields you want to update.
5. Click **Save**.

### Editable Fields

All fields shown in the Add Employee form can be edited, including:
- Name, Email, Slack ID
- Employment Type, Status
- Password (admin can reset any employee's password)

> [!NOTE]
> The **Employee ID** and **Username** cannot be changed after creation. If an employee's name changes, the username remains the original auto-generated value.

### Success Message

> ✅ "Employee updated successfully."

---

## 4. Employee Status: Active vs Inactive

| Status | Behavior |
|--------|----------|
| **Active** | Employee can log in; appears in dropdowns and reports |
| **Inactive** | Employee cannot log in; hidden from most dropdowns |

> [!CAUTION]
> Setting an employee to **Inactive** immediately prevents them from logging in. Their historical timesheet data is preserved.

---

## 5. Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "Email already exists" | Duplicate email address | Use a different email |
| "Employee ID already exists" | Duplicate ID number | Use a unique numeric ID |
| "Invalid email format" | Email doesn't match `name@domain.com` pattern | Correct the email address |
| "All required fields must be filled" | Missing mandatory field | Fill all required fields |

---

## 6. Employee Permissions

After creating an employee, you can grant additional access from **Settings → Employee Permissions**:

| Permission | What it Unlocks |
|------------|-----------------|
| `project_update_access` | Allows the employee to edit the Project Update grid |
| `allow_add_project` | Allows the employee to access the Add Project staging area |

See [System Settings →](./08-system-settings.md) for details.

---

## 7. Employee 2FA Management (Tab: 🔐 2FA Management)

Admins can centrally enable or disable Two-Factor Authentication (2FA) for individual employees:

1. Open **Employees → 🔐 2FA Management**.
2. Review each employee's **2FA Status**:
   - **Enabled (Verified):** Employee has configured an authenticator app.
   - **Enabled (Pending Setup):** Admin enabled 2FA; the employee will be prompted to scan a QR code and configure their authenticator app on their next login.
   - **Disabled:** Employee logs in with username and password only.
3. Click **Enable 2FA** or **Disable 2FA** next to any employee. Status updates immediately.
4. Expand **Recent 2FA Security Audit Logs** at the bottom of the tab to review enrollment, verification, and admin enable/disable events.

> [!NOTE]
> For security, employee authenticator secrets are encrypted at rest and are **never** visible to Admins.

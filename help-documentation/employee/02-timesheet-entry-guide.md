# Employee Guide 2 — Timesheet Entry Guide

> [!IMPORTANT]
> You can only add, edit, or delete **your own** timesheet entries. Admins can manage entries for all employees.

---

## Overview

The Timesheet module is where you log your daily working hours for each project. This is the most important thing you do in the app — accurate timesheet entries help the company track project effort and billing.

**Navigation:** Sidebar → 🗒️ **Timesheet**

---

## 1. Understanding the Timesheet Page

When you open the Timesheet module, you see:

- A **date range selector** at the top
- A **table** listing your existing timesheet entries
- An **"+ Add Entry"** button to log new hours
- An **"⛱️ Add Leave"** button for leave entries
- An **"Export"** button to download your data

---

## 2. Viewing Your Timesheets

### Changing the Date Range

By default, you see the **current 4-week cycle**.

To change the period:
1. Click the **Date Range** selector.
2. Choose a preset:
   - **This Week** — current Monday to Sunday
   - **Last Week** — previous Monday to Sunday
   - **Current 4-Week Cycle** — this billing period
   - **Previous 4-Week Cycle** — last billing period
   - **Custom Range** — pick any start and end date

### Filtering by Project

If you work on many projects, use the **Project filter** to show entries for a specific project only.

---

## 3. Adding a New Timesheet Entry

### Step-by-Step

1. Click the **"+ Add Entry"** button.
2. A dialog box appears. Fill in all required fields.
3. Click **Save**.

### Field Reference

| Field | Required | What to Enter | Validation |
|-------|----------|---------------|------------|
| **Project** | ✅ Yes | Search and select the project | Must select from the list |
| **Activity** | ✅ Yes | Select the type of work | Must select from dropdown |
| **Date** | ✅ Yes | The date you worked | Cannot be a future date |
| **Hours** | ✅ Yes | How many hours you worked | Must be between 0.5 and 24 |
| **Description** | No | Brief notes about what you did | Free text |

---

## 4. How to Select a Project

The project field uses a **search-and-select** workflow:

1. In the Project field, **type part of the project name or code**.
2. A list of matching projects appears below.
3. **Click the radio button** next to the project you want.
4. A confirmation box shows the selected project name and code.
5. If wrong, search again and select a different one.

> [!TIP]
> You can search by either the project code (e.g., `1042`) or any word in the project name. Short searches give more results; specific searches give fewer but more relevant results.

---

## 5. How to Select an Activity

Click the **Activity** dropdown and choose the type of work:

Common activity types include:
- Design
- Development
- Testing
- Review
- Meeting
- Documentation
- Support

> [!NOTE]
> The activity list is configured by your admin. If you can't find the right activity type, contact your admin.

---

## 6. Entering Hours

- Enter hours as a **decimal number**:
  - 1 hour = `1` or `1.0`
  - 1 hour 30 minutes = `1.5`
  - 7 hours 30 minutes = `7.5`
  - 15 minutes = `0.25`

- **Minimum:** 0.5 hours
- **Maximum:** 24 hours per entry

> [!TIP]
> You can have **multiple entries for the same day** — one per project. For example, if you worked on 3 projects on Monday, add 3 separate entries.

---

## 7. Adding a Description

The **Description** field is optional but recommended. Use it to:
- Briefly explain what you worked on
- Note specific tasks or deliverables
- Reference ticket numbers or feature names

Example: `Implemented user authentication flow — JIRA-234`

---

## 8. Saving the Entry

1. After filling in all required fields, click **Save**.
2. A success toast appears at the bottom of the screen:
   > ✅ "Timesheet entry added successfully."
3. The dialog closes and your new entry appears in the table.

---

## 9. Editing an Existing Entry

You can edit your entries within the **current week** (Monday to Sunday).

> [!WARNING]
> Entries from **past weeks** are locked — you cannot edit them. If you need to correct a past entry, contact your admin.

### How to Edit

1. Find the entry in the table.
2. Click the **Edit** button (pencil ✏️ icon) in the Actions column.
3. The edit dialog opens with current values.
4. Make your changes.
5. Click **Save**.

---

## 10. Deleting an Entry

You can delete entries from the **current week only**.

### How to Delete

1. Find the entry in the table.
2. Click the **Delete** button (🗑️ trash icon) in the Actions column.
3. A confirmation prompt appears.
4. Click **Confirm** to permanently delete the entry.

> [!CAUTION]
> Deleted entries **cannot be recovered**. Only delete an entry if it was added by mistake.

---

## 11. Identifying Missing Timesheet Entries

You may receive a **reminder email** if you have missing entries for the current timesheet cycle.

To check for missing entries yourself:
1. Set the Date Range to **Current 4-Week Cycle**.
2. Count the working days (excluding weekends and holidays).
3. Check if you have at least one entry for each working day.
4. If a day is missing, add an entry for that day.

> [!TIP]
> Leave entries (sick leave, annual leave) also count — you don't need to log project hours on days when you're on leave. See [Leave Management →](./03-leave-management.md).

---

## 12. Exporting Your Timesheets

1. Set the Date Range to the period you want to export.
2. Click the **"Export"** button.
3. An Excel file downloads with all your visible entries.

---

## 13. Common Validation Errors

| Error Message | What It Means | How to Fix |
|---------------|---------------|------------|
| "Please select a project" | No project selected | Search and click a project in the list |
| "Please select an activity" | No activity selected | Pick an activity from the dropdown |
| "Hours must be between 0.5 and 24" | Invalid hours value | Enter a number from 0.5 to 24 |
| "Date cannot be in the future" | Future date selected | Select today or a past date |
| "Please select a date" | Date field left empty | Click the date field and pick a date |

---

## 14. Week Boundaries

Timesheets follow a **Monday–Sunday** week:

| Day | Week |
|-----|------|
| Monday | Start of week |
| Sunday | End of week |

Entries from previous weeks become locked (read-only) for employees. The admin can still edit past entries if needed.

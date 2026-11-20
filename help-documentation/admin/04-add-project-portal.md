# Admin Guide 4 — Add Project Portal

> [!IMPORTANT]
> This module is accessible to **Admins** and employees with the `allow_add_project` permission.

---

## Overview

The Add Project Portal is a **staging workspace** for new projects that have not yet been synced to the FMP master list. It lets you create, track, and export new project entries before they are officially added to the system.

**Navigation:** Sidebar → ➕ **Add Project**

---

## 1. What Is This Module For?

When a new project is initiated, it may not yet exist in FMP. The Add Project Portal lets you:

- Pre-create the project record with all relevant details
- Track its status (whether it's been added to FMP, exported, etc.)
- Export the list to share with FMP administrators

This is **not** the same as the master project list (which comes from FMP via Import).

---

## 2. Viewing Existing Staged Projects

The main view shows a grid of all staged projects with columns:

| Column | Description |
|--------|-------------|
| Project Name | Name of the new project |
| Project Code | Unique project code |
| Priority | Priority value (decimals allowed, e.g., `1.5`) |
| Status | Current status of the staged project |
| Lead Engineer | Assigned lead |
| Phase | Current project phase |
| Trello Link | Trello board URL |
| Prototype Link | Prototype/design URL |
| Slack Link | Slack channel URL |
| Estimated Days | Planned project duration |
| Actual Days | Actual days spent so far |
| BC | Checkbox: Business Case created |
| Trello | Checkbox: Trello board created |
| WA | Checkbox: Work Authorization issued |
| WS | Checkbox: Workspace created |
| Notes | Free-text notes |
| FMP Added | Has this project been added to FMP? |
| Exported | Has this record been exported? |

---

## 3. Adding a New Staged Project

### How to Add

1. Click the **"Add Project"** or **"+ New"** button in the portal.
2. A form opens. Fill in the required fields.
3. Click **Save**.

### Fields

| Field | Required | Description | Validation |
|-------|----------|-------------|------------|
| Project Name | ✅ Yes | Full name of the project | Cannot be blank |
| Project Code | ✅ Yes | Unique numeric/alphanumeric code | Must be unique in the staging table |
| Priority | No | Priority level | Decimal numbers allowed (e.g., `1`, `2.5`) |
| Status | No | Project status | Select from predefined options |
| Lead Engineer | No | Name of responsible engineer | Free text |
| Phase | No | Current phase name | Free text |
| Trello Link | No | URL of Trello board | Should be a valid URL |
| Prototype Link | No | URL of prototype/design | Should be a valid URL |
| Slack Link | No | URL of Slack channel | Should be a valid URL |
| Estimated Days | No | Planned duration in days | Numeric |
| Actual Days | No | Days spent so far | Numeric |
| BC | No | Business Case created? | Checkbox (true/false) |
| Trello ✓ | No | Trello board created? | Checkbox |
| WA | No | Work Authorization issued? | Checkbox |
| WS | No | Workspace created? | Checkbox |
| Notes | No | Additional notes | Free text |

### Success Message
> ✅ "Project added successfully."

---

## 4. Editing a Staged Project

### How to Edit

1. Click the row or select the project you want to edit.
2. Click the **Edit** button (pencil icon).
3. The form opens pre-filled with current values.
4. Make changes and click **Save**.

### Success Message
> ✅ "Project updated successfully."

---

## 5. Deleting Staged Projects

### Single Delete

1. Select the project row.
2. Click the **Delete** button (trash icon).
3. Confirm deletion in the dialog.

### Bulk Delete

1. Select multiple rows using checkboxes.
2. Click **Delete Selected**.
3. Confirm bulk deletion.

> [!CAUTION]
> Deletion is **permanent**. Deleted staged projects cannot be recovered. Only delete records you are sure should be removed.

---

## 6. Marking Projects as FMP Added

Once a project has been officially added to FMP:

1. Select the project row(s).
2. Click **"Mark as FMP Added"**.
3. The `FMP Added` column updates to ✅.

This helps track which staged projects have been processed.

---

## 7. Export / Mark as Exported

1. Select the project row(s) to export.
2. Click **"Export"** or **"Mark as Exported"**.
3. An Excel file downloads with the project data.
4. The `Exported` column updates to ✅ for exported records.

You can filter to show only **Non-Exported** records to identify what hasn't been shared yet.

---

## 8. Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "Project Code already exists" | Duplicate code in staging table | Use a unique project code |
| "Project Name is required" | Name field left blank | Enter a project name |
| "Invalid URL format" | Link field has non-URL text | Enter a proper URL starting with `http://` or `https://` |

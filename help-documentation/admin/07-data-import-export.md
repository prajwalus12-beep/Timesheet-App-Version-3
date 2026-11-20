# Admin Guide 7 — Data Import & Export

> [!IMPORTANT]
> This module is accessible to **Admins only**.

---

## Overview

The Import Data module allows admins to bulk-load records from Excel files into the system. It supports 5 import types. Data is validated before import and the system shows a summary of new, updated, and skipped records.

**Navigation:** Sidebar → 📥 **Import Data**

---

## ⚠️ Import Order — CRITICAL

> [!CAUTION]
> You **must** import data in this order. Some imports depend on data from previous imports.
>
> **Required Order:**
> 1. Import Employees
> 2. Import Projects ← must come before Import Update Projects
> 3. Import Assignments
> 4. Import Update Projects ← requires projects to exist first
> 5. Import Holidays

If you import **Update Projects** before **Projects**, records will be skipped because the project codes will not be found in the database.

---

## 1. Import Employees

Imports employee records from an Excel file.

### Required Columns

| Column Name | Description |
|-------------|-------------|
| Employee ID | Unique numeric ID |
| Name | Full employee name |
| Email | Work email address |
| Slack ID | Slack handle |
| Employment Type | Full-Time / Part-Time / Contractor / Intern |
| Status | Active / Inactive |

### Steps

1. Click the **"Import Employees"** section.
2. Click **"Download Sample"** to get the template Excel file.
3. Fill the template with employee data.
4. Click **"Browse"** and select your filled Excel file.
5. Click **"Import"**.
6. Review the result summary (new, updated, skipped counts).

### Result Summary

| Message | Meaning |
|---------|---------|
| `X new employees added` | Records inserted for the first time |
| `X employees updated` | Existing records updated with new data |
| `X skipped` | Records skipped due to errors or missing data |

---

## 2. Import Projects

Imports project master records from an Excel file (typically exported from FMP).

### Required Columns

| Column Name | Description |
|-------------|-------------|
| Job No | Unique project code |
| Project Name | Full project name |
| Status | Project status (Active/Completed/On Hold/Cancelled) |
| Priority | Priority value |
| Lead Engineer | Responsible engineer name |
| Trello Link | Trello board URL (optional) |

### Steps

1. Click **"Import Projects"** section.
2. Download the sample template.
3. Prepare your Excel file following the column names exactly.
4. Upload and click **"Import"**.
5. Review the result summary.

### Notes

- Project names with trailing spaces or tabs are automatically stripped before saving.
- Invalid status values (not in the approved list) are **skipped** — only valid statuses are imported.
- If a project code already exists, its record is **updated** (not duplicated).

### Valid Status Values

`Active`, `Completed`, `On Hold`, `Cancelled`

> [!WARNING]
> Status values like `_`, blank, or unrecognized strings will be **skipped** automatically.

---

## 3. Import Assignments

Imports project-employee assignments (which employees are assigned to which projects).

### Required Columns

| Column Name | Description |
|-------------|-------------|
| Employee ID | Employee's numeric ID |
| Job No | Project code |

### Steps

Standard import steps: Download sample → Fill data → Upload → Review summary.

---

## 4. Import Update Projects (Project Reports)

Imports or updates the project update/status fields (the editable data shown in Project Updates V2).

> [!IMPORTANT]
> **Import Projects must be run first.** This import reads project codes from the `project_reports` table, which is populated by the Projects import.

### Required Columns

| Column Name | Maps To | Description |
|-------------|---------|-------------|
| Job No | Project code | Must match an existing project code |
| Current Phase_g | Phase | Current project phase |
| Status | Status | Project status |
| Actual Days | Actual days | Days spent (fractional values are rounded) |
| Notes | Notes | Project notes |

### Steps

1. Click **"Import Update Projects"** section.
2. Download the sample template.
3. Upload your prepared Excel file.
4. A **preview table** appears showing:
   - Rows with **differences** highlighted in red
   - A mismatch summary table showing old vs new values
5. Review the preview carefully.
6. Click **"Continue Import"** to apply changes, or **"Cancel"** to abort.

### Result Summary

| Message | Meaning |
|---------|---------|
| `X updated` | Records where data was different and updated |
| `X new entries` | New project codes added (only if not in DB) |
| `X skipped (FK not found)` | Project code doesn't exist in master — skipped |

> [!NOTE]
> If all project codes already exist and have matching data, you will see `0 new entries` — this is correct behavior, not an error.

---

## 5. Import Holidays

Imports public holiday records for the year.

### Required Columns

| Column Name | Description |
|-------------|-------------|
| Date | Holiday date (YYYY-MM-DD or DD/MM/YYYY) |
| Name | Holiday name |
| Region | Applicable region (optional) |

### Steps

Standard import steps: Download sample → Fill data → Upload → Review summary.

---

## 6. Downloading Sample Templates

Every import section has a **"Download Sample"** button that provides a correctly formatted Excel template.

> [!TIP]
> Always start from the sample template. Using your own Excel file with different column names will cause import failures.

---

## 7. Common Import Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "0 new entries" on Update Projects | All project codes already exist in DB | Expected behavior if data was imported before. Upload a file with new project codes. |
| "Project code not found" | Update Projects uploaded before Projects import | Import Projects first, then import Update Projects |
| "Invalid column: [column name]" | Column name doesn't match expected format | Use the sample template exactly |
| "Workbook contains no default style" | Minor Excel formatting warning | Safe to ignore — data imports correctly |
| "X skipped (FK not found)" | A project code in the update file doesn't exist in the master list | Import Projects first; verify the project code is correct |

---

## 8. Export Data

The **Project Update V2** page (editable grid) supports Excel export with:
- Yellow highlighting for fields that were manually updated
- FMP-compatible column names and format

See [Project Updates](./03-project-management.md) for export instructions from that page.

# Admin Guide 7 — Data Import & Export

> [!IMPORTANT]
> This module is accessible to **Admins only**.

---

## Overview

The Import Data module allows admins to bulk-load records from Excel or CSV files into the system. It supports 4 import modules, including a **single unified Projects & Project Updates import** that updates both the **Project V1** and **Project Update V2** screens. Data is validated before import and the system shows a summary of new, updated, and skipped records.

**Navigation:** Sidebar → 📥 **Import Data**

---

## 📋 Recommended Import Order

1. **Import Employees**
2. **Import Projects & Project Updates** *(Unified — updates both Project V1 and Project Update V2)*
3. **Import Assignments**
4. **Import Holidays**

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

## 2. Import Projects & Project Updates (Unified)

This **single, unified import** updates **both** the **Project V1** screen and the **Project Update V2** screen from one Excel/CSV sheet.

### Required & Supported Columns

| Column Name | Maps To | Description |
|-------------|---------|-------------|
| Job No | Project code | Unique project code |
| Job Priority | Priority | Numeric or decimal priority (e.g., `1.1`) |
| Priority | Project Name | Used as Project Name if `Project` column is missing |
| Lead engineer | Lead Engineer | Assigned engineer name |
| Search_Project / Status | Status | Project status (supports aliases) |
| Current Phase_g | Phase | Current project phase |
| Start Date / Finish Date | Dates | Project start and finish dates |
| CheckBoxe BC / Trello / WA / WS | Checkboxes | Boolean flags |
| Estimated Days / Actual Days | Days | Planned and actual days (fractional values are rounded) |
| Notes | Notes | Optional project notes |

### Steps

1. Locate the **"🔄 Projects & Project Updates"** section.
2. Click **"📥 Sample Project / Update Excel"** to download the template.
3. Upload your prepared Excel or CSV file.
4. Click **"Import & Update Projects"**.
5. If conflicts or manual UI updates exist, a **preview table** appears showing:
   - Rows with **differences** highlighted in red
   - A mismatch summary table showing old vs new values
6. Review the preview carefully and click **"Continue Import"** to apply changes, or **"Cancel"** to abort.

### Result Summary

| Message | Meaning |
|---------|---------|
| `X updated` | Existing project records updated across Project V1 & Project Update V2 |
| `X new entries` | New project codes added |
| `X skipped` | Records skipped due to invalid data or missing required fields |

> [!NOTE]
> If all project codes already exist and have matching data, you will see `0 new entries` — this is expected behavior, not an error.

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

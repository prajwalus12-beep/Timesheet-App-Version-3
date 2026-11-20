# Missing Screenshots Inventory

> [!IMPORTANT]
> Screenshots must be captured from the **live running application**. Never use fake or mock screenshots.
> Run the Playwright capture script: `automation/screenshot_generator.py`

---

## Status Legend

| Symbol | Meaning |
|--------|---------|
| ⏳ | Pending capture |
| ✅ | Captured |
| ♻️ | Needs recapture (UI changed) |

---

## Admin Screenshots

| # | File Name | Description | Status | Referenced In |
|---|-----------|-------------|--------|---------------|
| 1 | `admin/employee-directory.png` | Employee directory tab with list of employees | ⏳ | admin/02-employee-management.md |
| 2 | `admin/add-employee-form.png` | Add employee form with all fields | ⏳ | admin/02-employee-management.md |
| 3 | `admin/edit-employee-form.png` | Edit employee form pre-filled | ⏳ | admin/02-employee-management.md |
| 4 | `admin/projects-master-list.png` | Projects master list page (compact view) | ⏳ | admin/03-project-management.md |
| 5 | `admin/add-project-portal.png` | Add Project staging grid | ⏳ | admin/04-add-project-portal.md |
| 6 | `admin/add-project-form.png` | New project form with fields | ⏳ | admin/04-add-project-portal.md |
| 7 | `admin/add-project-fmp-added.png` | Mark FMP Added action on a project row | ⏳ | admin/04-add-project-portal.md |
| 8 | `admin/timesheet-admin-view.png` | Timesheet admin view — all employees | ⏳ | admin/05-timesheet-administration.md |
| 9 | `admin/add-timesheet-dialog.png` | Add timesheet entry dialog (admin) | ⏳ | admin/05-timesheet-administration.md |
| 10 | `admin/edit-timesheet-dialog.png` | Edit timesheet entry dialog | ⏳ | admin/05-timesheet-administration.md |
| 11 | `admin/add-leave-dialog.png` | Add leave dialog for any employee | ⏳ | admin/05-timesheet-administration.md |
| 12 | `admin/timesheet-date-range.png` | Date range selector dropdown | ⏳ | admin/05-timesheet-administration.md |
| 13 | `admin/reports-kpi-cards.png` | Reports page KPI summary cards | ⏳ | admin/06-reports-and-analytics.md |
| 14 | `admin/reports-pie-project.png` | Hours by Project pie chart | ⏳ | admin/06-reports-and-analytics.md |
| 15 | `admin/reports-bar-trend.png` | Hours trend bar chart | ⏳ | admin/06-reports-and-analytics.md |
| 16 | `admin/reports-pdf-export.png` | Sample PDF export output | ⏳ | admin/06-reports-and-analytics.md |
| 17 | `admin/import-data-overview.png` | Import Data page — all 5 sections | ⏳ | admin/07-data-import-export.md |
| 18 | `admin/import-projects-result.png` | Import Projects upload and result summary | ⏳ | admin/07-data-import-export.md |
| 19 | `admin/import-update-preview.png` | Import Update Projects preview with red highlights | ⏳ | admin/07-data-import-export.md |
| 20 | `admin/import-update-confirm.png` | Continue/Cancel dialog for Update Projects import | ⏳ | admin/07-data-import-export.md |
| 21 | `admin/settings-lockout.png` | Settings — Lockout Schedule tab | ⏳ | admin/08-system-settings.md |
| 22 | `admin/settings-permissions.png` | Settings — Employee Permissions tab | ⏳ | admin/08-system-settings.md |
| 23 | `admin/settings-reminders.png` | Settings — Reminder Settings tab | ⏳ | admin/08-system-settings.md |
| 24 | `admin/settings-holidays.png` | Settings — Holiday Management tab | ⏳ | admin/08-system-settings.md |

---

## Employee Screenshots

| # | File Name | Description | Status | Referenced In |
|---|-----------|-------------|--------|---------------|
| 25 | `employee/timesheet-listing.png` | Employee timesheet listing page | ⏳ | employee/02-timesheet-entry-guide.md |
| 26 | `employee/add-timesheet-dialog.png` | Add timesheet entry dialog (employee view) | ⏳ | employee/02-timesheet-entry-guide.md |
| 27 | `employee/project-search.png` | Project search and radio button selection | ⏳ | employee/02-timesheet-entry-guide.md |
| 28 | `employee/timesheet-validation-error.png` | Example of a timesheet validation error message | ⏳ | employee/02-timesheet-entry-guide.md |
| 29 | `employee/edit-timesheet-dialog.png` | Edit timesheet dialog (employee view) | ⏳ | employee/02-timesheet-entry-guide.md |
| 30 | `employee/add-leave-dialog.png` | Add Leave dialog with fields | ⏳ | employee/03-leave-management.md |
| 31 | `employee/leave-in-timesheet.png` | Leave entry showing in timesheet table | ⏳ | employee/03-leave-management.md |
| 32 | `employee/project-updates-view-only.png` | Project Updates grid — grayed out view-only | ⏳ | employee/04-project-updates.md |
| 33 | `employee/project-updates-edit.png` | Project Updates grid — cell in edit mode | ⏳ | employee/04-project-updates.md |
| 34 | `employee/project-updates-yellow-highlight.png` | Yellow highlighted cell in project grid | ⏳ | employee/04-project-updates.md |
| 35 | `employee/add-project-staging.png` | Add Project staging grid | ⏳ | employee/05-add-project-staging.md |
| 36 | `employee/add-project-form.png` | New project staging form | ⏳ | employee/05-add-project-staging.md |
| 37 | `employee/sidebar-change-password.png` | Sidebar popover with Change Password option | ⏳ | employee/06-profile-and-security.md |
| 38 | `employee/change-password-dialog.png` | Change Password dialog with 3 fields | ⏳ | employee/06-profile-and-security.md |
| 39 | `employee/password-error.png` | Password validation error example | ⏳ | employee/06-profile-and-security.md |

---

## How to Capture Screenshots

### Using the Playwright Script

```bash
cd "c:\FMP TS\update project include project updatation page\Timesheet-App-Version-3"
python help-documentation/automation/screenshot_generator.py
```

### Manual Capture Instructions

If the Playwright script cannot run:

1. Start the application: `streamlit run app.py`
2. Open the application in Chrome or Edge
3. Log in with admin credentials for admin screenshots, employee credentials for employee screenshots
4. Navigate to each page listed above
5. Use browser's built-in screenshot (F12 → `Ctrl+Shift+P` → "Screenshot") or a tool like Snipping Tool
6. Save to the correct path in `help-documentation/screenshots/`
7. Update this file — change ⏳ to ✅ for each captured screenshot

### Screenshot Guidelines

- Capture the **full relevant page or dialog** (not just part of it)
- Remove personal data (blur employee emails, names if needed)
- Use 1280×720 or higher resolution
- Save as `.png` format
- File names must match exactly what's listed above

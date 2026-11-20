# Comprehensive Implementation Plan: Automated Help Documentation System for Admin & Employee

## 1. Executive Summary & Objective

The objective of this initiative is to create a robust, production-grade, and role-segregated **Help Documentation System** for the **Timesheet & Project Management Web Application (Streamlit + Supabase + React Components)**. The documentation will serve non-technical employees, project leads, and system administrators, enabling complete self-service without developer or support intervention.

Furthermore, this system introduces an **automated synchronization and change-detection pipeline** that continuously monitors application code (Streamlit pages, React frontend components, Supabase queries, scheduled background jobs, and validation schemas) to identify changes in forms, fields, business rules, or permissions, and keeps the documentation and screenshot inventory perpetually up-to-date.

---

## 2. Existing Application Architecture Analysis

A full-codebase inspection of the application reveals a multi-tiered hybrid Streamlit and React architecture connected to Supabase:

### 2.1 Technology Stack & Structure
- **Backend & Application Server**: Python 3.10+ / Streamlit multi-page framework (`app.py`, `pages/`).
- **Database & Data Layer**: Supabase PostgreSQL database managed via the Supabase Python SDK and postgrest clients (`database/connection.py`, `database/queries.py`).
- **Cryptography & Security**: Symmetric encryption (Fernet) for project names and credentials, bcrypt hashing for passwords, role-based lockout mechanisms, and rate-limiting (`services/auth_service.py`, `utils/lockout_helpers.py`).
- **Custom Interactive Frontend (Bridges)**: Custom React / Vite bidirectional iframe components:
  - `components/project_update_react/` (Project Update V2 table with inline editing, batch saves, and export).
  - `components/add_project_react/` (Add Project component for staged FMP project imports).
  - `components/timesheet_v2/` (Alternative grid-based timesheet view).
- **Background Automation & Scheduling**: Python `APScheduler` background service executing automated reminder emails, scheduled PDF timesheet reports, and lockout checks (`services/scheduler_service.py`, `services/automated_scheduler.py`, `services/report_email_service.py`, `services/timesheet_reminder_service.py`).
- **Export / Import Engine**: `openpyxl` and `pandas` based custom Excel builders with styling, number format fixes, data cleansing, and validation mapping (`utils/xlsx_export.py`, `utils/project_update_import_validator.py`).

### 2.2 Role-Based Access Control (RBAC) Matrix

| Feature / Page | System Administrator (`admin`) | Employee (`employee` - Default) | Employee with Special Flag (`allow_add_project` / `project_update_access`) | Inactive Employee (`status=0`) |
| :--- | :---: | :---: | :---: | :---: |
| **Login & CAPTCHA** | Full Access | Full Access | Full Access | Blocked / Inactive warning |
| **Change Password** | Full Access | Full Access | Full Access | Read-Only |
| **Timesheet Entries - View** | All Employees | Self Only | Self Only | Self Only (Read-Only) |
| **Timesheet - Add Entry** | No (Disabled) | Yes (Active only) | Yes (Active only) | Disabled |
| **Timesheet - Add Leave** | Yes (For anyone) | Yes (Self only) | Yes (Self only) | Disabled |
| **Timesheet - Edit / Delete Entry** | Yes (Any record, past/future) | Yes (Own record, active week) | Yes (Own record, active week) | Disabled |
| **Timesheet - Send Reminder Email** | Yes (Manual / Force Resend) | No (Hidden) | No (Hidden) | No (Hidden) |
| **Timesheet - Excel Export** | All filtered records | Self filtered records | Self filtered records | Read-only |
| **Projects (Project V1)** | View-Only Compact Grid | View-Only Compact Grid | View-Only Compact Grid | View-Only |
| **Project Update V2** | Full Edit & Export | View-Only (Default) | Full Edit (if `project_update_access=True`) | View-Only |
| **Add Project** | Full Create / Edit / Delete / Export | Hidden / Access Denied | Full Create / Edit / Delete / Export (if `allow_add_project=True`) | Read-Only / Disabled |
| **Employees Directory** | Full CRUD + Password View | Hidden / Blocked | Hidden / Blocked | Hidden / Blocked |
| **Reports (Summary & Charts)** | Full Access (All Employees) | Hidden / Blocked | Hidden / Blocked | Hidden / Blocked |
| **Import Data (4 Modules)** | Full Access | Hidden / Blocked | Hidden / Blocked | Hidden / Blocked |
| **System Settings (5 Tabs)** | Full Access | Hidden / Blocked | Hidden / Blocked | Hidden / Blocked |

---

## 3. Module Breakdown & Verification

### 3.1 Authentication & Security (`pages/login_page.py`, `services/auth_service.py`)
- **Username Dropdown**: Select username from dynamic database roster.
- **CAPTCHA**: Dynamic 6-character distorted text code (`ABCDEFGHJKLMNPQRSTUVWXYZ23456789`) with noise bars.
- **Password Policy**: Minimum 8 characters, at least 1 uppercase letter, 1 lowercase letter, 1 digit, and 1 special symbol (`@$!%*?&#^_-`).
- **Account Lockout**: 5 failed consecutive attempts trigger a 15-minute lockout (`locked_until` in database).

### 3.2 Timesheet Entries (`pages/timesheet_page/`, `components/dialogs.py`)
- **Filters**:
  - Date Range: "This Week", "Last Week", "Current 4 Week Cycle", "Previous 4 Week Cycle", "Custom Range".
  - Employee Filter: Selectable for Admin; locked to logged-in user for Employee.
  - Project Filter: Searchable multi-project selector sorted by numerical job code descending.
- **Add Entry Dialog**:
  - Mandatory Fields: Employee, Date (restricted to current week ending Sunday), Project (radio button with 20-item paging and keyword search), Hours (> 0.0, max 24.0), Phase (Analysis, Design, Development, Testing, Deployment, Support), Comment (mandatory, max 400 characters, whitespace-stripped).
  - Business Validations: Cannot log on a date marked as Approved Leave or Company Holiday; cannot submit future dates beyond current week; inactive employees blocked.
- **Add Leave Dialog**:
  - Types: Casual Leave (CL), Sick Leave (SL), Earned/Paid Leave (PL), Unpaid Leave (UL), Holiday.
  - Automatic Exclusions: Automatically inserts zero-hour/standard leave codes, suppresses "Missing Timesheet" automated reminder emails, omits from billable client reports.
- **Edit / Delete Entry Dialog**:
  - Modal with populated data. Admins can adjust any date; employees are restricted to current week.
- **Admin Send Reminder Button**:
  - Triggers automated scanning of active employees missing 8h/day or 40h/week, dispatching SMTP emails. "Force resend" checkbox bypasses 7-day duplicate suppression.

### 3.3 Projects Page — Project V1 (`pages/projects_page.py`)
- Compact read-only portfolio overview displaying Project Code, Encrypted Project Name (decrypted in transit), Status, Priority, Lead Engineer, and Trello link.

### 3.4 Project Update V2 (`pages/project_update_page_v2.py`, `components/project_update_react/`)
- Interactive React AG-Grid-like editable spreadsheet:
  - Editable columns: Status (9 states), Phase, Priority (supports decimal e.g. 1.1), Lead Engineer, Start Date, End Date, Estimated Days, Actual Days (auto-rounded to nearest integer), Checkboxes (BC, Trello, WA, WS), Trello Link, Slack Link, Prototype Link, Notes.
  - Change tracking: Tracks manual edits by toggling `*_updated` boolean flags in PostgreSQL.
  - Excel Export: Preserves FMP compatibility, maps names to numeric employee IDs, and highlights modified cells in yellow if requested.

### 3.5 Add Project (`pages/add_project_page.py`, `components/add_project_react/`)
- Dedicated staging workspace for creating and importing new projects before syncing to FMP.
- Role checks: Restricted to Admin or employees with `allow_add_project=True`.
- Backend uniqueness check: Prevents duplicate project codes before insert.
- Action items: Multi-delete, single delete, mark as exported/non-exported, export to FMP format or TS format.

### 3.6 Employees Management (`pages/employees_page.py`)
- Admin-only directory:
  - **Employee List**: Search by name, email, or Slack ID. Displays decrypted password, employment type (Full-Time, Part-Time, Contractor, Intern), and Active/Inactive badge.
  - **Add Employee**: Employee ID (numeric/alphanumeric unique), Name, Slack ID, Email (regex validation), Employment Type, Status. Automatically generates username and assigns default encrypted password.
  - **Edit Employee**: Update employee profile details, toggle active/inactive status, or reset credentials.

### 3.7 Timesheet Reports & Analytics (`pages/reports_page.py`, `utils/chart_helpers.py`)
- Admin-only executive analytics suite:
  - **KPI Metric Cards**: Total Logged Hours, Converted Working Days (8 hours/day), Active Headcount, Active Projects.
  - **Interactive Pie Charts**: Hours allocation grouped by Project Status, Project Name, and Employee with overflow truncation and slice thresholding.
  - **Interactive Stacked / Grouped Bar Charts**: Weekly & 4-week cycle trends with employee initial badges and project color gradients.
  - **PDF Export Engine**: Vector ReportLab generation producing downloadable presentation-ready executive briefs (`utils/chart_helpers.py`).

### 3.8 Import Data (`pages/import_page.py`, `utils/project_update_import_validator.py`)
- **Employees Import**: Maps `a__Serial`, `Name`, `Slack ID`, `Email`.
- **Projects Import**: Bulk imports master projects into `project` table. Automatically handles lead engineer ID-to-name conversion and sanitizes project names.
- **Assignments Import**: Bulk creates employee-to-project mappings using `Projects_Resources::a_EmployeeID` and `Projects_Resources::a_ProjectID`.
- **Update Projects Import**:
  - Compares sheet against database for manual edits.
  - Displays inline side-by-side mismatch warning table and red-cell preview if manual changes would be overwritten.
  - Requires user confirmation ("Continue Import") with persistent session state handling.
- **Holidays Import**: Imports company-wide holiday schedules.

### 3.9 System Settings (`pages/settings_page.py`)
- **Weekly Lockout Schedule**: Sunday through Saturday individual locks to block all employee project edits on specific days.
- **Employee Permissions**: Granular toggles for `project_update_access` and `allow_add_project`.
- **Timesheet Reminder Settings**: Configure SMTP credentials, reminder execution days/times, target email lists, and subject templates.
- **Send Report Settings**: Automated dispatch configuration for management reports.
- **Holiday Management**: Add, Edit, Delete, and exclude individual employees from official holidays.

---

## 4. Proposed Documentation Structure

```text
help-documentation/
│
├── README.md                           # Master documentation portal and index
│
├── admin/
│   ├── 01-getting-started.md           # Login, CAPTCHA, navigation, profile
│   ├── 02-employee-management.md       # Directory, Add/Edit employee, status toggle
│   ├── 03-project-management.md        # Project V1, Update V2, staging, FMP sync
│   ├── 04-add-project-portal.md        # Staging new projects, code generation, exports
│   ├── 05-timesheet-administration.md  # All-employee timesheet auditing, reminders, overrides
│   ├── 06-reports-and-analytics.md     # Charts, KPI metrics, PDF generation, filtering
│   ├── 07-data-import-export.md        # 4 import modules, conflict resolution, exports
│   ├── 08-system-settings.md           # Weekly lockout, permissions, scheduler, holidays
│   └── 09-troubleshooting-faq.md       # Admin validation directory & recovery workflows
│
├── employee/
│   ├── 01-getting-started.md           # Login, CAPTCHA, password rules, navigation
│   ├── 02-timesheet-entry-guide.md     # In-depth step-by-step logging guide
│   ├── 03-leave-management.md          # Logging Sick/Casual/Earned/Unpaid leave
│   ├── 04-project-updates.md           # Project Update V2 guide (permissions, inline edits)
│   ├── 05-add-project-staging.md       # Add Project guide (for authorized employees)
│   ├── 06-profile-and-security.md      # Password updates, session rules, lockout prevention
│   └── 07-validations-and-errors.md    # Plain-English glossary of every warning & error
│
├── screenshots/
│   ├── admin/                          # Annotated UI screenshots for Admin views
│   └── employee/                       # Annotated UI screenshots for Employee views
│
├── automation/                         # Automated change-detection and doc sync scripts
│   ├── doc_sync_engine.py              # AST & schema analyzer for code changes
│   ├── screenshot_generator.py         # Playwright headless browser automation
│   ├── doc_validator.py                # Broken links, missing images, and schema linter
│   └── templates/                      # Documentation templates for diff reporting
│
└── CHANGELOG.md                        # Audit trail of documentation updates
```

---

## 5. Detailed Timesheet & Project Management Documentation Specification

### 5.1 Timesheet Module (Employee Focus)
To resolve usability issues for non-technical employees, the Timesheet Guide will break down every workflow:
1. **Navigating to the Timesheet**: Left sidebar -> click "📋 Timesheet".
2. **Selecting Project Status**: Choice between "In-Progress" (active projects) and "Complete" (archived/finished projects).
3. **Searching and Selecting Projects**: How to use the interactive keyword search box; explaining that projects are displayed 20 per page sorted by Job Number descending; hover tooltips for full project descriptions.
4. **Selecting Dates**: Explaining the week boundary rule (Monday 00:00 to Sunday 23:59). Preventing future-date errors.
5. **Entering Hours**: Decimal support (e.g., 2.5h, 4.0h, 8.0h); validation against 0h or negative hours.
6. **Writing Mandatory Comments**: Minimum non-whitespace requirement; clear examples of good work descriptions vs. invalid blanks; max 400 characters limit.
7. **Selecting Phase**: Explanation of each phase (Analysis = Requirements/WBS; Design = UI/UX/Wireframes; Development = Coding/Database; Testing = QA/Testing; Deployment = Release/Publishing; Support = Maintenance/Bugfixes).
8. **Submitting Entries**: Explanation of the green toast confirmation; how entries immediately appear in the lower table.
9. **Editing Existing Logs**: Clicking the ✏️ pencil icon; restrictions on modifying locked/approved past weeks.
10. **Deleting Entries**: Clicking the 🗑️ trash icon; confirmation dialogs.
11. **Leave and Holiday Logging**: Using the "⛱️ Add Leave" modal to mark Sick/Casual leave so that automated missing timesheet emails are not sent.

### 5.2 Every Timesheet Validation & Plain-English Solutions

| Validation Condition | Actual Message in UI | Root Cause | Employee Actionable Solution |
| :--- | :--- | :--- | :--- |
| **Empty or Blank Comment** | `Comment is required. Please provide details before submitting.` | Comment text area left empty or only contains spaces. | Type a concise summary of tasks done (e.g. "Worked on login bug fix"). |
| **Future Week Date** | `Cannot submit entry for a future week date.` | Selected date is beyond the upcoming Sunday. | Choose today's date or a past date within the current week. |
| **Date is Approved Leave** | `This date is registered as approved leave. Standard work hours cannot be logged for leave dates.` | Employee already logged Sick/Casual Leave on that date. | If you actually worked on this date, edit or delete the leave entry first. |
| **Date is Company Holiday** | `This date is configured as a Holiday ('...'). If you worked on this day, please remove the holiday entry first.` | The selected date is an official company holiday. | Company holidays give automatic 8h. If you worked overtime, remove the holiday entry first. |
| **Zero or Negative Hours** | `Please enter valid hours.` | Hours input set to 0.0 or negative. | Enter positive hours between 0.5 and 24.0. |
| **No Project Selected** | `⚠️ No project selected — pick one from the list above` | Radio button not clicked in the project list. | Type project name in search box and click the round radio button next to it. |
| **Filter Switched After Selection** | `⚠️ Selected project is no longer in the current filter. Please re-select the project.` | Switched radio from "In-Progress" to "Complete" while project was selected. | Re-search and click the project in the currently active tab. |
| **Inactive Employee** | `Employee is inactive. This action is not available for inactive employees.` | Admin marked employee as Inactive in directory. | Contact administrator to reactivate your employee profile. |

---

## 6. Screenshot Automation & Visual Documentation Strategy

To comply with the strict instruction **never to generate fake screenshots or mockups**:
1. **Playwright Headless Browser Integration**: A dedicated Python script (`automation/screenshot_generator.py`) will launch Chromium against the local Streamlit application (`http://localhost:8501`).
2. **Automated Role Switching**:
   - Authenticates as `admin` to capture full administration screens.
   - Authenticates as an `employee` to capture employee-restricted views.
3. **Capture Catalog**:
   - `admin/01-login-screen.png` (Login page with CAPTCHA and username selector)
   - `admin/02-timesheet-admin-view.png` (Timesheet entries with "Send Reminder" and "Force resend")
   - `admin/03-project-v1.png` (Project V1 compact read-only view)
   - `admin/04-project-update-v2.png` (Project Update V2 AG-Grid table)
   - `admin/05-add-project-staging.png` (Add project page with export dialogs)
   - `admin/06-employee-directory.png` (Employee management list with decrypted passwords)
   - `admin/07-reports-dashboard.png` (Analytics dashboard with Pie & Bar charts)
   - `admin/08-import-modules.png` (Import page showing all 4 import uploaders)
   - `admin/09-system-settings.png` (Settings tabs: Lockout schedule, permissions, holidays)
   - `employee/01-timesheet-employee-view.png` (Timesheet page with "Add Entry" and "Add Leave")
   - `employee/02-add-entry-modal.png` (Modal dialog with custom project search and phase selector)
   - `employee/03-add-leave-modal.png` (Add Leave dialog with leave types)
   - `employee/04-validation-error-sample.png` (Real application validation warning banner)
   - `employee/05-project-update-v2-readonly.png` (View-only Project Update screen for unpermitted users)
   - `employee/06-change-password-modal.png` (Change password dialog with password strength criteria)
4. **Missing Screenshot Fallback**: If Playwright cannot run due to missing environment binaries, the system will output an explicit `MISSING_SCREENSHOTS.md` catalog detailing exact dimensions, viewport settings, and required views rather than placeholders.

---

## 7. Automatic Documentation Update System Architecture

```text
[ Developer Commits Code / PR ]
                │
                ▼
     [ Git Pre-Push Hook / CI Action ]
                │
                ▼
  [ 1. Change Detection Engine (AST & Diff Analysis) ]
    ├── Analyzes pages/*.py, components/*, database/queries.py
    ├── Extracts Form Fields, Validation Strings, Error Messages
    └── Maps Changes to Specific Markdown Guide Files
                │
                ▼
  [ 2. Documentation Diff & Verification Engine ]
    ├── Checks if Modified Fields/Rules are in Markdown
    ├── Identifies Stale Screenshots
    └── Generates Documentation Change Report
                │
                ▼
  [ 3. Automated Sync & PR Generation ]
    ├── Updates Markdown Files with New Rules/Fields
    ├── Appends Audit Record to CHANGELOG.md
    └── Captures New Screenshots via Playwright
```

### 7.1 Code Analysis & Heuristic Triggers
The synchronization engine (`automation/doc_sync_engine.py`) uses Python's built-in `ast` (Abstract Syntax Tree) module to inspect code without executing arbitrary files:
- **Form Inspection**: Detects changes in `st.text_input`, `st.selectbox`, `st.date_input`, `st.number_input`, `st.text_area`.
- **Validation Message Detection**: Extracts literal string arguments passed to `st.warning()`, `st.error()`, `st.toast()`, or `return False, "..."` in `database/queries.py`.
- **Route & Navigation Inspection**: Analyzes `sidebar.py` and `app.py` for new entries in `options` or `page_map`.
- **Permission Flag Inspection**: Monitors checks like `user.get("role") == "admin"` or `get_employee_add_project_access()`.

### 7.2 Documentation Sync Rules
- **No Silent Removals**: If a feature is modified, existing text is retained or revised; deprecations are flagged with `> [!WARNING] Deprecated`.
- **Automatic Changelog**: Appends detected diffs into `help-documentation/CHANGELOG.md` with timestamps and commit references.
- **Link & Asset Validation**: Ensures every `![Screenshot](...)` and `[Link](...)` path resolves to a valid existing file.

---

## 8. Implementation Phases & Estimated Effort

| Phase | Description | Deliverables | Estimated Effort |
| :---: | :--- | :--- | :---: |
| **Phase 1** | Deep Codebase Analysis & Mapping (Completed) | Architecture and validation inventory | 4 Hours |
| **Phase 2** | Technical Implementation Plan | `HELP_DOCUMENTATION_IMPLEMENTATION_PLAN.md` | 3 Hours |
| **Phase 3** | Admin Documentation Authoring | 9 Markdown files in `help-documentation/admin/` | 6 Hours |
| **Phase 4** | Employee Documentation Authoring | 7 Markdown files in `help-documentation/employee/` | 6 Hours |
| **Phase 5** | Screenshot Capture & Annotation | Real UI screenshots in `help-documentation/screenshots/` | 4 Hours |
| **Phase 6** | Documentation Automation Engine | `automation/doc_sync_engine.py` & validator | 6 Hours |
| **Phase 7** | Verification, Linting & Review Report | Validated Markdown links and CHANGELOG | 3 Hours |
| **Total** | | | **32 Hours** |

---

## 9. Acceptance Criteria

1. **Role Segregation**: Clear distinction between Admin and Employee capabilities; employees are never shown instructions for features they cannot access.
2. **Completeness**: Every form, button, filter, export, and import across all 8 modules is fully documented with exact field names and constraints.
3. **Usability**: Written in clear, non-technical English with actionable problem-solving instructions for every validation message.
4. **Accuracy**: 100% matched to actual source code in `Timesheet-App-Version-3` without assumptions.
5. **Authentic Visuals**: Real application screenshots matching current styles and UI widgets.
6. **Automation Readiness**: Self-contained synchronization script capable of detecting code changes and outputting structured change reports.

---

*This plan is ready for review. Full implementation of the documentation structure and synchronization scripts will commence upon user approval.*


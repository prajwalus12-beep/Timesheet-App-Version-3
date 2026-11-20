# Documentation Changelog

All notable changes to this Help Documentation are recorded here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [1.1.0] — 2026-11-20

### Added — In-App React Help Center
- Built standalone custom React frontend component: `components/help_react`
- Added interactive navigation sidebar with real-time documentation search
- Added interactive Error Lookup tool in the frontend for instantaneous validation troubleshooting
- Added role-aware views: Admins can toggle between Admin and Employee manuals; Employees see dedicated Employee documentation
- Added `"❓  Help"` option in Streamlit sidebar for both Admin and Employee roles with bidirectional routing in `app.py`
- Added `pages/help_page.py` that dynamically loads Markdown files from disk and serves them to the React component
- Added fallback rendering mechanism for 100% resilience

---

## [1.0.0] — 2026-11-20

### Added — Initial Documentation Release

**Admin Documentation (9 files)**
- `admin/01-getting-started.md` — Login, CAPTCHA, lockout, navigation, password change
- `admin/02-employee-management.md` — Employee directory, add, edit, permissions
- `admin/03-project-management.md` — Project master list (read-only view)
- `admin/04-add-project-portal.md` — Staging workspace for new projects
- `admin/05-timesheet-administration.md` — All-employee timesheet view, add/edit/delete, leave, export, reminders
- `admin/06-reports-and-analytics.md` — KPIs, charts, PDF export
- `admin/07-data-import-export.md` — 5 import modules with column specifications and conflict resolution
- `admin/08-system-settings.md` — Lockout schedule, employee permissions, reminders, report settings, holiday management
- `admin/09-troubleshooting-faq.md` — Common errors and step-by-step solutions

**Employee Documentation (7 files)**
- `employee/01-getting-started.md` — Login, CAPTCHA, lockout, navigation, module access
- `employee/02-timesheet-entry-guide.md` — Full step-by-step timesheet logging guide
- `employee/03-leave-management.md` — Add, edit, delete leave; leave types; impact on reminders
- `employee/04-project-updates.md` — View-only vs edit access; inline editing; yellow highlights; export
- `employee/05-add-project-staging.md` — Create and track staged projects (permission required)
- `employee/06-profile-and-security.md` — Password change, lockout recovery, session behavior
- `employee/07-validations-and-errors.md` — Every error message with cause and resolution

**Supporting Files**
- `README.md` — Master index with role-based navigation
- `CHANGELOG.md` — This file
- `screenshots/MISSING_SCREENSHOTS.md` — Inventory of screenshots pending capture
- `automation/README.md` — Documentation sync system overview
- `automation/doc_sync_engine.py` — AST-based change detection engine
- `automation/screenshot_generator.py` — Playwright screenshot capture script
- `automation/doc_validator.py` — Markdown link and image validator

**Coverage**
- 16 application modules documented
- 42 validation rules documented with error messages and fixes
- 25 screenshots identified (pending Playwright capture)
- Role-based access matrix established for Admin and Employee

---

## Upcoming

The following are planned but not yet implemented:

- [ ] Automated screenshot capture via Playwright
- [ ] CI/CD integration for auto-detection of documentation drift
- [ ] PDF export of full documentation set
- [ ] Interactive HTML version of help docs

---

## How Documentation Is Updated

When application code changes:

1. Run `automation/doc_sync_engine.py` to detect changes
2. Review the generated change report
3. Update affected `.md` files
4. Update or flag affected screenshots in `screenshots/MISSING_SCREENSHOTS.md`
5. Add an entry to this CHANGELOG with the version date and what changed

See `automation/README.md` for full instructions.

# Admin Guide 3 — Project Management (Master List)

> [!IMPORTANT]
> This is a **read-only** view of the project master list. To edit project data, use [Project Updates →](./05-timesheet-administration.md) or [Add Project Portal →](./04-add-project-portal.md).

---

## Overview

The Project Management page shows the **master list of all projects** synced from FMP (the company's ERP system). This view is designed for quick reference and is intentionally compact.

**Navigation:** Sidebar → 📁 **Projects**

**Who can access:** Admin + Employees (read-only for all)

---

## 1. What You See

The Projects page displays a compact table with the following columns:

| Column | Description |
|--------|-------------|
| Project Code | Unique numeric code (e.g., `1001`) |
| Project Name | Full project name (decrypted for display) |
| Status | Current project status |
| Priority | Project priority level |
| Lead Engineer | Assigned engineer name |
| Trello Link | Link to the project's Trello board (if set) |

---

## 2. What This Page Does NOT Support

| Action | Supported? | Alternative |
|--------|------------|-------------|
| Edit project details | ❌ No | Use Project Update V2 |
| Delete a project | ❌ No | Not supported (data comes from FMP) |
| Add a project | ❌ No | Use Add Project Portal |
| Filter by status | ❌ No | Use Project Update V2 for filtering |
| Export to Excel | ❌ No | Use Project Update V2 export |

> [!NOTE]
> The master project list is populated via **Import → Import Projects**. Project data originates from FMP and should not be manually edited from this view.

---

## 3. Project Statuses

| Status | Meaning |
|--------|---------|
| Active | Project is currently ongoing |
| Completed | Project has been finished |
| On Hold | Project is temporarily paused |
| Cancelled | Project has been cancelled |

---

## 4. Reading the Project List

- **Project Code** is the primary identifier used across all modules (timesheets, reports, imports).
- **Project Name** is stored encrypted in the database; it is decrypted automatically for display.
- **Trello Link** opens in a new browser tab if clicked.

---

## 5. Relationship to Other Modules

```
Import → Import Projects
        ↓
  Project Master List  ←─── This page
        ↓
  Project Update V2 (editable status/phase/notes)
        ↓
  Timesheet entries reference Project Code
        ↓
  Reports filter by Project
```

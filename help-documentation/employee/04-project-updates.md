# Employee Guide 4 — Project Updates

---

## Overview

The Project Updates module shows the editable status and progress information for all projects. Depending on your permissions, you may be able to **view only** or **edit** project update fields.

**Navigation:** Sidebar → 🔄 **Project Updates**

---

## 1. What You See

The Project Updates page displays an interactive grid (table) with one row per project. Each row shows:

| Column | Description |
|--------|-------------|
| Project Code | Unique project identifier |
| Project Name | Full name of the project |
| Status | Current project status |
| Phase | Current project phase |
| Start Date | When the project started |
| End Date | Expected or actual end date |
| Lead Engineer | Responsible engineer |
| Trello Link | Link to Trello board |
| Prototype Link | Link to prototype/design |
| Slack Link | Link to Slack channel |
| Estimated Days | Planned project duration |
| Actual Days | Days spent so far |
| BC | Business Case created? (checkbox) |
| Trello ✓ | Trello board set up? (checkbox) |
| WA | Work Authorization issued? (checkbox) |
| WS | Workspace created? (checkbox) |
| Notes | Free-text notes |

---

## 2. View-Only Access (Default)

If you do **not** have `project_update_access` permission, all columns in the grid are **grayed out** and you cannot click to edit them.

You can still:
- Scroll and read all project data
- Use Trello/Prototype/Slack links (they open in a new tab)
- See yellow-highlighted fields (fields that have been manually updated)

> [!NOTE]
> To request edit access, ask your admin to enable `project_update_access` for your account in **Settings → Employee Permissions**.

---

## 3. Edit Access (With `project_update_access` Permission)

If your admin has granted you edit access, you can **click any cell** to edit it inline.

### How to Edit a Cell

1. Click the cell you want to change.
2. The cell becomes editable (a text box, dropdown, or date picker appears).
3. Enter the new value.
4. Click **anywhere outside the cell** (or press Enter) to save.
5. The cell shows a **yellow highlight** to indicate it was manually updated.

> [!TIP]
> Yellow highlighting means the field was manually changed from the original imported value. This helps the team track which fields have been manually reviewed and updated.

---

## 4. Editable Fields

| Field | Type | Allowed Values |
|-------|------|---------------|
| Status | Dropdown | Active / Completed / On Hold / Cancelled |
| Phase | Text | Any text (e.g., "Design", "Development") |
| Start Date | Date picker | Any date |
| End Date | Date picker | Any date |
| Lead Engineer | Text | Engineer's name |
| Trello Link | Text (URL) | Full URL |
| Prototype Link | Text (URL) | Full URL |
| Slack Link | Text (URL) | Full URL |
| Estimated Days | Number | Whole number |
| Actual Days | Number | Whole number |
| BC | Checkbox | True / False |
| Trello ✓ | Checkbox | True / False |
| WA | Checkbox | True / False |
| WS | Checkbox | True / False |
| Notes | Long text | Any text |

> [!NOTE]
> **Project Code** and **Project Name** are read-only. They come from the master project list and can only be changed via import.

---

## 5. Auto-Save Behavior

Changes are saved **automatically** when you:
- Click away from the edited cell
- Click a different row
- Click the **Save** button (if present)

You do **not** need to press a separate "Save All" button — changes are written to the database as you go.

---

## 6. Exporting Project Updates to Excel

1. Click the **"Export"** button at the top of the grid.
2. An Excel file downloads with all current project data.
3. Fields that were manually updated will be highlighted in **yellow** in the Excel file (matching what you see on screen).

This export format is compatible with FMP for sharing updated project status.

---

## 7. Using Project Links

If a project has Trello, Prototype, or Slack links set:
- The links appear as clickable URLs in the grid.
- Clicking opens the link in a **new browser tab**.
- If a link field is empty, nothing happens when you click it.

---

## 8. Understanding Project Status Values

| Status | Meaning |
|--------|---------|
| **Active** | Project is currently in progress |
| **Completed** | Project has been finished |
| **On Hold** | Project is temporarily paused |
| **Cancelled** | Project has been cancelled |

---

## 9. What You Cannot Do

| Action | Supported? | Alternative |
|--------|------------|-------------|
| Delete a project | ❌ No | Only admins via import |
| Change project code | ❌ No | Fixed — set during import |
| Change project name | ❌ No | Only via admin import |
| Add a new project | ❌ No | Use Add Project Portal (if permitted) |

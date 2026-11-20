# Employee Guide 5 — Add Project Staging

> [!IMPORTANT]
> This module is only visible if your admin has granted you the `allow_add_project` permission. If you don't see "Add Project" in your sidebar, contact your admin.

---

## Overview

The Add Project Staging area allows you to create new project entries before they are officially added to FMP (the company's project management system). Think of it as a **draft workspace** where new projects are recorded and tracked until they're formally processed.

**Navigation:** Sidebar → ➕ **Add Project**

---

## 1. What Is This Module For?

When a new project is initiated, it may not yet be in the FMP system. This module lets you:
- Pre-create the project with all relevant details
- Track its progress (whether Trello is set up, work authorization issued, etc.)
- Signal when it's ready for FMP by marking it "FMP Added"

---

## 2. Viewing Staged Projects

The main view shows a grid with all staged projects. You can scroll horizontally to see all columns.

---

## 3. Creating a New Project

### How to Add

1. Click the **"+ Add Project"** or **"+ New"** button.
2. A form opens. Fill in the details.
3. Click **Save**.

### Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| **Project Name** | ✅ Yes | The full name of the new project |
| **Project Code** | ✅ Yes | A unique code for this project |
| Priority | No | Priority level (decimals OK, e.g., `1.5`) |
| Status | No | Current status of the project |
| Lead Engineer | No | Name of the responsible engineer |
| Phase | No | Current project phase |
| Trello Link | No | URL of the Trello board |
| Prototype Link | No | URL of the prototype or design |
| Slack Link | No | URL of the Slack channel |
| Estimated Days | No | Planned duration in days |
| Actual Days | No | Days spent so far |
| BC | No | ✅ if Business Case is created |
| Trello ✓ | No | ✅ if Trello board is set up |
| WA | No | ✅ if Work Authorization is issued |
| WS | No | ✅ if Workspace is set up |
| Notes | No | Any additional information |

### Success Message
> ✅ "Project added successfully."

---

## 4. Editing a Project

1. Find the project in the grid.
2. Click the **Edit** button.
3. Modify the fields.
4. Click **Save**.

---

## 5. Deleting a Project

> [!CAUTION]
> Deletion is permanent. Only delete a staged project if it was added by mistake.

1. Click the **Delete** button for the project.
2. Confirm deletion.

---

## 6. What "FMP Added" Means

Once your admin confirms that a staged project has been officially added to FMP:

- The project row will be marked with **FMP Added = ✅**
- This tells you the project is now in the main system and no longer just in the staging area

You may see a **"Mark FMP Added"** button for projects you've staged — your admin or you can click this to update the status.

---

## 7. What "Exported" Means

The **Exported** field shows whether the staged project data has been exported and shared (typically as an Excel file):

- **Exported = ✅** — The data has been shared/exported
- **Exported = ❌** — Not yet exported

---

## 8. Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "Project Name is required" | Name field left blank | Enter the project name |
| "Project Code already exists" | Code is already used | Choose a unique project code |
| "Invalid URL" | Link doesn't start with `http://` or `https://` | Enter a complete URL |

---

## 9. Important Notes

- Staged projects here do **not** automatically appear in the main Projects list (which comes from FMP).
- The staged project will only appear system-wide once it's officially imported via **Import → Import Projects** by an admin.
- Use this module as a tracking tool, not as a live project record.

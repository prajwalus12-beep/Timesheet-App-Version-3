"""
Help Page for Admin and Employee Documentation
===============================================
Renders the interactive React Help Component.
Dynamically loads Markdown documentation from the help-documentation/ directory.
"""

import os
import re
from pathlib import Path
import streamlit as st
from components.help_react import help_component

PROJECT_ROOT = Path(__file__).resolve().parents[1]
HELP_DOCS_ROOT = PROJECT_ROOT / "help-documentation"


def _extract_title_from_md(content: str, default_name: str) -> str:
    """Extract first H1 heading from Markdown content, or format filename."""
    match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    if match:
        raw_title = match.group(1).strip()
        # Clean common prefixes like 'Admin Guide 1 — ' or 'Employee Guide 2 — '
        clean_title = re.sub(r"^(Admin|Employee)\s+Guide\s+\d+\s+[—–-]\s*", "", raw_title)
        return clean_title
    # Fallback to readable filename
    clean_name = re.sub(r"^\d+-", "", default_name).replace(".md", "").replace("-", " ").title()
    return clean_name


def _categorize_doc(filename: str, role: str) -> str:
    """Determine category for sidebar grouping."""
    f = filename.lower()
    if "getting-started" in f:
        return "Getting Started"
    if "timesheet" in f or "leave" in f:
        return "Timesheet & Leave"
    if "project" in f:
        return "Projects"
    if "employee" in f:
        return "Team Management"
    if "report" in f:
        return "Reports & Analytics"
    if "import" in f:
        return "Data Import/Export"
    if "setting" in f:
        return "System Settings"
    if "validation" in f or "troubleshoot" in f or "faq" in f:
        return "Troubleshooting & Errors"
    return "General"


@st.cache_data(ttl=60)
def load_all_documentation():
    """
    Read all markdown files from help-documentation/admin and /employee.
    Returns a dict with 'admin' and 'employee' lists of doc objects.
    """
    docs_data = {"admin": [], "employee": []}

    for role in ["admin", "employee"]:
        role_dir = HELP_DOCS_ROOT / role
        if not role_dir.exists():
            continue

        md_files = sorted(role_dir.glob("*.md"))
        for f in md_files:
            try:
                content = f.read_text(encoding="utf-8")
                title = _extract_title_from_md(content, f.name)
                category = _categorize_doc(f.name, role)
                doc_id = f"{role}_{f.stem}"

                docs_data[role].append({
                    "id": doc_id,
                    "filename": f.name,
                    "title": title,
                    "category": category,
                    "role": role,
                    "content": content,
                })
            except Exception as e:
                print(f"Error reading doc {f}: {e}")

    return docs_data


def render_help_page(user):
    """Render the Help page for Admin or Employee."""
    role = user.get("role", "employee")
    username = user.get("username", "User")

    # Load docs dynamically
    docs_data = load_all_documentation()

    # Check if directed from a specific module banner
    initial_page = st.session_state.pop("help_initial_page", None)
    initial_doc_id = ""
    if initial_page:
        keyword = {
            "Timesheet Entries": "timesheet",
            "Projects": "project-management",
            "Project Update": "project-update",
            "Add Project": "add-project",
            "Employees": "employee",
            "Reports": "report",
            "Import Data": "import",
            "Settings": "setting",
            "2FA Security": "security" if role == "employee" else "getting-started",
        }.get(initial_page, "")
        if keyword:
            role_docs = docs_data.get(role, [])
            for d in role_docs:
                if keyword in d["filename"]:
                    initial_doc_id = d["id"]
                    break

    # Pass to React custom component
    try:
        help_component(
            docs=docs_data,
            user_role=role,
            user_name=username,
            initial_doc_id=initial_doc_id,
            key="help_react_portal"
        )
    except Exception as e:
        st.warning("Loading React Help Component...")
        # Graceful fallback: render using Streamlit native UI
        _render_native_fallback(docs_data, role)


def _render_native_fallback(docs_data, role):
    """Native Streamlit fallback view if React component encounters any issue."""
    st.title("📚 Help & Documentation")
    available_docs = docs_data.get(role, [])

    if not available_docs:
        st.info("No documentation available.")
        return

    titles = [d["title"] for d in available_docs]
    selected_idx = st.selectbox("Select Guide:", range(len(titles)), format_func=lambda i: titles[i])

    selected_doc = available_docs[selected_idx]
    st.markdown(selected_doc["content"])

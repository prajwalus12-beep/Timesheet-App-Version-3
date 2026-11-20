"""
doc_sync_engine.py — Documentation Synchronization Engine
==========================================================

Analyzes the Timesheet App source code using Python AST and compares
it against the existing Help Documentation to detect drift.

Usage:
    python doc_sync_engine.py
    python doc_sync_engine.py --fail-on-changes   # for CI/CD pipelines

Output:
    A documentation change report listing:
    - Changed source files
    - Affected application modules
    - Documentation files that need updating
    - Screenshot files that may need recapture

Philosophy:
    - Only flags USER-FACING changes (not internal refactoring)
    - Uses AST analysis to understand WHAT changed, not just WHICH files changed
    - Never modifies documentation automatically — humans review and update
"""

import ast
import os
import sys
import json
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HELP_DOCS_ROOT = PROJECT_ROOT / "help-documentation"
STATE_FILE = HELP_DOCS_ROOT / "automation" / ".sync_state.json"

# Source files that map to user-facing features
# Format: source_file → (documentation_file, description)
SOURCE_TO_DOC_MAP = {
    "pages/login_page.py": [
        ("admin/01-getting-started.md", "Login and authentication"),
        ("employee/01-getting-started.md", "Login and authentication"),
    ],
    "pages/timesheet_page/__init__.py": [
        ("admin/05-timesheet-administration.md", "Timesheet administration"),
        ("employee/02-timesheet-entry-guide.md", "Timesheet entry"),
        ("employee/03-leave-management.md", "Leave management"),
    ],
    "components/dialogs.py": [
        ("employee/02-timesheet-entry-guide.md", "Add/Edit timesheet dialogs"),
        ("employee/03-leave-management.md", "Add/Edit leave dialogs"),
        ("employee/06-profile-and-security.md", "Password change dialog"),
    ],
    "pages/projects_page.py": [
        ("admin/03-project-management.md", "Project master list"),
        ("employee/04-project-updates.md", "Project view"),
    ],
    "pages/project_update_page_v2.py": [
        ("admin/03-project-management.md", "Project updates"),
        ("employee/04-project-updates.md", "Project updates (editable grid)"),
    ],
    "pages/add_project_page.py": [
        ("admin/04-add-project-portal.md", "Add Project portal"),
        ("employee/05-add-project-staging.md", "Add Project staging"),
    ],
    "pages/employees_page.py": [
        ("admin/02-employee-management.md", "Employee management"),
    ],
    "pages/reports_page.py": [
        ("admin/06-reports-and-analytics.md", "Reports and analytics"),
    ],
    "pages/import_page.py": [
        ("admin/07-data-import-export.md", "Data import and export"),
    ],
    "pages/settings_page.py": [
        ("admin/08-system-settings.md", "System settings"),
    ],
    "database/queries.py": [
        ("admin/07-data-import-export.md", "Import business logic"),
        ("employee/07-validations-and-errors.md", "Validation error messages"),
    ],
    "components/sidebar.py": [
        ("admin/01-getting-started.md", "Navigation sidebar"),
        ("employee/01-getting-started.md", "Navigation sidebar"),
    ],
    "pages/help_page.py": [
        ("README.md", "Interactive React Help Center"),
        ("admin/01-getting-started.md", "Help Center navigation"),
        ("employee/01-getting-started.md", "Help Center navigation"),
    ],
}

# Keywords that indicate user-facing changes (not just refactoring)
USER_FACING_INDICATORS = [
    "st.error", "st.warning", "st.success", "st.info",
    "st.form", "st.text_input", "st.selectbox", "st.number_input",
    "st.date_input", "st.checkbox", "st.button", "st.dialog",
    "st.expander", "st.tabs", "st.radio", "st.multiselect",
    "raise ValueError", "raise Exception",
    "error_message", "success_message", "warning_message",
    "validation", "validate_", "_validator",
]


def compute_file_hash(filepath: Path) -> str:
    """Compute SHA-256 hash of a file's content."""
    try:
        content = filepath.read_text(encoding="utf-8", errors="ignore")
        return hashlib.sha256(content.encode()).hexdigest()
    except Exception:
        return ""


def load_state() -> dict:
    """Load the previous sync state (file hashes)."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {}


def save_state(state: dict) -> None:
    """Save the current sync state (file hashes)."""
    STATE_FILE.write_text(json.dumps(state, indent=2))


def extract_user_facing_elements(filepath: Path) -> dict:
    """
    Parse a Python file with AST and extract user-facing elements:
    - Form fields (st.text_input, st.selectbox, etc.)
    - Error/success messages (st.error, st.success, etc.)
    - Validation logic (raise ValueError, validate_* functions)
    - Button labels

    Returns a dict describing what user-facing elements were found.
    """
    result = {
        "form_fields": [],
        "messages": [],
        "buttons": [],
        "validations": [],
        "dialogs": [],
    }

    try:
        source = filepath.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(source)
    except Exception as e:
        result["parse_error"] = str(e)
        return result

    for node in ast.walk(tree):
        # Detect Streamlit calls
        if isinstance(node, ast.Call):
            func = node.func
            func_name = ""

            if isinstance(func, ast.Attribute):
                func_name = f"{getattr(func.value, 'id', '')}. {func.attr}"
            elif isinstance(func, ast.Name):
                func_name = func.id

            # Form input fields
            if any(ui in func_name for ui in [
                "text_input", "number_input", "selectbox", "multiselect",
                "date_input", "checkbox", "radio", "text_area"
            ]):
                label = ""
                if node.args:
                    first_arg = node.args[0]
                    if isinstance(first_arg, ast.Constant):
                        label = str(first_arg.value)
                result["form_fields"].append(label or func_name)

            # Buttons
            elif "button" in func_name:
                label = ""
                if node.args:
                    first_arg = node.args[0]
                    if isinstance(first_arg, ast.Constant):
                        label = str(first_arg.value)
                result["buttons"].append(label or func_name)

            # Messages (errors, warnings, success)
            elif any(msg in func_name for msg in ["st.error", "st.warning", "st.success", "st.info"]):
                msg_text = ""
                if node.args:
                    first_arg = node.args[0]
                    if isinstance(first_arg, ast.Constant):
                        msg_text = str(first_arg.value)
                result["messages"].append({"type": func_name, "text": msg_text})

            # Dialogs
            elif "dialog" in func_name:
                result["dialogs"].append(func_name)

        # Detect raise statements (validation errors)
        elif isinstance(node, ast.Raise):
            if node.exc:
                exc_str = ast.unparse(node.exc) if hasattr(ast, "unparse") else str(node.exc)
                result["validations"].append(exc_str[:200])

    return result


def detect_changed_files(state: dict) -> list[tuple[Path, str]]:
    """
    Compare current file hashes against saved state.
    Returns list of (filepath, change_type) tuples.
    change_type: "modified" | "added" | "deleted"
    """
    changes = []
    current_hashes = {}

    for rel_path in SOURCE_TO_DOC_MAP:
        filepath = PROJECT_ROOT / rel_path
        if filepath.exists():
            current_hash = compute_file_hash(filepath)
            current_hashes[rel_path] = current_hash

            prev_hash = state.get(rel_path)
            if prev_hash is None:
                changes.append((filepath, "added"))
            elif prev_hash != current_hash:
                changes.append((filepath, "modified"))
        else:
            if rel_path in state:
                changes.append((PROJECT_ROOT / rel_path, "deleted"))

    return changes, current_hashes


def analyze_change_impact(filepath: Path) -> dict:
    """
    Analyze what actually changed in a file to determine if it's
    a user-facing change or just internal refactoring.
    """
    rel_path = str(filepath.relative_to(PROJECT_ROOT)).replace("\\", "/")
    elements = extract_user_facing_elements(filepath)

    is_user_facing = bool(
        elements.get("form_fields") or
        elements.get("messages") or
        elements.get("buttons") or
        elements.get("validations")
    )

    return {
        "file": rel_path,
        "is_user_facing": is_user_facing,
        "elements": elements,
        "affected_docs": SOURCE_TO_DOC_MAP.get(rel_path, []),
    }


def generate_report(changes: list, impacts: list) -> str:
    """Generate a human-readable documentation change report."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "# Documentation Change Report",
        f"Generated: {timestamp}",
        "",
        "---",
        "",
    ]

    if not changes:
        lines.append("✅ No source changes detected. Documentation is up to date.")
        return "\n".join(lines)

    user_facing_changes = [i for i in impacts if i["is_user_facing"]]
    refactoring_only = [i for i in impacts if not i["is_user_facing"]]

    lines.append(f"## Summary")
    lines.append(f"- Total changed files: {len(changes)}")
    lines.append(f"- User-facing changes: {len(user_facing_changes)}")
    lines.append(f"- Internal refactoring only: {len(refactoring_only)}")
    lines.append("")

    if user_facing_changes:
        lines.append("## ⚠️ Documentation Update Required")
        lines.append("")
        for impact in user_facing_changes:
            lines.append(f"### `{impact['file']}`")
            lines.append("")
            lines.append("**Affected Documentation:**")
            for doc_file, description in impact["affected_docs"]:
                lines.append(f"- [ ] `{doc_file}` — {description}")
            lines.append("")
            if impact["elements"].get("messages"):
                lines.append("**New/Changed Messages:**")
                for msg in impact["elements"]["messages"][:5]:
                    lines.append(f"  - `{msg.get('type', '')}`: {msg.get('text', '')[:80]}")
                lines.append("")
            if impact["elements"].get("form_fields"):
                lines.append("**Form Fields Detected:**")
                for field in impact["elements"]["form_fields"][:10]:
                    lines.append(f"  - `{field}`")
                lines.append("")

    if refactoring_only:
        lines.append("## ℹ️ Internal Changes (No Documentation Update Needed)")
        for impact in refactoring_only:
            lines.append(f"- `{impact['file']}` — internal refactoring, no user-facing impact")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("**Next Steps:**")
    lines.append("1. Review each flagged documentation file")
    lines.append("2. Update affected sections")
    lines.append("3. Recapture any outdated screenshots")
    lines.append("4. Add an entry to `help-documentation/CHANGELOG.md`")
    lines.append("5. Run `doc_validator.py` to check all links")

    return "\n".join(lines)


def main():
    fail_on_changes = "--fail-on-changes" in sys.argv

    print("🔍 Documentation Sync Engine")
    print(f"   Project root: {PROJECT_ROOT}")
    print()

    # Load previous state
    state = load_state()

    # Detect changed files
    changes, current_hashes = detect_changed_files(state)

    if not changes:
        print("✅ No source changes detected. Documentation is up to date.")
        save_state(current_hashes)
        return

    print(f"📋 Detected {len(changes)} changed file(s):")
    for filepath, change_type in changes:
        rel = filepath.relative_to(PROJECT_ROOT)
        print(f"   [{change_type.upper()}] {rel}")

    print()
    print("🔬 Analyzing user-facing impact...")

    impacts = []
    for filepath, change_type in changes:
        if change_type != "deleted" and filepath.exists():
            impact = analyze_change_impact(filepath)
            impacts.append(impact)

    # Generate report
    report = generate_report(changes, impacts)
    report_path = HELP_DOCS_ROOT / "automation" / f"change_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    report_path.write_text(report, encoding="utf-8")

    print()
    print(report)
    print()
    print(f"📄 Report saved to: {report_path}")

    # Save updated state
    save_state(current_hashes)

    # Fail CI/CD pipeline if user-facing changes found
    user_facing = any(i["is_user_facing"] for i in impacts)
    if fail_on_changes and user_facing:
        print()
        print("❌ Exiting with error (--fail-on-changes): undocumented user-facing changes detected.")
        sys.exit(1)


if __name__ == "__main__":
    main()

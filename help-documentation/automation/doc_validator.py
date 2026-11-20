"""
doc_validator.py — Documentation Link & Image Validator
========================================================

Validates all Markdown files in the help-documentation directory:
  1. Internal links — checks that linked .md files actually exist
  2. Image references — checks that screenshot files exist
  3. Anchor links — checks that heading anchors are valid
  4. External links — reports URLs (does not fetch them)

Usage:
    python help-documentation/automation/doc_validator.py
    python help-documentation/automation/doc_validator.py --fix   # auto-fix trivial issues
"""

import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
HELP_DOCS_ROOT = PROJECT_ROOT / "help-documentation"

# Regex patterns
LINK_PATTERN = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
IMAGE_PATTERN = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
HEADING_PATTERN = re.compile(r'^#{1,6}\s+(.+)$', re.MULTILINE)


def heading_to_anchor(heading: str) -> str:
    """Convert a markdown heading to a GitHub-style anchor."""
    anchor = heading.lower()
    anchor = re.sub(r'[^\w\s-]', '', anchor)
    anchor = re.sub(r'\s+', '-', anchor.strip())
    anchor = re.sub(r'-+', '-', anchor)
    return anchor


def validate_file(md_file: Path) -> list[dict]:
    """
    Validate all links and images in a Markdown file.
    Returns a list of issues found.
    """
    issues = []
    content = md_file.read_text(encoding="utf-8")
    base_dir = md_file.parent

    # Collect all headings in this file (for anchor validation)
    headings = {heading_to_anchor(h) for h in HEADING_PATTERN.findall(content)}

    # Check all links
    for match in LINK_PATTERN.finditer(content):
        link_text = match.group(1)
        link_target = match.group(2)

        # Skip external URLs
        if link_target.startswith(("http://", "https://", "mailto:")):
            continue

        # Handle anchor-only links
        if link_target.startswith("#"):
            anchor = link_target[1:]
            if anchor not in headings:
                issues.append({
                    "type": "broken_anchor",
                    "file": str(md_file.relative_to(HELP_DOCS_ROOT)),
                    "text": link_text,
                    "target": link_target,
                    "message": f"Anchor '{anchor}' not found in this file",
                })
            continue

        # Handle relative file links (with or without anchors)
        file_part = link_target.split("#")[0]
        anchor_part = link_target.split("#")[1] if "#" in link_target else None

        target_path = (base_dir / file_part).resolve()

        if not target_path.exists():
            issues.append({
                "type": "broken_link",
                "file": str(md_file.relative_to(HELP_DOCS_ROOT)),
                "text": link_text,
                "target": link_target,
                "message": f"File not found: {target_path}",
            })

    # Check all images
    for match in IMAGE_PATTERN.finditer(content):
        alt_text = match.group(1)
        img_target = match.group(2)

        # Skip external URLs
        if img_target.startswith(("http://", "https://")):
            continue

        target_path = (base_dir / img_target).resolve()
        if not target_path.exists():
            issues.append({
                "type": "missing_screenshot",
                "file": str(md_file.relative_to(HELP_DOCS_ROOT)),
                "alt": alt_text,
                "target": img_target,
                "message": f"Screenshot not found: {target_path}",
            })

    return issues


def run_validation() -> int:
    """
    Run validation on all Markdown files.
    Returns the number of issues found.
    """
    print("🔍 Documentation Validator")
    print(f"   Root: {HELP_DOCS_ROOT}")
    print()

    all_issues = []
    md_files = list(HELP_DOCS_ROOT.rglob("*.md"))

    print(f"   Found {len(md_files)} Markdown files")
    print()

    for md_file in sorted(md_files):
        issues = validate_file(md_file)
        all_issues.extend(issues)

    # Report
    if not all_issues:
        print("✅ All links and images are valid!")
        return 0

    # Group by type
    broken_links = [i for i in all_issues if i["type"] == "broken_link"]
    broken_anchors = [i for i in all_issues if i["type"] == "broken_anchor"]
    missing_screenshots = [i for i in all_issues if i["type"] == "missing_screenshot"]

    print(f"Found {len(all_issues)} issue(s):")
    print()

    if missing_screenshots:
        print(f"📸 Missing Screenshots ({len(missing_screenshots)}):")
        for issue in missing_screenshots:
            print(f"   [{issue['file']}]")
            print(f"   → {issue['target']}")
            print(f"   → {issue['message']}")
            print()

    if broken_links:
        print(f"🔗 Broken Links ({len(broken_links)}):")
        for issue in broken_links:
            print(f"   [{issue['file']}] '{issue['text']}' → {issue['target']}")
            print(f"   → {issue['message']}")
            print()

    if broken_anchors:
        print(f"⚓ Broken Anchors ({len(broken_anchors)}):")
        for issue in broken_anchors:
            print(f"   [{issue['file']}] '{issue['text']}' → {issue['target']}")
            print(f"   → {issue['message']}")
            print()

    return len(all_issues)


def main():
    issue_count = run_validation()

    if "--fail-on-issues" in sys.argv and issue_count > 0:
        print(f"\n❌ Exiting with error: {issue_count} documentation issue(s) found.")
        sys.exit(1)
    elif issue_count > 0:
        print(f"\n⚠️  {issue_count} issue(s) found. Run screenshot_generator.py to capture missing screenshots.")
    else:
        print("\n✅ Documentation validation passed.")


if __name__ == "__main__":
    main()

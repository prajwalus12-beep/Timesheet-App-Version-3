"""
screenshot_generator.py — Automated Screenshot Capture
=======================================================

Captures screenshots from the live Timesheet Application using Playwright.
Saves screenshots to help-documentation/screenshots/admin/ and /employee/

Prerequisites:
    pip install playwright
    playwright install chromium

Usage:
    # Start the app first:
    streamlit run app.py

    # Then run this script:
    python help-documentation/automation/screenshot_generator.py

    # With custom URL:
    python help-documentation/automation/screenshot_generator.py --url http://localhost:8501

    # Admin screenshots only:
    python help-documentation/automation/screenshot_generator.py --role admin

    # Employee screenshots only:
    python help-documentation/automation/screenshot_generator.py --role employee
"""

import sys
import time
import argparse
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCREENSHOTS_DIR = PROJECT_ROOT / "help-documentation" / "screenshots"

# ─────────────────────────────────────────────
# Screenshot Specifications
# ─────────────────────────────────────────────

ADMIN_SCREENSHOTS = [
    {
        "name": "employee-directory.png",
        "nav": ["Employees"],
        "tab": "Directory",
        "description": "Employee directory listing",
    },
    {
        "name": "add-employee-form.png",
        "nav": ["Employees"],
        "tab": "Add Employee",
        "description": "Add employee form",
    },
    {
        "name": "projects-master-list.png",
        "nav": ["Projects"],
        "description": "Projects master list",
    },
    {
        "name": "timesheet-admin-view.png",
        "nav": ["Timesheet"],
        "description": "Admin timesheet — all employees",
    },
    {
        "name": "reports-kpi-cards.png",
        "nav": ["Reports"],
        "description": "Reports KPI cards",
    },
    {
        "name": "import-data-overview.png",
        "nav": ["Import Data"],
        "description": "Import Data page overview",
    },
    {
        "name": "settings-lockout.png",
        "nav": ["Settings"],
        "tab": "Lockout Schedule",
        "description": "Settings — Lockout Schedule tab",
    },
    {
        "name": "settings-permissions.png",
        "nav": ["Settings"],
        "tab": "Employee Permissions",
        "description": "Settings — Employee Permissions tab",
    },
]

EMPLOYEE_SCREENSHOTS = [
    {
        "name": "timesheet-listing.png",
        "nav": ["Timesheet"],
        "description": "Employee timesheet listing",
    },
    {
        "name": "project-updates-view-only.png",
        "nav": ["Project Updates"],
        "description": "Project Updates — view-only mode",
    },
]


def capture_screenshot(page: Page, spec: dict, output_dir: Path) -> bool:
    """
    Capture a screenshot based on the specification.
    Returns True if successful, False if failed.
    """
    output_path = output_dir / spec["name"]
    description = spec.get("description", spec["name"])

    try:
        # Wait for page to settle
        page.wait_for_load_state("networkidle", timeout=10000)
        time.sleep(1)  # Extra settle time for Streamlit

        # Click tab if specified
        if spec.get("tab"):
            tab_elements = page.locator(f"text={spec['tab']}")
            if tab_elements.count() > 0:
                tab_elements.first.click()
                time.sleep(0.5)

        # Take screenshot
        page.screenshot(path=str(output_path), full_page=False)
        print(f"   ✅ Captured: {spec['name']}")
        return True

    except Exception as e:
        print(f"   ❌ Failed: {spec['name']} — {e}")
        return False


def run_capture(app_url: str, role: str, admin_creds: dict, employee_creds: dict) -> None:
    """Main capture function using Playwright."""
    if not PLAYWRIGHT_AVAILABLE:
        print("❌ Playwright is not installed.")
        print("   Run: pip install playwright && playwright install chromium")
        return

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1280, "height": 720})
        page = context.new_page()

        def login(credentials: dict) -> bool:
            """Log in to the application."""
            try:
                page.goto(app_url, timeout=30000)
                page.wait_for_load_state("networkidle", timeout=15000)
                time.sleep(2)  # Streamlit startup

                # Select username from dropdown
                username_field = page.locator("select, [data-testid='stSelectbox']").first
                if username_field.count() > 0:
                    username_field.select_option(label=credentials.get("username", ""))

                # Enter password
                password_field = page.locator("input[type='password']").first
                if password_field.count() > 0:
                    password_field.fill(credentials.get("password", ""))

                # Note: CAPTCHA requires manual solving — cannot be automated
                print("   ⚠️  CAPTCHA detected — manual intervention required")
                print("   Please solve the CAPTCHA in the browser and press Enter to continue...")
                input()

                # Click login button
                login_btn = page.locator("button:has-text('Login')").first
                if login_btn.count() > 0:
                    login_btn.click()
                    page.wait_for_load_state("networkidle", timeout=15000)
                    return True

            except Exception as e:
                print(f"   ❌ Login failed: {e}")
            return False

        # Capture admin screenshots
        if role in ("admin", "both"):
            print("\n📸 Capturing ADMIN screenshots...")
            admin_dir = SCREENSHOTS_DIR / "admin"
            admin_dir.mkdir(parents=True, exist_ok=True)

            if login(admin_creds):
                for spec in ADMIN_SCREENSHOTS:
                    # Navigate to the module
                    if spec.get("nav"):
                        nav_text = spec["nav"][0]
                        nav_link = page.locator(f"text={nav_text}").first
                        if nav_link.count() > 0:
                            nav_link.click()
                            time.sleep(1)

                    capture_screenshot(page, spec, admin_dir)
            else:
                print("   ❌ Admin login failed — skipping admin screenshots")

        # Capture employee screenshots
        if role in ("employee", "both"):
            print("\n📸 Capturing EMPLOYEE screenshots...")
            employee_dir = SCREENSHOTS_DIR / "employee"
            employee_dir.mkdir(parents=True, exist_ok=True)

            if login(employee_creds):
                for spec in EMPLOYEE_SCREENSHOTS:
                    if spec.get("nav"):
                        nav_text = spec["nav"][0]
                        nav_link = page.locator(f"text={nav_text}").first
                        if nav_link.count() > 0:
                            nav_link.click()
                            time.sleep(1)

                    capture_screenshot(page, spec, employee_dir)
            else:
                print("   ❌ Employee login failed — skipping employee screenshots")

        browser.close()
    print("\n✅ Screenshot capture complete.")
    print(f"   Saved to: {SCREENSHOTS_DIR}")


def main():
    parser = argparse.ArgumentParser(description="Capture application screenshots")
    parser.add_argument("--url", default="http://localhost:8501", help="Application URL")
    parser.add_argument("--role", choices=["admin", "employee", "both"], default="both")
    parser.add_argument("--admin-user", default="", help="Admin username")
    parser.add_argument("--admin-pass", default="", help="Admin password")
    parser.add_argument("--emp-user", default="", help="Employee username")
    parser.add_argument("--emp-pass", default="", help="Employee password")
    args = parser.parse_args()

    print("📸 Screenshot Generator — Timesheet App Help Documentation")
    print(f"   App URL: {args.url}")
    print(f"   Role: {args.role}")
    print()
    print("⚠️  NOTE: The app uses CAPTCHA for login.")
    print("   The script will pause at the CAPTCHA step for manual solving.")
    print()

    admin_creds = {"username": args.admin_user, "password": args.admin_pass}
    employee_creds = {"username": args.emp_user, "password": args.emp_pass}

    run_capture(args.url, args.role, admin_creds, employee_creds)


if __name__ == "__main__":
    main()

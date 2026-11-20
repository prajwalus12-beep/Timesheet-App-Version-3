"""
Help Banner Component
=====================
Renders a professional, contextual help notification banner across all application pages.
Provides guidance and a one-click navigation link to the interactive Help Documentation.
"""

import streamlit as st

# Contextual messages customized per page and role
PAGE_HELP_INFO = {
    "Timesheet Entries": {
        "title": "Timesheet & Leave Management",
        "employee_msg": "Unsure how to log your daily working hours, submit leave requests, or resolve validation errors? Take help from our step-by-step employee guide.",
        "admin_msg": "Need assistance managing employee timesheets, modifying past entries, or sending reminder emails? Take help from the timesheet administration guide.",
    },
    "Projects": {
        "title": "Projects Directory",
        "employee_msg": "Need guidance searching project codes, identifying lead engineers, or tracking project master information? Take help from our project guide.",
        "admin_msg": "Need guidance reviewing project master records, statuses, or tracking FMP-synced projects? Take help from our project guide.",
    },
    "Project Update": {
        "title": "Project Updates",
        "employee_msg": "Need clarification on inline cell editing, understanding yellow change highlights, or exporting status sheets? Take help from our update guide.",
        "admin_msg": "Need help managing update permissions, tracking modifications, or exporting FMP-compatible Excel reports? Take help from our guide.",
    },
    "Add Project": {
        "title": "Add Project Staging",
        "employee_msg": "Unsure how to fill staging fields, business case checkboxes, or track FMP sync status? Take help from our staging guide.",
        "admin_msg": "Need help staging new projects, managing deletions, or marking projects as added to FMP? Take help from our guide.",
    },
    "Employees": {
        "title": "Employee Management",
        "employee_msg": "Need information regarding employee directory access or profile management? Take help from our documentation.",
        "admin_msg": "Need guidance creating employee accounts, managing permissions (Add Project, Project Updates), or resetting credentials? Take help from our guide.",
    },
    "Reports": {
        "title": "Reports & Analytics",
        "employee_msg": "Need help understanding time logging metrics or report summaries? Take help from our documentation.",
        "admin_msg": "Need help applying employee/project filters, interpreting hour trends, or generating PDF management reports? Take help from our guide.",
    },
    "Import Data": {
        "title": "Data Import & Synchronization",
        "employee_msg": "Need information on system data synchronization? Take help from our documentation.",
        "admin_msg": "Unsure about required Excel column formats, foreign-key import sequence (Projects before Update Projects), or conflict resolution? Take help from our import guide.",
    },
    "Settings": {
        "title": "System Settings",
        "employee_msg": "Need information on weekly lockout hours or timesheet submission schedules? Take help from our guide.",
        "admin_msg": "Need help configuring weekly lockout days, employee permissions, reminder SMTP schedules, or public holiday exclusions? Take help from our guide.",
    },
}

DEFAULT_HELP = {
    "title": "Documentation",
    "employee_msg": "If you do not understand any form, validation rule, or workflow on this page, please take help from our comprehensive documentation.",
    "admin_msg": "If you do not understand any configuration, permission, or administrative operation on this page, please take help from our documentation.",
}


def render_help_banner(page_name: str, user: dict):
    """
    Render a professional contextual banner at the top of any page with a link
    to navigate directly to the interactive Help Documentation.
    """
    if page_name == "Help":
        return

    is_admin = user.get("role") == "admin"
    info = PAGE_HELP_INFO.get(page_name, DEFAULT_HELP)
    msg = info["admin_msg"] if is_admin else info["employee_msg"]
    title = info["title"]

    with st.container():
        col_text, col_btn = st.columns([5.5, 1.0])

        with col_text:
            st.markdown(
                f"""
                <div style="
                    background: linear-gradient(90deg, #F0FDF4 0%, #EFF6FF 100%);
                    border: 1px solid #BFDBFE;
                    border-left: 4px solid #2563EB;
                    border-radius: 8px;
                    padding: 8px 14px;
                    display: flex;
                    align-items: center;
                    gap: 12px;
                    margin-bottom: 8px;
                    min-height: 44px;
                ">
                    <span style="font-size: 20px; flex-shrink: 0;">💡</span>
                    <div style="line-height: 1.35;">
                        <div style="font-weight: 600; font-size: 13px; color: #1E3A8A;">
                            Need assistance with {title}?
                        </div>
                        <div style="font-size: 11.5px; color: #475569;">
                            {msg}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with col_btn:
            # Styled yellow pill button matching the reference screenshot
            st.markdown(
                """
                <div id="help-pill-btn-marker"></div>
                <style>
                div[data-testid="stColumn"]:has(#help-pill-btn-marker) div.stButton > button {
                    background: linear-gradient(180deg, #FBBF24 0%, #F59E0B 100%) !important;
                    background-color: #F59E0B !important;
                    color: #451A03 !important;
                    border: 2.5px solid #FDE68A !important;
                    border-radius: 9999px !important;
                    font-weight: 700 !important;
                    font-size: 14.5px !important;
                    height: 42px !important;
                    min-height: 42px !important;
                    padding: 0 16px !important;
                    box-shadow: 0 2px 6px rgba(245, 158, 11, 0.35) !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    transition: all 0.15s ease-in-out !important;
                }
                div[data-testid="stColumn"]:has(#help-pill-btn-marker) div.stButton > button:hover {
                    background: linear-gradient(180deg, #F59E0B 0%, #D97706 100%) !important;
                    background-color: #D97706 !important;
                    border-color: #FEF3C7 !important;
                    color: #260E01 !important;
                    box-shadow: 0 4px 10px rgba(217, 119, 6, 0.45) !important;
                    transform: translateY(-1px) !important;
                }
                div[data-testid="stColumn"]:has(#help-pill-btn-marker) div.stButton > button:active {
                    transform: translateY(0) !important;
                    box-shadow: 0 1px 3px rgba(217, 119, 6, 0.4) !important;
                }
                div[data-testid="stColumn"]:has(#help-pill-btn-marker) div.stButton > button p {
                    font-weight: 700 !important;
                    font-size: 14.5px !important;
                    color: #451A03 !important;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "❓  Help",
                key=f"help_nav_banner_btn_{page_name}",
                use_container_width=True,
                type="primary",
                help=f"Click to open the Help Documentation for {title}",
            ):
                st.session_state["page"] = "Help"
                st.session_state["help_initial_page"] = page_name
                st.session_state["nav_version"] = st.session_state.get("nav_version", 0) + 1
                st.rerun()

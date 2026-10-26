import streamlit as st
import pandas as pd
from database.queries import import_employees, import_projects, import_assignments, import_project_updates, import_holidays
from utils.xlsx_export import build_clean_xlsx
from utils.project_update_import_validator import validate_project_updates_import, FIELD_LABELS, FIELD_ALIASES, get_column_mapping

def get_excel_download(df):
    return build_clean_xlsx(df)

def read_excel_or_csv(uploaded_file):
    """Read File depending on extension."""
    na_vals = [
        '#N/A', '#N/A N/A', '#NA', '-1.#IND', '-1.#QNAN', '-NaN', '-nan',
        '1.#IND', '1.#QNAN', '<NA>', 'N/A', 'NULL', 'NaN', 'n/a', 'nan', 'null', ''
    ]
    if uploaded_file.name.endswith('.csv'):
        try:
            return pd.read_csv(uploaded_file, keep_default_na=False, na_values=na_vals, dtype=str)
        except UnicodeDecodeError:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, encoding='cp1252', keep_default_na=False, na_values=na_vals, dtype=str)
    else:
        return pd.read_excel(uploaded_file, keep_default_na=False, na_values=na_vals, dtype=str)



def render_import_page():
    st.subheader("Import Data", divider="blue")
    col_emp, col_proj = st.columns(2)
    col_assign, col_update = st.columns(2)
    
    with col_emp:
        st.markdown('<div class="table-container" style="padding: 20px;">', unsafe_allow_html=True)
        st.write("### 👥 Employees")
        uploaded_file = st.file_uploader("Upload Employees File", type=["xls", "xlsx", "csv"], key="emp_csv")
        if uploaded_file:
            df = read_excel_or_csv(uploaded_file)
            if st.button("Import Employees", type="primary"):
                success, msg = import_employees(df)
                st.success(msg) if success else st.error(msg)
        
        sample_emp = pd.DataFrame([["101", "John Doe", "U12345", "john.doe@example.com"]], columns=['a__Serial', 'Name', 'Slack ID', 'Email'])
        st.download_button("📥 Sample Employee Excel", get_excel_download(sample_emp), "sample_employees.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        st.info("Required: 'a__Serial', 'Name', 'Slack ID', 'Email'.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_proj:
        st.markdown('<div class="table-container" style="padding: 20px;">', unsafe_allow_html=True)
        st.write("### 🏗️ Projects")
        uploaded_file = st.file_uploader("Upload Projects File", type=["xls", "xlsx", "csv"], key="proj_csv")
        if uploaded_file:
            df = read_excel_or_csv(uploaded_file)
            if st.button("Import Projects", type="primary"):
                success, msg = import_projects(df)
                st.success(msg) if success else st.error(msg)
        
        sample_proj = pd.DataFrame([["P001", "1.1", "Website Redesign", "In progress", "Alice", "https://trello.com/b/123"]], columns=['Job No', 'Job Priority', 'Project', 'Status', 'Lead engineer', 'Trello'])
        st.download_button("📥 Sample Project Excel", get_excel_download(sample_proj), "sample_projects.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        st.info("Required: 'Job No', 'Job Priority', 'Project', 'Status', 'Lead engineer', 'Trello'. Supports decimal priority (e.g. 1.1).")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_assign:
        st.markdown('<div class="table-container" style="padding: 20px;">', unsafe_allow_html=True)
        st.write("### 🔗 Assignments")
        uploaded_file = st.file_uploader("Upload Assignments File", type=["xls", "xlsx", "csv"], key="assign_csv")
        if uploaded_file:
            df = read_excel_or_csv(uploaded_file)
            if st.button("Import Assignments", type="primary"):
                success, msg = import_assignments(df)
                st.success(msg) if success else st.error(msg)
        
        sample_assign = pd.DataFrame([["101", "P001"]], columns=['Projects_Resources::a_EmployeeID', 'Projects_Resources::a_ProjectID'])
        st.download_button("📥 Sample Assignment Excel", get_excel_download(sample_assign), "sample_assignments.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        st.info("Required: 'Projects_Resources::a_EmployeeID', 'Projects_Resources::a_ProjectID'.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col_update:
        st.markdown('<div class="table-container" style="padding: 20px;">', unsafe_allow_html=True)
        st.write("### 🔄 Update Projects")
        uploaded_file = st.file_uploader("Upload Update Projects File", type=["xls", "xlsx", "csv"], key="update_proj_csv")
        if uploaded_file:
            df = read_excel_or_csv(uploaded_file)
            # ── Check Validation when button clicked ──
            if st.button("Import Update Project", type="primary", key="btn_validate_update_proj"):
                validation = validate_project_updates_import(df)
                if validation.get("has_conflicts") or validation.get("has_manual_updates"):
                    st.session_state["show_update_preview"] = True
                    st.session_state["update_validation_data"] = validation
                else:
                    success, msg = import_project_updates(df)
                    if success:
                        st.success(msg)
                        st.session_state["import_success_msg"] = msg
                    else:
                        st.error(msg)
                    st.session_state.pop("show_update_preview", None)
                    st.session_state.pop("update_validation_data", None)

            # ── If conflicts or manual updates exist, show inline warning & preview ──
            if st.session_state.get("show_update_preview") and st.session_state.get("update_validation_data"):
                validation = st.session_state["update_validation_data"]
                mismatches = validation.get("mismatches_count", 0)
                comparison_rows = validation.get("comparison_rows", [])

                # 1. Warning Box
                st.markdown(
                    """
                    <div style="background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 12px 16px; border-radius: 6px; margin-top: 14px; margin-bottom: 14px;">
                        <p style="margin: 0; color: #991b1b; font-weight: 700; font-size: 0.95rem;">
                            ⚠️ Warning: Project Updates May Be Reset
                        </p>
                        <p style="margin: 4px 0 0 0; color: #7f1d1d; font-size: 0.88rem; line-height: 1.4;">
                            Importing this sheet may reset the project update fields to their normal/default values. Please review the fields being updated before proceeding.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if mismatches > 0:
                    st.markdown(
                        f"**{mismatches} project update field(s)** currently marked as updated do not match the imported sheet and may be overwritten or reset."
                    )
                else:
                    st.markdown(
                        "The following project update fields are currently marked as updated in the system and will be refreshed by this sheet:"
                    )

                # 2. Comparison Table
                if comparison_rows:
                    comp_df = pd.DataFrame(comparison_rows)
                    display_cols = ["Project Code", "Project Name", "Field", "Current Project Value", "Imported Sheet Value", "Status"]
                    table_df = comp_df[display_cols].copy()

                    def _style_comparison_table(row):
                        status = str(row["Status"])
                        if "Mismatch" in status or "Missing" in status:
                            return ["background-color: #fee2e2; color: #991b1b; font-weight: 500;"] * len(row)
                        return ["background-color: #f0fdf4; color: #166534;"] * len(row)

                    st.dataframe(table_df.style.apply(_style_comparison_table, axis=1), use_container_width=True, hide_index=True)

                # 3. Sheet Preview with Red Highlighted Mismatches
                st.markdown("##### 📄 Sheet Preview")
                st.caption("🔴 Cells highlighted in red show values that differ from manually updated project data.")
                
                col_mapping = get_column_mapping(df.columns)
                proj_comparisons = validation.get("project_comparisons", {})

                def _style_sheet_preview(data_df):
                    styles = pd.DataFrame("", index=data_df.index, columns=data_df.columns)
                    for idx, row in data_df.iterrows():
                        code = str(row.get('Job No') or row.get('Project Code') or row.get('Job_No') or row.get('Project_Code') or '').strip()
                        diffs = proj_comparisons.get(code, [])
                        diff_map = {d["field"]: d for d in diffs}
                        for db_f, mapped_col in col_mapping.items():
                            if mapped_col and mapped_col in styles.columns:
                                d = diff_map.get(db_f)
                                if d and not d.get("is_match", True) and d.get("is_manually_updated", False):
                                    styles.at[idx, mapped_col] = "background-color: #fca5a5; color: #7f1d1d; font-weight: bold;"
                    for uc in validation.get("unrecognised_columns", []):
                        if uc in styles.columns:
                            styles[uc] = "background-color: #fef3c7; color: #92400e;"
                    return styles

                st.dataframe(df.style.apply(_style_sheet_preview, axis=None), use_container_width=True)

                # 4. Confirmation Question and Action Buttons: Cancel and Continue
                st.markdown("---")
                st.markdown("##### Do you want to continue with the import?")
                col_btn_cancel, col_btn_continue = st.columns([1, 1.2])

                with col_btn_cancel:
                    if st.button("❌ Cancel", use_container_width=True, key="btn_cancel_update_import"):
                        st.session_state.pop("show_update_preview", None)
                        st.session_state.pop("update_validation_data", None)
                        st.info("Import cancelled. Existing project updates remain unchanged.")
                        st.rerun()

                with col_btn_continue:
                    if st.button("✅ Continue Import", type="primary", use_container_width=True, key="btn_confirm_update_import"):
                        st.session_state.pop("show_update_preview", None)
                        st.session_state.pop("update_validation_data", None)
                        success, msg = import_project_updates(df)
                        if success:
                            st.success(msg)
                            st.session_state["import_success_msg"] = msg
                        else:
                            st.error(msg)
                        st.rerun()
        
        sample_update_proj = pd.DataFrame(
            [[
                "852", "1.1", "St Paul's College Trip Payment", "Not started", "Kritika Wadhwa", 
                "https://trello.com/...", "https://slack.com/...", "https://figma.com/...", 
                "14-05-2026", "15-05-2026", "Development", "1", "1", "1", "1", "166", "117",
                "Initial scope review complete. Awaiting client sign-off."
            ]],
            columns=[
                'Job No', 'Job Priority', 'Priority', 'Search_Project', 'Lead engineer', 
                'Trello', 'Slack', 'Prototype', 'Start Date', 'Finish Date', 'Current Phase_g',
                'CheckBoxe BC', 'CheckBoxe Trello', 'CheckBoxe WA', 'CheckBoxe WS',
                'Estimated Days', 'Actual Days', 'Notes'
            ]
        )
        st.download_button("📥 Sample Update Project Excel", get_excel_download(sample_update_proj), "sample_update_projects.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        st.info("Required: 'Job No', 'Job Priority' (numeric or decimal e.g. 1.1), 'Priority' (used as Name if 'Project' is missing), 'Lead engineer'. Supports multiple aliases for Status, Phase, Dates, and Checkboxes (BC, Trello, WA, WS). Optional: 'Notes' column for project notes.")
        st.markdown('</div>', unsafe_allow_html=True)

    # --- Row 3: Holiday Import ---
    col_holiday, col_blank = st.columns(2)
    with col_holiday:
        st.markdown('<div class="table-container" style="padding: 20px;">', unsafe_allow_html=True)
        st.write("### 🏖️ Holidays")
        uploaded_file = st.file_uploader("Upload Holidays File", type=["xls", "xlsx", "csv"], key="holiday_csv")
        if uploaded_file:
            df = read_excel_or_csv(uploaded_file)
            if st.button("Import Holidays", type="primary"):
                success, msg, details = import_holidays(df)
                if success:
                    st.success(msg)
                else:
                    st.error(msg)
                    if "errors" in details:
                        with st.expander("🔍 View Row-Level Validation Errors", expanded=True):
                            for err in details["errors"]:
                                st.markdown(f"- {err}")
        sample_holiday = pd.DataFrame(
            [["2026-10-02", "Gandhi Jayanti"], ["2026-12-25", "Christmas"]],
            columns=['date', 'holiday name']
        )
        st.download_button("📥 Sample Holiday Excel", get_excel_download(sample_holiday), "sample_holidays.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
        st.info("Required: 'date' (YYYY-MM-DD or DD-MM-YYYY), 'holiday name'. Holidays apply automatically to all active employees.")
        st.markdown('</div>', unsafe_allow_html=True)

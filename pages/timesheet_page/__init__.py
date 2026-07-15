import streamlit as st
import datetime
import pandas as pd
import io
import openpyxl
from database.queries import get_timesheets, get_all_employees, get_all_projects, delete_timesheet_entry, add_timesheet_entry
from components.dialogs import entry_form_dialog, edit_form_dialog
from utils.date_helpers import get_curr_cycle_dates

def render_timesheet_page(user):
    hdr_col, btn_col1, btn_col2 = st.columns([7, 1.5, 1.5])
    with hdr_col:
        st.subheader("Timesheet Entries", divider="blue")
        st.caption("Review and manage time logs")

    emps = get_all_employees()
    current_emp_id = user.get("employee_id")
    emp_labels = {f"{r['employee_name']} ({r['employee_id']})": r['employee_id'] for _, r in emps.iterrows()}

    current_emp_name_label = next((k for k, v in emp_labels.items() if v == current_emp_id), "All")
    is_admin = user.get("role") == "admin"
    default_emp_filter = "All" if is_admin else current_emp_name_label

    # Handle reset flag BEFORE widgets are instantiated
    if st.session_state.pop('_reset_filters', False):
        st.session_state.date_range_preset = "This Week"
        st.session_state.filter_emp = default_emp_filter
        st.session_state.filter_proj = "All"

    # Initialize filters
    if 'start_date' not in st.session_state:
        st.session_state.start_date = datetime.date.today() - datetime.timedelta(days=30)
    if 'end_date' not in st.session_state:
        st.session_state.end_date = datetime.date.today()
    if 'date_range_preset' not in st.session_state:
        st.session_state.date_range_preset = "This Week"
    if 'filter_emp' not in st.session_state:
        st.session_state.filter_emp = default_emp_filter
    if 'filter_proj' not in st.session_state:
        st.session_state.filter_proj = "All"

    with st.container(border=True):
        # Dynamic ratios to minimize space when Custom Range is not active
        date_range_preset = st.session_state.get('date_range_preset', 'This Week')
        if date_range_preset == "Custom Range":
            ratios = [1.5, 2.7, 2.3, 2.3, 1.2]
        else:
            ratios = [2.5, 0.1, 3.0, 3.0, 1.4]
            
        col_preset, col_custom, col_emp, col_proj, col_clear = st.columns(ratios)
        
        with col_preset:
            date_range_option = st.selectbox("Date Range", ["This Week", "Last Week", "Current 4 Week Cycle", "Previous 4 Week Cycle", "Custom Range"], key="date_range_preset")
            today = datetime.date.today()
            start_of_this_week = today - datetime.timedelta(days=today.weekday())
            
            if date_range_option == "This Week":
                calc_start, calc_end = start_of_this_week, start_of_this_week + datetime.timedelta(days=6)
            elif date_range_option == "Last Week":
                calc_start, calc_end = start_of_this_week - datetime.timedelta(days=7), start_of_this_week - datetime.timedelta(days=1)
            elif date_range_option == "Current 4 Week Cycle":
                calc_start, calc_end = get_curr_cycle_dates(today)
            elif date_range_option == "Previous 4 Week Cycle":
                curr_start, _ = get_curr_cycle_dates(today)
                calc_start, calc_end = curr_start - datetime.timedelta(days=28), curr_start - datetime.timedelta(days=1)

        with col_custom:
            st.markdown('<div class="filter-label-phantom">&nbsp;</div>', unsafe_allow_html=True)
            if date_range_option == "Custom Range":
                sub1, sub2 = st.columns(2)
                start_date = sub1.date_input("Start", key="start_date")
                end_date = sub2.date_input("End", key="end_date")
                if end_date < start_date:
                    st.error("⚠️ End date can't be smaller than start date")
                    st.stop()
            else:
                start_date, end_date = calc_start, calc_end

        with col_emp:
            if is_admin:
                emp_options = ["All"] + list(emp_labels.keys())
                selected_emp_name = st.selectbox("Employee", emp_options, key="filter_emp")
            else:
                emp_options = [current_emp_name_label]
                selected_emp_name = st.selectbox("Employee", emp_options, disabled=True, key="filter_emp")
            
            selected_emp_id = emp_labels.get(selected_emp_name) if selected_emp_name != "All" else None

        with col_proj:
            all_projs = get_all_projects()
            all_projs['job_no_numeric'] = pd.to_numeric(all_projs['project_code'], errors='coerce')
            all_projs = all_projs.sort_values(by=['job_no_numeric', 'project_code'], ascending=[False, False])
            
            proj_options = {f"{r['project_code']} - {r['project_name']}": r['project_code'] for _, r in all_projs.iterrows()}
            selected_proj_name = st.selectbox("Project", ["All"] + list(proj_options.keys()), key="filter_proj")
            selected_proj_code = proj_options[selected_proj_name] if selected_proj_name != "All" else None
        
        with col_clear:
            st.markdown('<div class="filter-label-phantom">&nbsp;</div>', unsafe_allow_html=True)
            if st.button("🧹 Clear", use_container_width=True, key="clear_main_filters"):
                st.session_state._reset_filters = True
                st.rerun()

    # Integrated Date Range Display under the filter box
    st.caption(f"Showing records from :blue[**{start_date.strftime('%d-%m-%Y')}**] to :blue[**{end_date.strftime('%d-%m-%Y')}**]")

    # Initialize fixed multi-level sorting
    if 'ts_sort_priority' not in st.session_state:
        # Date is ALWAYS primary. Format: [('date', 'desc'), (secondary_col, order)]
        st.session_state.ts_sort_priority = [('date', 'desc')]

    def toggle_ts_sort(col):
        if col == 'date':
            # Toggle primary date sort order
            c, o = st.session_state.ts_sort_priority[0]
            new_order = "desc" if o == "asc" else "asc"
            st.session_state.ts_sort_priority[0] = ('date', new_order)
        else:
            # Handle secondary sort (Project Code or Project Name)
            if len(st.session_state.ts_sort_priority) > 1 and st.session_state.ts_sort_priority[1][0] == col:
                # Same secondary column: toggle order
                c, o = st.session_state.ts_sort_priority[1]
                new_order = "desc" if o == "asc" else "asc"
                st.session_state.ts_sort_priority[1] = (col, new_order)
            else:
                # New secondary column or first secondary: replace/add
                if len(st.session_state.ts_sort_priority) > 1:
                    st.session_state.ts_sort_priority[1] = (col, 'asc')
                else:
                    st.session_state.ts_sort_priority.append((col, 'asc'))
        st.rerun()

    def get_sort_info(col):
        for i, (c, o) in enumerate(st.session_state.ts_sort_priority):
            if c == col:
                icon = "🔼" if o == 'asc' else "🔽"
                # For Date, just show the icon. For secondary, show '2' if helpful, 
                # but following user request just the icon/arrow is usually enough.
                # Let's show (P) for Primary and (S) for Secondary or just arrows.
                label = " (P)" if i == 0 else " (S)"
                return f"{icon}{label}"
        return "↕️"

    data = get_timesheets(start_date, end_date, selected_emp_id, selected_proj_code)

    # Apply hierarchical sorting logic
    if not data.empty:
        sort_fields = []
        sort_ascending = []
        
        # Mapping UI columns to DB/Helper fields
        col_to_field = {
            'date': 'sort_date_helper',
            'project_code': 'sort_code_helper',
            'project_name': 'project_name'
        }
        
        # Prepare helper columns
        data['sort_date_helper'] = pd.to_datetime(data['date'])
        data['sort_code_helper'] = pd.to_numeric(data['project_code'], errors='coerce')
        
        for col_name, order in st.session_state.ts_sort_priority:
            field = col_to_field.get(col_name)
            if field and field in data.columns:
                sort_fields.append(field)
                sort_ascending.append(order == 'asc')
        
        if sort_fields:
            # Final tie-breaker
            sort_fields.append('id')
            sort_ascending.append(False)
            data = data.sort_values(by=sort_fields, ascending=sort_ascending)

    with btn_col1:
        st.write("")
        if user["role"] != "admin":
            if st.button("➕ Add Entry", type="primary", use_container_width=True):
                entry_form_dialog(user, emp_labels, current_emp_id)
    
    with btn_col2:
        st.write("")
        if not data.empty:
            export_df = data.copy().rename(columns={
                'project_code': 'Project_Code', 
                'emp_name': 'Emp_Name', 
                'project_name': 'Project_Name', 
                'date': 'Date', 
                'hours': 'Hours', 
                'Phase': 'Phase',
                'project_status': 'Status',
                'comment': 'Comment'
            })
            export_df['Emp_Code'] = data['emp_id']
            export_df['Date'] = pd.to_datetime(export_df['Date']).dt.strftime('%d-%m-%Y')
            phase_map = {"1": "Analysis", "2": "Design", "3": "Development", "4": "Testing", "5": "Deployement", "6": "Support"}
            export_df['Phase'] = export_df['Phase'].astype(str).map(phase_map).fillna(export_df['Phase'])
            export_df.rename(columns={'Phase': 'Phases'}, inplace=True)
            
            # Convert columns to numeric to avoid Excel "Number Stored as Text" warnings
            export_df['Emp_Code'] = pd.to_numeric(export_df['Emp_Code'], errors='coerce')
            export_df['Project_Code'] = pd.to_numeric(export_df['Project_Code'], errors='coerce')
            
            # Sort by Employee Code then Date to match screenshot
            export_df = export_df.sort_values(by=['Emp_Code', 'Date'])
            
            # Select columns in requested order
            output_df = export_df[['Date', 'Emp_Code', 'Emp_Name', 'Project_Code', 'Project_Name', 'Status', 'Phases', 'Comment', 'Hours']]
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                output_df.to_excel(writer, index=False, sheet_name='Timesheets')
                
                # Remove default pandas header styling (bold, borders)
                worksheet = writer.sheets['Timesheets']
                for cell in worksheet[1]:
                    if cell.font:
                        cell.font = openpyxl.styles.Font(bold=False)
                    if cell.border:
                        cell.border = openpyxl.styles.Border()
                
                # Auto-adjust column widths and wrap text for Comment
                for col_idx, col in enumerate(worksheet.columns, 1):
                    max_length = 0
                    column = col[0].column_letter # Get the column name
                    is_comment = False
                    for cell in col:
                        if cell.row == 1:
                            if cell.value == 'Comment':
                                is_comment = True
                        if is_comment and cell.row > 1:
                            cell.alignment = openpyxl.styles.Alignment(wrap_text=True)
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    if is_comment:
                        adjusted_width = 40
                    else:
                        adjusted_width = (max_length + 2)
                    worksheet.column_dimensions[column].width = adjusted_width
            
            export_dt = datetime.datetime.now()
            file_name = f"TS_Exp_{export_dt.strftime('%Y%m%d')}_{export_dt.strftime('%H%M')}_Rng_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.xlsx"
            
            st.download_button(
                label="📥 Export Excel", 
                data=buffer.getvalue(), 
                file_name=file_name, 
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                use_container_width=True,
                type="primary"
            )
    # Pagination & Table
    rows_per_page = 10
    if not data.empty:
        total_pages = (len(data) - 1) // rows_per_page + 1
        if "page_num" not in st.session_state: st.session_state.page_num = 1
        st.session_state.page_num = max(1, min(st.session_state.page_num, total_pages))
        
        start_idx = (st.session_state.page_num - 1) * rows_per_page
        subset = data.iloc[start_idx:start_idx + rows_per_page]

        # CSS for spacing and clear dividers
        css_style = """
        .ts-table-container { border: 1px solid #cbd5e1; border-radius: 8px; overflow: hidden; background-color: #ffffff; margin-top: 10px; }
        
        /* Header Design Restoration */
        .ts-hdr-row { 
            background-color: #f8fafc; 
            border-top: 1px solid #cbd5e1;
            border-bottom: 2px solid #e2e8f0; 
            display: flex;
            align-items: stretch;
            width: 100%;
            height: 52px;
        }
        
        .ts-hdr-col-wrap {
            flex: 1;
            border-right: 1px solid #e2e8f0;
            padding: 8px 15px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            min-width: 0;
        }
        .ts-hdr-col-wrap:last-child { border-right: none; }

        .ts-hdr-main-lbl {
            font-size: 0.72rem;
            font-weight: 700;
            color: #475569;
            text-transform: uppercase;
            display: flex;
            align-items: center;
            gap: 6px;
            line-height: 1.2;
        }
        .ts-hdr-sub-lbl {
            font-size: 0.62rem;
            font-weight: 600;
            color: #64748b;
            display: flex;
            align-items: center;
            gap: 4px;
            margin-top: 2px;
            text-transform: uppercase;
        }
        
        .ts-hdr-row { 
            background-color: #f8fafc; 
            padding: 12px 1rem; 
            border-bottom: 2px solid #e2e8f0; 
            display: flex; 
            align-items: stretch; 
            width: 100%; 
        }
        .ts-hdr-lbl { 
            font-size: 0.72rem; 
            font-weight: 700; 
            color: #475569; 
            text-transform: uppercase; 
            letter-spacing: 0.05em; 
            padding: 0 15px; 
            border-right: 1px solid #e2e8f0; 
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .ts-hdr-lbl:last-child { border-right: none; }
        .ts-hdr-sub { 
            font-size: 0.65rem; 
            font-weight: 600; 
            color: #64748b; 
            display: flex; 
            align-items: center; 
            gap: 4px; 
            margin-top: 2px; 
        }
        
        .ts-c-date { flex: 1.2; min-width: 0; }
        .ts-c-proj { flex: 3.5; min-width: 0; }
        .ts-c-emp { flex: 2.0; min-width: 0; }
        .ts-c-phase { flex: 1.5; min-width: 0; }
        .ts-c-action { flex: 1.2; min-width: 0; display: flex; align-items: center; justify-content: center; }

        /* Sorting Chip Styling */
        .stButton > button {
            transition: all 0.2s;
            border-radius: 6px !important;
        }
        [key^="sort_chip_"] button {
            font-size: 0.65rem !important;
            padding: 4px 10px !important;
            height: auto !important;
            min-height: 0 !important;
            text-transform: uppercase !important;
            font-weight: 700 !important;
        }
        .ts-entry-row { 
            padding: 1px 0;
            background-color: #cbd5e1;
            display: flex;
            align-items: stretch;
            width: 100%;
            transition: background-color 0.1s;
            border-bottom: 1px solid #e2e8f0;
        }
        .ts-entry-row:first-child { 
            border-top: none; 
        }
        .ts-entry-row:last-child { 
            border-bottom: 2px solid #cbd5e1; 
        }
        
        .ts-entry-col { padding: 0 15px; border-right: 1px solid #e2e8f0; display: flex; flex-direction: column; justify-content: center; min-width: 0; }
        .ts-entry-col:last-child { border-right: none; }
        
        .ts-entry-box { border: 1px solid #e2e8f0; border-radius: 6px; padding: 8px 12px; min-height: 38px; display: block; background-color: #ffffff; font-size: 0.85rem; color: #334155; margin-bottom: 6px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05); width: 100%; line-height: 20px; }
        .ts-entry-box-emp { background-color: #f1f5f9; border-color: #e2e8f0; color: #475569; }
        .ts-entry-box:last-child { margin-bottom: 0; }
        
        /* Precision Center Icons in Buttons */
        [data-testid="stBaseButton-secondary"] div, [data-testid="stBaseButton-primary"] div { display: flex !important; align-items: center !important; justify-content: center !important; width: 100%; height: 100%; }
        [data-testid="stIconMaterial"] { line-height: 1 !important; display: inline-flex !important; align-items: center !important; justify-content: center !important; font-size: 20px !important; margin: 0 !important; }
        
        .ts-action-lnk { display: none; }
        
        /* Clean Row Divider Spacing */
        [data-testid="stVerticalBlock"] > div:has(.ts-entry-row) {
            margin-bottom: 12px !important;
            padding-bottom: 0 !important;
        }
        
        /* Basic Responsiveness */
        @media (max-width: 768px) {
            .ts-hdr-row { display: none; }
            .ts-entry-row { flex-direction: column; padding: 15px; }
            .ts-entry-col { border-right: none !important; border-bottom: 1px solid #e2e8f0; padding: 10px 0; }
            .ts-entry-col:last-child { border-bottom: none; }
        }
        """.replace("\n", " ")
        
        st.markdown(f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0" /><style>{css_style}</style>', unsafe_allow_html=True)
        
        # Start Table Container
        st.markdown('<div class="ts-table-container">', unsafe_allow_html=True)
            
        # Sorting Controls Above Table
        st.markdown('<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px; padding: 5px 15px; background: #f8fafc; border-radius: 8px; border: 1px solid #e2e8f0;">'
                    '<span style="font-size: 0.75rem; font-weight: 700; color: #64748b; text-transform: uppercase;">Sort By:</span>', unsafe_allow_html=True)
        
        s_col1, s_col2, s_col3, s_col_rest = st.columns([1.2, 2.2, 2.2, 4.4])
        
        with s_col1:
            # Date is always primary
            d_order = next((o for c, o in st.session_state.ts_sort_priority if c == 'date'), 'desc')
            d_icon = "▼" if d_order == 'desc' else "▲"
            if st.button(f"DATE {d_icon}", key="sort_chip_date", use_container_width=True, help="Toggle Date Sorting"):
                toggle_ts_sort('date')
                
        with s_col2:
            # Project Code (Secondary)
            c_active = len(st.session_state.ts_sort_priority) > 1 and st.session_state.ts_sort_priority[1][0] == 'project_code'
            c_order = st.session_state.ts_sort_priority[1][1] if c_active else ""
            c_icon = (" ▲" if c_order == 'asc' else " ▼") if c_active else ""
            btn_label = f"PROJECT CODE{c_icon}"
            if st.button(btn_label, key="sort_chip_code", use_container_width=True, help="Sort by Project Code within Date", type="primary" if c_active else "secondary"):
                toggle_ts_sort('project_code')

        with s_col3:
            # Project Name (Secondary)
            n_active = len(st.session_state.ts_sort_priority) > 1 and st.session_state.ts_sort_priority[1][0] == 'project_name'
            n_order = st.session_state.ts_sort_priority[1][1] if n_active else ""
            n_icon = (" ▲" if n_order == 'asc' else " ▼") if n_active else ""
            btn_label = f"PROJECT NAME{n_icon}"
            if st.button(btn_label, key="sort_chip_name", use_container_width=True, help="Sort by Project Name within Date", type="primary" if n_active else "secondary"):
                toggle_ts_sort('project_name')
        
        st.markdown('</div>', unsafe_allow_html=True)

        # Start Table Container
        st.markdown('<div class="ts-table-container">', unsafe_allow_html=True)
            
        # Restore Original Header Row HTML
        st.markdown(f"""
            <div class="ts-hdr-row">
                <div class="ts-c-date ts-hdr-lbl">
                    DATE<br>
                    <div class="ts-hdr-sub">PROJECT CODE</div>
                </div>
                <div class="ts-c-proj ts-hdr-lbl">
                    PROJECT NAME<br>
                    <div class="ts-hdr-sub">
                        <span class="material-symbols-outlined" style="font-size:14px; vertical-align:middle;">message</span> COMMENT
                    </div>
                </div>
                <div class="ts-c-emp ts-hdr-lbl">
                    EMPLOYEE<br>
                    <div class="ts-hdr-sub">
                        <span class="material-symbols-outlined" style="font-size:14px; vertical-align:middle;">insights</span> STATUS
                    </div>
                </div>
                <div class="ts-c-phase ts-hdr-lbl">
                    PHASE<br>
                    <div class="ts-hdr-sub">
                        <span class="material-symbols-outlined" style="font-size:14px; vertical-align:middle;">schedule</span> HOURS
                    </div>
                </div>
                <div class="ts-c-action ts-hdr-lbl" style="text-align:center; border-right:none;">ACTIONS</div>
            </div>
        """, unsafe_allow_html=True)

        start_of_week = today - datetime.timedelta(days=today.weekday())
        end_of_week = start_of_week + datetime.timedelta(days=6)
        phase_labels = {"1": "Analysis", "2": "Design", "3": "Development", "4": "Testing", "5": "Deployement", "6": "Support"}

        for idx, row in subset.iterrows():
            r_date_val = row['date']
            if isinstance(r_date_val, str): r_date_val = datetime.datetime.strptime(r_date_val, '%Y-%m-%d').date()

            # Row Container
            st.markdown('<div class="ts-entry-row">', unsafe_allow_html=True)
            r_col_date, r_col_proj, r_col_emp, r_col_phase, r_col_action = st.columns([1.2, 3.5, 2.0, 1.5, 1.2])
            
            with r_col_date:
                st.markdown('<div class="ts-entry-col" style="border-right: 1px solid #e2e8f0; height: 100%;">', unsafe_allow_html=True)
                st.markdown(f'<div class="ts-entry-box" style="margin-bottom: 4px;"><b>{r_date_val.strftime("%Y-%m-%d")}</b></div>', unsafe_allow_html=True)
                st.markdown(f'<div class="ts-entry-box" style="margin-bottom:0; font-size: 0.8rem; color: #64748b; background-color: #f8fafc;">{row["project_code"]}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with r_col_proj:
                st.markdown('<div class="ts-entry-col" style="border-right: 1px solid #e2e8f0; height: 100%;">', unsafe_allow_html=True)
                st.markdown(f'<div class="ts-entry-box" title="{row["project_name"]}" style="margin-bottom: 4px;">{row["project_name"]}</div>', unsafe_allow_html=True)
                comment_val = row.get('comment', '') if pd.notna(row.get('comment')) else '—'
                st.markdown(f'<div class="ts-entry-box" title="{comment_val}" style="font-style: italic; color: #64748b; font-size: 0.8rem; margin-bottom:0;">{comment_val}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with r_col_emp:
                st.markdown('<div class="ts-entry-col" style="border-right: 1px solid #e2e8f0; height: 100%;">', unsafe_allow_html=True)
                st.markdown(f'<div class="ts-entry-box ts-entry-box-emp" title="{row["emp_name"]}" style="margin-bottom: 4px;">{row["emp_name"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="ts-entry-box" style="margin-bottom:0;">{row["project_status"]}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with r_col_phase:
                st.markdown('<div class="ts-entry-col" style="border-right: 1px solid #e2e8f0; height: 100%;">', unsafe_allow_html=True)
                p_val = str(row.get("Phase", "1"))
                p_text = phase_labels.get(p_val, p_val)
                st.markdown(f'<div class="ts-entry-box" style="margin-bottom: 4px;">{p_text}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="ts-entry-box" style="margin-bottom:0;">{row["hours"]:.2f} hrs</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            
            with r_col_action:
                st.markdown('<div class="ts-entry-col" style="border-right: none; height: 100%; display: flex; align-items: center; justify-content: center;">', unsafe_allow_html=True)
                # Actions
                if start_of_week <= r_date_val <= end_of_week:
                    act_edit, act_del, act_dup = st.columns([1, 1, 1], gap="small")
                    if act_edit.button(":material/edit:", key=f"edit_btn_{row['id']}", help="Edit Record"):
                        edit_form_dialog(row.to_dict(), emp_labels, current_emp_id, user["role"])
                    if act_del.button(":material/delete:", key=f"del_btn_{row['id']}", help="Delete"):
                        delete_timesheet_entry(row['id'])
                        st.rerun()
                    if act_dup.button(":material/content_copy:", key=f"dup_btn_{row['id']}", help="Duplicate"):
                        add_timesheet_entry(
                            row['emp_id'], row['emp_name'], row['project_code'], 
                            row['project_name'], row['date'], row['hours'], 
                            row['Phase'], row['project_status'], row.get('comment', '')
                        )
                        st.rerun()
                else:
                    act_lock, act_dup = st.columns([1, 1], gap="small")
                    act_lock.button(":material/lock:", key=f"lock_btn_{row['id']}", disabled=True, help="Locked")
                    if act_dup.button(":material/content_copy:", key=f"dup_btn_{row['id']}", help="Duplicate"):
                        add_timesheet_entry(
                            row['emp_id'], row['emp_name'], row['project_code'], 
                            row['project_name'], row['date'], row['hours'], 
                            row['Phase'], row['project_status'], row.get('comment', '')
                        )
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True) # End ts-entry-row

        # End Table Container
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Pagination Controls — Centered and dynamically sized
        st.write("")
        num_page_btns = min(5, total_pages)
        # Ratios: large spacer on left to push buttons to the right
        ratios = [10, 0.6] + [0.6] * num_page_btns + [0.6, 0.1]
        cols = st.columns(ratios, gap="small")
        
        p_prev = cols[1]
        page_btns = cols[2 : 2 + num_page_btns]
        p_next = cols[-2]

        if p_prev.button("◀", key="pg_prev", disabled=(st.session_state.page_num == 1), use_container_width=True):
            st.session_state.page_num -= 1
            st.rerun()
            
        for i in range(num_page_btns):
            if page_btns[i].button(str(i+1), key=f"pg_{i+1}", type="primary" if st.session_state.page_num == i+1 else "secondary", use_container_width=True):
                st.session_state.page_num = i+1
                st.rerun()
                
        if p_next.button("▶", key="pg_next", disabled=(st.session_state.page_num == total_pages), use_container_width=True):
            st.session_state.page_num += 1
            st.rerun()
    else: st.info("No records found.")

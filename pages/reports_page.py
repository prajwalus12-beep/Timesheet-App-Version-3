import streamlit as st
import datetime
import pandas as pd
import json
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode, JsCode
from database.queries import get_all_employees, get_timesheets, get_all_projects
from utils.date_helpers import get_curr_cycle_dates

def render_reports_page(user):
    hdr_col, exp_col = st.columns([6.5, 3.5])
    with hdr_col:
        st.subheader("Timesheet Reports", divider="blue")
        st.caption("Employee timesheet summary and statistics")
    # Handle reset flag BEFORE widgets are instantiated
    if st.session_state.pop('_reset_report_filters', False):
        st.session_state.report_emp = "All Employees"
        st.session_state.report_proj = "All Projects"
        st.session_state.report_date_range_picker = "This Week"
        st.session_state.report_start_date = datetime.date.today() - datetime.timedelta(days=30)
        st.session_state.report_end_date = datetime.date.today()

    exp_btn_placeholder = exp_col.empty()

    # Initialize custom dates if not present
    if 'report_start_date' not in st.session_state:
        st.session_state.report_start_date = datetime.date.today() - datetime.timedelta(days=30)
    if 'report_end_date' not in st.session_state:
        st.session_state.report_end_date = datetime.date.today()

    range_opt = st.session_state.get('report_date_range_picker', 'This Week')
    
    with st.container(border=True):
        # Dynamic ratios to accommodate Custom Range inputs - giving more space to Clear button
        if range_opt == "Custom Range":
            ratios = [1.8, 1.8, 1.8, 3.4, 1.2]
        else:
            ratios = [2.5, 2.5, 2.5, 0.1, 1.2]
        
        c1, c2, c3, c4, c5 = st.columns(ratios)
        
        with c1:
            report_emps = get_all_employees(exclude_admin=True)
            report_emp_options = {f"{r['employee_name']} ({r['employee_id']})": r['employee_id'] for _, r in report_emps.iterrows()}
            sel_emp_name = st.selectbox("Employee", ["All Employees"] + list(report_emp_options.keys()), key="report_emp")
            sel_emp_id = report_emp_options[sel_emp_name] if sel_emp_name != "All Employees" else None
        
        with c2:
            all_projs = get_all_projects()
            proj_options = {f"{r['project_code']} - {r['project_name']}": r['project_code'] for _, r in all_projs.iterrows()}
            sel_proj_name = st.selectbox("Project", ["All Projects"] + list(proj_options.keys()), key="report_proj")
            sel_proj_code = proj_options[sel_proj_name] if sel_proj_name != "All Projects" else None
            
        with c3:
            range_opt = st.selectbox("Date Range", ["This Week", "Last Week", "Current 4 Week Cycle", "Previous 4 Week Cycle", "Custom Range"], key="report_date_range_picker")
            today = datetime.date.today()
            start_week = today - datetime.timedelta(days=today.weekday())
            
            if range_opt == "This Week": r_start_calc, r_end_calc = start_week, start_week + datetime.timedelta(days=6)
            elif range_opt == "Last Week": r_start_calc, r_end_calc = start_week - datetime.timedelta(days=7), start_week - datetime.timedelta(days=1)
            elif range_opt == "Current 4 Week Cycle": r_start_calc, r_end_calc = get_curr_cycle_dates(today)
            elif range_opt == "Previous 4 Week Cycle":
                cs, _ = get_curr_cycle_dates(today)
                r_start_calc, r_end_calc = cs - datetime.timedelta(days=28), cs - datetime.timedelta(days=1)
            else:
                r_start_calc, r_end_calc = None, None
        
        with c4:
            st.markdown('<div class="filter-label-phantom">&nbsp;</div>', unsafe_allow_html=True)
            if range_opt == "Custom Range":
                sub1, sub2 = st.columns(2)
                r_start = sub1.date_input("Start", key="report_start_date")
                r_end = sub2.date_input("End", key="report_end_date")
                if r_end < r_start:
                    st.error("⚠️ End date can't be smaller than start date")
                    st.stop()
            else:
                r_start, r_end = r_start_calc, r_end_calc
        
        with c5:
            st.markdown('<div class="filter-label-phantom">&nbsp;</div>', unsafe_allow_html=True)
            if st.button("🧹 Clear", key="clear_report_filters_btn", use_container_width=True):
                st.session_state._reset_report_filters = True
                st.rerun()

    all_employees = get_all_employees(exclude_admin=True)
    if sel_emp_id: all_employees = all_employees[all_employees['employee_id'] == sel_emp_id]
    ts_data = get_timesheets(r_start, r_end, sel_emp_id, sel_proj_code)

    if not all_employees.empty:
        num_days = (r_end - r_start).days + 1
        all_dates = [r_start + datetime.timedelta(days=i) for i in range(num_days)]
        day_cols = [d.strftime("%d %a").upper() for d in all_dates]
        
        # Build pivot
        pivot_rows = []
        emp_day_hours = {}
        if not ts_data.empty:
            ts_data['date'] = pd.to_datetime(ts_data['date']).dt.date
            for _, row in ts_data.iterrows():
                eid, d, h = row['emp_id'], row['date'], float(row['hours'])
                if eid not in emp_day_hours: emp_day_hours[eid] = {}
                emp_day_hours[eid][d] = emp_day_hours[eid].get(d, 0) + h

        all_weekdays = [d for d in all_dates if d.weekday() < 5]
        for _, emp in all_employees.iterrows():
            eid, ename = emp['employee_id'], emp['employee_name']
            hours = emp_day_hours.get(eid, {})
            r_dict = {'EMP Id': eid, 'Employee Name': ename}
            wt, df = 0.0, 0
            for d, c_name in zip(all_dates, day_cols):
                h = hours.get(d, 0.0)
                r_dict[c_name] = h if h > 0 else None
                if d.weekday() < 5:
                    wt += h
                    if h > 0: df += 1
            r_dict['Total Hours'] = wt
            r_dict['Status'] = '✅' if len(all_weekdays) > 0 and df == len(all_weekdays) else '❌'
            pivot_rows.append(r_dict)

        df_pivot = pd.DataFrame(pivot_rows)
        
        # Calculate Metrics
        total_emps = len(df_pivot)
        completed_count = len(df_pivot[df_pivot['Status'] == '✅'])
        uncompleted_count = total_emps - completed_count
        total_hours = df_pivot['Total Hours'].sum()

        st.write("### 📊 Summary")
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        col_s1.metric("Total Employees", total_emps)
        col_s2.metric("Completed", completed_count)
        col_s3.metric("Uncompleted", uncompleted_count)
        col_s4.metric("Total Hours (Mon-Fri)", f"{total_hours:.1f}h")
        
        st.write("### 📋 Employee Details")
        st.caption(f"Showing records from :blue[**{r_start.strftime('%d-%m-%Y')}**] to :blue[**{r_end.strftime('%d-%m-%Y')}**]")
        gb = GridOptionsBuilder.from_dataframe(df_pivot)
        gb.configure_default_column(sortable=False, filterable=False, resizable=True)
        
        # Row style: highlight uncompleted rows in pink
        row_style_jscode = JsCode("""
        function(params) {
            if (params.data && params.data['Status'] && params.data['Status'].indexOf('\u274c') !== -1) {
                return {backgroundColor: '#ffe4e6', color: '#991b1b'};
            }
            return {};
        }
        """)

        # Weekend cell style: light yellow only when value exists
        weekend_cell_style = JsCode("""
        function(params) {
            if (params.value !== null && params.value !== undefined && params.value !== 0) {
                return {backgroundColor: '#fefce8', color: '#78350f', fontWeight: 'bold'};
            }
            return {};
        }
        """)

        gb.configure_column("EMP Id", pinned='left', width=90, suppressSizeToFit=True)
        gb.configure_column("Employee Name", sortable=True, pinned='left', width=200, suppressSizeToFit=True)

        for col in day_cols:
            if 'SAT' in col or 'SUN' in col:
                gb.configure_column(col, width=100, cellStyle=weekend_cell_style)
            else:
                gb.configure_column(col, width=100)

        gb.configure_column("Total Hours", width=120)
        gb.configure_column("Status", width=120)
        gb.configure_grid_options(getRowStyle=row_style_jscode)

        grid_opts = gb.build()
        
        # Suppress the filter/menu icon from all column headers
        grid_opts['defaultColDef']['suppressMenu'] = True
        for col_def in grid_opts.get('columnDefs', []):
            col_def['suppressMenu'] = True
        
        AgGrid(
            df_pivot, 
            gridOptions=grid_opts, 
            height=500, 
            theme='alpine',
            allow_unsafe_jscode=True,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            update_mode=GridUpdateMode.MODEL_CHANGED
        )
        
        
        # Export buttons
        with exp_btn_placeholder.container():
            st.download_button(
                "📥 Export CSV", 
                df_pivot.to_csv(index=False), 
                "report.csv", 
                "text/csv", 
                use_container_width=True,
                key="report_csv_download_btn",
                type="primary"
            )
            
            # JSON Export for Admin: Incomplete Timesheets
            if user["role"] == "admin":
                incomplete_logs = []
                
                for _, emp in all_employees.iterrows():
                    eid, ename, slack_id = emp['employee_id'], emp['employee_name'], emp.get('slack_id', '-')
                    if eid == 'admin': continue
                    
                    emp_hours_map = emp_day_hours.get(eid, {})
                    # Identify all incomplete days (h < 8) in the selected range
                    incomplete_dates = []
                    for d in all_dates:
                        if d.weekday() >= 5: continue # Skip Weekends (Sat=5, Sun=6)
                        h = emp_hours_map.get(d, 0.0)
                        if h < 8.0:
                            incomplete_dates.append(d.strftime('%d-%m-%Y'))
                    
                    if incomplete_dates:
                        dates_str = ", ".join(incomplete_dates)
                        msg = f"Hello {ename}, you have incomplete timesheet entries for following dates: {dates_str}. Please complete your timesheet."
                        
                        incomplete_logs.append({
                            "Slack Id": slack_id,
                            "Message": msg
                        })
                
                if incomplete_logs:
                    st.download_button(
                        "📥 Export JSON (Incomplete)", 
                        json.dumps(incomplete_logs, indent=2), 
                        "incomplete_timesheets.json", 
                        "application/json",
                        use_container_width=True,
                        key="report_json_download_btn",
                        type="primary"
                    )
    else: st.info("No employees found.")

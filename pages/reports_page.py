import streamlit as st
import datetime
import pandas as pd
import json
import io

from database.queries import get_all_employees, get_timesheets, get_all_projects, get_all_holidays, get_project_reports
from utils.date_helpers import get_curr_cycle_dates
from utils.chart_helpers import (
    convert_hours_to_days,
    format_days_display,
    format_project_employee_initials,
    wrap_project_name,
    format_date_short,
    build_project_metadata_text,
    build_charts_pdf_report
)

@st.cache_data(ttl=60, show_spinner=False)
def _cached_project_reports():
    try:
        return get_project_reports()
    except Exception:
        return pd.DataFrame()

def render_reports_page(user):
    hdr_col, exp_col = st.columns([6.5, 3.5])
    with hdr_col:
        st.subheader("Timesheet Reports", divider="blue")
        st.caption("Employee timesheet summary and statistics")
    # Handle reset flag BEFORE widgets are instantiated
    if st.session_state.pop('_reset_report_filters', False):
        st.session_state.report_emp = []
        st.session_state.report_proj = []
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
            if 'status' in report_emps.columns:
                report_emps = report_emps[report_emps['status'].astype(int) == 1]
            if 'emp_type' in report_emps.columns:
                report_emps = report_emps[report_emps['emp_type'] != 'Intern']
            report_emp_options = {f"{r['employee_name']} ({r['employee_id']})": r['employee_id'] for _, r in report_emps.iterrows()}
            sel_emp_names = st.multiselect("Employee", list(report_emp_options.keys()), placeholder="All Employees", key="report_emp")
            sel_emp_ids = [report_emp_options[n] for n in sel_emp_names]
        
        with c2:
            all_projs = get_all_projects()
            all_projs['job_no_numeric'] = pd.to_numeric(all_projs['project_code'], errors='coerce')
            all_projs = all_projs.sort_values(by=['job_no_numeric', 'project_code'], ascending=[False, False])
            
            proj_options = {f"{r['project_code']} - {r['project_name']}": r['project_code'] for _, r in all_projs.iterrows()}
            sel_proj_names = st.multiselect("Project", list(proj_options.keys()), placeholder="All Projects", key="report_proj")
            sel_proj_codes = [proj_options[n] for n in sel_proj_names]
            
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
    if 'status' in all_employees.columns:
        all_employees = all_employees[all_employees['status'].astype(int) == 1]
    if 'emp_type' in all_employees.columns:
        all_employees = all_employees[all_employees['emp_type'] != 'Intern']
    if sel_emp_ids:
        all_employees = all_employees[all_employees['employee_id'].astype(str).isin([str(e) for e in sel_emp_ids])]
        
    ts_data = get_timesheets(r_start, r_end, None, None)
    if not ts_data.empty:
        if sel_emp_ids:
            ts_data = ts_data[ts_data['emp_id'].astype(str).isin([str(e) for e in sel_emp_ids])]
        if sel_proj_codes:
            ts_data = ts_data[ts_data['project_code'].astype(str).isin([str(p) for p in sel_proj_codes])]

    if not all_employees.empty:
        num_days = (r_end - r_start).days + 1
        all_dates = [r_start + datetime.timedelta(days=i) for i in range(num_days)]
        day_cols = [d.strftime("%d %a").upper() for d in all_dates]
        
        # Fetch active holidays in this range
        h_df = get_all_holidays()
        holiday_date_map = {}
        if not h_df.empty:
            h_df['_hdate'] = pd.to_datetime(h_df['holiday_date']).dt.date
            h_in_range = h_df[(h_df['_hdate'] >= r_start) & (h_df['_hdate'] <= r_end)]
            holiday_date_map = {row['_hdate']: str(row['holiday_name']) for _, row in h_in_range.iterrows()}
        holiday_dates = set(holiday_date_map.keys())
        
        # Build pivot
        pivot_rows = []
        emp_day_data = {}
        if not ts_data.empty:
            ts_data['date'] = pd.to_datetime(ts_data['date']).dt.date
            for _, row in ts_data.iterrows():
                eid = str(row['emp_id'])
                d = row['date']
                p_code = str(row.get('project_code', '')).strip()
                p_name = str(row.get('project_name', '')).strip()
                p_status = str(row.get('project_status', '')).strip()
                p_phase = str(row.get('Phase', '')).strip()
                try:
                    h = float(row.get('hours', 0) or 0)
                except (ValueError, TypeError):
                    h = 0.0

                if eid not in emp_day_data:
                    emp_day_data[eid] = {}
                if d not in emp_day_data[eid]:
                    emp_day_data[eid][d] = {
                        'work_hours': 0.0,
                        'leave_text': None,
                        'holiday_text': None
                    }

                is_leave = p_code.startswith('LEAVE-') or p_status in ('Leave', 'Approved Leave') or p_phase == 'Leave'
                is_holiday = p_code.startswith('HOLIDAY') or p_status == 'Holiday' or p_phase == 'Holiday'

                if is_leave:
                    leave_label = p_name if (p_name and p_name.lower() not in ('nan', 'none', '')) else "Leave"
                    emp_day_data[eid][d]['leave_text'] = leave_label
                elif is_holiday:
                    h_label = p_name if (p_name and p_name.lower() not in ('nan', 'none', '')) else "Holiday"
                    emp_day_data[eid][d]['holiday_text'] = h_label
                    holiday_dates.add(d)
                else:
                    emp_day_data[eid][d]['work_hours'] += h

        all_weekdays = [d for d in all_dates if d.weekday() < 5 and d not in holiday_dates]
        for _, emp in all_employees.iterrows():
            eid = str(emp['employee_id'])
            ename = emp['employee_name']
            emp_records = emp_day_data.get(eid, {})
            r_dict = {'EMP Id': eid, 'Employee Name': ename}
            wt, df = 0.0, 0
            for d, c_name in zip(all_dates, day_cols):
                rec = emp_records.get(d, {'work_hours': 0.0, 'leave_text': None, 'holiday_text': None})
                work_h = rec['work_hours']
                leave_txt = rec['leave_text']
                holiday_txt = rec['holiday_text']

                if work_h > 0:
                    r_dict[c_name] = int(work_h) if float(work_h).is_integer() else round(work_h, 2)
                    if d.weekday() < 5:
                        wt += work_h
                        df += 1
                elif d in holiday_date_map:
                    # Recognized company holiday
                    r_dict[c_name] = holiday_date_map[d]
                elif holiday_txt:
                    # Holiday entry from timesheet
                    r_dict[c_name] = holiday_txt
                elif leave_txt:
                    # Approved leave: display leave as text, do not count hours in total
                    r_dict[c_name] = leave_txt
                    if d.weekday() < 5:
                        df += 1
                else:
                    r_dict[c_name] = None

            r_dict['Total Hours'] = int(wt) if float(wt).is_integer() else round(wt, 2)
            r_dict['Status'] = '✅' if len(all_weekdays) > 0 and df >= len(all_weekdays) else '❌'
            pivot_rows.append(r_dict)

        df_pivot = pd.DataFrame(pivot_rows, dtype=object)
        
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

        # ── Charts & Analytics ────────────────────────────────────────────────
        try:
            import plotly.graph_objects as go

            # Prepare chart data from the filtered timesheet data
            # Exclude LEAVE and HOLIDAY project codes from chart data
            chart_data = pd.DataFrame()
            if not ts_data.empty:
                chart_data = ts_data[
                    ~ts_data['project_code'].astype(str).str.startswith(('LEAVE-', 'HOLIDAY'))
                ].copy()
                chart_data['hours'] = pd.to_numeric(chart_data['hours'], errors='coerce').fillna(0)

            # Only display the charts section if there is actual data to plot
            if not chart_data.empty and chart_data['hours'].sum() > 0:
                chart_hdr_col, chart_exp_col = st.columns([7, 3])
                with chart_hdr_col:
                    st.write("### 📈 Charts & Analytics")
                # chart_exp_col used later after charts are built

                # Display charts stacked vertically for maximum readability
                # ── Shared Project Data for Charts ────────────────────────────
                pr_df = _cached_project_reports()
                pr_map = {}
                pr_name_map = {}
                if pr_df is not None and not pr_df.empty:
                    for _, pr_r in pr_df.iterrows():
                        c = str(pr_r.get('project_code', '')).strip()
                        n = str(pr_r.get('project_name', '')).strip().lower()
                        d = pr_r.to_dict()
                        if c:
                            pr_map[c] = d
                        if n:
                            pr_name_map[n] = d

                project_records = []
                for p_name, group in chart_data.groupby('project_name'):
                    h = group['hours'].sum()
                    if h <= 0:
                        continue
                    days = convert_hours_to_days(h)
                    codes = [str(c).strip() for c in group['project_code'].dropna().unique() if str(c).strip()]
                    p_code = codes[0] if codes else ""
                    emp_names = group['emp_name'].dropna().unique().tolist()
                    ts_statuses = [str(s).strip() for s in group['project_status'].dropna().unique() if str(s).strip() and str(s).strip().lower() not in ('nan', 'none', '_', '')]
                    ts_status = ts_statuses[-1] if ts_statuses else ""

                    pr_rec = pr_map.get(p_code)
                    if not pr_rec:
                        pr_rec = pr_name_map.get(str(p_name).strip().lower(), {})

                    start_date = pr_rec.get('start_date') if pr_rec else None
                    end_date = pr_rec.get('end_date') if pr_rec else None
                    status = (pr_rec.get('status') if pr_rec and pd.notna(pr_rec.get('status')) else None) or ts_status

                    project_records.append({
                        'project_name': p_name,
                        'project_code': p_code,
                        'hours': h,
                        'days': days,
                        'emp_names': emp_names,
                        'initials': format_project_employee_initials(emp_names),
                        'start_date': start_date,
                        'end_date': end_date,
                        'start_str': format_date_short(start_date),
                        'end_str': format_date_short(end_date),
                        'status': status
                    })

                sorted_proj_records = sorted(project_records, key=lambda x: x['days'], reverse=True)
                total_project_days = sum(p['days'] for p in sorted_proj_records)

                # ── Pie Chart: Distribution by Project (Days) ──────────────────
                def _pie_legend_label(project_name, meta_txt, wrap_width=42):
                    wrapped = wrap_project_name(project_name, width=wrap_width, html=True)
                    return f"{wrapped}<br>{meta_txt}"

                pie_rows = []
                pie_source = sorted_proj_records
                other_days = 0.0
                if len(sorted_proj_records) > 10:
                    pie_source = sorted_proj_records[:10]
                    other_days = sum(p['days'] for p in sorted_proj_records[10:])

                for p in pie_source:
                    pct = (p['days'] / total_project_days * 100) if total_project_days > 0 else 0
                    meta_txt = build_project_metadata_text(
                        p['days'], pct, p['initials'], p['start_str'], p['end_str'], p['status']
                    )
                    pie_rows.append({
                        'project_name': p['project_name'],
                        'display_name': p['project_name'],
                        'days': p['days'],
                        'pct': pct,
                        'metadata_text': meta_txt,
                        'legend_label': _pie_legend_label(p['project_name'], meta_txt),
                    })
                if other_days > 0:
                    other_pct = (other_days / total_project_days * 100) if total_project_days > 0 else 0
                    other_meta = f"{format_days_display(other_days)} ({other_pct:.1f}%)"
                    pie_rows.append({
                        'project_name': 'Other',
                        'display_name': 'Other',
                        'days': other_days,
                        'pct': other_pct,
                        'metadata_text': other_meta,
                        'legend_label': _pie_legend_label('Other', other_meta),
                    })

                pie_df = pd.DataFrame(pie_rows)

                pie_customdata = []
                legend_line_count = 0
                for _, row in pie_df.iterrows():
                    d_str = format_days_display(row['days'])
                    pct = row['pct']
                    p_name = str(row['project_name'])
                    meta = str(row['metadata_text'])
                    pie_customdata.append([d_str, pct, p_name, meta])
                    legend_line_count += max(2, 1 + str(row['legend_label']).count('<br>'))

                # ── Pie Chart: Left column, Legend: Right column ───────────────
                # This matches the PDF layout exactly: donut on the left,
                # rich text legend panel on the right.
                num_pie_slices = len(pie_df)

                # Pastel palette matching the PDF
                PIE_COLORS = [
                    '#8dd3c7','#ffffb3','#bebada','#fb8072','#80b1d3',
                    '#fdb462','#b3de69','#fccde5','#d9d9d9','#bc80bd','#ccebc5'
                ]

                # Build the pie figure (occupies the left column)
                fig_pie = go.Figure(go.Pie(
                    labels=pie_df['project_name'],   # plain text — no HTML
                    values=pie_df['days'],
                    hole=0.40,
                    customdata=pie_customdata,
                    textinfo='percent',
                    textposition='inside',
                    insidetextorientation='horizontal',
                    texttemplate='<b>%{percent:.1%}</b>',
                    textfont=dict(size=13, color='#1e293b'),
                    hovertemplate=(
                        '<b>%{customdata[2]}</b><br>'
                        '%{customdata[3]}'
                        '<extra></extra>'
                    ),
                    marker=dict(
                        colors=PIE_COLORS[:num_pie_slices],
                        line=dict(color='#ffffff', width=2)
                    ),
                    showlegend=False,
                    sort=False,   # Other stays last
                ))

                fig_pie.update_layout(
                    title=dict(
                        text='<b>Total Value by Project</b>',
                        font=dict(size=17, color='#1e293b'),
                        x=0,
                        xanchor='left',
                    ),
                    margin=dict(l=10, r=10, t=50, b=10),
                    height=460,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    uniformtext=dict(mode='hide', minsize=10),
                    autosize=True,
                )

                # Build legend HTML items (matching PDF: bold name + metadata line)
                legend_items_html = []
                for i, row in pie_df.iterrows():
                    color = PIE_COLORS[i % len(PIE_COLORS)]
                    proj_name = str(row['project_name'])
                    meta = str(row['metadata_text'])
                    legend_items_html.append(
                        f'<div style="display:flex;align-items:flex-start;gap:8px;margin-bottom:8px;">'
                        f'<div style="width:13px;height:13px;min-width:13px;background:{color};'
                        f'border:1px solid #bbb;border-radius:2px;margin-top:3px;"></div>'
                        f'<div>'
                        f'<div style="font-weight:700;font-size:0.8rem;color:#1e293b;'
                        f'line-height:1.3;word-break:break-word;">{proj_name}</div>'
                        f'<div style="font-size:0.72rem;color:#475569;line-height:1.4;'
                        f'word-break:break-word;">{meta}</div>'
                        f'</div></div>'
                    )

                # Side-by-side: pie left (55%), legend right (45%)
                pie_col, legend_col = st.columns([55, 45])
                with pie_col:
                    st.plotly_chart(fig_pie, use_container_width=True, key="report_pie_chart")
                with legend_col:
                    st.markdown(
                        '<div style="background:#fff;border:1px solid #e2e8f0;border-radius:8px;'
                        'padding:14px 16px;margin-top:4px;max-height:480px;overflow-y:auto;">'
                        + "".join(legend_items_html)
                        + '</div>',
                        unsafe_allow_html=True
                    )

                st.markdown("<br>", unsafe_allow_html=True)

                # ── Bar Chart: Total Value by Project (Days) ──────────────────
                if project_records:
                    bar_top20 = sorted_proj_records[:20]
                    bar_total_days = sum(p['days'] for p in bar_top20)
                    bar_rows = []
                    for p in bar_top20:
                        pct = (p['days'] / bar_total_days * 100) if bar_total_days > 0 else 0
                        meta_txt = build_project_metadata_text(
                            p['days'], pct, p['initials'], p['start_str'], p['end_str'], p['status']
                        )
                        wrapped = wrap_project_name(p['project_name'], width=38, html=True)
                        bar_rows.append({
                            'project_name': p['project_name'],
                            'project_code': p['project_code'],
                            'hours': p['hours'],
                            'days': p['days'],
                            'pct': pct,
                            'initials': p['initials'],
                            'start_str': p['start_str'],
                            'end_str': p['end_str'],
                            'status': p['status'],
                            'metadata_text': meta_txt,
                            'wrapped_name': wrapped,
                        })
                    bar_df = pd.DataFrame(bar_rows)

                    # Customdata for hover: [full_name, formatted_days, metadata_text]
                    bar_customdata = list(zip(
                        bar_df['project_name'],
                        [format_days_display(d) for d in bar_df['days']],
                        bar_df['metadata_text']
                    ))

                    fig_bar = go.Figure(go.Bar(
                        x=bar_df['days'],
                        y=bar_df['project_name'],
                        orientation='h',
                        customdata=bar_customdata,
                        cliponaxis=False,
                        marker=dict(
                            color=bar_df['days'],
                            colorscale='Blues',
                            showscale=False,
                            line=dict(color='rgba(58,134,255,0.5)', width=0.5)
                        ),
                        hovertemplate=(
                            '<b>%{customdata[0]}</b><br>'
                            '%{customdata[2]}'
                            '<extra></extra>'
                        ),
                        text=None,
                        textposition='none',
                    ))

                    # Plotly annotation per bar — shows full metadata text
                    # matching the PDF: "6.9d (13.0%) — SD, SH | Start: 31 Jul | End: 31 Jul | Complete"
                    bar_max_days = bar_df['days'].max() if not bar_df.empty else 1.0
                    bar_annotations = []
                    for _, brow in bar_df.iterrows():
                        bar_annotations.append(dict(
                            x=brow['days'],
                            y=brow['project_name'],
                            text=f"  {brow['metadata_text']}",
                            showarrow=False,
                            xanchor='left',
                            yanchor='middle',
                            font=dict(size=11, color='#1e293b'),
                            xref='x',
                            yref='y',
                        ))

                    # Estimate characters in the longest annotation to set x-axis range.
                    # At ~6.5px per char, font-size 11 in a ~1200px wide container:
                    # 1px ≈ (bar_max / chart_width_px) data-units.
                    # We use a conservative 4x multiplier so text never clips.
                    max_meta_len = max((len(str(r)) for r in bar_df['metadata_text']), default=40)
                    # Each char ≈ 0.13 * bar_max_days of horizontal space (empirical)
                    text_width_units = max_meta_len * 0.13 * (bar_max_days / 10)
                    x_range_max = bar_max_days + max(bar_max_days * 2.2, text_width_units * 1.5, 1.0)

                    bar_height = max(500, len(bar_df) * 42 + 100)
                    fig_bar.update_layout(
                        title=dict(
                            text='<b>Total Value by Project (Top 20)</b>',
                            font=dict(size=18, color='#1e293b'),
                            x=0,
                            xanchor='left',
                        ),
                        xaxis=dict(
                            title=dict(text='Days', font=dict(size=13, color='#475569')),
                            gridcolor='#f1f5f9',
                            zeroline=False,
                            tickfont=dict(size=11, color='#64748b'),
                            range=[0, x_range_max],
                            automargin=True,
                        ),
                        yaxis=dict(
                            autorange='reversed',
                            tickfont=dict(size=11, color='#1e293b'),
                            showgrid=False,
                            automargin=True,
                        ),
                        annotations=bar_annotations,
                        margin=dict(l=20, r=20, t=55, b=50),
                        height=bar_height,
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)',
                        bargap=0.35,
                        autosize=True,
                    )
                    st.plotly_chart(fig_bar, use_container_width=True, key="report_bar_chart")
                else:
                    st.info("No project data available for the selected filters.")
                    bar_df = pd.DataFrame()

                # ── Export Charts as PDF (ReportLab server-side, zero Chrome/Kaleido) ──
                with chart_exp_col:
                    st.markdown('<div style="margin-top:1.6rem"></div>', unsafe_allow_html=True)
                    try:
                        fname = f"charts_{r_start.strftime('%d%m%Y')}_{r_end.strftime('%d%m%Y')}.pdf"
                        pdf_bytes = build_charts_pdf_report(
                            r_start,
                            r_end,
                            pie_df,
                            total_project_days,
                            bar_df
                        )
                        st.download_button(
                            label="📄 Export PDF",
                            data=pdf_bytes,
                            file_name=fname,
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    except Exception as _pdf_err:
                        st.error(f"⚠️ PDF generation failed: {_pdf_err}")
            else:
                st.info("No project data available for the selected filters.")



        except ImportError:
            st.warning("⚠️ Charts require the `plotly` library. Run `pip install plotly` to enable them.")
        except Exception as _chart_err:
            st.warning(f"⚠️ Charts could not be rendered: {_chart_err}")

        st.write("### 📋 Employee Details")
        st.caption(f"Showing records from :blue[**{r_start.strftime('%d-%m-%Y')}**] to :blue[**{r_end.strftime('%d-%m-%Y')}**]")
        def style_table(styler):
            # Row style for uncompleted rows
            def row_style(row):
                if '\u274c' in str(row.get('Status', '')) or '❌' in str(row.get('Status', '')):
                    return ['background-color: #ffe4e6; color: #991b1b'] * len(row)
                return [''] * len(row)
            
            styler = styler.apply(row_style, axis=1)
            
            # Weekend styling
            weekend_cols = [c for c in day_cols if 'SAT' in c or 'SUN' in c]
            def weekend_style(val):
                if pd.notna(val) and val != 0 and str(val).strip() != '':
                    return 'background-color: #fefce8; color: #78350f; font-weight: bold'
                return ''
            
            if weekend_cols:
                styler = styler.map(weekend_style, subset=weekend_cols)
                
            # Cell-level styling for Holidays and Leaves across day columns
            holiday_names_set = set(holiday_date_map.values())
            def cell_holiday_or_leave_style(val):
                if isinstance(val, str) and val not in ('✅', '❌', ''):
                    lower_val = val.lower()
                    if 'leave' in lower_val:
                        return 'background-color: #fef3c7; color: #92400e; font-weight: bold'
                    if val in holiday_names_set or 'holiday' in lower_val:
                        return 'background-color: #f5f3ff; color: #6d28d9; font-weight: bold; font-style: italic'
                return ''
            
            if day_cols:
                if hasattr(styler, 'map'):
                    styler = styler.map(cell_holiday_or_leave_style, subset=day_cols)
                else:
                    styler = styler.applymap(cell_holiday_or_leave_style, subset=day_cols)
                
            return styler

        styled_df = df_pivot.style.pipe(style_table)
        st.dataframe(styled_df, use_container_width=True, height=500, hide_index=True)
        
        
        # Export buttons
        with exp_btn_placeholder.container():
            with st.popover("📥 Export Options", use_container_width=True):
                excel_export = df_pivot.copy()
                if 'Status' in excel_export.columns:
                    excel_export['Status'] = excel_export['Status'].replace({'✅': 'Complete', '❌': 'Incomplete'})
                
                from utils.xlsx_export import build_clean_xlsx, build_styled_summary_xlsx
                # Collect weekday column names (excluding holidays) to highlight missing hours
                weekday_col_names = {day_cols[i] for i, d in enumerate(all_dates) if d.weekday() < 5 and d not in holiday_dates}
                if not excel_export.empty:
                    xlsx_bytes = build_styled_summary_xlsx(excel_export, weekday_col_names=weekday_col_names, sheet_name='Summary')
                else:
                    xlsx_bytes = build_styled_summary_xlsx(pd.DataFrame(), sheet_name='Summary')
                
                st.download_button(
                    "📊 Export Summary (Excel)", 
                    xlsx_bytes, 
                    f"report_summary_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx", 
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", 
                    use_container_width=True,
                    key="report_excel_summary_download_btn"
                )
                
                # Excel export for Phase Breakdown
                if not ts_data.empty:
                    phase_inv_map = {"1": "Analysis", "2": "Design", "3": "Development", "4": "Testing", "5": "Deployment", "6": "Support"}
                    df_export = ts_data[~ts_data['project_code'].astype(str).str.startswith(('LEAVE-', 'HOLIDAY'))].copy()
                    df_export['Phase'] = df_export['Phase'].astype(str).map(phase_inv_map).fillna(df_export['Phase'])
                    df_export['hours'] = pd.to_numeric(df_export['hours'], errors='coerce').fillna(0)
                    df_export.rename(columns={'project_name': 'Row Labels', 'Phase': 'Column Labels', 'hours': 'Sum of Hours'}, inplace=True)
                    
                    pivot_export = pd.pivot_table(
                        df_export, 
                        values='Sum of Hours', 
                        index='Row Labels', 
                        columns='Column Labels', 
                        aggfunc='sum', 
                        margins=True, 
                        margins_name='Grand Total'
                    )
                    
                    # Flatten the pivot table layout to make it simple
                    pivot_export = pivot_export.reset_index()
                    pivot_export.columns.name = None
                    
                    # Replace NaN with None so blank cells are truly empty in Excel
                    pivot_export = pivot_export.where(pivot_export.notna(), other=None)
                    
                    # Remove decimals if whole number
                    def _format_val(v):
                        if isinstance(v, (int, float)) and pd.notna(v):
                            return int(v) if float(v).is_integer() else round(v, 2)
                        return v
                    
                    if hasattr(pivot_export, 'map'):
                        pivot_export = pivot_export.map(_format_val)
                    else:
                        pivot_export = pivot_export.applymap(_format_val)
                    
                    xlsx_phase_bytes = build_clean_xlsx(pivot_export, sheet_name='Sheet1')
                else:
                    xlsx_phase_bytes = build_clean_xlsx(pd.DataFrame(), sheet_name='Sheet1')
                
                st.download_button(
                    "📈 Export By Phase (Excel)", 
                    xlsx_phase_bytes, 
                    f"report_phase_breakdown_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.xlsx", 
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                    key="report_excel_download_btn"
                )

                # JSON Export for Admin: Incomplete Timesheets
                if user["role"] == "admin":
                    incomplete_logs = []
                    
                    for _, emp in all_employees.iterrows():
                        eid, ename, slack_id = emp['employee_id'], emp['employee_name'], emp.get('slack_id', '-')
                        if eid == 'admin': continue
                        
                        emp_records = emp_day_data.get(eid, {})
                        # Identify all incomplete days in the selected range, skipping weekends, holidays, and approved leaves
                        incomplete_dates = []
                        for d in all_dates:
                            if d.weekday() >= 5: continue # Skip Weekends (Sat=5, Sun=6)
                            if d in holiday_dates: continue # Skip Company Holidays
                            rec = emp_records.get(d, {})
                            if rec.get('leave_text') or rec.get('holiday_text'): continue # Skip Approved Leaves & Holidays
                            work_h = rec.get('work_hours', 0.0)
                            if work_h < 8.0:
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
                            "📥 Export Incomplete Logs (JSON)", 
                            json.dumps(incomplete_logs, indent=2), 
                            f"incomplete_timesheets_{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json", 
                            "application/json",
                            use_container_width=True,
                            key="report_json_download_btn"
                        )
    else: st.info("No employees found.")

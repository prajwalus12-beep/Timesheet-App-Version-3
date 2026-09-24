import sys
path = 'components/dialogs.py'
with open(path, 'r', encoding='utf-8') as f:
    content = f.read()

target = '''    col_start, col_end = st.columns(2)
    with col_start:
        start_date = st.date_input("Start Date", datetime.date.today(), format="DD-MM-YYYY", key="leave_start_modal")
    with col_end:
        end_date = st.date_input("End Date", datetime.date.today(), format="DD-MM-YYYY", key="leave_end_modal")
        
    reason = st.text_area("Reason / Notes", placeholder="e.g. Personal errand / Doctor appointment", key="leave_reason_modal")'''

replacement = '''    if leave_type == "Holiday":
        holidays_df = get_all_holidays(include_inactive=False)
        if holidays_df.empty:
            st.warning("No holidays configured in the system.")
            st.stop()
        
        holiday_options = {f"{r['holiday_name']} ({r['holiday_date']})": r for _, r in holidays_df.iterrows()}
        selected_holiday_label = st.selectbox("Select Holiday", list(holiday_options.keys()), key="holiday_select_modal")
        selected_holiday = holiday_options[selected_holiday_label]
        
        start_date = pd.to_datetime(selected_holiday['holiday_date']).date()
        end_date = start_date
        reason = selected_holiday['holiday_name']
        st.info(f"Holiday Date: {start_date.strftime('%d-%m-%Y')}")
    else:
        col_start, col_end = st.columns(2)
        with col_start:
            start_date = st.date_input("Start Date", datetime.date.today(), format="DD-MM-YYYY", key="leave_start_modal")
        with col_end:
            end_date = st.date_input("End Date", datetime.date.today(), format="DD-MM-YYYY", key="leave_end_modal")
            
        reason = st.text_area("Reason / Notes", placeholder="e.g. Personal errand / Doctor appointment", key="leave_reason_modal")'''

if target in content:
    content = content.replace(target, replacement)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Replaced target 1 successfully')
else:
    print('Target 1 not found')

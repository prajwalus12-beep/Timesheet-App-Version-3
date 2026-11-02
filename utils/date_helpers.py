import datetime

def get_curr_cycle_dates(target_date):
    """Calculate the 4-week cycle start and end dates for a given date."""
    target_monday = target_date - datetime.timedelta(days=target_date.weekday())
    year_start = datetime.date(target_monday.year, 1, 1)
    first_monday = year_start
    while first_monday.weekday() != 0:
        first_monday += datetime.timedelta(days=1)
    if target_monday < first_monday:
        year_prev = target_monday.year - 1
        year_start = datetime.date(year_prev, 1, 1)
        first_monday = year_start
        while first_monday.weekday() != 0:
            first_monday += datetime.timedelta(days=1)
    weeks_since = (target_monday - first_monday).days // 7
    cycle_start_week = (weeks_since // 4) * 4
    start_date = first_monday + datetime.timedelta(weeks=cycle_start_week)
    end_date = start_date + datetime.timedelta(days=27)
    return start_date, end_date

def format_date_display(date_obj):
    """Format date for display in the UI (DD-MM-YYYY)."""
    if isinstance(date_obj, str):
        date_obj = datetime.datetime.strptime(date_obj, '%Y-%m-%d').date()
    return date_obj.strftime("%d-%m-%Y")


def calculate_report_date_range(filter_type, custom_start=None, custom_end=None, reference_date=None):
    """
    Calculate the date range for report generation based on filter type.
    
    Parameters:
    -----------
    filter_type : str
        One of: 'this_week', 'last_week', 'current_cycle', 'previous_cycle', 'custom'
    custom_start : date, optional
        Start date for custom range (required if filter_type is 'custom')
    custom_end : date, optional
        End date for custom range (required if filter_type is 'custom')
    reference_date : date, optional
        Reference date for calculations (defaults to today)
    
    Returns:
    --------
    tuple : (start_date, end_date)
    """
    if reference_date is None:
        reference_date = datetime.date.today()
    
    # Get Monday of current week
    start_of_week = reference_date - datetime.timedelta(days=reference_date.weekday())
    
    if filter_type == 'this_week':
        # Monday to Sunday of current week
        return start_of_week, start_of_week + datetime.timedelta(days=6)
    
    elif filter_type == 'last_week':
        # Previous week (Monday to Sunday)
        last_week_start = start_of_week - datetime.timedelta(days=7)
        return last_week_start, last_week_start + datetime.timedelta(days=6)
    
    elif filter_type == 'current_cycle':
        # Current 4-week cycle
        return get_curr_cycle_dates(reference_date)
    
    elif filter_type == 'previous_cycle':
        # Previous 4-week cycle
        curr_start, _ = get_curr_cycle_dates(reference_date)
        return curr_start - datetime.timedelta(days=28), curr_start - datetime.timedelta(days=1)
    
    elif filter_type == 'custom':
        # Custom date range
        if custom_start is None or custom_end is None:
            raise ValueError("Custom date range requires both start and end dates")
        
        # Parse if strings
        if isinstance(custom_start, str):
            custom_start = datetime.datetime.strptime(custom_start, '%Y-%m-%d').date()
        if isinstance(custom_end, str):
            custom_end = datetime.datetime.strptime(custom_end, '%Y-%m-%d').date()
        
        return custom_start, custom_end
    
    else:
        raise ValueError(f"Invalid filter type: {filter_type}")


def get_date_range_display_name(filter_type, custom_start=None, custom_end=None):
    """Get human-readable name for date range filter."""
    if filter_type == 'this_week':
        return 'This Week'
    elif filter_type == 'last_week':
        return 'Last Week'
    elif filter_type == 'current_cycle':
        return 'Current 4-Week Cycle'
    elif filter_type == 'previous_cycle':
        return 'Previous 4-Week Cycle'
    elif filter_type == 'custom' and custom_start and custom_end:
        start_str = format_date_display(custom_start)
        end_str = format_date_display(custom_end)
        return f'Custom ({start_str} to {end_str})'
    else:
        return 'Unknown'

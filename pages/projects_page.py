import streamlit as st
import datetime
import pandas as pd
import io
from database.queries import get_project_reports


@st.cache_data(ttl=60, show_spinner=False)
def _cached_project_reports():
    return get_project_reports()

def _prepare_projects_list(df):
    """Convert DataFrame rows to JSON-serialisable dicts for the React component."""
    projects_list = []
    for _, row in df.iterrows():
        record = {}
        for col in df.columns:
            val = row[col]
            if pd.isna(val) or str(val).strip().lower() in ('nan', 'none', 'nat', ''):
                record[col] = None
            elif hasattr(val, 'isoformat'):
                record[col] = val.isoformat()
            elif col in ['start_date', 'end_date']:
                try:
                    record[col] = pd.to_datetime(val).date().isoformat()
                except Exception:
                    record[col] = str(val)
            elif isinstance(val, bool):
                record[col] = val
            else:
                if col == 'priority' and val is not None:
                    try:
                        f_val = float(val)
                        record[col] = str(int(f_val)) if f_val == int(f_val) else str(val)
                    except (ValueError, TypeError):
                        record[col] = str(val)
                else:
                    record[col] = str(val) if val is not None else None
        projects_list.append(record)
    return projects_list

def render_projects_page():
    st.subheader("Projects", divider="blue")
    
    df = _cached_project_reports()
    
    if df.empty:
        st.info("No projects found.")
        return

    # 1. Prepare data for the React component
    projects_list = _prepare_projects_list(df)

    lead_engineers = sorted(set(
        str(e).strip() for e in df['lead_engineer'].dropna().unique() 
        if str(e).strip() and str(e).strip().lower() != 'nan'
    ))
    
    status_options = [
        "Not started", "Awaiting Info", "At Beta", "In progress",
        "In testing", "Complete", "To be deployed", "Duplicate - Closed", "Ongoing"
    ]

    # 2. Render the React component in compact/read-only mode
    from components.project_update_react import project_update_component
    
    project_update_component(
        projects=projects_list,
        lead_engineers=lead_engineers,
        current_user=st.session_state.get("user", {}).get("employee_name", ""),
        user_role=st.session_state.get("user", {}).get("role", "employee"),
        phase_options=[], # Not needed in compact mode
        status_options=status_options,
        read_only=True,
        is_compact=True,
        key="projects_v1_react"
    )

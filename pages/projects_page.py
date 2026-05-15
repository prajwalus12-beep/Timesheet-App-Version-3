import streamlit as st
import datetime
import pandas as pd
import io
from database.queries import get_all_projects


@st.cache_data(ttl=60, show_spinner=False)
def _cached_all_projects():
    return get_all_projects()

def render_projects_page():
    st.subheader("Projects", divider="blue")
    
    projs = _cached_all_projects()
    
    if projs.empty:
        st.info("No projects found.")
        return

    # 1. Prepare data for the React component
    projects_list = []
    for _, row in projs.iterrows():
        record = {
            'project_code': str(row['project_code']),
            'project_name': str(row['project_name']),
            'status': str(row['status']) if pd.notna(row['status']) else None,
            'priority': str(row['priority']) if pd.notna(row['priority']) else None,
            'lead_engineer': str(row['lead_engineer']) if pd.notna(row['lead_engineer']) else None,
            'trello_link': str(row['trello_link']) if pd.notna(row['trello_link']) else None,
            # Fill missing v2 columns with None
            'start_date': None, 'end_date': None, 'phase': None,
            'prototype_link': None, 'slack_link': None, 'estimated_days': None,
            'checkbox_bc': None, 'checkbox_trello': None, 'checkbox_wa': None, 'checkbox_ws': None
        }
        projects_list.append(record)

    lead_engineers = sorted(set(
        str(e).strip() for e in projs['lead_engineer'].dropna().unique() 
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

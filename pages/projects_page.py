import streamlit as st
import datetime
from database.queries import get_all_projects

def render_projects_page():
    col_title, col_export = st.columns([7, 1.5])
    with col_title: st.subheader("Projects", divider="blue")
    
    projs = get_all_projects()
    with col_export:
        if not projs.empty:
            st.download_button("📥 Export CSV", projs.to_csv(index=False), f"projects_{datetime.date.today()}.csv", "text/csv", use_container_width=True)
    
    st.write("### 🏗️ Project List")
    if not projs.empty:
        st.markdown('<div class="table-container">', unsafe_allow_html=True)
        st.markdown('<div class="table-header"><div style="flex: 1;">Job No</div><div style="flex: 3.5;">Project Name</div><div style="flex: 2;">Status</div><div style="flex: 3.5;"></div></div>', unsafe_allow_html=True)
        for _, row in projs.iterrows():
            st.markdown('<div class="table-row">', unsafe_allow_html=True)
            c1, c2, c3, _ = st.columns([1, 3.5, 2, 3.5])
            c1.markdown(f'<div class="table-cell"><b>{row["project_code"]}</b></div>', unsafe_allow_html=True)
            p_name = row["project_name"]
            disp = (p_name[:30] + '..') if len(p_name) > 30 else p_name
            c2.markdown(f'<div class="table-cell" title="{p_name}">{disp}</div>', unsafe_allow_html=True)
            c3.markdown(f'<div class="table-cell">{row.get("status", "")}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else: st.info("No projects found.")

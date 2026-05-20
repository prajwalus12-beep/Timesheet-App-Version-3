"""Python wrapper for the Project Update React custom component."""
import os
import streamlit.components.v1 as components

# When built (production), serve from the build folder
_RELEASE = True

if _RELEASE:
    _parent_dir = os.path.dirname(os.path.abspath(__file__))
    _build_dir = os.path.join(_parent_dir, "frontend", "build")
    _component_func = components.declare_component(
        "project_update_react", path=_build_dir
    )
else:
    # During development, connect to the React dev server
    _component_func = components.declare_component(
        "project_update_react", url="http://localhost:3001"
    )


def project_update_component(projects, lead_engineers, employees=None, current_user="", user_role="employee", phase_options=None, status_options=None, read_only=False, is_compact=False, key=None):
    """
    Render the React-based Project Update table.

    Parameters
    ----------
    projects : list[dict]
        List of project dicts from the database.
    lead_engineers : list[str]
        Sorted list of unique lead engineer names.
    current_user : str, optional
        Name of the currently logged-in user to set as default filter.
    user_role : str, optional
        Role of the user ('admin' or 'employee').
    phase_options : list[str], optional
        Phase dropdown options.
    status_options : list[str], optional
        Status dropdown options.
    read_only : bool, optional
        If True, prevents editing in the UI.
    is_compact : bool, optional
        If True, renders a simplified report view.
    key : str, optional
        Streamlit widget key.

    Returns
    -------
    dict or None
        Action payload from React, e.g.:
        {"action": "save", "edits": {"1001": {"project_name": "New Name"}}}
        {"action": "export", "type": "all"}
    """
    if phase_options is None:
        phase_options = ["Analysis", "Design", "Development", "Testing", "Deployment", "Support"]
    if status_options is None:
        status_options = ["In progress", "Complete", "On hold", "Cancelled"]

    component_value = _component_func(
        projects=projects,
        lead_engineers=lead_engineers,
        employees=employees or [],
        current_user=current_user,
        user_role=user_role,
        phase_options=phase_options,
        status_options=status_options,
        read_only=read_only,
        is_compact=is_compact,
        key=key,
        default=None,
    )
    return component_value

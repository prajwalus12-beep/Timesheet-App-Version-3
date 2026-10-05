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


def project_update_component(projects, lead_engineers, employees=None, current_user="", user_role="employee", phase_options=None, status_options=None, read_only=False, is_compact=False, is_add_mode=False, key=None):
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
        is_add_mode=is_add_mode,
        key=key,
        default=None,
    )
    return component_value

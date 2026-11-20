"""Python wrapper for the Help Documentation React custom component."""
import os
import streamlit.components.v1 as components

# When built (production), serve from the build folder
_RELEASE = True

if _RELEASE:
    _parent_dir = os.path.dirname(os.path.abspath(__file__))
    _build_dir = os.path.join(_parent_dir, "frontend", "build")
    _component_func = components.declare_component(
        "help_react", path=_build_dir
    )
else:
    # During development, connect to the React dev server
    _component_func = components.declare_component(
        "help_react", url="http://localhost:3002"
    )


def help_component(docs, user_role="employee", user_name="", initial_doc_id="", key=None):
    """
    Render the React-based Help Documentation component.

    Parameters
    ----------
    docs : dict
        Dict with keys "admin" and "employee", each containing a list of document dicts:
        {"id": str, "title": str, "filename": str, "content": str, "category": str}
    user_role : str
        "admin" or "employee"
    user_name : str
        Logged in username
    initial_doc_id : str, optional
        Document ID to display initially
    key : str, optional
        Streamlit widget key
    """
    return _component_func(
        docs=docs,
        user_role=user_role,
        user_name=user_name,
        initial_doc_id=initial_doc_id,
        key=key,
        default=None,
    )

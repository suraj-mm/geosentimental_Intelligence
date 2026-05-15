"""
globe_component.py — Streamlit custom component wrapper for the Globe.gl frontend.
Passes region_sentiments dict to the globe so points can be colored by sentiment.
"""

import os
import streamlit.components.v1 as components

_FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "globe_frontend")

_globe_component_func = components.declare_component(
    "globe_component",
    path=_FRONTEND_DIR,
)


def render_globe(region_sentiments: dict = None, key: str = "globe") -> str | None:
    """
    Renders the interactive Globe.gl component inside Streamlit.

    Args:
        region_sentiments: dict mapping region name → avg sentiment score [-1, 1].
                           Used to color-code globe points.
        key: Streamlit component key.

    Returns:
        The name of the clicked region (str), or None if nothing clicked yet.
    """
    return _globe_component_func(
        region_sentiments=region_sentiments or {},
        key=key,
        default=None,
    )

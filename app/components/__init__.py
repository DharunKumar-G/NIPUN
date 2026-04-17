"""Shared page utilities — setup_page() and render_footer() called by every page."""
import sys
from pathlib import Path

# Ensure project root is on sys.path (needed when components/__init__ is imported
# as a side-effect of a page load rather than via a streamlit run call).
_root = str(Path(__file__).resolve().parent.parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st

CSS_PATH = Path(__file__).parent.parent / "styles" / "custom.css"


def setup_page(title: str = "NIPUN Compass", layout: str = "wide") -> None:
    st.set_page_config(
        page_title=f"{title} · NIPUN Compass",
        page_icon="🧭",
        layout=layout,
        initial_sidebar_state="expanded",
    )
    if CSS_PATH.exists():
        st.markdown(f"<style>{CSS_PATH.read_text()}</style>", unsafe_allow_html=True)


def render_footer() -> None:
    st.markdown("---")
    st.caption("**NIPUN Compass** · Data: ASER Rural 2008–2022 (asercentre.org)")

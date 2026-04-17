"""Shared page setup utility — call setup_page() at the top of every page."""
from pathlib import Path
import streamlit as st

CSS_PATH = Path(__file__).parent.parent / "styles" / "custom.css"


def setup_page(title: str = "NIPUN Compass", layout: str = "wide"):
    st.set_page_config(
        page_title=f"{title} · NIPUN Compass",
        page_icon="🧭",
        layout=layout,
        initial_sidebar_state="expanded",
    )
    if CSS_PATH.exists():
        st.markdown(f"<style>{CSS_PATH.read_text()}</style>", unsafe_allow_html=True)

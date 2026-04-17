"""
NIPUN Compass — entry point.
Section 8.2: app opens on Priority Queue, Bihar, latest year, above the fold.
"""
import sys
from pathlib import Path

# Ensure project root is on sys.path so 'from app.xxx import' works
# regardless of where `streamlit run app/main.py` is invoked from.
_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

import streamlit as st

st.switch_page("pages/1_Priority_Queue.py")

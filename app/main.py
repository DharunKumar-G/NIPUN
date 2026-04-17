"""NIPUN Compass — landing page."""
import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

from app.components import setup_page, render_footer
setup_page("NIPUN Compass")

import streamlit as st

st.markdown(
    """
    <div style='text-align:center;padding:2rem 0 1rem'>
      <h1 style='color:#1F2937;font-size:2.4rem;margin:0'>🧭 NIPUN Compass</h1>
      <p style='color:#64748B;font-size:1.1rem;margin-top:0.5rem'>
        Data-driven school prioritisation for State Education Departments
      </p>
    </div>
    """,
    unsafe_allow_html=True,
)

cols = st.columns(2, gap="large")
pages = [
    ("🎯", "Priority Queue",  "pages/1_Priority_Queue.py",  "Which 20 schools need BEOs this week?"),
    ("🔬", "School Diagnosis","pages/2_School_Diagnosis.py", "Deep-dive into any school's learning gaps"),
    ("📋", "Interventions",   "pages/3_Interventions.py",   "Evidence-based playbooks for BEOs"),
    ("📊", "Tracker",         "pages/4_Tracker.py",         "Track visit outcomes over time"),
    ("📅", "Monthly Review",  "pages/5_Monthly_Review.py",  "Cluster-level trend report for DEOs"),
    ("🗺️", "School Clusters", "pages/6_School_Clusters.py", "Geographic cluster analysis"),
]
for i, (icon, title, page_path, desc) in enumerate(pages):
    with cols[i % 2]:
        st.page_link(
            page_path,
            label=f"**{icon} {title}**\n\n{desc}",
            use_container_width=True,
        )

st.divider()
st.caption("**NIPUN Compass** · Data: ASER Rural 2019–2023 · asercentre.org")

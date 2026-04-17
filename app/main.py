"""
NIPUN Compass — The Monday-morning tool for District Education Officers.

Entrypoint: streamlit run app/main.py
"""

import streamlit as st

st.set_page_config(
    page_title="NIPUN Compass",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Inline CSS (loaded once here, applies globally) ─────────────────────────
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .block-container { padding-top: 1.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Landing copy ─────────────────────────────────────────────────────────────
st.title("NIPUN Compass")
st.caption("The Monday-morning tool for District Education Officers.")

st.markdown(
    """
**District Education Officers in low-performing states receive ASER reports every 2 years
but have no tool to translate district-level learning data into school-level action plans.**
This means they spend hours manually scanning spreadsheets to build priority lists that are
already outdated, and interventions end up reactive and poorly targeted — leading to the same
states (Bihar, UP, Rajasthan) showing up at the bottom of every ASER cycle.

---

**NIPUN Compass** turns 200-page ASER reports into a weekly school-visit list, a diagnosis
for each failing school, and an intervention matched to your block budget — so DEOs stop
reacting to 2-year-old data and start acting on it.

Use the sidebar to navigate to a feature.
"""
)

col1, col2, col3 = st.columns(3)
with col1:
    st.info("**Send your BEOs here this week**\nPriority Queue — Feature 1")
with col2:
    st.info("**Has this school gotten better or worse?**\nSchool Diagnosis — Feature 2")
with col3:
    st.info("**What worked in similar schools?**\nIntervention Recommender — Feature 3")

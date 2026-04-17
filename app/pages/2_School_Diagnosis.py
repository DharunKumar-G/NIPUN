"""
Feature 2 — School Diagnosis (Diagnosis)
DEO question: For each of those schools, what specifically is broken?

Acceptance criteria:
- Click a school → opens detail view
- Shows grade × subject × level heatmap for this school
- 3-year trend line vs district average vs state average
- Auto-generated paragraph (template-based, not LLM — see diagnosis_generator.py)
- "Copy diagnosis to report" button (plain text)
- All charts Plotly and respond to hover
"""
from app.components import setup_page
setup_page("Has this school gotten better or worse?")

import streamlit as st
import pandas as pd
from app.services.data_loader import (
    get_states, get_districts, load_schools, get_latest_year, get_school_list
)
from app.services.priority_scorer import compute_priority, _years_declining
from app.services.forecaster import school_trajectory
from app.components.diagnosis_generator import generate_diagnosis, diagnosis_as_plaintext
from app.components.charts import trend_chart, heatmap_grade_subject

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Select a School")
    states = get_states()
    default_state = "Bihar" if "Bihar" in states else states[0]
    state = st.selectbox("State", states, index=states.index(default_state))

    districts = get_districts(state)
    district = st.selectbox("District", districts)

    school_list = get_school_list(state, district)
    if school_list.empty:
        st.warning("No schools found.")
        st.stop()

    # Allow pre-selection via session state (from Feature 1 deep-link)
    default_idx = 0
    if "selected_school" in st.session_state:
        matches = school_list[school_list["school_code"] == st.session_state["selected_school"]]
        if not matches.empty:
            default_idx = int(matches.index[0])

    school_name = st.selectbox(
        "School",
        school_list["school_name"].tolist(),
        index=default_idx,
    )

# ── Load school data ──────────────────────────────────────────────────────────
year = get_latest_year()
df = load_schools()

school_row = school_list[school_list["school_name"] == school_name].iloc[0]
school_code = school_row["school_code"]
school_df = df[df["school_code"] == school_code].copy()

# District / state averages
dist_sub = df[
    (df["state"] == state) & (df["district"] == district) & (df["year"] == year)
]
dist_read_avg = dist_sub[dist_sub["subject"] == "reading"]["percentage"].mean()
dist_math_avg = dist_sub[dist_sub["subject"] == "math"]["percentage"].mean()

state_sub = df[(df["state"] == state) & (df["year"] == year)]
state_read_avg = state_sub[state_sub["subject"] == "reading"]["percentage"].mean()
state_math_avg = state_sub[state_sub["subject"] == "math"]["percentage"].mean()

# School's latest values
lat = school_df[school_df["year"] == year]
reading_row = lat[lat["subject"] == "reading"]
math_row    = lat[lat["subject"] == "math"]
reading_pct = float(reading_row["percentage"].values[0]) if not reading_row.empty else None
math_pct    = float(math_row["percentage"].values[0])    if not math_row.empty    else None

# Trend
r_series = school_df[school_df["subject"] == "reading"].sort_values("year")["percentage"].values
m_series = school_df[school_df["subject"] == "math"].sort_values("year")["percentage"].values
read_declining = _years_declining(r_series)
math_declining = _years_declining(m_series)

# Priority rank
ranked = compute_priority(state, district, year)
rank_row = ranked[ranked["school_code"] == school_code]
rank     = int(rank_row["rank"].values[0]) if not rank_row.empty else "—"
total    = len(ranked)
months_since = float(rank_row["months_since"].values[0]) if not rank_row.empty else 12.0

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown(
    f"<div class='nipun-header'>"
    f"<h2 style='margin:0;color:#0F3057'>{school_name}</h2>"
    f"<p style='margin:4px 0 0;color:#64748B'>"
    f"Block: {school_row['block']} · District: {district}, {state} · "
    f"Priority rank #{rank} of {total}</p>"
    f"</div>",
    unsafe_allow_html=True,
)

# ── KPI strip ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric(
    "Grade 5 reading",
    f"{reading_pct:.0f}%" if reading_pct is not None else "—",
    delta=f"{reading_pct - dist_read_avg:.0f} pp vs district" if reading_pct is not None else None,
    delta_color="inverse",
)
k2.metric(
    "Grade 5 math",
    f"{math_pct:.0f}%" if math_pct is not None else "—",
    delta=f"{math_pct - dist_math_avg:.0f} pp vs district" if math_pct is not None else None,
    delta_color="inverse",
)
k3.metric("Years declining", f"{max(read_declining, math_declining)}")
k4.metric("Priority rank", f"#{rank} / {total}")

# ── Auto-generated diagnosis ──────────────────────────────────────────────────
st.divider()
diagnosis_md = generate_diagnosis(
    school_name=school_name,
    reading_pct=reading_pct,
    math_pct=math_pct,
    dist_read_avg=dist_read_avg,
    dist_math_avg=dist_math_avg,
    read_declining=read_declining,
    math_declining=math_declining,
    rank=rank if isinstance(rank, int) else 0,
    total=total,
    months_since=months_since,
)
st.info(diagnosis_md)

# Copy to report button
with st.expander("Copy diagnosis to report (plain text)"):
    st.code(diagnosis_as_plaintext(diagnosis_md), language=None)

# ── Charts ────────────────────────────────────────────────────────────────────
st.subheader("Learning trajectory")

col_r, col_m = st.columns(2)

for subject, col, dist_avg, state_avg, yd in [
    ("reading", col_r, dist_read_avg, state_read_avg, read_declining),
    ("math",    col_m, dist_math_avg, state_math_avg, math_declining),
]:
    series = (
        school_df[school_df["subject"] == subject]
        .sort_values("year")[["year", "percentage"]]
        .dropna()
    )
    if series.empty:
        col.info(f"No {subject} data.")
        continue

    forecast = school_trajectory(school_df, school_code, subject)

    if yd >= 2:
        t = f"{subject.title()} has declined {yd} years in a row — intervention urgent"
    elif yd == 1:
        t = f"{subject.title()} dipped last year — watch closely"
    else:
        t = f"{subject.title()} is holding steady — keep monitoring"

    fig = trend_chart(
        years=series["year"].tolist(),
        values=series["percentage"].tolist(),
        title=t,
        district_avg=dist_avg,
        state_avg=state_avg,
        forecast=forecast,
    )
    col.plotly_chart(fig, use_container_width=True)

# ── Grade × subject heatmap ───────────────────────────────────────────────────
st.subheader("Which grade is falling behind?")

if not school_df[school_df["year"] == year].empty:
    # Insight title: point at the weakest cell
    pivot = school_df[school_df["year"] == year].copy()
    worst = pivot.loc[pivot["percentage"].idxmin()] if not pivot.empty else None
    hm_title = (
        f"Grade {int(worst['grade'])} {worst['subject']} is the weakest spot "
        f"({worst['percentage']:.0f}%)"
        if worst is not None
        else "Grade × subject performance"
    )
    fig_hm = heatmap_grade_subject(school_df, year, hm_title)
    st.plotly_chart(fig_hm, use_container_width=True)
else:
    st.info("Heatmap requires data for the selected year.")

# ── Navigation shortcut ───────────────────────────────────────────────────────
st.divider()
if st.button("Get intervention recommendations for this school →"):
    st.session_state["diag_school_code"] = school_code
    st.session_state["diag_reading_gap"] = (
        (dist_read_avg - reading_pct) if reading_pct is not None else 0
    )
    st.session_state["diag_math_gap"] = (
        (dist_math_avg - math_pct) if math_pct is not None else 0
    )
    st.session_state["diag_school_name"] = school_name
    st.switch_page("pages/3_Interventions.py")

import sys
from pathlib import Path
_root = str(Path(__file__).resolve().parent.parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

"""
Feature 7 — NIPUN Target Clock
DEO question: Is my district on track to hit the NIPUN 2026 foundational literacy target?
"""
from app.components import setup_page, render_footer
setup_page("Is your district on track for 2026?")

import streamlit as st
import pandas as pd
from app.services.data_loader import (
    get_states, get_districts, load_schools, load_aser_data, get_latest_year,
)
from app.services.forecaster import forecast_trajectory
from app.components.charts import trend_chart
from app.components.maps import nipun_state_bubble_map

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## District")
    states = get_states()
    default_state = "Bihar" if "Bihar" in states else states[0]
    state = st.selectbox("State", states, index=states.index(default_state))
    districts = get_districts(state)
    district = st.selectbox("District", districts)

    st.divider()
    st.markdown("## NIPUN Target")
    target_pct = st.slider("Grade 3 reading target (%)", 20, 80, 50, step=5)
    target_year = st.slider("By year", 2025, 2030, 2026)
    st.caption(
        "NIPUN Bharat: all Grade 3 children at foundational literacy by 2026–27. "
        "Adjust the target to match your state's milestone."
    )

# ── District-level trend from simulated school data ───────────────────────────
year = get_latest_year()
schools_df = load_schools()

dist_read = (
    schools_df[
        (schools_df["state"] == state) &
        (schools_df["district"] == district) &
        (schools_df["subject"] == "reading") &
        (schools_df["grade"] == 3)
    ]
    .groupby("year")["percentage"].mean()
    .sort_index()
)

if dist_read.empty:
    st.warning("No school data for this district.")
    st.stop()

years_avail = dist_read.index.tolist()
dist_series = dist_read.values.tolist()
current_val = dist_series[-1]

yoy = 0.0
if len(years_avail) >= 2:
    fc_full = forecast_trajectory(years_avail, dist_series)
    yoy = fc_full["slope"]
else:
    fc_full = None

gap = target_pct - current_val
if yoy > 0:
    years_needed = gap / yoy
    projected_year = int(round(years_avail[-1] + years_needed))
    years_behind = max(0, projected_year - target_year)
    on_track = projected_year <= target_year
elif gap <= 0:
    projected_year = years_avail[-1]
    years_behind = 0
    on_track = True
else:
    projected_year = None
    years_behind = None
    on_track = False

clock_color = "#16A34A" if on_track else "#DC2626"

if projected_year and not on_track:
    headline = (
        f"At current rate (+{yoy:.1f} pp/yr), {district} hits {target_pct}% "
        f"in {projected_year} — {years_behind} year{'s' if years_behind != 1 else ''} behind the {target_year} target."
    )
elif on_track:
    headline = f"{district} is on track — projected to hit {target_pct}% by {projected_year or target_year}."
else:
    headline = f"{district} is declining — will not reach {target_pct}% at current rate."

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(
    f"<div class='nipun-header' style='border-color:{clock_color}'>"
    f"<h2 style='margin:0;color:#1F2937'>Is {district} on track for {target_year}?</h2>"
    f"<p style='margin:6px 0 0;color:#64748B'>{headline}</p>"
    f"</div>",
    unsafe_allow_html=True,
)

# ── KPI strip ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric(f"Current ({year})", f"{current_val:.1f}%")
k2.metric("NIPUN target", f"{target_pct}%")
k3.metric(
    "Gap to close",
    f"{gap:.1f} pp",
    delta=f"{yoy:+.1f} pp/yr currently",
    delta_color="normal" if yoy >= 0 else "inverse",
)
if projected_year:
    k4.metric(
        "Projected year",
        str(projected_year),
        delta=(
            f"On track" if on_track
            else f"{years_behind} yr behind {target_year}"
        ),
        delta_color="normal" if on_track else "inverse",
    )
else:
    k4.metric("Projected year", "Declining", delta="No progress", delta_color="inverse")

st.divider()

# ── Trend chart (left) + India state map (right) ──────────────────────────────
chart_col, map_col = st.columns([5, 4])

with chart_col:
    title_str = (
        f"Reading is {'+' if yoy >= 0 else ''}{yoy:.1f} pp/yr — "
        f"target {target_pct}% by {target_year}"
    )
    fig = trend_chart(years_avail, dist_series, title_str, forecast=fc_full)

    # Target line
    fig.add_hline(
        y=target_pct,
        line_dash="dash",
        line_color=clock_color,
        line_width=2,
        annotation_text=f"NIPUN target  {target_pct}%",
        annotation_position="top left",
        annotation_font_color=clock_color,
        annotation_font_size=12,
    )
    st.plotly_chart(fig, use_container_width=True)

with map_col:
    # Build state-level summary from real ASER data
    aser = load_aser_data()
    state_rows = []

    for s in aser["state"].unique():
        s_data = (
            aser[
                (aser["state"] == s) &
                (aser["subject"] == "reading") &
                (aser["level"] == "story") &
                (aser["grade"] == 3)
            ]
            .sort_values("year")
        )
        if len(s_data) < 2:
            continue
        curr = float(s_data.iloc[-1]["percentage"])
        prev = float(s_data.iloc[-2]["percentage"])
        yr_c = int(s_data.iloc[-1]["year"])
        yr_p = int(s_data.iloc[-2]["year"])
        rate = (curr - prev) / max(1, yr_c - yr_p)
        gap_s = target_pct - curr
        proj = int(round(yr_c + gap_s / rate)) if rate > 0 else 2099
        proj = min(proj, 2060)
        state_rows.append({
            "state":         s,
            "current_pct":   round(curr, 1),
            "gap_to_target": round(gap_s, 1),
            "rate_pp_yr":    round(rate, 2),
            "projected_year": proj,
        })

    state_df = pd.DataFrame(state_rows)

    fig_map = nipun_state_bubble_map(
        state_df,
        value_col="current_pct",
        color_col="gap_to_target",
        title=f"India states — gap to {target_pct}% NIPUN target",
    )
    st.plotly_chart(fig_map, use_container_width=True)
    st.caption(
        "Bubble size = current reading %. "
        "Red = far from target. Green = close or already there."
    )

st.divider()

# ── All-states table (identical to what goes in .pbix) ────────────────────────
st.subheader("All states — progress tracker")
st.caption(
    "These numbers match the Power BI dataset. "
    "Sort by 'Projected year' to find the states most behind."
)

display = state_df.sort_values("gap_to_target", ascending=False).copy()
display["Status"] = display["projected_year"].apply(
    lambda y: "On track" if y <= target_year else f"{y - target_year} yr late"
)
display = display.rename(columns={
    "state":          "State",
    "current_pct":    f"Reading % ({year})",
    "gap_to_target":  "Gap to target (pp)",
    "rate_pp_yr":     "Rate (pp/yr)",
    "projected_year": "Projected year",
})
st.dataframe(display, use_container_width=True, hide_index=True)

st.divider()

# ── What it takes ─────────────────────────────────────────────────────────────
st.subheader(f"What it takes for {district} to hit {target_pct}% by {target_year}")

years_left = max(1, target_year - years_avail[-1])
required_rate = gap / years_left
shortfall = required_rate - yoy

if shortfall > 0:
    st.markdown(
        f"""<div style="
            background:#FEF2F2;border-radius:12px;
            padding:1.1rem 1.4rem;border-left:4px solid #DC2626;
            margin-bottom:0.5rem
        ">
          <div style="font-size:1rem;font-weight:700;color:#1F2937;margin-bottom:0.35rem">
            Current rate: <span style="color:#DC2626">+{yoy:.1f} pp/year</span>
          </div>
          <div style="font-size:0.9rem;color:#475569;margin-bottom:0.25rem">
            Required to hit {target_pct}% by {target_year}:
            <strong>+{required_rate:.1f} pp/year</strong>
          </div>
          <div style="font-size:0.88rem;color:#DC2626;font-weight:600">
            Shortfall: {shortfall:.1f} additional pp/year — roughly
            2–3 more TaRL or Phonics camps per block, per year.
          </div>
        </div>""",
        unsafe_allow_html=True,
    )
elif gap <= 0:
    st.success(f"{district} has already exceeded the {target_pct}% target.")
else:
    st.success(
        f"{district} is improving at {yoy:.1f} pp/year — ahead of the "
        f"{required_rate:.1f} pp/year required. Current trajectory is enough."
    )

render_footer()

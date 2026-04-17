import sys
from pathlib import Path
# Project root → sys.path so 'from app.xxx import' works on any machine
_root = str(Path(__file__).resolve().parent.parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

"""
Feature 1 — Your 20 Schools This Week (Triage)
DEO question: Which 20 schools do I send BEOs to this week?
"""
from app.components import setup_page, render_footer
setup_page("Send your BEOs here this week")

import streamlit as st
from app.services.data_loader import (
    get_states, get_districts, get_blocks, load_schools, get_latest_year,
)
from app.services.priority_scorer import compute_priority
from app.components.school_card import render_school_card

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Your District")
    states = get_states()
    default_state = "Bihar" if "Bihar" in states else states[0]
    state = st.selectbox("State", states, index=states.index(default_state))

    districts = get_districts(state)
    district = st.selectbox("District", districts)

    all_blocks = get_blocks(state, district)
    block_filter = st.multiselect("Filter by block (leave blank for all)", all_blocks)

    top_n = st.slider("Schools to review", 5, 50, 20)

    st.divider()
    st.markdown("## How schools are ranked")
    st.caption(
        "Adjust the weights to match your district's priorities. "
        "This is not AI — it is transparent arithmetic."
    )
    w_reading   = st.slider("Reading gap weight",               0.0, 1.0, 0.35, 0.05)
    w_math      = st.slider("Math gap weight",                  0.0, 1.0, 0.30, 0.05)
    w_declining = st.slider("Years of decline weight",          0.0, 1.0, 0.20, 0.05)
    w_months    = st.slider("Months since last visit weight",   0.0, 1.0, 0.15, 0.05)

    total_w = w_reading + w_math + w_declining + w_months
    if abs(total_w - 1.0) > 0.01:
        st.warning(f"Weights sum to {total_w:.2f} — scores are still proportional.")

# ── Compute rankings ──────────────────────────────────────────────────────────
year = get_latest_year()

with st.spinner("Ranking schools — hang on..."):
    ranked = compute_priority(
        state, district, year,
        w_reading=w_reading, w_math=w_math,
        w_declining=w_declining, w_months=w_months,
    )

if block_filter:
    ranked = ranked[ranked["block"].isin(block_filter)].reset_index(drop=True)
    ranked["rank"] = range(1, len(ranked) + 1)

if ranked.empty:
    st.warning("No school data found for this state and district.")
    st.stop()

n_schools = len(ranked)
n_show = min(top_n, n_schools)
top_n_df = ranked.head(n_show)

# ── Above-the-fold hero — Section 8.2 ────────────────────────────────────────
st.markdown(
    f"<div class='nipun-header'>"
    f"<h2 style='margin:0;color:#0F3057'>"
    f"{district} district has {n_schools} government schools. "
    f"{n_show} need your BEOs this week.</h2>"
    f"<p style='margin:6px 0 0;color:#64748B;font-size:0.92rem'>"
    f"Transparent priority score · Updated from ASER {year} + monthly block tests · "
    f"3-min read.</p>"
    f"</div>",
    unsafe_allow_html=True,
)

# ── KPI strip ─────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Schools ranked", n_schools)
k2.metric(
    "How many Grade 3 kids can read a story? (top 20 avg)",
    f"{top_n_df['reading_pct'].mean():.0f}%",
    delta=f"−{top_n_df['reading_gap'].mean():.0f} pp vs district",
    delta_color="inverse",
)
k3.metric(
    "Math gap — top 20",
    f"{top_n_df['math_gap'].mean():.0f} pp below avg",
)
k4.metric(
    "Schools with no recent visit",
    f"{(top_n_df['months_since'] >= 12).sum()} of {n_show}",
)

st.divider()

# ── WhatsApp bulk copy ────────────────────────────────────────────────────────
with st.expander("Copy this week's list to WhatsApp"):
    lines = [f"NIPUN Compass — {district} priority list ({year})\n"]
    for _, r in top_n_df.iterrows():
        reasons = []
        if r.get("reading_gap", 0) > 5:
            reasons.append(f"reading {r['reading_gap']:.0f} pp below avg")
        if r.get("math_gap", 0) > 5:
            reasons.append(f"math {r['math_gap']:.0f} pp below avg")
        if r.get("years_declining", 0) >= 2:
            reasons.append(f"declining {int(r['years_declining'])} yrs")
        lines.append(
            f"#{int(r['rank'])} {r['school_name']} ({r['block']}): "
            f"{'; '.join(reasons) or 'multiple factors'}"
        )
    st.code("\n".join(lines), language=None)

# ── School cards ──────────────────────────────────────────────────────────────
st.subheader(f"Send your BEOs to these {n_show} schools this week")
st.caption(
    "Score = reading gap × 0.35 + math gap × 0.30 + "
    "years declining × 0.20 + months since last visit × 0.15  ·  "
    "Adjust weights in sidebar to match your priorities."
)

for _, row in top_n_df.iterrows():
    render_school_card(row, show_whatsapp=True)

# ── Full ranked table ─────────────────────────────────────────────────────────
with st.expander("See all ranked schools as a table"):
    cols = ["rank", "school_name", "block", "reading_pct", "math_pct",
            "years_declining", "months_since", "score"]
    cols = [c for c in cols if c in ranked.columns]
    display = ranked[cols].rename(columns={
        "school_name": "School", "block": "Block",
        "reading_pct": "Reading %", "math_pct": "Math %",
        "years_declining": "Yrs declining",
        "months_since": "Months since visit",
        "score": "Priority score",
    })
    display["Priority score"] = (display["Priority score"] * 100).round(1)
    st.dataframe(display, use_container_width=True, hide_index=True)

render_footer()

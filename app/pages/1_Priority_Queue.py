"""
Feature 1 — Your 20 Schools This Week (Triage)
DEO question: Which 20 schools do I send BEOs to this week?

Acceptance criteria:
- List updates live when district/block slicer changes
- Each row has "Why this school?" expander showing score breakdown
- "Copy list to WhatsApp" button (plain-text block)
- Weights adjustable via sliders (transparent — DEO can override)
- Uses real ASER state/district data + simulated school-level data
- NOT "AI ranks schools" — always "transparent rule-based priority score"
"""
from app.components import setup_page
setup_page("Send your BEOs here this week")

import streamlit as st
import pandas as pd
from app.services.data_loader import (
    get_states, get_districts, get_blocks, load_schools, get_latest_year
)
from app.services.priority_scorer import compute_priority
from app.components.school_card import render_school_card

# ── Sidebar — filters + weight sliders ───────────────────────────────────────
with st.sidebar:
    st.markdown("## Your District")
    states = get_states()
    default_state = "Bihar" if "Bihar" in states else states[0]
    state = st.selectbox("State", states, index=states.index(default_state))

    districts = get_districts(state)
    district = st.selectbox("District", districts)

    all_blocks = get_blocks(state, district)
    block_filter = st.multiselect("Filter by block (optional)", all_blocks)

    top_n = st.slider("Schools to show", 5, 50, 20)

    st.divider()
    st.markdown("## Priority Score Weights")
    st.caption("Adjust to match your district's priorities. Must sum to 1.0.")

    w_reading  = st.slider("Reading gap",               0.0, 1.0, 0.35, 0.05)
    w_math     = st.slider("Math gap",                  0.0, 1.0, 0.30, 0.05)
    w_declining= st.slider("Years of decline",          0.0, 1.0, 0.20, 0.05)
    w_months   = st.slider("Months since intervention", 0.0, 1.0, 0.15, 0.05)

    total_w = w_reading + w_math + w_declining + w_months
    if abs(total_w - 1.0) > 0.01:
        st.warning(f"Weights sum to {total_w:.2f}. Scores are still proportional.")

# ── Compute ───────────────────────────────────────────────────────────────────
year = get_latest_year()
df_schools = load_schools()

ranked = compute_priority(
    state, district, year,
    w_reading=w_reading, w_math=w_math,
    w_declining=w_declining, w_months=w_months,
)

if block_filter:
    ranked = ranked[ranked["block"].isin(block_filter)].reset_index(drop=True)
    ranked["rank"] = range(1, len(ranked) + 1)

# ── Above-the-fold hero (Section 8.2) ────────────────────────────────────────
n_schools = len(ranked)
n_show = min(top_n, n_schools)

st.markdown(
    f"<div class='nipun-header'>"
    f"<h2 style='margin:0;color:#0F3057'>{district} district has "
    f"{n_schools} government schools. "
    f"{n_show} need your BEOs this week.</h2>"
    f"<p style='margin:4px 0 0;color:#64748B;font-size:0.9rem'>"
    f"Transparent priority score · Updated from ASER {year} + monthly block tests · "
    f"3-min read.</p>"
    f"</div>",
    unsafe_allow_html=True,
)

if ranked.empty:
    st.warning("No school data found for this selection.")
    st.stop()

# ── KPI strip ─────────────────────────────────────────────────────────────────
top20 = ranked.head(top_n)
k1, k2, k3, k4 = st.columns(4)
k1.metric("Schools ranked", n_schools)
k2.metric(
    "Avg reading gap — top 20",
    f"{top20['reading_gap'].mean():.1f} pp" if "reading_gap" in top20.columns else "—",
)
k3.metric(
    "Avg math gap — top 20",
    f"{top20['math_gap'].mean():.1f} pp" if "math_gap" in top20.columns else "—",
)
k4.metric(
    "With no recent intervention",
    f"{(top20['months_since'] >= 12).sum()} schools",
)

st.divider()

# ── WhatsApp bulk copy ────────────────────────────────────────────────────────
with st.expander("Copy full list to WhatsApp"):
    wa_lines = [f"NIPUN Compass — {district} priority list ({year})\n"]
    for _, r in top20.iterrows():
        reason = []
        if r.get("reading_gap", 0) > 5:
            reason.append(f"reading {r['reading_gap']:.0f}pp below avg")
        if r.get("math_gap", 0) > 5:
            reason.append(f"math {r['math_gap']:.0f}pp below avg")
        if r.get("years_declining", 0) >= 2:
            reason.append(f"declining {int(r['years_declining'])}yr")
        wa_lines.append(
            f"#{int(r['rank'])} {r['school_name']} ({r['block']}): "
            f"{'; '.join(reason) or 'multiple factors'}"
        )
    st.code("\n".join(wa_lines), language=None)

# ── School cards ──────────────────────────────────────────────────────────────
st.subheader(f"Top {n_show} schools — send BEOs here this week")
st.caption(
    "Scoring rule (transparent, DEO-editable above): "
    "reading gap × 0.35 + math gap × 0.30 + years declining × 0.20 + "
    "months since last intervention × 0.15. This is not AI — it is arithmetic."
)

for _, row in top20.iterrows():
    render_school_card(row, show_whatsapp=True)

# ── Full table ────────────────────────────────────────────────────────────────
with st.expander("See all ranked schools as a table"):
    cols = ["rank", "school_name", "block", "reading_pct", "math_pct",
            "years_declining", "months_since", "score"]
    cols = [c for c in cols if c in ranked.columns]
    display = ranked[cols].rename(columns={
        "reading_pct": "Reading %",
        "math_pct": "Math %",
        "years_declining": "Yrs declining",
        "months_since": "Months since intervention",
        "score": "Priority score",
    })
    display["Priority score"] = (display["Priority score"] * 100).round(1)
    st.dataframe(display, use_container_width=True, hide_index=True)

"""
School card — ranked row with one-line reason + "Why this school?" score breakdown.
Copy-to-WhatsApp uses st.code (easy to long-press copy on mobile).
"""
from __future__ import annotations
import streamlit as st
import pandas as pd


def _score_bar(val: float, max_val: float = 0.35) -> str:
    filled = int(round((val / max_val) * 10)) if max_val > 0 else 0
    return "█" * min(filled, 10) + "░" * (10 - min(filled, 10))


def _one_line_reason(row: pd.Series) -> str:
    reasons = []
    if row.get("reading_gap", 0) > 5:
        reasons.append(f"reading {row['reading_gap']:.0f} pp below avg")
    if row.get("math_gap", 0) > 5:
        reasons.append(f"math {row['math_gap']:.0f} pp below avg")
    if row.get("years_declining", 0) >= 2:
        reasons.append(f"declining {int(row['years_declining'])} years")
    if row.get("months_since", 12) >= 12:
        reasons.append(f"no intervention in {int(row['months_since'])} months")
    return "; ".join(reasons) if reasons else "below-average on multiple indicators"


def render_school_card(row: pd.Series, show_whatsapp: bool = False):
    score_pct = int(row["score"] * 100)
    reason = _one_line_reason(row)

    if score_pct >= 70:
        badge_color = "#C2362F"
        urgency = "URGENT"
    elif score_pct >= 45:
        badge_color = "#E76F24"
        urgency = "MONITOR"
    else:
        badge_color = "#4A7C59"
        urgency = "REVIEW"

    with st.container(border=True):
        top_left, top_mid, top_right = st.columns([1, 7, 2])

        with top_left:
            st.markdown(
                f"<div style='font-size:1.6rem;font-weight:700;color:#0F3057;line-height:1.1'>"
                f"#{int(row['rank'])}</div>",
                unsafe_allow_html=True,
            )

        with top_mid:
            st.markdown(f"**{row['school_name']}**")
            st.caption(f"Block: {row['block']} · {reason}")

        with top_right:
            st.markdown(
                f"<div style='text-align:right'>"
                f"<span style='font-size:1.3rem;font-weight:700;color:{badge_color}'>{score_pct}</span>"
                f"<span style='font-size:0.75rem;color:#94A3B8'>/100 · {urgency}</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

        # "Why this school?" expander with score breakdown
        with st.expander("Why this school? (score breakdown)"):
            col_a, col_b = st.columns(2)
            with col_a:
                r_pts = row.get("score_reading", 0) * 100
                m_pts = row.get("score_math", 0) * 100
                st.markdown(
                    f"**Reading gap** · {row.get('reading_pct', 0):.0f}% "
                    f"(gap {row.get('reading_gap', 0):.1f} pp) → **{r_pts:.1f} pts**"
                )
                st.markdown(
                    f"**Math gap** · {row.get('math_pct', 0):.0f}% "
                    f"(gap {row.get('math_gap', 0):.1f} pp) → **{m_pts:.1f} pts**"
                )
            with col_b:
                d_pts  = row.get("score_declining", 0) * 100
                mo_pts = row.get("score_months", 0) * 100
                st.markdown(
                    f"**Years declining** · {int(row.get('years_declining', 0))} yr → **{d_pts:.1f} pts**"
                )
                st.markdown(
                    f"**Months since intervention** · {row.get('months_since', 12):.0f} mo → **{mo_pts:.1f} pts**"
                )
            st.markdown(
                f"*Ranked #{int(row['rank'])} because: "
                f"reading {row.get('reading_gap', 0):.0f} pp below district avg "
                f"(weight 0.35 → {r_pts:.1f} pts), "
                f"math {row.get('math_gap', 0):.0f} pp below district avg "
                f"(weight 0.30 → {m_pts:.1f} pts), "
                f"declining {int(row.get('years_declining', 0))} years "
                f"(weight 0.20 → {d_pts:.1f} pts), "
                f"no intervention in {row.get('months_since', 12):.0f} months "
                f"(weight 0.15 → {mo_pts:.1f} pts).*"
            )

        if show_whatsapp:
            wa = (
                f"Priority visit #{int(row['rank'])}: {row['school_name']}, {row['block']}.\n"
                f"Reason: {reason}.\n"
                f"Priority score: {score_pct}/100."
            )
            st.code(wa, language=None)

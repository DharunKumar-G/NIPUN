"""
School card — HTML card with urgency left-border, score progress bar,
"Why this school?" expander, and "→ Full diagnosis" navigation button.
"""
from __future__ import annotations
import streamlit as st
import pandas as pd


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
    school_code = row.get("school_code", "")
    card_key = f"{school_code}_{int(row['rank'])}"

    if score_pct >= 70:
        border_color = "#DC2626"
        bg_color = "#FEF2F2"
        urgency = "URGENT"
    elif score_pct >= 45:
        border_color = "#D97706"
        bg_color = "#FFFBEB"
        urgency = "MONITOR"
    else:
        border_color = "#16A34A"
        bg_color = "#F0FDF4"
        urgency = "REVIEW"

    r_pts = row.get("score_reading", 0) * 100
    m_pts = row.get("score_math", 0) * 100
    d_pts = row.get("score_declining", 0) * 100
    mo_pts = row.get("score_months", 0) * 100

    # Component bar widths (clamped 0–100%)
    r_bar  = min(100, int(r_pts  / 35 * 100))
    m_bar  = min(100, int(m_pts  / 30 * 100))
    d_bar  = min(100, int(d_pts  / 20 * 100))
    mo_bar = min(100, int(mo_pts / 15 * 100))

    st.markdown(
        f"""
<div class="nipun-card" style="
    border-left: 5px solid {border_color};
    background: {bg_color};
    border-radius: 0 10px 10px 0;
    padding: 1rem 1.25rem 0.85rem;
    margin-bottom: 0.35rem;
    box-shadow: 0 1px 6px rgba(0,0,0,0.07);
">
  <div style="display:flex;align-items:flex-start;gap:1rem">
    <div style="font-size:2rem;font-weight:800;color:#1F2937;min-width:3rem;line-height:1;padding-top:2px">
      #{int(row['rank'])}
    </div>
    <div style="flex:1;min-width:0">
      <div style="display:flex;align-items:center;gap:0.5rem;flex-wrap:wrap;margin-bottom:2px">
        <span style="font-size:1.05rem;font-weight:700;color:#1F2937">{row['school_name']}</span>
        <span class="urgency-pill" style="background:{border_color}">{urgency}</span>
      </div>
      <div style="font-size:0.82rem;color:#64748B">Block: {row['block']} &nbsp;·&nbsp; {reason}</div>
    </div>
    <div style="text-align:right;min-width:4.5rem;flex-shrink:0">
      <div style="font-size:2rem;font-weight:800;color:{border_color};line-height:1">{score_pct}</div>
      <div style="font-size:0.7rem;color:#94A3B8;margin-top:-2px">/100 score</div>
    </div>
  </div>
  <!-- Main score bar -->
  <div class="score-track">
    <div class="score-fill" style="width:{score_pct}%;background:{border_color}"></div>
  </div>
  <!-- Per-component contribution bars -->
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.4rem;margin-top:0.55rem">
    <div style="font-size:0.68rem;color:#64748B">
      <div style="background:#E2E8F0;height:3px;border-radius:2px;margin-bottom:2px">
        <div style="width:{r_bar}%;background:#1F2937;height:100%;border-radius:2px"></div>
      </div>
      Reading · {r_pts:.1f}
    </div>
    <div style="font-size:0.68rem;color:#64748B">
      <div style="background:#E2E8F0;height:3px;border-radius:2px;margin-bottom:2px">
        <div style="width:{m_bar}%;background:#1F2937;height:100%;border-radius:2px"></div>
      </div>
      Math · {m_pts:.1f}
    </div>
    <div style="font-size:0.68rem;color:#64748B">
      <div style="background:#E2E8F0;height:3px;border-radius:2px;margin-bottom:2px">
        <div style="width:{d_bar}%;background:#1F2937;height:100%;border-radius:2px"></div>
      </div>
      Decline · {d_pts:.1f}
    </div>
    <div style="font-size:0.68rem;color:#64748B">
      <div style="background:#E2E8F0;height:3px;border-radius:2px;margin-bottom:2px">
        <div style="width:{mo_bar}%;background:#1F2937;height:100%;border-radius:2px"></div>
      </div>
      Visit · {mo_pts:.1f}
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )

    # Interactive section below the card
    exp_col, btn_col = st.columns([3, 1])

    with exp_col:
        with st.expander("Why this school? (score breakdown)"):
            ca, cb = st.columns(2)
            with ca:
                st.markdown(
                    f"**Reading gap** · {row.get('reading_pct', 0):.0f}% "
                    f"(gap {row.get('reading_gap', 0):.1f} pp) → **{r_pts:.1f} pts**"
                )
                st.markdown(
                    f"**Math gap** · {row.get('math_pct', 0):.0f}% "
                    f"(gap {row.get('math_gap', 0):.1f} pp) → **{m_pts:.1f} pts**"
                )
            with cb:
                st.markdown(
                    f"**Years declining** · {int(row.get('years_declining', 0))} yr → **{d_pts:.1f} pts**"
                )
                st.markdown(
                    f"**Months since intervention** · {row.get('months_since', 12):.0f} mo → **{mo_pts:.1f} pts**"
                )
            st.markdown(
                f"*Ranked #{int(row['rank'])} of {int(row.get('total', '?'))} because: "
                f"reading {row.get('reading_gap', 0):.0f} pp below district avg "
                f"(weight 0.35 → {r_pts:.1f} pts), "
                f"math {row.get('math_gap', 0):.0f} pp below district avg "
                f"(weight 0.30 → {m_pts:.1f} pts), "
                f"declining {int(row.get('years_declining', 0))} years "
                f"(weight 0.20 → {d_pts:.1f} pts), "
                f"no intervention in {row.get('months_since', 12):.0f} months "
                f"(weight 0.15 → {mo_pts:.1f} pts).*"
                if row.get("total") else
                f"*Score = {r_pts:.1f} (reading) + {m_pts:.1f} (math) + "
                f"{d_pts:.1f} (decline) + {mo_pts:.1f} (visit gap) = {score_pct}/100.*"
            )

    with btn_col:
        if st.button("→ Diagnose", key=f"diag_btn_{card_key}", use_container_width=True):
            st.session_state["selected_school"] = school_code
            st.switch_page("pages/2_School_Diagnosis.py")

    if show_whatsapp:
        wa = (
            f"Priority visit #{int(row['rank'])}: {row['school_name']}, {row['block']}.\n"
            f"Reason: {reason}.\n"
            f"Priority score: {score_pct}/100."
        )
        st.code(wa, language=None)

    st.markdown("<div style='margin-bottom:0.75rem'></div>", unsafe_allow_html=True)

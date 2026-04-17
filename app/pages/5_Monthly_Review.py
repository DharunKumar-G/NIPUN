"""
Feature 5 — Monthly Review Builder (Escalation)
DEO question: What do I tell my DM at 3 PM?

Contents:
- District summary: schools visited, interventions launched, trajectory vs ASER baseline
- Block-level breakdown: which blocks improving, which declining
- Top 5 schools in priority queue this month
- Top 5 interventions completed with outcomes
- Projected trajectory (linear regression + confidence band)
- Export to PDF (reportlab)

Acceptance criteria:
- Loads in <2 seconds
- Single page, scrollable, print-ready
- Uses real ASER data for baselines
- PDF export looks professional (not Streamlit default screenshot)
"""
import io
import textwrap
from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable

from app.components import setup_page
from app.components.charts import trend_chart, block_bar
from app.services.data_loader import (
    get_states, get_districts, get_blocks, load_schools, get_latest_year
)
from app.services.priority_scorer import compute_priority
from app.services.forecaster import forecast_trajectory

setup_page("Print for your DM meeting")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Report Parameters")
    states = get_states()
    default_state = "Bihar" if "Bihar" in states else states[0]
    state = st.selectbox("State", states, index=states.index(default_state))
    districts = get_districts(state)
    district = st.selectbox("District", districts)
    report_month = st.date_input("Report month", value=date.today())

# ── Load data ─────────────────────────────────────────────────────────────────
year = get_latest_year()
df = load_schools()
ranked = compute_priority(state, district, year)

if ranked.empty:
    st.warning("No data found for this state/district.")
    st.stop()

# District time series
dist_data = df[(df["state"] == state) & (df["district"] == district)]
years_avail = sorted(dist_data["year"].unique().tolist())


def _series(subject: str) -> list[float]:
    return [
        dist_data[(dist_data["year"] == y) & (dist_data["subject"] == subject)]["percentage"].mean()
        for y in years_avail
    ]


read_series = _series("reading")
math_series = _series("math")
read_fc = forecast_trajectory(years_avail, read_series) if len(years_avail) >= 2 else None
math_fc = forecast_trajectory(years_avail, math_series) if len(years_avail) >= 2 else None

# State averages (for baseline comparison)
state_sub = df[(df["state"] == state) & (df["year"] == year)]
state_read = state_sub[state_sub["subject"] == "reading"]["percentage"].mean()
state_math = state_sub[state_sub["subject"] == "math"]["percentage"].mean()

read_latest = read_series[-1] if read_series else 0.0
math_latest = math_series[-1] if math_series else 0.0

slope_read = read_fc["slope"] if read_fc else 0.0
slope_math = math_fc["slope"] if math_fc else 0.0

trend_read = "improving" if slope_read > 0.5 else "declining" if slope_read < -0.5 else "flat"
trend_math = "improving" if slope_math > 0.5 else "declining" if slope_math < -0.5 else "flat"

# Interventions from DB
from pathlib import Path
import sqlite3

DB_PATH = Path(__file__).parent.parent.parent / "db" / "interventions.db"


def _load_interventions(district_: str) -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(str(DB_PATH))
        df_i = pd.read_sql(
            "SELECT * FROM interventions WHERE district=? ORDER BY created_at DESC",
            conn, params=(district_,),
        )
        conn.close()
        return df_i
    except Exception:
        return pd.DataFrame()


df_intv = _load_interventions(district)
df_completed = df_intv[df_intv["status"] == "completed"] if not df_intv.empty else pd.DataFrame()
df_active    = df_intv[df_intv["status"] == "active"]    if not df_intv.empty else pd.DataFrame()

# Block-level trend (most recent two available years)
def _block_deltas() -> pd.DataFrame:
    blocks = get_blocks(state, district)
    if len(years_avail) < 2:
        return pd.DataFrame()
    y_prev, y_curr = years_avail[-2], years_avail[-1]
    rows = []
    for b in blocks:
        bsub = dist_data[dist_data["block"] == b]
        for subj in ["reading", "math"]:
            prev = bsub[(bsub.year == y_prev) & (bsub.subject == subj)]["percentage"].mean()
            curr = bsub[(bsub.year == y_curr) & (bsub.subject == subj)]["percentage"].mean()
            if not (pd.isna(prev) or pd.isna(curr)):
                rows.append({"block": b, "subject": subj, "delta": curr - prev})
    return pd.DataFrame(rows)


block_deltas = _block_deltas()

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(
    f"<div class='nipun-header'>"
    f"<h2 style='margin:0;color:#0F3057'>"
    f"{district} District — Monthly Review "
    f"({report_month.strftime('%B %Y')})</h2>"
    f"<p style='margin:4px 0 0;color:#64748B'>"
    f"Auto-generated from ASER {year} + {len(df_intv)} logged interventions · "
    f"Print-ready · PDF export below.</p>"
    f"</div>",
    unsafe_allow_html=True,
)

# ── KPI summary strip ─────────────────────────────────────────────────────────
k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Schools ranked",       len(ranked))
k2.metric("Active interventions", len(df_active))
k3.metric("Completed (with data)",len(df_completed))
k4.metric(
    f"Reading ({year})",
    f"{read_latest:.1f}%",
    delta=f"{slope_read:+.1f} pp/yr · {trend_read}",
    delta_color="normal" if slope_read >= 0 else "inverse",
)
k5.metric(
    f"Math ({year})",
    f"{math_latest:.1f}%",
    delta=f"{slope_math:+.1f} pp/yr · {trend_math}",
    delta_color="normal" if slope_math >= 0 else "inverse",
)

st.divider()

# ── Trajectory charts ─────────────────────────────────────────────────────────
st.subheader("Is the district on track to meet NIPUN Bharat targets?")
col_r, col_m = st.columns(2)

if len(years_avail) >= 2:
    read_title = (
        f"Reading is {trend_read} — {slope_read:+.1f} pp/year vs state avg {state_read:.0f}%"
    )
    math_title = (
        f"Math is {trend_math} — {slope_math:+.1f} pp/year vs state avg {state_math:.0f}%"
    )
    with col_r:
        fig = trend_chart(years_avail, read_series, read_title,
                         state_avg=state_read, forecast=read_fc, color="#0F3057")
        st.plotly_chart(fig, use_container_width=True)
    with col_m:
        fig = trend_chart(years_avail, math_series, math_title,
                         state_avg=state_math, forecast=math_fc, color="#E76F24")
        st.plotly_chart(fig, use_container_width=True)

# ── Block-level breakdown ─────────────────────────────────────────────────────
if not block_deltas.empty:
    st.subheader("Which blocks are improving — and which need urgent attention?")
    col_br, col_bm = st.columns(2)
    for subj, col in [("reading", col_br), ("math", col_bm)]:
        sub = block_deltas[block_deltas["subject"] == subj].copy()
        if sub.empty:
            continue
        improving = (sub["delta"] > 0).sum()
        declining = (sub["delta"] <= 0).sum()
        worst = sub.loc[sub["delta"].idxmin(), "block"] if not sub.empty else "—"
        title = (
            f"{subj.title()}: {improving} blocks improving, {declining} declining "
            f"— {worst} is falling fastest"
        )
        fig = block_bar(sub, title)
        col.plotly_chart(fig, use_container_width=True)

# ── Top 5 priority schools ────────────────────────────────────────────────────
st.subheader("Top 5 schools — still need BEO visits this month")
top5 = ranked.head(5)[
    ["rank", "school_name", "block", "reading_pct", "math_pct", "score"]
].copy()
top5["score"] = (top5["score"] * 100).round(0).astype(int)
top5 = top5.rename(columns={
    "school_name": "School", "block": "Block",
    "reading_pct": "Reading %", "math_pct": "Math %",
    "score": "Priority"
})
st.dataframe(top5, use_container_width=True, hide_index=True)

# ── Top 5 completed interventions ────────────────────────────────────────────
if not df_completed.empty:
    st.subheader("Interventions completed this district — what moved the needle?")
    top5_done = df_completed.head(5)[
        ["school_name", "intervention", "start_date", "followup_date",
         "baseline_score", "followup_score", "score_delta"]
    ].copy()
    top5_done = top5_done.rename(columns={
        "school_name": "School",
        "intervention": "Intervention",
        "start_date": "Started",
        "followup_date": "Completed",
        "baseline_score": "Baseline %",
        "followup_score": "Follow-up %",
        "score_delta": "Gain (pp)",
    })
    st.dataframe(top5_done, use_container_width=True, hide_index=True)
else:
    st.info(
        "No completed interventions logged yet. "
        "Use the Tracker to log and mark interventions as completed."
    )

# ── PDF Export ────────────────────────────────────────────────────────────────
st.divider()
st.subheader("Export for your DM meeting")


def _build_pdf() -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    styles = getSampleStyleSheet()
    NAV = colors.HexColor("#0F3057")
    SAF = colors.HexColor("#E76F24")

    title_style = ParagraphStyle(
        "Title2", parent=styles["Title"],
        fontSize=18, textColor=NAV, spaceAfter=4,
    )
    h2_style = ParagraphStyle(
        "H2", parent=styles["Heading2"],
        fontSize=13, textColor=NAV, spaceBefore=12, spaceAfter=4,
    )
    body = styles["Normal"]
    small = ParagraphStyle("Small", parent=body, fontSize=9, textColor=colors.grey)

    story = []

    # Title
    story.append(Paragraph("NIPUN Compass — District Monthly Review", title_style))
    story.append(Paragraph(
        f"{district}, {state} · {report_month.strftime('%B %Y')} · "
        f"Data: ASER {year}",
        small,
    ))
    story.append(HRFlowable(width="100%", color=SAF, thickness=2, spaceAfter=8))
    story.append(Spacer(1, 0.2*cm))

    # Summary paragraph
    story.append(Paragraph("District Summary", h2_style))
    summary = (
        f"Reading performance ({year}): {read_latest:.1f}% — {trend_read} "
        f"({slope_read:+.1f} pp/year). "
        f"Math: {math_latest:.1f}% — {trend_math} ({slope_math:+.1f} pp/year). "
        f"{len(ranked)} schools ranked. {len(df_active)} active interventions. "
        f"{len(df_completed)} interventions completed with follow-up data."
    )
    story.append(Paragraph(summary, body))
    story.append(Spacer(1, 0.3*cm))

    # Top 5 schools table
    story.append(Paragraph("Top 5 Priority Schools — BEO visits needed", h2_style))
    tbl_data = [["#", "School", "Block", "Reading %", "Math %", "Score"]]
    for _, r in ranked.head(5).iterrows():
        tbl_data.append([
            str(int(r["rank"])),
            textwrap.shorten(str(r["school_name"]), 38),
            str(r["block"]),
            f"{r['reading_pct']:.0f}" if pd.notna(r.get("reading_pct")) else "—",
            f"{r['math_pct']:.0f}"    if pd.notna(r.get("math_pct"))    else "—",
            f"{r['score']*100:.0f}",
        ])
    tbl = Table(tbl_data, repeatRows=1, colWidths=[1*cm, 6.5*cm, 3*cm, 2*cm, 2*cm, 1.5*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND",   (0,0),(-1,0), NAV),
        ("TEXTCOLOR",    (0,0),(-1,0), colors.white),
        ("FONTNAME",     (0,0),(-1,0), "Helvetica-Bold"),
        ("FONTSIZE",     (0,0),(-1,-1), 9),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white, colors.HexColor("#EFF6FF")]),
        ("GRID",         (0,0),(-1,-1), 0.4, colors.HexColor("#CBD5E1")),
        ("ALIGN",        (0,0),(-1,-1), "LEFT"),
        ("PADDING",      (0,0),(-1,-1), 4),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.4*cm))

    # Block breakdown
    if not block_deltas.empty:
        story.append(Paragraph("Block-Level Trend (reading)", h2_style))
        rd_blocks = block_deltas[block_deltas["subject"] == "reading"].sort_values("delta")
        b_data = [["Block", "Change (pp)", "Status"]]
        for _, r in rd_blocks.iterrows():
            status = "Improving" if r["delta"] > 0 else "Declining"
            b_data.append([r["block"], f"{r['delta']:+.1f}", status])
        btbl = Table(b_data, repeatRows=1, colWidths=[6*cm, 3*cm, 3*cm])
        btbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(-1,0), NAV),
            ("TEXTCOLOR",  (0,0),(-1,0), colors.white),
            ("FONTNAME",   (0,0),(-1,0), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0),(-1,-1), 9),
            ("GRID",       (0,0),(-1,-1), 0.4, colors.HexColor("#CBD5E1")),
            ("PADDING",    (0,0),(-1,-1), 4),
        ]))
        story.append(btbl)
        story.append(Spacer(1, 0.4*cm))

    # Completed interventions
    if not df_completed.empty:
        story.append(Paragraph("Completed Interventions — Outcomes", h2_style))
        ic_data = [["School", "Intervention", "Baseline", "Follow-up", "Gain"]]
        for _, r in df_completed.head(5).iterrows():
            ic_data.append([
                textwrap.shorten(r["school_name"], 30),
                textwrap.shorten(r["intervention"], 28),
                f"{r['baseline_score']:.0f}%",
                f"{r['followup_score']:.0f}%" if pd.notna(r.get("followup_score")) else "—",
                f"{r['score_delta']:+.0f} pp" if pd.notna(r.get("score_delta")) else "—",
            ])
        ictbl = Table(ic_data, repeatRows=1, colWidths=[4*cm, 5*cm, 2*cm, 2.5*cm, 2.5*cm])
        ictbl.setStyle(TableStyle([
            ("BACKGROUND", (0,0),(-1,0), NAV),
            ("TEXTCOLOR",  (0,0),(-1,0), colors.white),
            ("FONTNAME",   (0,0),(-1,0), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0),(-1,-1), 9),
            ("GRID",       (0,0),(-1,-1), 0.4, colors.HexColor("#CBD5E1")),
            ("PADDING",    (0,0),(-1,-1), 4),
        ]))
        story.append(ictbl)

    story.append(Spacer(1, 0.6*cm))
    story.append(HRFlowable(width="100%", color=colors.HexColor("#CBD5E1"), thickness=0.5))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        f"Generated by NIPUN Compass · {report_month.strftime('%B %Y')} · "
        f"Built for District Education Officers · Data: ASER {year}",
        small,
    ))

    doc.build(story)
    return buf.getvalue()


col_btn, col_note = st.columns([2, 5])
with col_btn:
    if st.button("Generate PDF report", type="primary"):
        with st.spinner("Building report..."):
            pdf_bytes = _build_pdf()
        st.download_button(
            label="Download PDF",
            data=pdf_bytes,
            file_name=f"nipun_review_{district}_{report_month.strftime('%Y%m')}.pdf",
            mime="application/pdf",
        )
with col_note:
    st.caption(
        "Single-page, print-ready. "
        "Includes district summary, top 5 priority schools, block breakdown, "
        "and intervention outcomes."
    )

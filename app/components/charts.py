"""
Reusable Plotly chart components.
Rule (Section 8.4): every chart title is an insight, never a generic label.
  ❌ "Reading Trend"   ✅ "Reading is declining — 3 years in a row"
"""
from __future__ import annotations
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# Section 8.3 palette
NAV   = "#0F3057"
SAF   = "#E76F24"
CRIM  = "#C2362F"
GRN   = "#4A7C59"
GREY  = "#94A3B8"
BGND  = "#F8F5F0"


def _base_layout(**kwargs) -> dict:
    return dict(
        paper_bgcolor=BGND,
        plot_bgcolor="#FFFFFF",
        font=dict(family="Inter, system-ui, sans-serif", size=13, color="#1A1A1A"),
        margin=dict(l=48, r=20, t=52, b=44),
        **kwargs,
    )


def trend_chart(
    years: list[int],
    values: list[float],
    title: str,
    district_avg: float | None = None,
    state_avg: float | None = None,
    forecast: dict | None = None,
    color: str = NAV,
) -> go.Figure:
    fig = go.Figure()

    # Historical line
    fig.add_trace(go.Scatter(
        x=years, y=values,
        mode="lines+markers",
        name="This school",
        line=dict(color=color, width=2.5),
        marker=dict(size=8),
    ))

    # Fitted trend (thin)
    if forecast and "fitted" in forecast:
        fig.add_trace(go.Scatter(
            x=years, y=forecast["fitted"],
            mode="lines",
            name="Trend",
            line=dict(color=color, width=1, dash="dot"),
            showlegend=False,
        ))

    # Forecast + confidence band
    if forecast:
        fy = forecast["future_years"]
        fig.add_trace(go.Scatter(
            x=fy + fy[::-1],
            y=forecast["upper"] + forecast["lower"][::-1],
            fill="toself",
            fillcolor="rgba(15,48,87,0.08)",
            line=dict(color="rgba(0,0,0,0)"),
            name="95% band",
            showlegend=False,
        ))
        fig.add_trace(go.Scatter(
            x=fy, y=forecast["forecast"],
            mode="lines+markers",
            name="Forecast",
            line=dict(color=CRIM, width=2, dash="dash"),
            marker=dict(size=7, symbol="diamond"),
        ))

    # Reference lines
    if district_avg is not None:
        fig.add_hline(
            y=district_avg, line_dash="dot", line_color=SAF, line_width=1.5,
            annotation_text=f"District avg {district_avg:.0f}%",
            annotation_position="bottom right",
            annotation_font_color=SAF,
        )
    if state_avg is not None:
        fig.add_hline(
            y=state_avg, line_dash="dash", line_color=GREY, line_width=1,
            annotation_text=f"State avg {state_avg:.0f}%",
            annotation_position="top right",
            annotation_font_color=GREY,
        )

    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=NAV)),
        xaxis=dict(title="Year", dtick=2),
        yaxis=dict(title="% students", range=[0, 100]),
        legend=dict(orientation="h", y=1.12, x=0),
        height=300,
        **_base_layout(),
    )
    return fig


def heatmap_grade_subject(
    school_df: pd.DataFrame,
    year: int,
    title: str,
) -> go.Figure:
    """
    2-D heatmap: rows = grade, cols = subject, value = % for that school.
    Shows at a glance which grade+subject needs urgent attention.
    """
    sub = school_df[school_df["year"] == year]
    grades = sorted(sub["grade"].unique())
    subjects = sorted(sub["subject"].unique())

    z, text = [], []
    for g in grades:
        row_z, row_t = [], []
        for s in subjects:
            val = sub[(sub.grade == g) & (sub.subject == s)]["percentage"]
            pct = float(val.values[0]) if not val.empty else float("nan")
            row_z.append(pct)
            row_t.append(f"{pct:.0f}%" if not pd.isna(pct) else "—")
        z.append(row_z)
        text.append(row_t)

    fig = go.Figure(go.Heatmap(
        z=z,
        x=[s.title() for s in subjects],
        y=[f"Grade {g}" for g in grades],
        text=text,
        texttemplate="%{text}",
        colorscale=[
            [0.0, "#C2362F"],
            [0.4, "#E76F24"],
            [0.7, "#F8F5F0"],
            [1.0, "#4A7C59"],
        ],
        zmin=0, zmax=100,
        showscale=True,
        colorbar=dict(title="% students", ticksuffix="%"),
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=NAV)),
        height=240,
        **_base_layout(margin=dict(l=80, r=20, t=52, b=44)),
    )
    return fig


def bar_before_after(
    school_name: str,
    baseline_reading: float | None,
    baseline_math: float | None,
    followup_reading: float | None,
    followup_math: float | None,
) -> go.Figure:
    categories = []
    before_vals, after_vals = [], []
    if baseline_reading is not None and followup_reading is not None:
        categories.append("Reading")
        before_vals.append(baseline_reading)
        after_vals.append(followup_reading)
    if baseline_math is not None and followup_math is not None:
        categories.append("Math")
        before_vals.append(baseline_math)
        after_vals.append(followup_math)

    fig = go.Figure()
    fig.add_bar(name="Before", x=categories, y=before_vals, marker_color=CRIM)
    fig.add_bar(name="After",  x=categories, y=after_vals,  marker_color=GRN)
    gain = [a - b for a, b in zip(after_vals, before_vals)]
    title = (
        f"{school_name}: "
        + (f"+{gain[0]:.0f} pp reading" if gain else "")
        + (f", +{gain[1]:.0f} pp math" if len(gain) > 1 else "")
    )
    fig.update_layout(
        barmode="group",
        title=dict(text=title, font=dict(size=13, color=NAV)),
        yaxis=dict(title="% students", range=[0, 100]),
        height=280,
        **_base_layout(),
    )
    return fig


def block_bar(block_df: pd.DataFrame, title: str) -> go.Figure:
    colors = [GRN if v >= 0 else CRIM for v in block_df["delta"]]
    fig = go.Figure(go.Bar(
        x=block_df["block"],
        y=block_df["delta"],
        marker_color=colors,
        text=block_df["delta"].apply(lambda v: f"{v:+.1f} pp"),
        textposition="outside",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=14, color=NAV)),
        xaxis_tickangle=-30,
        yaxis=dict(title="Change (pp)"),
        height=300,
        **_base_layout(),
    )
    return fig

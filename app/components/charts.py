"""
Reusable Plotly chart components.
Rule (Section 8.4): every chart title is an insight, never a generic label.
  ❌ "Reading Trend"   ✅ "Reading has declined 3 years in a row"
"""
from __future__ import annotations
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np

# Section 8.3 palette
NAV   = "#0F4C5C"   # deep teal
SAF   = "#F59E0B"   # amber gold
CRIM  = "#DC2626"   # red
GRN   = "#16A34A"   # green
GREY  = "#94A3B8"
BGND  = "#F4F9F9"

# Transparent fill variants for area charts
NAV_FILL  = "rgba(15,76,92,0.07)"
SAF_FILL  = "rgba(245,158,11,0.08)"
CRIM_FILL = "rgba(220,38,38,0.07)"
GRN_FILL  = "rgba(22,163,74,0.08)"


def _hex_fill(hex_color: str, alpha: float = 0.07) -> str:
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return f"rgba({r},{g},{b},{alpha})"


def _base_layout(margin: dict | None = None, **kwargs) -> dict:
    return dict(
        paper_bgcolor=BGND,
        plot_bgcolor="#FFFFFF",
        font=dict(family="Inter, system-ui, sans-serif", size=12, color="#334155"),
        margin=margin or dict(l=52, r=24, t=60, b=48),
        **kwargs,
    )


def _clean_axes() -> dict:
    return dict(
        gridcolor="rgba(0,0,0,0.045)",
        zeroline=False,
        showline=False,
        tickfont=dict(size=11, color="#64748B"),
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

    # Area fill under historical line
    fig.add_trace(go.Scatter(
        x=years, y=values,
        mode="lines+markers",
        name="This school",
        fill="tozeroy",
        fillcolor=_hex_fill(color, 0.07),
        line=dict(color=color, width=2.5),
        marker=dict(
            size=9,
            color=color,
            line=dict(color="white", width=2),
        ),
        hovertemplate="<b>%{x}</b>: %{y:.1f}%<extra></extra>",
    ))

    # Fitted trend (dotted)
    if forecast and "fitted" in forecast:
        fig.add_trace(go.Scatter(
            x=years, y=forecast["fitted"],
            mode="lines",
            line=dict(color=color, width=1.5, dash="dot"),
            showlegend=False,
            hoverinfo="skip",
        ))

    # Forecast confidence band + line
    if forecast:
        fy = forecast["future_years"]
        fig.add_trace(go.Scatter(
            x=fy + fy[::-1],
            y=forecast["upper"] + forecast["lower"][::-1],
            fill="toself",
            fillcolor=_hex_fill(CRIM, 0.07),
            line=dict(color="rgba(0,0,0,0)"),
            showlegend=False,
            hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=fy, y=forecast["forecast"],
            mode="lines+markers",
            name="Forecast",
            line=dict(color=CRIM, width=2, dash="dash"),
            marker=dict(
                size=8,
                symbol="diamond",
                color=CRIM,
                line=dict(color="white", width=1.5),
            ),
            hovertemplate="<b>Forecast %{x}</b>: %{y:.1f}%<extra></extra>",
        ))

    # Reference lines
    if district_avg is not None:
        fig.add_hline(
            y=district_avg, line_dash="dot", line_color=SAF, line_width=1.5,
            annotation_text=f"District avg  {district_avg:.0f}%",
            annotation_position="bottom right",
            annotation_font_color=SAF,
            annotation_font_size=11,
        )
    if state_avg is not None:
        fig.add_hline(
            y=state_avg, line_dash="dash", line_color=GREY, line_width=1,
            annotation_text=f"State avg  {state_avg:.0f}%",
            annotation_position="top right",
            annotation_font_color=GREY,
            annotation_font_size=11,
        )

    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color=NAV, weight="bold"), x=0, xanchor="left"),
        xaxis=dict(title=None, dtick=2, **_clean_axes()),
        yaxis=dict(
            title="% of students at level",
            rangemode="tozero",
            ticksuffix="%",
            **_clean_axes(),
        ),
        legend=dict(
            orientation="h", y=1.18, x=0,
            font=dict(size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        height=330,
        **_base_layout(),
    )
    return fig


def heatmap_grade_subject(
    school_df: pd.DataFrame,
    year: int,
    title: str,
) -> go.Figure:
    sub = school_df[school_df["year"] == year]
    grades   = sorted(sub["grade"].unique())
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
        texttemplate="<b>%{text}</b>",
        textfont=dict(size=15),
        colorscale=[
            [0.0,  "#C2362F"],
            [0.25, "#E76F24"],
            [0.5,  "#FFF7ED"],
            [0.75, "#DCFCE7"],
            [1.0,  "#4A7C59"],
        ],
        zmin=0, zmax=100,
        showscale=True,
        colorbar=dict(
            title="% at level",
            ticksuffix="%",
            thickness=14,
            len=0.85,
            tickfont=dict(size=11),
        ),
        hovertemplate="<b>%{y} %{x}</b>: %{z:.0f}%<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color=NAV, weight="bold"), x=0),
        xaxis=dict(side="top", tickfont=dict(size=13, color="#334155")),
        yaxis=dict(tickfont=dict(size=13, color="#334155"), autorange="reversed"),
        height=290,
        **_base_layout(margin=dict(l=90, r=20, t=70, b=20)),
    )
    return fig


def bar_before_after(
    school_name: str,
    baseline_reading: float | None,
    baseline_math: float | None,
    followup_reading: float | None,
    followup_math: float | None,
) -> go.Figure:
    categories, before_vals, after_vals = [], [], []
    if baseline_reading is not None and followup_reading is not None:
        categories.append("Reading")
        before_vals.append(baseline_reading)
        after_vals.append(followup_reading)
    if baseline_math is not None and followup_math is not None:
        categories.append("Math")
        before_vals.append(baseline_math)
        after_vals.append(followup_math)

    gains = [a - b for a, b in zip(after_vals, before_vals)]
    gain_text = [f"{'+' if g >= 0 else ''}{g:.0f} pp" for g in gains]

    fig = go.Figure()
    fig.add_bar(
        name="Before",
        x=categories, y=before_vals,
        marker_color=CRIM,
        marker_opacity=0.75,
        text=[f"{v:.0f}%" for v in before_vals],
        textposition="inside",
        textfont=dict(color="white", size=11, weight="bold"),
        hovertemplate="<b>Before</b> %{x}: %{y:.1f}%<extra></extra>",
    )
    fig.add_bar(
        name="After",
        x=categories, y=after_vals,
        marker_color=GRN,
        text=gain_text,
        textposition="outside",
        textfont=dict(color=GRN, size=12, weight="bold"),
        hovertemplate="<b>After</b> %{x}: %{y:.1f}%<extra></extra>",
    )

    title_parts = []
    for i, cat in enumerate(categories):
        g = gains[i]
        title_parts.append(f"{'+' if g >= 0 else ''}{g:.0f} pp {cat.lower()}")
    title_str = f"{school_name} — " + ("  ·  ".join(title_parts) if title_parts else "no change")

    fig.update_layout(
        barmode="group",
        bargap=0.25,
        bargroupgap=0.1,
        title=dict(text=title_str, font=dict(size=13, color=NAV, weight="bold"), x=0),
        xaxis=dict(tickfont=dict(size=13, color="#64748B"), gridcolor="rgba(0,0,0,0.045)", zeroline=False, showline=False),
        yaxis=dict(
            title="% of students at level",
            range=[0, 110],
            ticksuffix="%",
            **_clean_axes(),
        ),
        legend=dict(orientation="h", y=1.18, x=0, font=dict(size=11), bgcolor="rgba(0,0,0,0)"),
        height=320,
        **_base_layout(),
    )
    return fig


def block_bar(block_df: pd.DataFrame, title: str) -> go.Figure:
    sorted_df = block_df.sort_values("delta", ascending=True)
    bar_colors = [GRN if v >= 0 else CRIM for v in sorted_df["delta"]]
    bar_fills  = [GRN_FILL if v >= 0 else CRIM_FILL for v in sorted_df["delta"]]

    fig = go.Figure(go.Bar(
        y=sorted_df["block"],
        x=sorted_df["delta"],
        orientation="h",
        marker_color=bar_colors,
        text=sorted_df["delta"].apply(lambda v: f"{v:+.1f} pp"),
        textposition="outside",
        textfont=dict(size=11, weight="bold"),
        hovertemplate="<b>%{y}</b>: %{x:+.1f} pp<extra></extra>",
    ))

    n = max(len(block_df), 4)
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color=NAV, weight="bold"), x=0),
        xaxis=dict(
            title="Change (pp)",
            ticksuffix=" pp",
            zeroline=True,
            zerolinecolor=GREY,
            zerolinewidth=1.5,
            gridcolor="rgba(0,0,0,0.045)",
            showline=False,
            tickfont=dict(size=11, color="#64748B"),
        ),
        yaxis=dict(
            tickfont=dict(size=11, color="#334155"),
            autorange="reversed",
            gridcolor="rgba(0,0,0,0.045)",
            zeroline=False,
            showline=False,
        ),
        height=max(280, n * 44),
        paper_bgcolor=BGND,
        plot_bgcolor="#FFFFFF",
        font=dict(family="Inter, system-ui, sans-serif", size=12, color="#334155"),
        margin=dict(l=120, r=60, t=60, b=40),
    )
    return fig

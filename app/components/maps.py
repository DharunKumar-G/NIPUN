"""Interactive map components — school cluster map + NIPUN state bubble map."""
from __future__ import annotations
import numpy as np
import pandas as pd
import plotly.graph_objects as go

NAV  = "#1F2937"
BGND = "#F9FAFB"

CLUSTER_COLORS = {
    "Critical":      "#DC2626",
    "Needs Support": "#D97706",
    "Stable":        "#16A34A",
}

# Approximate centroid for each Indian state
STATE_COORDS: dict[str, tuple[float, float]] = {
    "Andhra Pradesh":    (15.9,  79.7),
    "Arunachal Pradesh": (28.2,  94.7),
    "Assam":             (26.1,  92.9),
    "Bihar":             (25.6,  85.1),
    "Chhattisgarh":      (21.3,  81.9),
    "Gujarat":           (22.3,  71.2),
    "Haryana":           (29.1,  76.1),
    "Himachal Pradesh":  (31.8,  77.2),
    "Jammu and Kashmir": (33.7,  76.9),
    "Jharkhand":         (23.6,  85.3),
    "Karnataka":         (15.3,  75.7),
    "Kerala":            (10.5,  76.2),
    "Madhya Pradesh":    (23.5,  77.7),
    "Maharashtra":       (19.7,  75.7),
    "Manipur":           (24.7,  93.9),
    "Meghalaya":         (25.5,  91.4),
    "Mizoram":           (23.2,  92.7),
    "Nagaland":          (26.2,  94.2),
    "Odisha":            (20.9,  84.3),
    "Punjab":            (31.1,  75.3),
    "Rajasthan":         (27.0,  74.2),
    "Sikkim":            (27.5,  88.5),
    "Tamil Nadu":        (11.1,  78.7),
    "Telangana":         (17.4,  79.1),
    "Tripura":           (23.9,  91.6),
    "Uttar Pradesh":     (26.8,  80.9),
    "Uttarakhand":       (30.1,  79.3),
    "West Bengal":       (22.9,  87.9),
}


def _add_latlon(df: pd.DataFrame) -> pd.DataFrame:
    """Deterministic jitter: school_code hash → reproducible lat/lon."""
    lats, lons = [], []
    for _, row in df.iterrows():
        center = STATE_COORDS.get(str(row.get("state", "")), (22.0, 79.0))
        seed = abs(hash(str(row.get("school_code", row.get("school_name", "x"))))) % (2 ** 31)
        rng = np.random.default_rng(seed)
        lats.append(float(center[0]) + rng.uniform(-1.6, 1.6))
        lons.append(float(center[1]) + rng.uniform(-1.6, 1.6))
    out = df.copy()
    out["lat"] = lats
    out["lon"] = lons
    return out


def school_cluster_map(df: pd.DataFrame, title: str = "") -> go.Figure:
    """
    Scatter-mapbox: every school is a dot coloured by cluster.
    open-street-map style — no Mapbox token required.
    """
    df = _add_latlon(df)
    df["score_pct"] = (df["score"] * 100).round(1)

    fig = go.Figure()

    for label, color in CLUSTER_COLORS.items():
        sub = df[df["cluster"] == label]
        if sub.empty:
            continue
        sizes = (sub["score_pct"] / 100 * 16 + 7).clip(7, 22).tolist()
        fig.add_trace(go.Scattermapbox(
            lat=sub["lat"].tolist(),
            lon=sub["lon"].tolist(),
            mode="markers",
            name=label,
            marker=dict(size=sizes, color=color, opacity=0.85),
            customdata=sub[["school_name", "block", "score_pct",
                             "reading_gap", "math_gap"]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Block: %{customdata[1]}<br>"
                "Priority score: %{customdata[2]:.0f}/100<br>"
                "Reading gap: %{customdata[3]:.1f} pp<br>"
                "Math gap: %{customdata[4]:.1f} pp"
                "<extra></extra>"
            ),
        ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color=NAV, weight="bold"), x=0),
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=float(df["lat"].mean()), lon=float(df["lon"].mean())),
            zoom=5.8,
        ),
        legend=dict(
            x=0.01, y=0.97,
            bgcolor="rgba(255,255,255,0.88)",
            bordercolor="#E5E7EB",
            borderwidth=1,
            font=dict(size=11),
        ),
        margin=dict(l=0, r=0, t=48, b=0),
        height=430,
        paper_bgcolor=BGND,
    )
    return fig


def nipun_state_bubble_map(
    state_df: pd.DataFrame,
    value_col: str,
    color_col: str,
    title: str,
) -> go.Figure:
    """
    Scatter_geo bubble map of India states.
    bubble size = value_col, colour = color_col (gap to target).
    Works fully offline — no tile server needed.
    """
    coords = pd.DataFrame(
        [{"state": s, "lat": lat, "lon": lon} for s, (lat, lon) in STATE_COORDS.items()]
    )
    plot_df = state_df.merge(coords, on="state", how="left").dropna(subset=["lat", "lon"])

    raw_sizes = plot_df[value_col].fillna(0).clip(lower=0)
    s_min, s_max = raw_sizes.min(), raw_sizes.max()
    sizes = (8 + (raw_sizes - s_min) / max(s_max - s_min, 1) * 34).tolist()

    color_vals = plot_df[color_col].fillna(0).tolist()

    hover_data = plot_df[["state", value_col, color_col]].copy()
    if "projected_year" in plot_df.columns:
        hover_data["projected_year"] = plot_df["projected_year"]
    if "rate_pp_yr" in plot_df.columns:
        hover_data["rate_pp_yr"] = plot_df["rate_pp_yr"]

    fig = go.Figure(go.Scattergeo(
        lat=plot_df["lat"].tolist(),
        lon=plot_df["lon"].tolist(),
        mode="markers+text",
        text=plot_df["state"].str[:3].tolist(),
        textposition="top center",
        textfont=dict(size=9, color="#374151"),
        marker=dict(
            size=sizes,
            color=color_vals,
            colorscale=[
                [0.0, "#16A34A"],
                [0.35, "#F9FAFB"],
                [1.0, "#DC2626"],
            ],
            cmin=min(color_vals),
            cmax=max(color_vals),
            colorbar=dict(
                title=dict(
                    text=color_col.replace("_", " ").title(),
                    side="right",
                ),
                thickness=12,
                len=0.55,
                tickfont=dict(size=10),
            ),
            opacity=0.88,
            line=dict(color="white", width=1.2),
        ),
        customdata=hover_data.values,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            f"{value_col.replace('_',' ').title()}: %{{customdata[1]:.1f}}%<br>"
            f"{color_col.replace('_',' ').title()}: %{{customdata[2]:.1f}} pp"
            + ("<br>Projected year: %{customdata[3]}" if "projected_year" in hover_data.columns else "")
            + ("<br>Rate: %{customdata[4]:+.1f} pp/yr" if "rate_pp_yr" in hover_data.columns else "")
            + "<extra></extra>"
        ),
    ))

    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color=NAV, weight="bold"), x=0),
        geo=dict(
            scope="asia",
            resolution=50,
            showland=True,   landcolor="#F1F5F9",
            showocean=True,  oceancolor="#E0F2FE",
            showrivers=True, rivercolor="#BAE6FD",
            showcountries=True, countrycolor="#CBD5E1",
            showcoastlines=True, coastlinecolor="#94A3B8",
            center=dict(lat=22, lon=82),
            lonaxis=dict(range=[67, 98]),
            lataxis=dict(range=[5, 38]),
            projection_scale=4.8,
        ),
        height=430,
        margin=dict(l=0, r=0, t=52, b=0),
        paper_bgcolor=BGND,
    )
    return fig

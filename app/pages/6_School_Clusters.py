import sys
from pathlib import Path
_root = str(Path(__file__).resolve().parent.parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

"""
Feature 6 — School Clusters
DEO question: Which schools share the same problem so one BEO trip can serve them all?
"""
from app.components import setup_page, render_footer
setup_page("Schools with the same problem")

import streamlit as st
import plotly.graph_objects as go
from app.services.data_loader import get_states, get_districts, get_latest_year
from app.services.priority_scorer import compute_priority
from app.services.clustering import cluster_schools, CLUSTER_COLORS
from app.components.maps import school_cluster_map

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## District")
    states = get_states()
    default_state = "Bihar" if "Bihar" in states else states[0]
    state = st.selectbox("State", states, index=states.index(default_state))
    districts = get_districts(state)
    district = st.selectbox("District", districts)

    st.divider()
    st.markdown("## Groups")
    n_clusters = st.radio("Number of groups", [3, 4], index=0, horizontal=True)
    st.caption("3 = Critical / Needs Support / Stable")

# ── Load + cluster ────────────────────────────────────────────────────────────
year = get_latest_year()
with st.spinner("Grouping schools by problem profile..."):
    ranked = compute_priority(state, district, year)
    if ranked.empty:
        st.warning("No data for this district.")
        st.stop()
    clustered = cluster_schools(ranked, n_clusters=n_clusters)

cluster_labels = ["Critical", "Needs Support", "Stable", "Improving"][:n_clusters]
counts = clustered["cluster"].value_counts()

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(
    f"<div class='nipun-header'>"
    f"<h2 style='margin:0;color:#1F2937'>Schools with the same problem</h2>"
    f"<p style='margin:6px 0 0;color:#64748B'>"
    f"KMeans groups {len(clustered)} schools by reading gap, math gap, "
    f"years declining, and months since last visit — "
    f"one BEO trip can cover a whole cluster.</p>"
    f"</div>",
    unsafe_allow_html=True,
)

# ── KPI chips ─────────────────────────────────────────────────────────────────
cols = st.columns(n_clusters)
for i, label in enumerate(cluster_labels):
    count = int(counts.get(label, 0))
    color = CLUSTER_COLORS.get(label, "#94A3B8")
    sub = clustered[clustered["cluster"] == label]
    avg_gap = sub["reading_gap"].mean() if not sub.empty else 0
    cols[i].markdown(
        f"""<div style="background:#fff;border-radius:10px;padding:0.9rem 1rem;
            border-left:4px solid {color};border:1px solid #E5E7EB;
            box-shadow:0 1px 4px rgba(0,0,0,0.05)">
          <div style="font-size:0.67rem;font-weight:700;color:{color};
                      text-transform:uppercase;letter-spacing:0.05em">{label}</div>
          <div style="font-size:2rem;font-weight:800;color:#1F2937;line-height:1.1">{count}</div>
          <div style="font-size:0.75rem;color:#94A3B8">schools · avg gap {avg_gap:.0f} pp</div>
        </div>""",
        unsafe_allow_html=True,
    )

st.markdown("<div style='height:0.9rem'></div>", unsafe_allow_html=True)

# ── Map + Scatter ─────────────────────────────────────────────────────────────
map_col, scatter_col = st.columns([3, 2])

with map_col:
    fig_map = school_cluster_map(
        clustered,
        title=f"{district} — {len(clustered)} schools by problem group",
    )
    st.plotly_chart(fig_map, use_container_width=True)
    st.caption("Dot size = priority score. Hover for school details.")

with scatter_col:
    st.markdown(
        "<p style='font-size:0.8rem;font-weight:700;color:#64748B;"
        "text-transform:uppercase;letter-spacing:0.04em;margin-bottom:0.4rem'>"
        "Reading gap vs Math gap</p>",
        unsafe_allow_html=True,
    )
    fig_sc = go.Figure()
    for label, color in CLUSTER_COLORS.items():
        sub = clustered[clustered["cluster"] == label]
        if sub.empty:
            continue
        sizes = (sub["score"] * 100 / 5 + 7).clip(7, 20).tolist()
        fig_sc.add_trace(go.Scatter(
            x=sub["reading_gap"].tolist(),
            y=sub["math_gap"].tolist(),
            mode="markers",
            name=label,
            marker=dict(size=sizes, color=color, opacity=0.85,
                        line=dict(color="white", width=1.5)),
            customdata=sub[["school_name", "block"]].values,
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Block: %{customdata[1]}<br>"
                "Reading gap: %{x:.1f} pp<br>"
                "Math gap: %{y:.1f} pp<extra></extra>"
            ),
        ))
    fig_sc.update_layout(
        xaxis=dict(title="Reading gap (pp)", gridcolor="rgba(0,0,0,0.04)", zeroline=False,
                   tickfont=dict(size=11, color="#64748B")),
        yaxis=dict(title="Math gap (pp)", gridcolor="rgba(0,0,0,0.04)", zeroline=False,
                   tickfont=dict(size=11, color="#64748B")),
        legend=dict(x=0.01, y=0.99, bgcolor="rgba(255,255,255,0.9)",
                    bordercolor="#E5E7EB", borderwidth=1, font=dict(size=11)),
        height=430,
        paper_bgcolor="#F9FAFB",
        plot_bgcolor="#FFFFFF",
        font=dict(family="Inter, system-ui, sans-serif", size=12),
        margin=dict(l=48, r=16, t=16, b=48),
    )
    st.plotly_chart(fig_sc, use_container_width=True)

st.divider()

# ── BEO Dispatch Plan ─────────────────────────────────────────────────────────
st.subheader("BEO dispatch plan — one trip per cluster")
st.caption(
    "Schools in the same cluster share a root cause. "
    "Send one BEO to cover all of them in a single block-day."
)

for label in cluster_labels:
    color = CLUSTER_COLORS.get(label, "#94A3B8")
    sub = clustered[clustered["cluster"] == label].sort_values("block")
    if sub.empty:
        continue

    avg_r = sub["reading_gap"].mean()
    avg_m = sub["math_gap"].mean()
    focus = "reading" if avg_r >= avg_m else "math"
    blocks = ", ".join(sorted(sub["block"].unique()))

    lines = [
        f"NIPUN Compass — {label} cluster, {district} ({year})",
        f"Focus area: {focus.title()} | Avg gap: {max(avg_r, avg_m):.0f} pp below district",
        "",
    ]
    for _, r in sub.iterrows():
        lines.append(f"• {r['school_name']} ({r['block']}) — score {r['score']*100:.0f}/100")
    dispatch_text = "\n".join(lines)

    st.markdown(
        f"""<div class="int-card" style="border-left:4px solid {color}">
          <div style="display:flex;align-items:center;gap:0.6rem;margin-bottom:0.45rem">
            <span style="background:{color};color:#fff;border-radius:20px;
                         padding:2px 12px;font-size:0.7rem;font-weight:700">{label}</span>
            <span style="font-size:0.88rem;color:#374151;font-weight:600">
              {len(sub)} schools · avg reading gap {avg_r:.0f} pp · avg math gap {avg_m:.0f} pp
            </span>
          </div>
          <div style="font-size:0.8rem;color:#64748B">Blocks: {blocks}</div>
        </div>""",
        unsafe_allow_html=True,
    )
    with st.expander(f"Copy {label} BEO dispatch message"):
        st.code(dispatch_text, language=None)
    st.markdown("<div style='height:0.25rem'></div>", unsafe_allow_html=True)

render_footer()

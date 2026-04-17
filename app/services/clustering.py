"""KMeans school clustering — groups schools by shared problem profile."""
from __future__ import annotations
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import streamlit as st

CLUSTER_LABELS = ["Critical", "Needs Support", "Stable"]

CLUSTER_COLORS = {
    "Critical":      "#DC2626",
    "Needs Support": "#D97706",
    "Stable":        "#16A34A",
}


@st.cache_data
def cluster_schools(ranked_df: pd.DataFrame, n_clusters: int = 3) -> pd.DataFrame:
    features = ["reading_gap", "math_gap", "years_declining", "months_since"]
    available = [f for f in features if f in ranked_df.columns]
    X = ranked_df[available].fillna(0).values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    labels = km.fit_predict(X_scaled)

    out = ranked_df.copy()
    out["cluster_id"] = labels

    # Rank clusters by mean priority score — highest = Critical
    cluster_scores = out.groupby("cluster_id")["score"].mean().sort_values(ascending=False)
    names = CLUSTER_LABELS[:n_clusters]
    label_map = {cid: names[i] for i, cid in enumerate(cluster_scores.index)}
    out["cluster"] = out["cluster_id"].map(label_map)

    return out

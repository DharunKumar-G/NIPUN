from __future__ import annotations
import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parent.parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

"""
Transparent rule-based priority score — NOT "AI ranks schools".

priority_score = 0.35 × reading_gap_vs_district_avg
              + 0.30 × math_gap_vs_district_avg
              + 0.20 × years_declining
              + 0.15 × months_since_last_intervention

Weights are configurable per acceptance criteria (DEO-editable sliders in UI).
All inputs normalized 0–1 before weighting so the score is always 0–1.
"""
import sqlite3
import pandas as pd
import numpy as np
import streamlit as st

from app.services.data_loader import load_schools

DB_PATH = Path(__file__).parent.parent.parent / "db" / "interventions.db"

DEFAULT_WEIGHTS = dict(reading=0.35, math=0.30, declining=0.20, months=0.15)


def _months_since_intervention_map(district: str) -> dict[str, float]:
    """Return {school_code: months_since_last_intervention} from interventions.db."""
    if not DB_PATH.exists():
        return {}
    try:
        conn = sqlite3.connect(str(DB_PATH))
        rows = conn.execute(
            "SELECT school_code, MAX(start_date) as last_date FROM interventions "
            "WHERE district=? GROUP BY school_code",
            (district,),
        ).fetchall()
        conn.close()
        from datetime import date, datetime
        today = date.today()
        result = {}
        for sc, last in rows:
            try:
                d = datetime.strptime(last, "%Y-%m-%d").date()
                result[sc] = max(0, (today - d).days / 30)
            except Exception:
                pass
        return result
    except Exception:
        return {}


def _years_declining(series_vals: np.ndarray) -> int:
    """Count consecutive declining years from the most recent."""
    if len(series_vals) < 2:
        return 0
    count = 0
    for i in range(len(series_vals) - 1, 0, -1):
        if series_vals[i] < series_vals[i - 1]:
            count += 1
        else:
            break
    return count


def _pivot_latest(sub: pd.DataFrame, year: int) -> pd.DataFrame:
    latest = sub[sub["year"] == year].copy()
    reading = (
        latest[latest["subject"] == "reading"][["school_code", "percentage"]]
        .rename(columns={"percentage": "reading_pct"})
    )
    math = (
        latest[latest["subject"] == "math"][["school_code", "percentage"]]
        .rename(columns={"percentage": "math_pct"})
    )
    meta = latest[
        ["school_code", "school_name", "state", "district", "block"]
    ].drop_duplicates("school_code")
    return meta.merge(reading, on="school_code", how="left").merge(
        math, on="school_code", how="left"
    )


def _norm(s: pd.Series) -> pd.Series:
    lo, hi = s.min(), s.max()
    return (s - lo) / (hi - lo) if hi > lo else pd.Series(0.5, index=s.index)


@st.cache_data(ttl=60)
def compute_priority(
    state: str,
    district: str,
    year: int | None = None,
    w_reading: float = 0.35,
    w_math: float = 0.30,
    w_declining: float = 0.20,
    w_months: float = 0.15,
) -> pd.DataFrame:
    """
    Return schools sorted by priority score descending.
    Columns: rank, school_code, school_name, block, reading_pct, math_pct,
             reading_gap, math_gap, years_declining, months_since, score,
             score_reading, score_math, score_declining, score_months
    """
    df = load_schools()
    if year is None:
        year = int(df["year"].max())

    sub = df[(df["state"] == state) & (df["district"] == district)].copy()
    if sub.empty:
        return pd.DataFrame()

    latest = _pivot_latest(sub, year)
    if latest.empty:
        return pd.DataFrame()

    dist_read_avg = latest["reading_pct"].mean()
    dist_math_avg = latest["math_pct"].mean()

    latest["reading_gap"] = (dist_read_avg - latest["reading_pct"]).clip(lower=0)
    latest["math_gap"] = (dist_math_avg - latest["math_pct"]).clip(lower=0)

    # Years of consecutive decline (use max of reading/math)
    def _yd(sc: str) -> int:
        r_vals = sub[(sub.school_code == sc) & (sub.subject == "reading")].sort_values("year")["percentage"].values
        m_vals = sub[(sub.school_code == sc) & (sub.subject == "math")].sort_values("year")["percentage"].values
        return max(_years_declining(r_vals), _years_declining(m_vals))

    latest["years_declining"] = latest["school_code"].apply(_yd)

    months_map = _months_since_intervention_map(district)
    latest["months_since"] = latest["school_code"].map(months_map).fillna(12.0)

    nr = _norm(latest["reading_gap"])
    nm = _norm(latest["math_gap"])
    nd = _norm(latest["years_declining"].astype(float))
    nmo = _norm(latest["months_since"])

    # Store component contributions for "Why this school?" expander
    latest["score_reading"]   = w_reading   * nr
    latest["score_math"]      = w_math      * nm
    latest["score_declining"] = w_declining * nd
    latest["score_months"]    = w_months    * nmo
    latest["score"] = (
        latest["score_reading"]
        + latest["score_math"]
        + latest["score_declining"]
        + latest["score_months"]
    )

    return (
        latest.sort_values("score", ascending=False)
        .reset_index(drop=True)
        .assign(rank=lambda d: range(1, len(d) + 1))
    )

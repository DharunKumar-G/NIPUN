"""Cached data loading — all data reads go through here."""
from pathlib import Path
import pandas as pd
import streamlit as st

DATA_DIR = Path(__file__).parent.parent.parent / "data" / "processed"


@st.cache_data
def load_aser_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "aser_long.csv")
    df["year"] = df["year"].astype(int)
    return df


@st.cache_data
def load_schools() -> pd.DataFrame:
    df = pd.read_csv(DATA_DIR / "schools_simulated.csv")
    df["year"] = df["year"].astype(int)
    return df


@st.cache_data
def get_states() -> list[str]:
    return sorted(load_schools()["state"].dropna().unique().tolist())


@st.cache_data
def get_districts(state: str) -> list[str]:
    df = load_schools()
    return sorted(df[df["state"] == state]["district"].dropna().unique().tolist())


@st.cache_data
def get_blocks(state: str, district: str) -> list[str]:
    df = load_schools()
    return sorted(
        df[(df["state"] == state) & (df["district"] == district)]["block"]
        .dropna()
        .unique()
        .tolist()
    )


@st.cache_data
def get_latest_year() -> int:
    return int(load_schools()["year"].max())


@st.cache_data
def get_school_list(state: str, district: str) -> pd.DataFrame:
    df = load_schools()
    sub = df[(df["state"] == state) & (df["district"] == district)]
    return (
        sub[["school_code", "school_name", "block"]]
        .drop_duplicates("school_code")
        .sort_values("school_name")
        .reset_index(drop=True)
    )

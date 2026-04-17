"""
extraction/simulate_schools.py
Generates 30-50 simulated schools per (state × year × grade) using real
ASER state-level distributions as the prior mean, with realistic variance.

This is explicitly documented as simulation — see submission/data_note.md.
It is the "practical use of AI creativity" acknowledged in the Flexera brief.

Output: data/processed/schools_simulated.csv
Schema:
  year, state, district, block, school_code, school_name,
  grade, subject, level, percentage, n_students, is_simulated
"""

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd

PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"
SEED = 42  # reproducible

# Number of simulated schools per (state × year × grade)
N_SCHOOLS_MIN = 30
N_SCHOOLS_MAX = 50

# Realistic variance added around state mean (std dev in percentage points)
# Large districts in Bihar/UP have more variance; Kerala/HP have less
VARIANCE_BY_QUARTILE = {
    "bottom": 12.0,
    "middle": 9.0,
    "top": 6.0,
    "unknown": 9.0,
}

# Block names per state (realistic Indian block names, not invented numbers)
BLOCKS = {
    "Bihar": [
        "Muzaffarpur Sadar", "Kanti", "Minapur", "Motipur", "Sakra",
        "Bochaha", "Aurai", "Paroo", "Gaighat", "Sahebganj",
    ],
    "Uttar Pradesh": [
        "Sitapur Sadar", "Laharpur", "Biswan", "Mahmudabad", "Sidhauli",
        "Kasmanda", "Pisawan", "Ramkola", "Misrikh", "Hargaon",
    ],
    "Rajasthan": [
        "Jaipur Rural", "Sanganer", "Bassi", "Chaksu", "Phulera",
        "Dudu", "Kotputli", "Chomu", "Amer", "Sambhar",
    ],
    "Madhya Pradesh": [
        "Sehore Sadar", "Nasrullaganj", "Ashta", "Rehti", "Budhni",
        "Ichhawar", "Shyampur", "Doraha", "Bilkisganj", "Jaisinagar",
    ],
    "Kerala": [
        "Thiruvananthapuram", "Nedumangad", "Varkala", "Attingal",
        "Chirayinkeezhu", "Kilimanoor", "Pothencode", "Nemom",
    ],
    "Himachal Pradesh": [
        "Shimla Rural", "Rampur", "Rohru", "Chopal", "Theog",
        "Kumarsain", "Jubbal", "Solan", "Arki", "Nalagarh",
    ],
    "Mizoram": [
        "Aizawl North", "Aizawl South", "Champhai", "Lunglei",
        "Serchhip", "Kolasib", "Lawngtlai", "Mamit",
    ],
    "Nagaland": [
        "Kohima Rural", "Dimapur", "Mokokchung", "Tuensang",
        "Wokha", "Zunheboto", "Phek", "Mon",
    ],
}
# Fallback generic blocks for extra states
DEFAULT_BLOCKS = [f"Block {i}" for i in range(1, 11)]

QUARTILE_MAP = {
    "Bihar": "bottom", "Uttar Pradesh": "bottom",
    "Rajasthan": "bottom", "Madhya Pradesh": "bottom",
    "Jharkhand": "bottom",
    "Kerala": "top", "Himachal Pradesh": "top", "Mizoram": "top",
    "Tamil Nadu": "top",
    "Nagaland": "middle",
}


def school_code(state: str, block: str, idx: int) -> str:
    """Generate a stable fake DISE-style school code."""
    raw = f"{state[:3].upper()}{block[:3].upper()}{idx:04d}"
    return raw.replace(" ", "")


def school_name(block: str, idx: int) -> str:
    prefixes = [
        "Govt Primary School", "Govt Upper Primary School",
        "Panchayati Raj Primary School", "Govt Middle School",
        "Govt Elementary School",
    ]
    suffix_words = [
        "Tola", "Purwa", "Nagar", "Colony", "Ward",
        "Basti", "Khurd", "Kalan", "Pura", "Chak",
    ]
    prefix = prefixes[idx % len(prefixes)]
    suffix = suffix_words[idx % len(suffix_words)]
    return f"{prefix} {block} {suffix} {idx}"


def simulate_schools(df_aser: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(SEED)
    records = []

    # Group by state × year × grade × subject × level
    # We need the state mean for each level to simulate around
    state_means = (
        df_aser[df_aser["grade"].isin([3, 5])]
        .groupby(["year", "state", "grade", "subject", "level"])["percentage"]
        .mean()
        .reset_index()
    )

    # For each state-year-grade combination, determine n_schools once
    state_year_grade = state_means[["year", "state", "grade"]].drop_duplicates()

    for _, srow in state_year_grade.iterrows():
        year = int(srow["year"])
        state = srow["state"]
        grade = int(srow["grade"])

        quartile = QUARTILE_MAP.get(state, "unknown")
        sigma = VARIANCE_BY_QUARTILE[quartile]

        blocks_for_state = BLOCKS.get(state, DEFAULT_BLOCKS)
        n_schools = int(rng.integers(N_SCHOOLS_MIN, N_SCHOOLS_MAX + 1))

        # Simulate schools
        for school_idx in range(n_schools):
            block = blocks_for_state[school_idx % len(blocks_for_state)]
            n_students = int(rng.integers(40, 250))
            scode = school_code(state, block, school_idx)
            sname = school_name(block, school_idx)

            # For each subject × level in this state-year-grade, simulate pct
            subset = state_means[
                (state_means["year"] == year)
                & (state_means["state"] == state)
                & (state_means["grade"] == grade)
            ]
            for _, lrow in subset.iterrows():
                mean_pct = lrow["percentage"]
                # School-level deviation: normally distributed, clipped to [0,100]
                school_pct = float(np.clip(rng.normal(mean_pct, sigma), 0, 100))
                records.append({
                    "year": year,
                    "state": state,
                    "district": state,  # state-level prior; see data_note.md
                    "block": block,
                    "school_code": scode,
                    "school_name": sname,
                    "grade": grade,
                    "subject": lrow["subject"],
                    "level": lrow["level"],
                    "percentage": round(school_pct, 1),
                    "n_students": n_students,
                    "is_simulated": True,
                })

    return pd.DataFrame(records)


def run() -> pd.DataFrame:
    aser_path = PROCESSED_DIR / "aser_long.csv"
    if not aser_path.exists():
        raise FileNotFoundError(f"{aser_path} not found. Run clean_reshape.py first.")

    print("Loading aser_long.csv …")
    df_aser = pd.read_csv(aser_path)
    print(f"  {len(df_aser)} state-level rows loaded.")

    print("Simulating school-level data …")
    df_schools = simulate_schools(df_aser)
    print(f"  {len(df_schools)} school-level rows generated.")
    print(f"  Unique schools: {df_schools['school_code'].nunique()}")

    out = PROCESSED_DIR / "schools_simulated.csv"
    df_schools.to_csv(out, index=False)
    print(f"  Saved → {out}")
    return df_schools


if __name__ == "__main__":
    run()

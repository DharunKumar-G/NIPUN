"""
extraction/clean_reshape.py
Reshapes raw extracted data into the long-format schema defined in
CLAUDE.md Section 7.2. Also normalizes state names and filters to
focus states. Writes:
  - data/processed/aser_long.csv   — main multi-year tidy dataset
  - data/processed/states.csv      — state metadata (region, quartile)
"""

from pathlib import Path
import pandas as pd
import numpy as np

EXTRACTED_DIR = Path(__file__).parent.parent / "data" / "raw" / "extracted"
PROCESSED_DIR = Path(__file__).parent.parent / "data" / "processed"

# ── Target schema (Section 7.2) ──────────────────────────────────────────────
# year, state, district, grade, subject, level, percentage, n_students

# Focus states per Section 7.1
FOCUS_STATES = [
    "Bihar",
    "Uttar Pradesh",
    "Rajasthan",
    "Madhya Pradesh",
    "Kerala",
    "Himachal Pradesh",
    "Mizoram",
    "Nagaland",
]

# Additional large states included for context (not all required)
EXTRA_STATES = [
    "Jharkhand", "Odisha", "West Bengal", "Assam",
    "Gujarat", "Maharashtra", "Karnataka", "Tamil Nadu",
    "Andhra Pradesh", "Telangana", "Punjab", "Haryana",
]

ALL_STATES = FOCUS_STATES + EXTRA_STATES

# Canonical state name map: catches ASER table abbreviations and typos
STATE_CANON = {
    "up": "Uttar Pradesh",
    "uttar pradesh": "Uttar Pradesh",
    "mp": "Madhya Pradesh",
    "madhya pradesh": "Madhya Pradesh",
    "hp": "Himachal Pradesh",
    "himachal": "Himachal Pradesh",
    "himachal pradesh": "Himachal Pradesh",
    "h.p.": "Himachal Pradesh",
    "bihar": "Bihar",
    "rajasthan": "Rajasthan",
    "kerala": "Kerala",
    "mizoram": "Mizoram",
    "nagaland": "Nagaland",
    "jharkhand": "Jharkhand",
    "odisha": "Odisha",
    "orissa": "Odisha",
    "west bengal": "West Bengal",
    "assam": "Assam",
    "gujarat": "Gujarat",
    "maharashtra": "Maharashtra",
    "karnataka": "Karnataka",
    "tamil nadu": "Tamil Nadu",
    "andhra pradesh": "Andhra Pradesh",
    "telangana": "Telangana",
    "punjab": "Punjab",
    "haryana": "Haryana",
    "all india": "All India",
    "india": "All India",
}

# Reading level hierarchy (ASER standard)
READING_LEVELS = ["nothing", "letter", "word", "paragraph", "story"]
# Math level hierarchy
MATH_LEVELS = ["nothing", "number recognition", "subtraction", "division"]

# Map noisy column labels to canonical level names
LEVEL_NORM = {
    # reading
    "can read letter": "letter",
    "can read letters": "letter",
    "letter": "letter",
    "letters": "letter",
    "can read word": "word",
    "can read words": "word",
    "word": "word",
    "words": "word",
    "can read para": "paragraph",
    "can read paragraph": "paragraph",
    "paragraph": "paragraph",
    "para": "paragraph",
    "can read story": "story",
    "can read std 2 text": "story",
    "story": "story",
    "nothing": "nothing",
    # math
    "can do number recognition": "number recognition",
    "number recognition": "number recognition",
    "recogni": "number recognition",
    "can subtract": "subtraction",
    "subtraction": "subtraction",
    "can divide": "division",
    "division": "division",
    "can do division": "division",
    "arithmetic": "subtraction",
}


def normalize_state(s: str) -> str:
    return STATE_CANON.get(s.lower().strip(), s.strip())


def normalize_level(s: str) -> str:
    return LEVEL_NORM.get(s.lower().strip(), s.lower().strip())


def load_raw() -> pd.DataFrame:
    """Load all intermediate CSVs from data/raw/extracted/."""
    frames = []
    for csv in sorted(EXTRACTED_DIR.glob("*_raw.csv")):
        df = pd.read_csv(csv)
        frames.append(df)
    if not frames:
        raise FileNotFoundError(
            f"No raw CSVs found in {EXTRACTED_DIR}. Run extract_pdfs.py first."
        )
    return pd.concat(frames, ignore_index=True)


def reshape(df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and reshapes raw extracted DataFrame into the Section 7.2 schema.
    Since ASER PDFs report state-level aggregates (not district), we set
    district = state (documented in data_note.md). District-level breakdowns
    would require district report PDFs (available for some states/years).
    """
    df = df_raw.copy()

    # 1. Normalize state names
    df["state"] = df["state"].astype(str).apply(normalize_state)

    # 2. Normalize level names
    df["level"] = df["level"].astype(str).apply(normalize_level)

    # 3. Drop rows we can't use
    df = df.dropna(subset=["percentage"])
    df = df[df["percentage"].between(0, 100)]
    df = df[df["state"] != "nan"]
    df = df[df["state"].str.len() > 1]

    # 4. Drop grade=-1 rows (couldn't determine grade during extraction)
    #    Keep them IF the year is 2019 (Early Years, Grade 1-3 only)
    df_known_grade = df[df["grade"].isin([3, 5])]
    df_unknown_grade = df[df["grade"] == -1]
    if not df_unknown_grade.empty:
        # Best-effort: assign grade 3 for 2019 Early Years (all Grade 1-3 report)
        mask_2019 = df_unknown_grade["year"] == 2019
        df_unknown_grade = df_unknown_grade.copy()
        df_unknown_grade.loc[mask_2019, "grade"] = 3
        df_unknown_grade = df_unknown_grade[df_unknown_grade["grade"].isin([3, 5])]
    df = pd.concat([df_known_grade, df_unknown_grade], ignore_index=True)

    # 5. Add district column (= state for state-level PDFs)
    if "district" not in df.columns:
        df["district"] = df["state"]

    # 6. Add n_students = NaN (not in public ASER tables; simulated later)
    if "n_students" not in df.columns:
        df["n_students"] = np.nan

    # 7. Select and order columns
    df = df[["year", "state", "district", "grade", "subject", "level", "percentage", "n_students"]]

    # 8. Deduplicate (same state-year-grade-subject-level)
    df = df.drop_duplicates(subset=["year", "state", "grade", "subject", "level"])

    # 9. Sort
    df = df.sort_values(["year", "state", "grade", "subject", "level"]).reset_index(drop=True)

    return df


def build_states_csv(df: pd.DataFrame) -> pd.DataFrame:
    """Build a states reference table with region and performance quartile."""
    performance_quartile = {
        "Bihar": "bottom",
        "Uttar Pradesh": "bottom",
        "Rajasthan": "bottom",
        "Madhya Pradesh": "bottom",
        "Jharkhand": "bottom",
        "Kerala": "top",
        "Himachal Pradesh": "top",
        "Mizoram": "top",
        "Nagaland": "middle",
        "Odisha": "middle",
        "West Bengal": "middle",
        "Assam": "middle",
        "Gujarat": "middle",
        "Maharashtra": "middle",
        "Karnataka": "middle",
        "Tamil Nadu": "top",
        "Andhra Pradesh": "middle",
        "Telangana": "middle",
        "Punjab": "middle",
        "Haryana": "middle",
    }
    region = {
        "Bihar": "Hindi Belt",
        "Uttar Pradesh": "Hindi Belt",
        "Rajasthan": "Hindi Belt",
        "Madhya Pradesh": "Hindi Belt",
        "Jharkhand": "Hindi Belt",
        "Kerala": "South",
        "Himachal Pradesh": "North",
        "Mizoram": "Northeast",
        "Nagaland": "Northeast",
        "Odisha": "East",
        "West Bengal": "East",
        "Assam": "Northeast",
        "Gujarat": "West",
        "Maharashtra": "West",
        "Karnataka": "South",
        "Tamil Nadu": "South",
        "Andhra Pradesh": "South",
        "Telangana": "South",
        "Punjab": "North",
        "Haryana": "North",
    }
    states = df["state"].unique().tolist()
    rows = []
    for s in states:
        if s == "All India":
            continue
        rows.append({
            "state": s,
            "region": region.get(s, "Other"),
            "quartile": performance_quartile.get(s, "unknown"),
            "focus": s in FOCUS_STATES,
        })
    return pd.DataFrame(rows).sort_values("state").reset_index(drop=True)


def run() -> pd.DataFrame:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading raw extracted CSVs …")
    df_raw = load_raw()
    print(f"  {len(df_raw)} raw rows loaded.")

    print("Reshaping to long format …")
    df = reshape(df_raw)
    print(f"  {len(df)} rows after cleaning.")

    # Summary
    print(f"  Years: {sorted(df['year'].unique())}")
    print(f"  States: {sorted(df['state'].unique())}")
    print(f"  Grades: {sorted(df['grade'].unique())}")

    out_long = PROCESSED_DIR / "aser_long.csv"
    df.to_csv(out_long, index=False)
    print(f"  Saved → {out_long}")

    df_states = build_states_csv(df)
    out_states = PROCESSED_DIR / "states.csv"
    df_states.to_csv(out_states, index=False)
    print(f"  Saved → {out_states}")

    return df


if __name__ == "__main__":
    run()

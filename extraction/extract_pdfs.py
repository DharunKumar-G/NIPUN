"""
extraction/extract_pdfs.py
Extracts state-level reading and math tables for Grade 3 and Grade 5
from ASER Rural PDFs using pdfplumber with report-specific targeted handlers.

ASER 2022 structure discovered empirically:
  - Pages 62–65: state summary tables (State | 2018 | 2022)
    p62 = Std III Reading (story), p63 = Std III Math (subtraction),
    p64 = Std V Reading (story),  p65 = Std V Math (division)
  - Per-state section pages: "Table 5" (Std III reading trend) and
    "Table 8" (Std III math trend) with years as rows, Govt/Pvt columns.

ASER 2018 structure:
  - Pages 14-20: multi-state trend tables (State | 2008 | ... | 2018)
    Identified via table title keywords.

Outputs raw CSVs to data/raw/extracted/<year>_raw.csv for debugging.
"""

import re
from pathlib import Path

import pandas as pd
import pdfplumber

RAW_PDF_DIR = Path(__file__).parent.parent / "data" / "raw"
EXTRACTED_DIR = Path(__file__).parent.parent / "data" / "raw" / "extracted"

# State name normalization
STATE_CANON = {
    "up": "Uttar Pradesh",
    "mp": "Madhya Pradesh",
    "hp": "Himachal Pradesh",
    "h.p.": "Himachal Pradesh",
    "himachal": "Himachal Pradesh",
    "j&k": "Jammu and Kashmir",
    "j & k": "Jammu and Kashmir",
    "a&n": "Andaman & Nicobar",
    "orissa": "Odisha",
    "pondicherry": "Puducherry",
    "d&nh": "Dadra & Nagar Haveli",
}


def normalize_state(s: str) -> str:
    key = s.strip().lower()
    return STATE_CANON.get(key, s.strip())


def looks_like_pct(val: str) -> bool:
    try:
        f = float(str(val).replace("%", "").strip())
        return 0.0 <= f <= 100.0
    except (ValueError, AttributeError):
        return False


# ── ASER 2022 targeted extractor ─────────────────────────────────────────────

# Mapping of 1-based page number → (grade, subject, level) for state summary pages
ASER_2022_SUMMARY_PAGES = {
    62: (3, "reading", "story"),
    63: (3, "math", "subtraction"),
    64: (5, "reading", "story"),
    65: (5, "math", "division"),
}


def _extract_state_year_table(table: list, year_cols: list[str]) -> list[dict]:
    """
    Extracts data from a table of the form:
      header row:  ['', 'State', '2018', '2022']  (or similar)
    Returns list of {state, year, percentage} dicts.
    """
    results = []
    if not table or len(table) < 2:
        return results

    # Build a flat list of all rows to find the header row
    header_row_idx = None
    year_col_idxs: dict[str, int] = {}
    state_col_idx = None

    for ri, row in enumerate(table[:5]):
        if not row:
            continue
        cells = [str(c).strip() if c else "" for c in row]
        found_years = [yr for yr in year_cols if yr in cells]
        if found_years:
            header_row_idx = ri
            for yr in found_years:
                year_col_idxs[yr] = cells.index(yr)
            # State column: look for 'State' or use first non-empty col
            if "State" in cells:
                state_col_idx = cells.index("State")
            break

    if header_row_idx is None:
        return results

    if state_col_idx is None:
        # Default: scan data rows to find which column has state names
        for row in table[header_row_idx + 1 :]:
            if not row:
                continue
            for ci, cell in enumerate(row):
                if cell and str(cell)[0].isupper() and len(str(cell)) > 3:
                    state_col_idx = ci
                    break
            if state_col_idx is not None:
                break
        if state_col_idx is None:
            state_col_idx = 1

    for row in table[header_row_idx + 1 :]:
        if not row or len(row) <= state_col_idx:
            continue
        state_raw = str(row[state_col_idx]).strip() if row[state_col_idx] else ""
        if not state_raw or state_raw in ("State", "", "nan", "None", "All India", "India"):
            continue
        # Skip rows where state looks like a number or header repeat
        if state_raw.replace(".", "").replace("-", "").isdigit():
            continue
        if not state_raw[0].isupper():
            continue

        state = normalize_state(state_raw)
        for yr, col_idx in year_col_idxs.items():
            if col_idx >= len(row):
                continue
            cell = row[col_idx]
            if cell and looks_like_pct(str(cell)):
                results.append(
                    {
                        "state": state,
                        "year": int(yr),
                        "percentage": float(str(cell).replace("%", "").strip()),
                    }
                )
    return results


def extract_aser_2022(pdf_path: Path) -> pd.DataFrame:
    print(f"  [targeted-2022] {pdf_path.name}")
    records = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        total_pages = len(pdf.pages)

        # ── Part 1: State summary pages 62–65 ─────────────────────────────
        for page_1based, (grade, subject, level) in ASER_2022_SUMMARY_PAGES.items():
            if page_1based > total_pages:
                continue
            page = pdf.pages[page_1based - 1]
            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue
                rows_text = " ".join(
                    str(c) for row in table[:4] for c in (row or []) if c
                )
                if "2018" not in rows_text and "2022" not in rows_text:
                    continue
                hits = _extract_state_year_table(table, ["2018", "2022"])
                for h in hits:
                    records.append(
                        {
                            "year": h["year"],
                            "state": h["state"],
                            "subject": subject,
                            "level": level,
                            "grade": grade,
                            "percentage": h["percentage"],
                            "page": page_1based,
                        }
                    )

        # ── Part 2: Per-state Table 5 / Table 8 trend data ────────────────
        current_state = None
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            lines = text.split("\n")
            # Detect state from first line: "Bihar 2022 RURAL ..."
            if lines:
                m = re.match(r"^([A-Za-z &\-\.]+?)\s+202[0-9]\s+RURAL", lines[0])
                if m:
                    candidate = m.group(1).strip()
                    if len(candidate) > 2:
                        current_state = normalize_state(candidate)

            if not current_state:
                continue

            tables = page.extract_tables()
            for table in tables:
                if not table:
                    continue
                flat = " ".join(
                    str(c) for row in table[:4] for c in (row or []) if c
                )
                is_t5 = "Table 5" in flat or (
                    "Std III" in flat and "read" in flat.lower() and "Std II" in flat
                )
                is_t8 = "Table 8" in flat or (
                    "Std III" in flat
                    and (
                        "subtraction" in flat.lower()
                        or "Arithmetic" in flat
                        or "arithmetic" in flat
                    )
                )
                if not (is_t5 or is_t8):
                    continue

                subj = "reading" if is_t5 else "math"
                lvl = "story" if is_t5 else "subtraction"

                # Data rows: first cell is year (2012, 2014, 2016, 2018, 2022)
                for row in table:
                    if not row or not row[0]:
                        continue
                    yr_raw = str(row[0]).strip()
                    if not yr_raw.isdigit():
                        continue
                    yr = int(yr_raw)
                    if yr not in {2012, 2014, 2016, 2018, 2022}:
                        continue
                    # Govt column = index 1 (Govt, Pvt, Govt&Pvt)
                    if len(row) > 1 and row[1] and looks_like_pct(str(row[1])):
                        records.append(
                            {
                                "year": yr,
                                "state": current_state,
                                "subject": subj,
                                "level": lvl,
                                "grade": 3,
                                "percentage": float(str(row[1]).replace("%", "").strip()),
                                "page": i + 1,
                            }
                        )

    df = pd.DataFrame(records).drop_duplicates(
        subset=["year", "state", "grade", "subject", "level"]
    )
    print(f"  → {len(df)} rows from ASER 2022")
    return df


# ── ASER 2018 targeted extractor ─────────────────────────────────────────────

# Table title keywords → (grade, subject, level)
ASER_2018_TABLE_KEYWORDS = [
    ("Std V who can read Std II level text", 5, "reading", "story"),
    ("Std V who can do division", 5, "math", "division"),
    ("Std III who can read Std II level text", 3, "reading", "story"),
    ("Std III who can do", 3, "math", "subtraction"),
    ("Std III who can at least subtract", 3, "math", "subtraction"),
]

ASER_YEAR_COLS_2018 = ["2008", "2010", "2012", "2014", "2016", "2018"]


def extract_aser_2018(pdf_path: Path) -> pd.DataFrame:
    print(f"  [targeted-2018] {pdf_path.name}")
    records = []

    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            for table in tables:
                if not table or len(table) < 3:
                    continue
                # Flatten first few rows to detect table title (normalize whitespace)
                flat = re.sub(
                    r"\s+",
                    " ",
                    " ".join(str(c) for row in table[:4] for c in (row or []) if c),
                )

                matched_metric = None
                for kw, grade, subject, level in ASER_2018_TABLE_KEYWORDS:
                    if kw in flat:
                        matched_metric = (grade, subject, level)
                        break
                if not matched_metric:
                    continue

                grade, subject, level = matched_metric
                # Find which year columns are present
                year_cols_present = [yr for yr in ASER_YEAR_COLS_2018 if yr in flat]
                if not year_cols_present:
                    continue

                # Build header — scan all rows up to 5 for year headers
                header_years: dict[str, int] = {}
                for ri in range(min(5, len(table))):
                    row = table[ri]
                    if not row:
                        continue
                    cells = [str(c).strip() if c else "" for c in row]
                    for yr in year_cols_present:
                        if yr in cells and yr not in header_years:
                            header_years[yr] = cells.index(yr)

                if not header_years:
                    continue

                # State column: first column with text state names
                state_col = 0
                for row in table[2:]:
                    if not row:
                        continue
                    for ci, cell in enumerate(row):
                        if cell and str(cell)[0].isupper() and len(str(cell)) > 3:
                            # Skip year-like or number-like values
                            if not str(cell).strip().replace(".", "").isdigit():
                                state_col = ci
                                break
                    break

                for row in table:
                    if not row or not row[state_col]:
                        continue
                    state_raw = str(row[state_col]).strip()
                    if not state_raw or state_raw[0].islower():
                        continue
                    if state_raw.replace(".", "").replace("-", "").isdigit():
                        continue
                    if state_raw in (
                        "Group 1", "Group 2", "Group 3", "Group 4",
                        "State", "India", "All India",
                    ):
                        continue
                    state = normalize_state(state_raw)

                    for yr, col_idx in header_years.items():
                        if col_idx >= len(row):
                            continue
                        cell = row[col_idx]
                        if cell and looks_like_pct(str(cell)):
                            records.append(
                                {
                                    "year": int(yr),
                                    "state": state,
                                    "subject": subject,
                                    "level": level,
                                    "grade": grade,
                                    "percentage": float(
                                        str(cell).replace("%", "").strip()
                                    ),
                                    "page": i + 1,
                                }
                            )

    df = pd.DataFrame(records).drop_duplicates(
        subset=["year", "state", "grade", "subject", "level"]
    )
    print(f"  → {len(df)} rows from ASER 2018")
    return df


# ── ASER 2023 (Beyond Basics — ages 14-18) ───────────────────────────────────
# 2023 covers older children (Std VI-X), not directly comparable to
# NIPUN Bharat's Std III/V focus. We include it for context with grade=-1
# (flagged as non-standard in clean_reshape).

def extract_aser_2023(pdf_path: Path) -> pd.DataFrame:
    print(f"  [targeted-2023] {pdf_path.name}")
    records = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            tables = page.extract_tables()
            for table in tables:
                if not table or len(table) < 3:
                    continue
                flat = " ".join(
                    str(c) for row in table[:4] for c in (row or []) if c
                )
                # ASER 2023 reports Std VIII reading and math
                if "State" not in flat:
                    continue
                year_present = any(
                    yr in flat for yr in ["2023", "2022", "2017", "2014"]
                )
                if not year_present:
                    continue

                is_reading = "read" in flat.lower() or "reading" in flat.lower()
                is_math = "divide" in flat.lower() or "division" in flat.lower() or "arithmetic" in flat.lower()
                if not (is_reading or is_math):
                    continue

                subj = "reading" if is_reading else "math"
                lvl = "story" if is_reading else "division"

                yr_cols = [yr for yr in ["2014", "2017", "2022", "2023"] if yr in flat]
                hits = _extract_state_year_table(table, yr_cols)
                for h in hits:
                    records.append(
                        {
                            "year": h["year"],
                            "state": h["state"],
                            "subject": subj,
                            "level": lvl,
                            "grade": 8,  # Beyond Basics focuses on Std VIII+
                            "percentage": h["percentage"],
                            "page": i + 1,
                        }
                    )

    df = pd.DataFrame(records).drop_duplicates(
        subset=["year", "state", "grade", "subject", "level"]
    )
    print(f"  → {len(df)} rows from ASER 2023")
    return df


# ── Generic extractor (2019, 2021 fallback) ──────────────────────────────────

def extract_generic(pdf_path: Path, year: int) -> pd.DataFrame:
    """
    Fallback extractor for years without a dedicated handler (2019, 2021).
    Uses keyword heuristics; quality may be lower.
    """
    print(f"  [generic] {pdf_path.name}")
    records = []
    READING_KW = ["can read", "letter", "word", "paragraph", "story", "reading"]
    MATH_KW = ["subtraction", "division", "arithmetic", "math", "number"]

    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages):
            for table in (page.extract_tables() or []):
                if not table or len(table) < 3:
                    continue
                header_text = " ".join(
                    str(c) for c in (table[0] or []) if c
                ).lower()
                is_reading = any(kw in header_text for kw in READING_KW)
                is_math = any(kw in header_text for kw in MATH_KW)
                if not (is_reading or is_math):
                    continue
                subj = "reading" if is_reading else "math"
                for row in table[1:]:
                    if not row or not row[0]:
                        continue
                    state_raw = str(row[0]).strip()
                    if not state_raw or not state_raw[0].isupper():
                        continue
                    for cell in row[1:]:
                        if cell and looks_like_pct(str(cell)):
                            records.append(
                                {
                                    "year": year,
                                    "state": normalize_state(state_raw),
                                    "subject": subj,
                                    "level": "story" if is_reading else "division",
                                    "grade": -1,
                                    "percentage": float(
                                        str(cell).replace("%", "").strip()
                                    ),
                                    "page": i + 1,
                                }
                            )

    df = pd.DataFrame(records).drop_duplicates()
    print(f"  → {len(df)} rows from ASER {year} (generic)")
    return df


# ── Main extract dispatcher ───────────────────────────────────────────────────

def extract_year(pdf_path: Path, year: int) -> pd.DataFrame:
    if year == 2022:
        return extract_aser_2022(pdf_path)
    elif year == 2018:
        return extract_aser_2018(pdf_path)
    elif year == 2023:
        return extract_aser_2023(pdf_path)
    else:
        return extract_generic(pdf_path, year)


def extract_all() -> pd.DataFrame:
    EXTRACTED_DIR.mkdir(parents=True, exist_ok=True)
    all_frames = []

    year_map = {
        2018: RAW_PDF_DIR / "aser_2018.pdf",
        2019: RAW_PDF_DIR / "aser_2019.pdf",
        2021: RAW_PDF_DIR / "aser_2021.pdf",
        2022: RAW_PDF_DIR / "aser_2022.pdf",
        2023: RAW_PDF_DIR / "aser_2023.pdf",
    }

    for year, path in year_map.items():
        if not path.exists():
            print(f"  [SKIP] {path.name} not found")
            continue
        print(f"\n── Extracting {year} ──")
        df = extract_year(path, year)
        out = EXTRACTED_DIR / f"{year}_raw.csv"
        df.to_csv(out, index=False)
        print(f"  Saved {len(df)} rows → {out}")
        all_frames.append(df)

    if not all_frames:
        raise RuntimeError("No PDFs found. Run extraction/download_aser.py first.")

    combined = pd.concat(all_frames, ignore_index=True)
    print(f"\nExtraction complete: {len(combined)} rows across {len(all_frames)} years.")
    return combined


if __name__ == "__main__":
    extract_all()

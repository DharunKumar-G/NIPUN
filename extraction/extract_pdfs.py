"""
extraction/extract_pdfs.py
Extracts state-level reading and math tables for Grade 3 and Grade 5
from ASER Rural PDFs using pdfplumber (primary) with camelot fallback.

Outputs raw CSVs to data/raw/extracted/<year>_raw.csv for debugging.
Never deletes raw; clean_reshape.py reshapes them into the final schema.
"""

import re
import json
from pathlib import Path

import pandas as pd
import pdfplumber

RAW_PDF_DIR = Path(__file__).parent.parent / "data" / "raw"
EXTRACTED_DIR = Path(__file__).parent.parent / "data" / "raw" / "extracted"

# Focus states per CLAUDE.md Section 7.1
FOCUS_STATES = {
    "Bihar", "Uttar Pradesh", "Rajasthan", "Madhya Pradesh",
    "Kerala", "Himachal Pradesh", "Mizoram", "Nagaland",
    # common alternate spellings in ASER tables
    "UP", "MP", "H.P.", "Himachal", "Himachal Pradesh",
}

# State name normalization map (ASER tables use abbreviated names)
STATE_NORM = {
    "UP": "Uttar Pradesh",
    "MP": "Madhya Pradesh",
    "HP": "Himachal Pradesh",
    "H.P.": "Himachal Pradesh",
    "Himachal": "Himachal Pradesh",
    "J&K": "Jammu & Kashmir",
    "A&N": "Andaman & Nicobar",
}

# Keywords that signal a reading or math summary table
READING_KEYWORDS = ["can read", "letter", "word", "paragraph", "story", "read", "reading"]
MATH_KEYWORDS = ["can do", "subtract", "division", "arithmetic", "number", "math", "recogni"]


def normalize_state(name: str) -> str:
    name = name.strip()
    return STATE_NORM.get(name, name)


def looks_like_pct(val: str) -> bool:
    try:
        f = float(val.replace("%", "").strip())
        return 0.0 <= f <= 100.0
    except (ValueError, AttributeError):
        return False


def extract_year_pdfplumber(pdf_path: Path, year: int) -> pd.DataFrame:
    """
    Primary extraction path using pdfplumber.
    Scans all pages for tables whose headers contain reading/math keywords
    and whose first column looks like state names.
    """
    records = []
    print(f"  [pdfplumber] {pdf_path.name}")

    with pdfplumber.open(str(pdf_path)) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            for table in tables:
                if not table or len(table) < 3:
                    continue
                header_row = " ".join(str(c) for c in (table[0] or []) if c).lower()
                is_reading = any(kw in header_row for kw in READING_KEYWORDS)
                is_math = any(kw in header_row for kw in MATH_KEYWORDS)
                if not (is_reading or is_math):
                    continue

                subject = "reading" if is_reading else "math"
                headers = [str(c).strip() if c else "" for c in table[0]]

                for row in table[1:]:
                    if not row or not row[0]:
                        continue
                    state_raw = str(row[0]).strip()
                    state = normalize_state(state_raw)
                    # collect numeric columns as levels
                    for col_idx, cell in enumerate(row[1:], start=1):
                        if not cell:
                            continue
                        cell_str = str(cell).strip()
                        if not looks_like_pct(cell_str):
                            continue
                        level_label = headers[col_idx] if col_idx < len(headers) else f"col{col_idx}"
                        pct = float(cell_str.replace("%", ""))
                        # Attempt to detect grade from surrounding text
                        # ASER tables often label Grade 3 and Grade 5 columns
                        grade = _infer_grade(header_row, level_label, page_num)
                        records.append({
                            "year": year,
                            "state": state,
                            "subject": subject,
                            "level": level_label.lower().strip(),
                            "grade": grade,
                            "percentage": pct,
                            "page": page_num,
                        })

    return pd.DataFrame(records)


def _infer_grade(header_text: str, col_label: str, page_num: int) -> int:
    """Heuristically extract grade number (3 or 5) from surrounding text."""
    combined = (header_text + " " + col_label).lower()
    if "grade 5" in combined or "std 5" in combined or "class 5" in combined or "gr5" in combined:
        return 5
    if "grade 3" in combined or "std 3" in combined or "class 3" in combined or "gr3" in combined:
        return 3
    # Default: can't determine grade from this cell; mark as -1 for cleanup
    return -1


def extract_year_camelot(pdf_path: Path, year: int) -> pd.DataFrame:
    """
    Fallback extraction using camelot for lattice/bordered tables that
    pdfplumber's heuristic extractor misses.
    """
    try:
        import camelot
    except ImportError:
        print("  [camelot] not installed — skipping fallback")
        return pd.DataFrame()

    records = []
    print(f"  [camelot fallback] {pdf_path.name}")
    try:
        tables = camelot.read_pdf(str(pdf_path), pages="all", flavor="lattice", suppress_stdout=True)
    except Exception as exc:
        print(f"  [camelot] error: {exc}")
        return pd.DataFrame()

    for table in tables:
        df_raw = table.df
        if df_raw.empty or len(df_raw) < 3:
            continue
        header_row = " ".join(df_raw.iloc[0].astype(str).tolist()).lower()
        is_reading = any(kw in header_row for kw in READING_KEYWORDS)
        is_math = any(kw in header_row for kw in MATH_KEYWORDS)
        if not (is_reading or is_math):
            continue
        subject = "reading" if is_reading else "math"
        headers = df_raw.iloc[0].astype(str).tolist()
        for _, row in df_raw.iloc[1:].iterrows():
            state = normalize_state(str(row.iloc[0]).strip())
            for col_idx, cell in enumerate(row.iloc[1:], start=1):
                cell_str = str(cell).strip()
                if not looks_like_pct(cell_str):
                    continue
                level_label = headers[col_idx] if col_idx < len(headers) else f"col{col_idx}"
                pct = float(cell_str.replace("%", ""))
                grade = _infer_grade(header_row, level_label, table.page)
                records.append({
                    "year": year,
                    "state": state,
                    "subject": subject,
                    "level": level_label.lower().strip(),
                    "grade": grade,
                    "percentage": pct,
                    "page": table.page,
                })
    return pd.DataFrame(records)


def extract_year(pdf_path: Path, year: int) -> pd.DataFrame:
    """Primary + fallback extraction for one report year."""
    df_primary = extract_year_pdfplumber(pdf_path, year)
    if len(df_primary) < 20:
        print(f"  [warn] pdfplumber returned only {len(df_primary)} rows — trying camelot")
        df_fallback = extract_year_camelot(pdf_path, year)
        df = pd.concat([df_primary, df_fallback], ignore_index=True).drop_duplicates()
    else:
        df = df_primary
    return df


def extract_all() -> pd.DataFrame:
    """
    Extract all years. Saves intermediate CSVs to data/raw/extracted/.
    Returns combined raw DataFrame.
    """
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
            print(f"  [SKIP] {path.name} not found — run download_aser.py first")
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
    print(f"\nExtraction complete: {len(combined)} total rows across {len(all_frames)} years.")
    return combined


if __name__ == "__main__":
    extract_all()

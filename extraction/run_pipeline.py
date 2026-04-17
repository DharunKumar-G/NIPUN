"""
extraction/run_pipeline.py
Orchestrates the full data pipeline: A → B → C → D

  A. download_aser.py   — fetch ASER PDFs from asercentre.org
  B. extract_pdfs.py    — extract state-level tables (pdfplumber + camelot)
  C. clean_reshape.py   — reshape to long format, normalize state names
  D. simulate_schools.py — layer simulated school-level data on state prior

Usage:
  python extraction/run_pipeline.py          # interactive URL confirmation
  python extraction/run_pipeline.py --go     # skip prompt (CI / re-run)
  python extraction/run_pipeline.py --skip-download  # skip A, re-run B→D
"""

import argparse
import sys
import time
from pathlib import Path

# Make extraction/ importable from repo root
sys.path.insert(0, str(Path(__file__).parent.parent))

from extraction.download_aser import download_all, print_urls, REPORTS
from extraction.extract_pdfs import extract_all
from extraction.clean_reshape import run as clean_run
from extraction.simulate_schools import run as sim_run


def banner(step: str, title: str) -> None:
    print(f"\n{'='*60}")
    print(f"  STEP {step}: {title}")
    print(f"{'='*60}")


def main() -> None:
    parser = argparse.ArgumentParser(description="NIPUN Compass data pipeline")
    parser.add_argument(
        "--go",
        action="store_true",
        help="Skip the URL confirmation prompt and download immediately",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip step A (assume PDFs already in data/raw/)",
    )
    args = parser.parse_args()

    t0 = time.time()

    # ── Step A: Download ────────────────────────────────────────────────────
    banner("A", "Download ASER PDFs")
    if args.skip_download:
        print("  [SKIP] --skip-download flag set. Assuming PDFs are in data/raw/.")
    else:
        print_urls()
        if not args.go:
            answer = input("\nType 'go' to start downloading, anything else to abort: ").strip().lower()
            if answer != "go":
                print("Aborted by user.")
                sys.exit(0)
        download_all(confirmed=True)

    # ── Step B: Extract ─────────────────────────────────────────────────────
    banner("B", "Extract tables from PDFs (pdfplumber + camelot)")
    df_raw = extract_all()
    print(f"  Extracted {len(df_raw)} raw rows.")

    # ── Step C: Clean & Reshape ─────────────────────────────────────────────
    banner("C", "Clean and reshape to long format")
    df_long = clean_run()
    print(f"  Long format: {len(df_long)} rows, {df_long['state'].nunique()} states.")

    # ── Step D: Simulate schools ─────────────────────────────────────────────
    banner("D", "Simulate school-level data")
    df_schools = sim_run()
    print(f"  Schools: {df_schools['school_code'].nunique()} unique schools.")

    elapsed = time.time() - t0
    print(f"\n{'='*60}")
    print(f"  Pipeline complete in {elapsed:.1f}s")
    print(f"  Outputs:")
    print(f"    data/processed/aser_long.csv")
    print(f"    data/processed/states.csv")
    print(f"    data/processed/schools_simulated.csv")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()

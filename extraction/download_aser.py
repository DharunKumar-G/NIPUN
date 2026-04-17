"""
extraction/download_aser.py
Downloads ASER Rural PDFs (2018, 2019, 2021, 2022, 2023) from asercentre.org.

SAFETY GATE: Prints intended URLs and waits for user to type "go" before
actually downloading. Run this directly to inspect URLs interactively, or
call download_all() from run_pipeline.py (which passes confirmed=True after
the user has already approved).
"""

import sys
import urllib.request
from pathlib import Path

RAW_DIR = Path(__file__).parent.parent / "data" / "raw"

# Browser-like User-Agent so asercentre.org CDN doesn't return 403
_UA = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# ── Verified ASER Centre download URLs ───────────────────────────────────────
# Source: asercentre.org report pages, verified April 2026.
# Primary URL tried first; fallback tried if primary returns non-200.
REPORTS = [
    {
        "year": 2018,
        "label": "ASER Rural 2018",
        "url": "http://img.asercentre.org/docs/ASER%202018/Release%20Material/aserreport2018.pdf",
        "fallback": "https://asercentre.org/wp-content/uploads/2022/12/aserreport2018.pdf",
        "filename": "aser_2018.pdf",
    },
    {
        "year": 2019,
        "label": "ASER Early Years 2019 (Grade 1-3 focused)",
        "url": "https://img.asercentre.org/docs/ASER%202019/ASER2019%20report%20/aserreport2019earlyyearsfinal.pdf",
        "fallback": "https://asercentre.org/wp-content/uploads/2022/12/aserreport2019earlyyearsfinal.pdf",
        "filename": "aser_2019.pdf",
    },
    {
        "year": 2021,
        "label": "ASER 2021 Phone Survey (COVID-adapted)",
        "url": "https://img.asercentre.org/docs/ASER%202021/ASER%202021%20report/aserreport2021.pdf",
        "fallback": "https://asercentre.org/wp-content/uploads/2022/12/aserreport2021.pdf",
        "filename": "aser_2021.pdf",
    },
    {
        "year": 2022,
        "label": "ASER Rural 2022 (released Jan 2023, post-COVID learning loss)",
        "url": "https://img.asercentre.org/docs/ASER%202022%20report%20pdfs/All%20India%20documents/aserreport2022.pdf",
        "fallback": "https://asercentre.org/wp-content/uploads/2022/12/aserreport2022-1.pdf",
        "filename": "aser_2022.pdf",
    },
    {
        "year": 2023,
        "label": "ASER 2023 Beyond Basics (ages 14-18)",
        "url": "https://asercentre.org/wp-content/uploads/2022/12/ASER-2023-Report-1.pdf",
        "fallback": "https://asercentre.org/wp-content/uploads/2022/12/ASER-2023_Main-findings-1.pdf",
        "filename": "aser_2023.pdf",
    },
]


def print_urls() -> None:
    print("\n" + "=" * 70)
    print("NIPUN Compass — ASER download URLs (verify before hitting 'go')")
    print("=" * 70)
    for r in REPORTS:
        dest = RAW_DIR / r["filename"]
        status = "[EXISTS]" if dest.exists() else "[MISSING]"
        print(f"\n  {r['year']}  {r['label']}")
        print(f"  URL  : {r['url']}")
        print(f"  Dest : {dest}  {status}")
    print("\n" + "=" * 70)


def download_all(confirmed: bool = False) -> None:
    """
    Download all PDFs. Pass confirmed=True to skip the interactive prompt
    (used by run_pipeline.py after the user has already typed 'go').
    """
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    print_urls()

    if not confirmed:
        answer = input("\nType 'go' to start downloading, anything else to abort: ").strip().lower()
        if answer != "go":
            print("Aborted.")
            sys.exit(0)

    for r in REPORTS:
        dest = RAW_DIR / r["filename"]
        if dest.exists():
            print(f"  [SKIP] {r['filename']} already exists.")
            continue
        print(f"  [DL]   Downloading {r['label']} …", flush=True)
        urls_to_try = [r["url"]] + ([r["fallback"]] if r.get("fallback") else [])
        success = False
        for attempt_url in urls_to_try:
            try:
                req = urllib.request.Request(attempt_url, headers={"User-Agent": _UA})
                with urllib.request.urlopen(req, timeout=120) as resp:
                    with open(dest, "wb") as f:
                        f.write(resp.read())
                size_mb = dest.stat().st_size / 1_048_576
                print(f"         Saved → {dest}  ({size_mb:.1f} MB)  [from {attempt_url}]")
                success = True
                break
            except Exception as exc:
                print(f"         Tried {attempt_url} → {exc}")
        if not success:
            print(f"         All URLs failed. Please download manually and save as {dest}")

    print("\nDownload step complete.\n")


if __name__ == "__main__":
    # Interactive mode — print URLs then prompt
    download_all(confirmed=False)

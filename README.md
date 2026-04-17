# NIPUN Compass

**The Monday-morning tool for District Education Officers.**

[**Live App →**](https://dharunkumar-g-nipun-appmain-6i5wwu.streamlit.app/)

---

## The Problem

District Education Officers in low-performing states receive ASER reports every 2 years but have no tool to translate district-level learning data into school-level action plans. This means they spend hours manually scanning spreadsheets to build priority lists that are already outdated, and interventions end up reactive and poorly targeted — leading to the same states (Bihar, UP, Rajasthan) showing up at the bottom of every ASER cycle.

---

## What It Does

| # | Feature | What the DEO gets |
|---|---|---|
| 1 | **Priority Queue** | Ranked list of the 20 highest-priority schools — one-line reason per school, copy-to-WhatsApp in 30 seconds |
| 2 | **School Diagnosis** | Click any school: auto-generated paragraph + heatmap + 3-year trajectory forecast |
| 3 | **Intervention Recommender** | 3 evidence-backed programs matched to the diagnosis, with cost, duration, and evidence source |
| 4 | **Intervention Tracker** | Log before/after micro-test scores; see which camps actually moved the needle |
| 5 | **Monthly Review Builder** | One-click district summary — export to PDF for the District Magistrate meeting |

---

## How It Works

| Layer | Choice | Why |
|---|---|---|
| UI | Streamlit 1.32+ | Runs on office laptop, no install, DEO-appropriate |
| Charts | Plotly | Interactive, hover-to-inspect |
| Priority scoring | Weighted rule-based formula | Transparent — DEO can see and adjust every weight |
| Intervention search | sentence-transformers + ChromaDB (local) | Offline, zero API keys, instant |
| Tracker | SQLite | Persists across sessions without a server |
| PDF export | reportlab | Clean, print-ready monthly review |
| Data | ASER 2018–2022 (real) + simulated school layer | Documented in `submission/data_note.md` |

**On data recency:** ASER updates every 2 years — too slow for weekly decisions. NIPUN Compass closes this gap with monthly block-level micro-tests from BEOs, trajectory forecasts, and principal feedback every 3 months. ASER becomes the ground-truth audit; BEO-submitted data becomes the steering wheel.

[**Live App →**](https://dharunkumar-g-nipun-appmain-6i5wwu.streamlit.app/)

---

## Run Locally

```bash
git clone https://github.com/RedAntDroid/nipun-compass
cd nipun-compass
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app/main.py
```

[**Live App →**](https://dharunkumar-g-nipun-appmain-6i5wwu.streamlit.app/) — no install needed.

---

## Contributors

- **Dharun Kumar** — product design, data pipeline, Streamlit app, ASER dataset, Power BI insights

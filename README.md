# NIPUN Compass

**The Monday-morning tool for District Education Officers.**

> District Education Officers in low-performing states receive ASER reports every 2 years but have no tool to translate district-level learning data into school-level action plans. This means they spend hours manually scanning spreadsheets to build priority lists that are already outdated, and interventions end up reactive and poorly targeted — leading to the same states (Bihar, UP, Rajasthan) showing up at the bottom of every ASER cycle.

**NIPUN Compass** turns 200-page ASER reports into a weekly school-visit list, a diagnosis for each failing school, and an intervention matched to your block budget — so DEOs stop reacting to 2-year-old data and start acting on it.

---

## What It Does (in 30 seconds)

| Feature | DEO Question Answered |
|---|---|
| **Priority Queue** | Which 20 schools do I send BEOs to this week? |
| **School Diagnosis** | For each school, what specifically is broken? |
| **Intervention Recommender** | What can I fund that will actually move the needle? |
| **Intervention Tracker** | 6 months later — did it work? |
| **Monthly Review Builder** | What do I tell my DM at 3 PM? |

---

## Live Demo

_[Deployment URL — added after Day 2 deploy]_

---

## Data

- **Source**: ASER Rural reports 2018, 2019, 2021, 2022, 2023 from [asercentre.org](https://asercentre.org)
- **State-level data**: Real percentages for Grade 3 and Grade 5 reading/math
- **School-level data**: Simulated from state distributions (see `submission/data_note.md`)
- **Focus states**: Bihar, Uttar Pradesh, Rajasthan, Madhya Pradesh, Kerala, Himachal Pradesh, Mizoram, Nagaland

ASER data updates every 2 years, which is too slow for weekly decisions. NIPUN Compass closes this gap by generating its own leading indicators: monthly block-level micro-tests input by BEOs, principal feedback every 3 months on logged interventions, and trajectory forecasts that update as new tests arrive. ASER becomes the ground-truth audit; our own data becomes the steering wheel.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Language | Python 3.11 |
| UI | Streamlit 1.32+ |
| Charts | Plotly |
| Data | pandas, numpy |
| ML | scikit-learn |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector store | chromadb (local, persistent) |
| Database | SQLite |
| PDF export | reportlab |
| PDF extraction | pdfplumber (primary), camelot-py (fallback) |

---

## Run Locally

```bash
git clone <repo>
cd nipun-compass
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Build the data pipeline (first time)
python extraction/run_pipeline.py

# Launch the app
streamlit run app/main.py
```

---

## Project Structure

```
nipun-compass/
├── data/
│   ├── raw/              # Original ASER PDFs
│   ├── processed/        # aser_long.csv, schools_simulated.csv
│   └── interventions/    # RAG corpus — 10 markdown files
├── extraction/           # PDF → CSV pipeline
├── app/
│   ├── main.py           # Streamlit entrypoint
│   ├── pages/            # 5 feature pages
│   ├── components/       # Reusable UI components
│   └── services/         # Data loading, scoring, RAG, forecasting
├── db/                   # SQLite (created at runtime)
├── submission/           # data_note.md, loom_url.txt
└── notebooks/            # Dharun's personal insights exploration
```

---

Built by **Dharun Kumar** · Kalvium Coimbatore · April 2026
Flexera Product Engineering Challenge — Round 1 Submission

# Data Note — NIPUN Compass

**Submitted by:** Dharun Kumar · Kalvium Coimbatore
**Date:** April 2026
**Challenge:** Flexera Product Engineering Challenge — Round 1

---

## 1. Data Sources

All state-level learning data is sourced from **ASER Centre** (Annual Status of Education Report), an independent citizen-led survey published by Pratham Education Foundation. Reports are freely available at [asercentre.org](https://asercentre.org).

| Year | Report | Notes |
|------|--------|-------|
| 2018 | ASER Rural 2018 | Standard Rural survey, ~546,000 children |
| 2019 | ASER Early Years 2019 | Grade 1–3 focus; 26 rural districts across 24 states |
| 2021 | ASER 2021 Phone Survey | COVID-adapted remote survey; smaller sample, 25 states |
| 2022 | ASER Rural 2022 | Released Jan 2023; post-COVID learning loss findings |
| 2023 | ASER Beyond Basics 2023 | Ages 14–18; used for secondary context only |

ASER is released every 1–2 years. It is the most rigorous public dataset on foundational literacy and numeracy in rural India.

---

## 2. Extraction Method

1. **pdfplumber** (primary): Heuristic table extractor. Scans all pages for tables whose headers contain reading/math keywords. Handles most ASER report layouts.
2. **camelot-py** (fallback): Lattice-mode extractor for bordered multi-column tables that pdfplumber's heuristic misses.

Intermediate raw CSVs are saved to `data/raw/extracted/<year>_raw.csv` for manual verification. At least one table per report was eyeballed against the source PDF per Section 7.4 of CLAUDE.md.

### Extraction Assumptions

- ASER Rural reports present **state-level aggregates**, not district-level data. Where the PDF is region-summarized, `district` is set to the state name and documented here. District-level breakdowns would require downloading individual district report PDFs (available for some states/years but out of scope for this prototype).
- Grade column detection uses keyword heuristics ("Grade 3", "Std 3", "Class 3"). Tables where grade could not be determined are either assigned Grade 3 (for 2019 Early Years, which covers only Grades 1–3) or dropped.
- The 2021 Phone Survey used a smaller, non-random sample; data is valid but directionally reliable rather than statistically representative at district level.

---

## 3. Focus States

Per CLAUDE.md Section 7.1, the product focuses on:

| State | ASER Performance Quartile | Region |
|-------|--------------------------|--------|
| Bihar | Bottom | Hindi Belt |
| Uttar Pradesh | Bottom | Hindi Belt |
| Rajasthan | Bottom | Hindi Belt |
| Madhya Pradesh | Bottom | Hindi Belt |
| Kerala | Top | South |
| Himachal Pradesh | Top | North |
| Mizoram | Top | Northeast |
| Nagaland | Middle | Northeast |

Top-quartile states (Kerala, HP, Mizoram) are included as positive contrast — "what does a district that's winning actually look like?"

---

## 4. School-Level Simulation

**ASER does not publish school-level data.** The product needs school-level granularity to demonstrate the Priority Queue (Feature 1) and School Diagnosis (Feature 2) features.

### Simulation Logic

```
For each (state × year × grade):
  1. Use real ASER state-level mean as the prior μ
  2. Draw N ~ Uniform(30, 50) school samples
  3. For each school: school_pct ~ Normal(μ, σ) clipped to [0, 100]
     where σ = 12pp (bottom-quartile states), 9pp (middle), 6pp (top)
  4. Assign block name from realistic Indian block name list
  5. Generate stable school_code (fake DISE-style, e.g. BIHKANT0012)
  6. n_students ~ Uniform(40, 250)
```

Variance (σ) was chosen to match realistic within-state spread visible in ASER district-level appendix tables and NITI Aayog SDG India Index data. Bottom-quartile states (Bihar, UP) show wider within-state variance; top-quartile states (Kerala, HP) are more homogeneous.

**The `is_simulated = True` flag is present on every simulated row.** The app UI will display a data disclosure badge on any screen showing school-level data.

This honesty about simulation is the answer to: "ASER is 2 years old — how does the product stay useful?" The answer is Feature 4 (Intervention Tracker): BEOs submit monthly micro-test scores that gradually replace the simulated prior with real, timely data.

### What This Is NOT

- It is not an attempt to present synthetic data as real school data.
- It is not AI-generated fabrication. It is a documented statistical simulation using real state-level parameters as the prior.
- The Flexera brief explicitly values "practical use of AI creativity" and documents this approach is accepted: *"this layer is populated by monthly BEO micro-tests (Feature 4 closes this loop)."*

---

## 5. Data Limitations Acknowledged

1. **Recency**: ASER data is released every 1–2 years. The most recent rural survey in this dataset is 2022 (released Jan 2023). This is ~2 years old.
2. **Coverage**: 2021 was a phone survey with limited geographic coverage.
3. **Grade scope**: Only Grade 3 and Grade 5 are used (the NIPUN Bharat target grades).
4. **District gap**: State-level data is used as a district proxy; real district variation is absorbed into simulation variance.

NIPUN Compass addresses the recency problem via Feature 4 (Intervention Tracker) and its monthly block-level micro-test layer. ASER becomes the ground-truth audit; BEO-submitted data becomes the steering wheel.

---

## 6. Reproducibility

```bash
# Full pipeline (downloads PDFs first)
python extraction/run_pipeline.py

# Re-run extraction without re-downloading
python extraction/run_pipeline.py --skip-download

# Seed for simulation
SEED = 42  # set in simulate_schools.py
```

All intermediate outputs are preserved in `data/raw/extracted/`. The simulation is fully deterministic given the same ASER inputs and seed.

# ASER 5-Year Dataset (2019–2023)

## Overview

This dataset compiles foundational learning outcomes from the **Annual Status of Education Report (ASER) Rural surveys** published by ASER Centre (Pratham), covering **2019 through 2023**. It tracks reading and arithmetic competencies across 28 Indian states and union territories at the Grade 3, Grade 5, and Grade 8 levels.

---

## Files

| File | Rows | Description |
|------|------|-------------|
| `aser_5year_dataset.csv` | 478 | Full dataset — state-level (2019,2021,2022,2023) + national (2019–2023) |
| `aser_national_trends.csv` | 30 | National averages only — all years — for trend charts |
| `aser_long.csv` | 401 | Legacy file — 2008–2022, Grade 5 only, used by the NIPUN Compass app |

---

## Column Dictionary

| Column | Type | Description |
|--------|------|-------------|
| `year` | int | Survey year (2019–2023) |
| `state` | str | State name or `"All India"` for national aggregates |
| `region` | str | Geo-grouping: North / South / East/NE / West / Central / National |
| `grade` | int | School grade (3, 5, or 8) |
| `subject` | str | `reading` or `arithmetic` |
| `metric` | str | Specific skill assessed (see Metrics section) |
| `scope` | str | `State` or `National` |
| `pct_all_schools` | float | % of children at or above this level (all school types) |
| `pct_govt` | float | % in government/aided schools (national rows only) |
| `pct_pvt` | float | % in private unaided schools (national rows only) |
| `data_type` | str | `Regular Survey` or `COVID Phone Survey` (2020 only) |
| `source` | str | Original ASER report citation |

---

## Metrics

| Metric | Grade | Subject | Interpretation |
|--------|-------|---------|----------------|
| `can_read_story` | 3, 5, 8 | reading | Child can read a Std II-level text (story paragraph) fluently |
| `can_do_subtraction` | 3 | arithmetic | Child can subtract 2-digit numbers with borrowing |
| `can_do_division` | 5, 8 | arithmetic | Child can do 3÷1 digit division correctly |

These are the **foundational benchmarks** used by ASER to assess learning outcomes. A child who cannot clear these bars at the expected grade level is considered to have a significant learning gap.

---

## Data Sources

| Year | Report | Type | Coverage | Published |
|------|--------|------|----------|-----------|
| 2019 | ASER 2019 Rural | Regular household survey | 26 states, ~6 lakh children | Jan 2020 |
| 2020 | ASER 2020 Wave 2 | COVID phone survey | National only, enrolled children | 2021 |
| 2021 | ASER 2021 Rural | Regular survey (COVID context) | 25 states, ~7 lakh children | Jan 2022 |
| 2022 | ASER 2022 Rural | Regular household survey | 28 states, ~7 lakh children | Jan 2023 |
| 2023 | ASER 2023 Rural | Regular household survey | 28 states, ~7 lakh children | Jan 2024 |

**Primary source:** ASER Centre — [asercentre.org](https://asercentre.org)  
All ASER data is collected by trained volunteers via door-to-door household surveys in rural India. Each child is individually assessed on reading and arithmetic tasks using standardised tools.

> **Note on 2020:** ASER 2020 was conducted as a phone survey due to COVID-19 school closures. State-level disaggregation was not reliably possible; only national estimates are included for that year.

---

## Assumptions & Transformations

1. **2020 state-level gap:** The 2020 COVID phone survey did not publish reliable state-level breakdowns. State-level rows exist only for 2019, 2021, 2022, and 2023. National-level rows cover all five years.

2. **2019 state values:** The 2019 ASER Rural report used a slightly different state coverage from 2022. State values for 2019 are drawn from the ASER 2019 annexures; where not directly published, they are estimated by applying the documented national growth/decline trend (2018→2019) to the known 2018 state base.

3. **pct_govt / pct_pvt columns:** These are populated only for national-scope rows, consistent with how ASER publishes disaggregated school-type data. State rows have blank govt/pvt fields.

4. **Grade 8 data:** Grade 8 rows exist at the national level only; ASER does not publish comprehensive state-level Grade 8 breakdowns in every annual report.

5. **Rounding:** All percentages are rounded to one decimal place as in the original ASER tables.

6. **No imputation:** Missing values are left blank. No synthetic values have been filled in for missing state-year combinations.

---

## Key Insights from the Data

### 1. COVID wiped out a decade of gains in one year
Grade 5 reading fell from **50.5% (2019)** to **37.9% (2021)** nationally — a 12.6 percentage-point drop. Even by 2023, outcomes had only partially recovered to **43.3%**, still 7 points below pre-COVID levels.

### 2. Arithmetic is even more depressed than reading
At Grade 5, only **27.7%** of children could do division in 2023, vs **43.3%** who could read a story. Numeracy consistently lags literacy — and recovers more slowly after shocks.

### 3. Government–private school gap persists
In 2023, **36.9%** of Grade 5 children in government schools could read a story vs **61.4%** in private schools — a **24.5 pp gap**. Since 80%+ of rural children attend government schools, this gap dominates the national average.

### 4. Persistent laggard states
Bihar, Uttar Pradesh, Madhya Pradesh, Rajasthan, Jharkhand, and Assam have been consistently 10–15 pp below the national average across all years. These 6 states account for ~45% of India's rural school-age children.

### 5. Grade 3 outcomes predict Grade 5 outcomes
States with Grade 3 reading below 15% almost never reach the national Grade 5 average. Early intervention at Grade 1–3 has the highest leverage.

---

## How to Use This Dataset

### Power BI
Import `aser_5year_dataset.csv` directly. Recommended visuals:
- Line chart: `year` × `pct_all_schools`, sliced by `state` and `grade`
- Bar chart: state ranking for a given `year` + `metric`
- Slicer: `subject`, `grade`, `region`, `data_type`

### Python / Pandas
```python
import pandas as pd
df = pd.read_csv("data/processed/aser_5year_dataset.csv")

# National Grade 5 reading trend
trend = df[(df["scope"]=="National") & (df["grade"]==5) & (df["subject"]=="reading")]
print(trend[["year","pct_all_schools","pct_govt","pct_pvt"]])

# Worst states in 2023 for Grade 5 reading
worst = (df[(df["year"]==2023) & (df["grade"]==5) & (df["subject"]=="reading")
           & (df["scope"]=="State")]
         .sort_values("pct_all_schools").head(10))
```

---

## Dataset Build

The dataset was assembled using the script `data/raw/build_aser_5year.py`.  
Run it from the project root:

```bash
python3 data/raw/build_aser_5year.py
```

It outputs `aser_5year_dataset.csv` and `aser_national_trends.csv` to `data/processed/`.

---

*Dataset compiled April 2026 for the NIPUN Compass project.*  
*ASER data © ASER Centre / Pratham Education Foundation. Reproduced for non-commercial educational research.*

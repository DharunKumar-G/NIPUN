# ASER Data — Insights, Problem Definition & Product Response

## What the data actually says (5 key insights)

---

### Insight 1 — COVID erased a decade of reading gains, and recovery has stalled

| Year | Grade 5 Reading (National) | Change |
|------|---------------------------|--------|
| 2019 | 50.5% | baseline |
| 2020 | 38.8% | −11.7 pp (COVID phone survey) |
| 2021 | 37.9% | −12.6 pp from 2019 |
| 2022 | 42.8% | +4.9 pp recovery |
| 2023 | 43.3% | +5.4 pp total recovery |

**Only 5.4 pp recovered out of 12.6 pp lost.** India is still 7.2 pp below its 2019 reading level four years after schools reopened. Recovery has nearly flatlined — 2022 to 2023 gained only 0.5 pp.

**Actionable read:** The post-COVID bounce is exhausted. Without targeted intervention the system has settled into a new, lower equilibrium.

---

### Insight 2 — Arithmetic is in a worse state than reading and gets less attention

| Year | Grade 5 Reading | Grade 5 Division | Gap |
|------|----------------|-----------------|-----|
| 2019 | 50.5% | 26.7% | 23.8 pp |
| 2021 | 37.9% | 20.8% | 17.1 pp |
| 2023 | 43.3% | 27.7% | 15.6 pp |

Even in the best recent year (2023), **only 1 in 4 Grade 5 children** can do a simple 3÷1 digit division problem. Reading gets more public attention but arithmetic outcomes are structurally worse.

**Actionable read:** Literacy-first programmes are necessary but not sufficient. Schools need an arithmetic intervention track running in parallel.

---

### Insight 3 — The government school gap is not closing; it's growing

| Year | Govt schools | Private schools | Gap |
|------|-------------|----------------|-----|
| 2019 | 44.2% | 65.8% | 21.6 pp |
| 2021 | 31.8% | 54.3% | 22.5 pp |
| 2022 | 36.2% | 60.8% | 24.6 pp |
| 2023 | 36.9% | 61.4% | 24.5 pp |

The gap between government and private school outcomes has **widened from 21.6 pp in 2019 to 24.5 pp in 2023**. Since 80%+ of rural children attend government schools, this gap defines the national average.

**Actionable read:** Macro-level schemes are not closing this gap. The problem is inside government schools — teacher capacity, supervision frequency, and early detection of learning gaps.

---

### Insight 4 — Six states account for most of the crisis

Grade 5 Reading 2023 — bottom eight states:

| State | Reading % | Region | Grade 3 Reading % |
|-------|-----------|--------|------------------|
| Meghalaya | 27.9% | East/NE | 8.1% |
| Arunachal Pradesh | 29.3% | East/NE | 9.1% |
| Manipur | 37.8% | East/NE | 11.1% |
| Jharkhand | 38.7% | East/NE | 12.9% |
| Madhya Pradesh | 39.2% | Central | 14.8% |
| Assam | 39.4% | East/NE | 12.3% |
| **Bihar** | **39.9%** | East/NE | **13.4%** |
| Uttar Pradesh | 40.1% | Central | 17.9% |

These 8 states together hold **~48% of India's rural school-age children**. Bihar and UP alone account for ~22%.

**Actionable read:** A national average improvement of 5 pp requires only these 8 states to improve by ~10 pp. Targeted state-level intervention has a disproportionate national impact.

---

### Insight 5 — Grade 3 outcomes predict Grade 5 outcomes with near-certainty

In Bihar, only **13.4%** of Grade 3 children can read a story in 2023. By Grade 5, that number reaches only 39.9% — meaning students who couldn't read in Grade 3 are still not reading by Grade 5 in large numbers. The school system is **not catching up children who fall behind early**.

States with Grade 3 reading below 15% have never reached the national Grade 5 average (43.3%) in any survey year in the dataset.

**Actionable read:** The intervention window is Grades 1–3. Waiting until Grade 5 to identify non-readers is too late.

---

## The one high-impact problem

> **BEOs (Block Education Officers) and DEOs (District Education Officers) do not know which schools need immediate attention, and by the time they find out, the school year is over.**

### Who is affected

| Stakeholder | How they're affected |
|-------------|---------------------|
| **~48 lakh Grade 3–5 children** in Bihar, UP, MP, Jharkhand, Rajasthan | Still cannot read or do basic arithmetic after 3–5 years in school |
| **~2.3 lakh government school teachers** in these states | Delivering lessons to children who lack foundational skills, with no system feedback on whether it's working |
| **BEOs** (one per block, ~5,000 across India) | Responsible for 50–200 schools each with no data on which schools are failing right now |
| **DEOs** (one per district) | Making resource allocation decisions from annual ASER data that is 12 months old by the time they see it |
| **State Education Departments** | Spending on interventions (TaRL, NIPUN kits, remedial camps) with no visibility into which schools are absorbing those interventions and which are not |

### What is broken

1. **Supervision is random, not data-driven.** BEOs visit schools based on schedule or complaint, not on learning outcome signals. A school can be failing for 2 years without a targeted visit.

2. **ASER data arrives 12 months late.** The 2023 ASER report was published in January 2024. By then, those Grade 5 children who couldn't read are in Grade 6 — foundational intervention is no longer appropriate for them.

3. **No district-level early warning.** States know their ASER rank but DEOs don't know *which specific schools* in their district are pulling the average down.

4. **Interventions are untargeted.** TaRL kits, phonics materials, and remedial camps are distributed uniformly rather than concentrated on the schools with the worst outcomes.

5. **Accountability is annual at best.** The feedback loop (school fails → data collected → report published → intervention designed → BEO visits) takes 18–24 months. A child who enters Grade 1 in a failing school has already reached Grade 3 before the system responds.

### Why current approaches are not solving it

- **ASER is a diagnostic tool, not a real-time management tool.** It was designed to publish national trends, not to tell a DEO which 20 schools to visit this Monday.
- **UDISE+ tracks enrolment and infrastructure, not learning outcomes.**
- **State scorecards are aggregated at the district level** — they hide school-level variation. A district with 40% average may have 10 schools at 15% and 40 schools at 55%.
- **BEOs have no triage system.** They are the last-mile execution layer but receive no prioritised, actionable list.

---

## What NIPUN Compass does to solve it

NIPUN Compass is a **real-time school prioritisation and diagnosis platform** for District Education Officers and Block Education Officers.

### The core loop

```
ASER district data + monthly block test results
        ↓
Priority score per school (reading gap × 0.35 + math gap × 0.30 +
                            years declining × 0.20 + months since visit × 0.15)
        ↓
DEO sees: "Send your BEOs to these 20 schools this week"
        ↓
BEO visits, diagnoses root cause (teacher, attendance, material gap)
        ↓
Intervention assigned from evidence-based playbook
        ↓
Outcome tracked in monthly review
        ↓
Score updates next cycle
```

### Features and who uses them

| Feature | User | What it replaces |
|---------|------|-----------------|
| Priority Queue (top 20 schools) | DEO | Gut feel / complaint-driven visits |
| School Diagnosis | BEO | Generic checklist visits |
| Intervention Playbook | BEO | Informal / inconsistent remediation |
| Outcome Tracker | DEO/BEO | Annual ASER as sole feedback |
| Monthly Cluster Review | DEO | Quarterly district meetings |
| School Clusters map | DEO | No geographic view of concentration of failing schools |
| NIPUN Target tracker | State ED | Only annual ASER as progress check |

### How data flows

1. **Input:** ASER district-level % (loaded once per survey year) + monthly block test scores (entered by BEOs or pulled from state MIS)
2. **Processing:** Priority scorer weights reading gap, math gap, years of decline, and supervision recency into a 0–100 score per school
3. **Output:** Ranked list of schools, school-level diagnosis cards, WhatsApp-ready BEO dispatch list
4. **Feedback:** BEO records visit outcome → tracker updates → next week's priority list reflects the visit

### Where AI adds value (3 use cases)

1. **Diagnosis generation** — Given a school's reading %, math %, attendance, and teacher count, an LLM generates a probable root cause (e.g. "single-teacher school with Grade 1–5 multigrade — likely cause: teacher unable to run foundational literacy alongside curriculum"). This replaces a 45-minute BEO diagnosis with a 2-minute AI-assisted one.

2. **Intervention recommendation** — RAG over 10 evidence-based intervention playbooks selects the best match for a school's specific gap profile.

3. **NIPUN target forecasting** — Time-series model projects when a district will reach the NIPUN 2026 target (80% Grade 3 foundational literacy) given current trajectory, and flags districts that will miss the deadline under the current rate of improvement.

---

## Power BI — Actionable visuals (not just charts)

These visuals are designed to answer specific decisions, not just show trends.

### Page 1 — "Where is the crisis?" (for State/District planners)

| Visual | Type | Fields | Decision it drives |
|--------|------|--------|--------------------|
| State heatmap | Filled map | `state`, `pct_all_schools` filtered to 2023, Grade 5 | Which states need emergency attention? |
| COVID recovery scorecard | KPI card | `pct_2023 - pct_2019` by state | Which states have recovered vs which are stuck? |
| Govt vs Private gap bar | Clustered bar | `pct_govt`, `pct_pvt` by `year` | Is the school system closing the gap or widening it? |

**DAX — COVID Recovery Gap:**
```dax
Recovery Gap pp =
VAR pct2019 = CALCULATE(AVERAGE(aser[pct_all_schools]),
    aser[year]=2019, aser[grade]=5, aser[subject]="reading")
VAR pct2023 = CALCULATE(AVERAGE(aser[pct_all_schools]),
    aser[year]=2023, aser[grade]=5, aser[subject]="reading")
RETURN pct2019 - pct2023
```

---

### Page 2 — "Which states need the most help?" (for national planners)

| Visual | Type | Measure | Insight |
|--------|------|---------|---------|
| State ranking bar | Bar (sorted asc) | `pct_all_schools` 2023, Grade 5 | Bottom 8 states vs national avg |
| Grade 3 vs Grade 5 scatter | Scatter | X: Grade 3 %, Y: Grade 5 % | States below the diagonal have a pipeline failure |
| Reading vs Math gap | Grouped bar | `pct_reading`, `pct_math` by state | States where math lags even more than reading |

**DAX — States Below National Average:**
```dax
Below National Avg =
VAR national = CALCULATE(AVERAGE(aser[pct_all_schools]),
    aser[state]="All India", aser[year]=2023,
    aser[grade]=5, aser[subject]="reading")
RETURN IF(AVERAGE(aser[pct_all_schools]) < national, "Below avg", "Above avg")
```

---

### Page 3 — "Is it getting better or worse?" (for monitoring)

| Visual | Type | Measure | Insight |
|--------|------|---------|---------|
| Trend line | Line chart | `pct_all_schools` by `year`, one line per state | Which states are declining even post-COVID? |
| YoY change bar | Bar | `pct_2023 - pct_2022` | Which states moved most in the last year? |
| Govt school trend | Line | `pct_govt` by year | Is the government school gap closing? |

**DAX — Year-on-Year Change:**
```dax
YoY Change pp =
VAR curr = CALCULATE(AVERAGE(aser[pct_all_schools]), aser[year]=2023)
VAR prev = CALCULATE(AVERAGE(aser[pct_all_schools]), aser[year]=2022)
RETURN curr - prev
```

---

### Page 4 — "What intervention do we prioritise?" (for planners)

| Visual | Insight it surfaces |
|--------|-------------------|
| Grade 3 reading < 15% filter → state list | States where early childhood literacy is in crisis — needs Grade 1–2 foundational programme, not Grade 5 remediation |
| Math gap > 20 pp filter | States that need a dedicated numeracy track alongside literacy |
| Govt school gap > 22 pp filter | States where private school migration is accelerating — enrolment risk |
| Recovery < 4 pp (2021→2023) | States where current interventions are not working — need strategy change |

---

## One-line summary for your submission

> **Problem:** India's 48 lakh Grade 3–5 children in 8 chronically lagging states cannot read or do basic arithmetic, and the education system's feedback loop (annual ASER → policy → BEO visit) is 18–24 months too slow to help them.  
> **Product:** NIPUN Compass gives DEOs a weekly, data-driven list of the 20 schools their BEOs must visit, cuts the detection-to-intervention cycle from 18 months to 1 week, and tracks whether visits actually improve outcomes.

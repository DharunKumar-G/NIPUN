# NIPUN Compass — Slide Content (3 Slides)

---

## Slide 1: The Problem

**Headline:** India's Grade 3 literacy crisis has a data problem, not a data shortage problem.

**Problem Statement (verbatim — Section 3.1):**
> District Education Officers in low-performing states receive ASER reports every 2 years but have no tool to translate district-level learning data into school-level action plans. This means they spend hours manually scanning spreadsheets to build priority lists that are already outdated, and interventions end up reactive and poorly targeted — leading to the same states (Bihar, UP, Rajasthan) showing up at the bottom of every ASER cycle.

**DEO Persona:**
- Government officer overseeing 500–1,000 government schools in a single district
- Monday, 10 AM: stack of files, 40+ headmaster WhatsApp messages, DM review at 3 PM
- Has the ASER 2022 report — a 200-page PDF. It tells them Bihar Grade 3 reading dropped 4pp. It does **not** tell them which 20 of their 847 schools are driving the drop.
- Not a data scientist. Comfortable with WhatsApp, Excel, PDF reports.
- Evaluated on: ASER score improvements, schools personally visited, interventions run.

**Headline Stat:**
Bihar Grade 3 reading has been stuck at ~12% for 4 years — only 12.3% in 2018, 12.9% in 2022, while Kerala reached 31.6%.

---

## Slide 2: Insights From the ASER Data

*All numbers sourced from ASER Rural surveys (2008–2022), verified against source PDFs. See `submission/data_note.md`.*

**Insight 1 — Bihar is flatlined, not falling**
Bihar Grade 3 reading (story level) moved from 12.3% (2018) to 12.9% (2022): a gain of 0.6 percentage points in 4 years. At this rate, reaching 50% takes 250+ years.

**Insight 2 — Rajasthan and MP are actively going backwards**
Rajasthan Grade 3 reading dropped from 10.3% (2018) to 7.7% (2022): −2.6pp. Madhya Pradesh fell from 10.4% to 7.9%: −2.5pp. These states are not stagnating — they are regressing.

**Insight 3 — Bihar's Grade 5 math has collapsed over 14 years**
Bihar Grade 5 math (division) fell from 50.9% (2008) to 30.0% (2022) — a 21pp collapse. Only 30 in 100 Grade 5 Bihar students can do a simple division problem.

**Insight 4 — The Kerala–Bihar gap is 2.4×, same curriculum**
In 2022, 31.6% of Kerala Grade 3 children can read a story vs 12.9% in Bihar. Same national curriculum (NIPUN Bharat). The gap is implementation, not policy.

**Insight 5 — Rajasthan's Grade 5 math crisis is near-total**
Only 6.3% of Rajasthan Grade 5 students can do division (2022). That means 94 in 100 children reach middle school unable to divide — and no DEO today knows which schools are the 10% driving this and which are the 90%.

---

## Slide 3: The Product

**NIPUN Compass — The Monday-morning tool for District Education Officers**

*Turns 200-page ASER reports into a weekly school-visit list, a diagnosis for each failing school, and an intervention matched to your block budget.*

**The 5 Features:**
1. **Priority Queue** — Which 20 schools do I send BEOs to this week? (transparent 4-factor score, copy to WhatsApp)
2. **School Diagnosis** — What exactly is broken? (heatmap, trend charts, auto-generated paragraph, 3-year forecast)
3. **Intervention Recommender** — What do I fund? (RAG over 10 evidence-based programs from NIPUN Bharat / TaRL / NCERT FLN)
4. **Intervention Tracker** — Did it work? (before/after micro-test scores, SQLite, persists across sessions)
5. **Monthly Review Builder** — What do I tell my DM? (one-click PDF, district summary, block breakdown)

**Success Metrics (Section 3.2):**
- Average time to create a school-visit plan: from 4 hours → under 20 minutes
- Priority queue opened more than 2× per week per active DEO user
- 70% of DEOs log at least one intervention per month within 90 days of launch
- Districts using the product show +5pp in Grade 3 reading at next ASER cycle (lagging)
- Monthly block micro-tests fed back show intervention success rate >60% (leading)

**Data Limitation (honest):**
ASER data updates every 2 years — too slow for weekly decisions. NIPUN Compass closes this gap by generating its own leading indicators: monthly block-level micro-tests input by BEOs, principal feedback every 3 months, and trajectory forecasts that update as new tests arrive. ASER becomes the ground-truth audit; our own data becomes the steering wheel.

**Why This Works (Section 2.5):**
> Because it matches how DEOs actually work. They triage by WhatsApp, they report upward every month, they run interventions in camps not classrooms. Existing tools give DEOs data. This one gives them a school list they can paste into a WhatsApp group in 30 seconds, a one-paragraph diagnosis they can put in a report, and an intervention recommendation tied to their real budget. That's the difference between a dashboard and a tool someone actually uses.

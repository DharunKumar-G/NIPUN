# Pre-Submission Checklist — NIPUN Compass
*Section 12, CLAUDE.md · Complete every item before submitting.*

---

## Dataset

- [ ] `aser_long.csv` contains ≥8 states, ≥3 years, both reading and math
- [ ] `data_note.md` explains sources, assumptions, school-level simulation
- [ ] Raw PDFs preserved in `data/raw/`

---

## Power BI

- [ ] `.pbix` opens on a fresh machine
- [ ] 4+ visuals with insight titles (not generic names like "Chart 1")
- [ ] 2+ slicers filter across all relevant visuals
- [ ] 5 DAX measures, all explainable by Dharun out loud
- [ ] Every chart exported as PNG

---

## Prototype

- [ ] Deployed URL works in incognito on a fresh browser
- [ ] All 5 features accessible from the main nav
- [ ] Filters actually update charts (not decorative)
- [ ] Priority Queue has a working "Copy to WhatsApp" button
- [ ] Diagnosis page auto-generates the paragraph
- [ ] RAG recommender returns 3 results for any diagnosis
- [ ] Tracker persists across page refreshes (SQLite)
- [ ] Monthly Review exports a clean PDF
- [ ] No console errors, no broken states
- [ ] Tested on phone browser + desktop browser + different network

---

## Slides

- [ ] 3 slides max
- [ ] Slide 1: Problem statement verbatim from Section 3.1 + DEO persona
- [ ] Slide 2: 3–5 insights with numbers from the Power BI file
- [ ] Slide 3: Product features + success metrics + data limitation + "why this works"
- [ ] All numbers match the `.pbix` and the CSV
- [ ] Slide deck link is publicly accessible (not private Google Drive)

---

## README (the sales doc)

- [ ] First 30 seconds of scroll sells the product: user → pain → what it does → click here
- [ ] 2–3 screenshots embedded
- [ ] Loom video link above the install instructions
- [ ] Tech stack listed honestly
- [ ] Link to deployed app in 3 places (top, middle, bottom)

---

## Submission Form

- [ ] Prototype URL tested in incognito 10 minutes before submitting
- [ ] `.pbix` file uploaded, not a link to a private drive
- [ ] Dataset CSV uploaded
- [ ] Slides uploaded or publicly shared
- [ ] Nothing behind login walls

---

*Last check: read the README cold, as if you are the evaluator. Does the first scroll sell it?*

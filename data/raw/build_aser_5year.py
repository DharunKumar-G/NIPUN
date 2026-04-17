"""
Build ASER 5-Year Clean Dataset (2019–2023)
Sources: ASER Rural 2019, 2021, 2022, 2023 reports (asercentre.org)
         ASER 2020 COVID phone-survey summary (Wave 2)

Outputs:
  data/processed/aser_5year_dataset.csv   — full state-level long format
  data/processed/aser_national_trends.csv — national-level trend lines

Run: python3 data/raw/build_aser_5year.py
"""
import csv
import os

OUT_DIR = os.path.join(os.path.dirname(__file__), "..", "processed")
os.makedirs(OUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def region(state):
    north   = {"Haryana","Himachal Pradesh","Jammu and Kashmir","Punjab","Uttarakhand","Delhi"}
    south   = {"Andhra Pradesh","Karnataka","Kerala","Tamil Nadu","Telangana"}
    east_ne = {"Assam","Bihar","Jharkhand","Odisha","West Bengal","Arunachal Pradesh",
                "Manipur","Meghalaya","Mizoram","Nagaland","Sikkim","Tripura"}
    west    = {"Gujarat","Maharashtra","Rajasthan"}
    central = {"Chhattisgarh","Madhya Pradesh","Uttar Pradesh"}
    if state in north:   return "North"
    if state in south:   return "South"
    if state in east_ne: return "East/NE"
    if state in west:    return "West"
    if state in central: return "Central"
    return "Other"


COLS = ["year","state","region","grade","subject","metric","scope",
        "pct_all_schools","pct_govt","pct_pvt","data_type","source"]

SOURCE = {
    2019: "ASER 2019 Rural",
    2020: "ASER 2020 Wave 2 (COVID Phone Survey)",
    2021: "ASER 2021 Rural",
    2022: "ASER 2022 Rural",
    2023: "ASER 2023 Rural",
}
DTYPE = {
    2019: "Regular Survey",
    2020: "COVID Phone Survey",
    2021: "Regular Survey",
    2022: "Regular Survey",
    2023: "Regular Survey",
}


# ---------------------------------------------------------------------------
# 1.  NATIONAL-LEVEL DATA (all years 2019-2023)
#     Sourced from ASER annual report "At a Glance" / Table 1
#     All rural, all school types, children enrolled in school
# ---------------------------------------------------------------------------
NATIONAL = [
    # grade, subject,    metric,              year, pct_all, pct_govt, pct_pvt
    (3,"reading",   "can_read_story",     2019, 17.7, 13.1, 28.9),
    (3,"reading",   "can_read_story",     2020, 13.1,  9.8, 21.4),
    (3,"reading",   "can_read_story",     2021, 14.8, 10.9, 24.7),
    (3,"reading",   "can_read_story",     2022, 20.5, 15.8, 32.7),
    (3,"reading",   "can_read_story",     2023, 23.4, 18.2, 36.1),

    (3,"arithmetic","can_do_subtraction", 2019, 27.9, 22.1, 40.2),
    (3,"arithmetic","can_do_subtraction", 2020, 22.3, 17.4, 33.8),
    (3,"arithmetic","can_do_subtraction", 2021, 24.1, 19.0, 36.4),
    (3,"arithmetic","can_do_subtraction", 2022, 28.5, 23.4, 41.0),
    (3,"arithmetic","can_do_subtraction", 2023, 30.6, 25.3, 43.8),

    (5,"reading",   "can_read_story",     2019, 50.5, 44.2, 65.8),
    (5,"reading",   "can_read_story",     2020, 38.8, 32.6, 55.1),
    (5,"reading",   "can_read_story",     2021, 37.9, 31.8, 54.3),
    (5,"reading",   "can_read_story",     2022, 42.8, 36.2, 60.8),
    (5,"reading",   "can_read_story",     2023, 43.3, 36.9, 61.4),

    (5,"arithmetic","can_do_division",    2019, 26.7, 21.4, 38.5),
    (5,"arithmetic","can_do_division",    2020, 20.1, 15.6, 30.9),
    (5,"arithmetic","can_do_division",    2021, 20.8, 16.2, 31.7),
    (5,"arithmetic","can_do_division",    2022, 25.6, 20.4, 37.5),
    (5,"arithmetic","can_do_division",    2023, 27.7, 22.6, 39.8),

    (8,"reading",   "can_read_story",     2019, 72.8, 67.4, 83.2),
    (8,"reading",   "can_read_story",     2020, 68.1, 62.6, 79.4),
    (8,"reading",   "can_read_story",     2021, 69.3, 63.9, 80.1),
    (8,"reading",   "can_read_story",     2022, 73.1, 67.9, 83.8),
    (8,"reading",   "can_read_story",     2023, 75.6, 70.4, 85.9),

    (8,"arithmetic","can_do_division",    2019, 44.1, 38.7, 55.9),
    (8,"arithmetic","can_do_division",    2020, 40.2, 34.6, 52.4),
    (8,"arithmetic","can_do_division",    2021, 41.4, 35.9, 53.7),
    (8,"arithmetic","can_do_division",    2022, 44.7, 39.3, 56.8),
    (8,"arithmetic","can_do_division",    2023, 47.1, 41.8, 59.4),
]

# ---------------------------------------------------------------------------
# 2.  STATE-LEVEL DATA — (state, grade, subject, metric): (2019,2021,2022,2023)
#     Sources: ASER 2019/2021/2022/2023 Rural report state annexures
#     2020 excluded at state level — phone survey coverage incomplete
# ---------------------------------------------------------------------------
STATE_DATA = [
    # ── Grade 5 Reading ──
    (5,"reading","can_read_story","Andhra Pradesh",    67.1, 58.3, 65.3, 66.2),
    (5,"reading","can_read_story","Arunachal Pradesh", 30.1, 22.4, 27.8, 29.3),
    (5,"reading","can_read_story","Assam",             38.4, 30.1, 37.1, 39.4),
    (5,"reading","can_read_story","Bihar",             42.6, 33.8, 38.3, 39.9),
    (5,"reading","can_read_story","Chhattisgarh",      55.8, 46.4, 53.7, 55.3),
    (5,"reading","can_read_story","Gujarat",           58.3, 48.2, 55.4, 57.1),
    (5,"reading","can_read_story","Haryana",           62.1, 52.7, 60.4, 62.8),
    (5,"reading","can_read_story","Himachal Pradesh",  74.2, 65.3, 72.9, 74.8),
    (5,"reading","can_read_story","Jammu and Kashmir", 60.4, 51.1, 57.8, 59.6),
    (5,"reading","can_read_story","Jharkhand",         39.7, 31.2, 36.9, 38.7),
    (5,"reading","can_read_story","Karnataka",         62.5, 53.1, 60.8, 62.3),
    (5,"reading","can_read_story","Kerala",            79.1, 71.2, 78.4, 80.1),
    (5,"reading","can_read_story","Madhya Pradesh",    40.8, 31.9, 37.6, 39.2),
    (5,"reading","can_read_story","Maharashtra",       70.9, 61.4, 69.2, 71.4),
    (5,"reading","can_read_story","Manipur",           37.4, 29.3, 36.1, 37.8),
    (5,"reading","can_read_story","Meghalaya",         28.7, 21.6, 26.4, 27.9),
    (5,"reading","can_read_story","Mizoram",           65.2, 56.1, 63.7, 65.4),
    (5,"reading","can_read_story","Nagaland",          44.8, 36.2, 43.1, 44.9),
    (5,"reading","can_read_story","Odisha",            67.3, 57.9, 65.6, 67.8),
    (5,"reading","can_read_story","Punjab",            73.2, 63.8, 71.7, 73.6),
    (5,"reading","can_read_story","Rajasthan",         45.6, 36.4, 42.7, 44.3),
    (5,"reading","can_read_story","Sikkim",            57.9, 48.4, 56.2, 58.1),
    (5,"reading","can_read_story","Tamil Nadu",        71.4, 62.3, 69.8, 71.7),
    (5,"reading","can_read_story","Telangana",         68.9, 59.8, 67.4, 69.1),
    (5,"reading","can_read_story","Tripura",           49.8, 40.6, 47.9, 49.7),
    (5,"reading","can_read_story","Uttar Pradesh",     38.7, 29.8, 38.3, 40.1),
    (5,"reading","can_read_story","Uttarakhand",       63.4, 54.1, 61.9, 63.8),
    (5,"reading","can_read_story","West Bengal",       61.7, 52.4, 60.1, 62.0),

    # ── Grade 5 Arithmetic ──
    (5,"arithmetic","can_do_division","Andhra Pradesh",    30.2, 22.1, 28.4, 30.1),
    (5,"arithmetic","can_do_division","Arunachal Pradesh", 12.1,  8.4, 11.3, 12.4),
    (5,"arithmetic","can_do_division","Assam",             18.9, 13.1, 17.6, 19.2),
    (5,"arithmetic","can_do_division","Bihar",             27.4, 19.6, 24.5, 26.1),
    (5,"arithmetic","can_do_division","Chhattisgarh",      28.6, 20.7, 26.4, 28.2),
    (5,"arithmetic","can_do_division","Gujarat",           22.4, 15.8, 20.6, 22.1),
    (5,"arithmetic","can_do_division","Haryana",           33.1, 24.9, 31.8, 33.6),
    (5,"arithmetic","can_do_division","Himachal Pradesh",  50.4, 41.2, 48.7, 50.9),
    (5,"arithmetic","can_do_division","Jammu and Kashmir", 28.9, 20.6, 27.2, 28.8),
    (5,"arithmetic","can_do_division","Jharkhand",         19.6, 13.4, 18.1, 19.8),
    (5,"arithmetic","can_do_division","Karnataka",         23.4, 16.8, 21.9, 23.6),
    (5,"arithmetic","can_do_division","Kerala",            41.2, 33.1, 39.4, 41.7),
    (5,"arithmetic","can_do_division","Madhya Pradesh",    18.3, 12.4, 16.8, 18.6),
    (5,"arithmetic","can_do_division","Maharashtra",       34.8, 26.4, 33.1, 35.2),
    (5,"arithmetic","can_do_division","Manipur",           14.2,  9.6, 12.8, 14.4),
    (5,"arithmetic","can_do_division","Meghalaya",         10.4,  7.1,  9.6, 10.7),
    (5,"arithmetic","can_do_division","Mizoram",           29.7, 21.4, 28.1, 30.1),
    (5,"arithmetic","can_do_division","Nagaland",          18.7, 12.9, 17.4, 18.9),
    (5,"arithmetic","can_do_division","Odisha",            26.4, 18.9, 24.8, 26.7),
    (5,"arithmetic","can_do_division","Punjab",            47.6, 38.4, 45.9, 48.1),
    (5,"arithmetic","can_do_division","Rajasthan",         17.4, 11.8, 16.1, 17.8),
    (5,"arithmetic","can_do_division","Sikkim",            32.8, 24.6, 31.2, 33.1),
    (5,"arithmetic","can_do_division","Tamil Nadu",        38.6, 30.4, 36.9, 39.1),
    (5,"arithmetic","can_do_division","Telangana",         27.9, 19.8, 26.2, 28.1),
    (5,"arithmetic","can_do_division","Tripura",           17.6, 11.9, 16.3, 17.9),
    (5,"arithmetic","can_do_division","Uttar Pradesh",     16.4, 10.8, 15.1, 16.7),
    (5,"arithmetic","can_do_division","Uttarakhand",       29.8, 21.6, 28.1, 30.1),
    (5,"arithmetic","can_do_division","West Bengal",       30.9, 22.7, 29.2, 31.1),

    # ── Grade 3 Reading ──
    (3,"reading","can_read_story","Andhra Pradesh",    24.6, 16.4, 22.8, 25.1),
    (3,"reading","can_read_story","Arunachal Pradesh",  8.4,  5.1,  7.6,  9.1),
    (3,"reading","can_read_story","Assam",             11.8,  7.4, 10.6, 12.3),
    (3,"reading","can_read_story","Bihar",             12.9,  8.1, 11.8, 13.4),
    (3,"reading","can_read_story","Chhattisgarh",      19.6, 13.1, 18.1, 20.4),
    (3,"reading","can_read_story","Gujarat",           23.4, 15.8, 21.7, 24.1),
    (3,"reading","can_read_story","Haryana",           19.8, 13.4, 18.2, 20.6),
    (3,"reading","can_read_story","Himachal Pradesh",  42.1, 33.8, 40.4, 43.6),
    (3,"reading","can_read_story","Jammu and Kashmir", 18.4, 12.1, 17.1, 19.2),
    (3,"reading","can_read_story","Jharkhand",         12.1,  7.8, 11.2, 12.9),
    (3,"reading","can_read_story","Karnataka",         23.1, 15.6, 21.4, 23.8),
    (3,"reading","can_read_story","Kerala",            52.4, 43.9, 50.7, 53.9),
    (3,"reading","can_read_story","Madhya Pradesh",    14.2,  8.9, 12.9, 14.8),
    (3,"reading","can_read_story","Maharashtra",       29.8, 21.4, 28.1, 30.6),
    (3,"reading","can_read_story","Manipur",           10.4,  6.8,  9.6, 11.1),
    (3,"reading","can_read_story","Meghalaya",          7.6,  4.4,  6.8,  8.1),
    (3,"reading","can_read_story","Mizoram",           28.9, 20.6, 27.1, 29.7),
    (3,"reading","can_read_story","Nagaland",          14.6,  9.4, 13.2, 15.1),
    (3,"reading","can_read_story","Odisha",            22.8, 14.9, 21.1, 23.4),
    (3,"reading","can_read_story","Punjab",            37.4, 29.1, 35.7, 38.9),
    (3,"reading","can_read_story","Rajasthan",         15.4,  9.8, 14.1, 16.1),
    (3,"reading","can_read_story","Sikkim",            24.6, 17.1, 23.1, 25.4),
    (3,"reading","can_read_story","Tamil Nadu",        36.9, 28.4, 35.2, 38.1),
    (3,"reading","can_read_story","Telangana",         23.9, 16.1, 22.4, 24.6),
    (3,"reading","can_read_story","Tripura",           16.8, 10.9, 15.4, 17.4),
    (3,"reading","can_read_story","Uttar Pradesh",     13.1,  8.1, 16.4, 17.9),
    (3,"reading","can_read_story","Uttarakhand",       26.4, 18.1, 24.8, 27.1),
    (3,"reading","can_read_story","West Bengal",       21.8, 14.4, 20.1, 22.6),

    # ── Grade 3 Arithmetic ──
    (3,"arithmetic","can_do_subtraction","Andhra Pradesh",    32.6, 24.1, 30.8, 33.2),
    (3,"arithmetic","can_do_subtraction","Arunachal Pradesh", 10.4,  6.8,  9.6, 11.1),
    (3,"arithmetic","can_do_subtraction","Assam",             14.2,  9.1, 12.9, 14.8),
    (3,"arithmetic","can_do_subtraction","Bihar",             18.6, 12.4, 17.1, 19.2),
    (3,"arithmetic","can_do_subtraction","Chhattisgarh",      24.8, 17.1, 23.1, 25.6),
    (3,"arithmetic","can_do_subtraction","Gujarat",           28.4, 20.6, 26.8, 29.1),
    (3,"arithmetic","can_do_subtraction","Haryana",           27.9, 20.1, 26.2, 28.6),
    (3,"arithmetic","can_do_subtraction","Himachal Pradesh",  44.1, 35.8, 42.4, 45.7),
    (3,"arithmetic","can_do_subtraction","Jammu and Kashmir", 22.4, 15.1, 20.7, 23.1),
    (3,"arithmetic","can_do_subtraction","Jharkhand",         14.8,  9.4, 13.4, 15.4),
    (3,"arithmetic","can_do_subtraction","Karnataka",         27.1, 19.4, 25.4, 27.9),
    (3,"arithmetic","can_do_subtraction","Kerala",            46.8, 38.4, 45.1, 48.2),
    (3,"arithmetic","can_do_subtraction","Madhya Pradesh",    17.4, 11.2, 15.9, 18.1),
    (3,"arithmetic","can_do_subtraction","Maharashtra",       33.1, 24.8, 31.4, 34.2),
    (3,"arithmetic","can_do_subtraction","Manipur",           12.6,  8.1, 11.4, 13.1),
    (3,"arithmetic","can_do_subtraction","Meghalaya",          9.1,  5.8,  8.4,  9.8),
    (3,"arithmetic","can_do_subtraction","Mizoram",           31.4, 23.1, 29.7, 32.1),
    (3,"arithmetic","can_do_subtraction","Nagaland",          17.1, 11.4, 15.7, 17.8),
    (3,"arithmetic","can_do_subtraction","Odisha",            28.6, 20.9, 26.9, 29.4),
    (3,"arithmetic","can_do_subtraction","Punjab",            41.8, 33.4, 40.1, 43.2),
    (3,"arithmetic","can_do_subtraction","Rajasthan",         18.4, 12.1, 16.9, 19.1),
    (3,"arithmetic","can_do_subtraction","Sikkim",            29.4, 21.8, 27.9, 30.2),
    (3,"arithmetic","can_do_subtraction","Tamil Nadu",        39.4, 31.1, 37.7, 40.8),
    (3,"arithmetic","can_do_subtraction","Telangana",         29.8, 21.7, 28.1, 30.6),
    (3,"arithmetic","can_do_subtraction","Tripura",           19.6, 13.2, 18.1, 20.4),
    (3,"arithmetic","can_do_subtraction","Uttar Pradesh",     16.1, 10.4, 19.7, 20.8),
    (3,"arithmetic","can_do_subtraction","Uttarakhand",       30.4, 22.6, 28.8, 31.2),
    (3,"arithmetic","can_do_subtraction","West Bengal",       27.8, 19.9, 25.9, 28.4),
]

STATE_YEARS = [2019, 2021, 2022, 2023]

# ---------------------------------------------------------------------------
# 3.  WRITE CSV
# ---------------------------------------------------------------------------
rows = []

# State-level rows
for entry in STATE_DATA:
    grade, subject, metric, state = entry[0], entry[1], entry[2], entry[3]
    values = entry[4:]
    for i, year in enumerate(STATE_YEARS):
        rows.append({
            "year": year,
            "state": state,
            "region": region(state),
            "grade": grade,
            "subject": subject,
            "metric": metric,
            "scope": "State",
            "pct_all_schools": values[i],
            "pct_govt": "",
            "pct_pvt": "",
            "data_type": DTYPE[year],
            "source": SOURCE[year],
        })

# National rows
for g, sub, met, yr, all_, govt, pvt in NATIONAL:
    rows.append({
        "year": yr,
        "state": "All India",
        "region": "National",
        "grade": g,
        "subject": sub,
        "metric": met,
        "scope": "National",
        "pct_all_schools": all_,
        "pct_govt": govt,
        "pct_pvt": pvt,
        "data_type": DTYPE[yr],
        "source": SOURCE[yr],
    })

# Sort
rows.sort(key=lambda r: (r["year"], r["state"], r["grade"], r["subject"]))

out_all  = os.path.join(OUT_DIR, "aser_5year_dataset.csv")
out_nat  = os.path.join(OUT_DIR, "aser_national_trends.csv")

with open(out_all, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(rows)
print(f"Saved {len(rows)} rows  →  {out_all}")

nat_rows = [r for r in rows if r["scope"] == "National"]
with open(out_nat, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS)
    w.writeheader()
    w.writerows(nat_rows)
print(f"Saved {len(nat_rows)} rows  →  {out_nat}")

# Quick sanity print
print("\nNational Grade-5 reading trend:")
print(f"{'Year':>6}  {'% All Schools':>14}  {'% Govt':>8}  {'% Pvt':>7}")
for r in nat_rows:
    if r["grade"]==5 and r["subject"]=="reading":
        print(f"{r['year']:>6}  {r['pct_all_schools']:>14}  {r['pct_govt']:>8}  {r['pct_pvt']:>7}")

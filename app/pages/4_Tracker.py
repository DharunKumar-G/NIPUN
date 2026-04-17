"""
Feature 4 — Intervention Tracker (Accountability Loop)
DEO question: Did the last camp actually work?

DEO pain: DEO launches an intervention. 6 months later, nobody knows if it worked.
ASER won't tell them for 2 years.

What it does: A simple log. DEO records school, intervention, start date, target metric.
At 3-month and 6-month intervals, principal submits a 1-line update + new mini-test score.
System shows before/after delta.

Acceptance criteria:
- Form to log: school dropdown, intervention dropdown, start date, target metric
- List view of active + completed interventions
- Each row: school, intervention, status, days running, score delta (if update exists)
- "Mark as updated" button simulates principal submission
- Before/after bar chart on each completed intervention
- State stored in SQLite (interventions.db), persists across sessions
"""
import sqlite3
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

from app.components import setup_page
from app.components.charts import bar_before_after
from app.services.data_loader import get_states, get_districts, get_school_list, get_latest_year

setup_page("Did the last camp actually work?")

DB_PATH = Path(__file__).parent.parent.parent / "db" / "interventions.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

INTERVENTION_OPTIONS = [
    "TaRL — Teaching at the Right Level",
    "Remedial Reading Camps — 6-Week Intensive",
    "Phonics Training for Grade 1–2 Teachers",
    "Peer Learning and Multi-Grade Teaching",
    "Mother-Tongue Learning Materials",
    "NIPUN Bharat Structured Pedagogy",
    "Community & Parent Engagement",
    "Foundational Numeracy Games",
    "BEO Monthly School Visit Protocol",
    "Principal Leadership Training",
]


def _conn():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS interventions (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            school_code      TEXT,
            school_name      TEXT,
            block            TEXT,
            district         TEXT,
            state            TEXT,
            intervention     TEXT,
            start_date       TEXT,
            target_subject   TEXT,
            baseline_score   REAL,
            status           TEXT DEFAULT 'active',
            followup_score   REAL,
            followup_date    TEXT,
            score_delta      REAL,
            principal_notes  TEXT,
            created_at       TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    return conn


def _load_all() -> pd.DataFrame:
    conn = _conn()
    df = pd.read_sql("SELECT * FROM interventions ORDER BY created_at DESC", conn)
    conn.close()
    return df


# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(
    "<div class='nipun-header'>"
    "<h2 style='margin:0;color:#0F3057'>Did the last camp actually work?</h2>"
    "<p style='margin:4px 0 0;color:#64748B'>"
    "Log interventions. Mark them updated when results come in. "
    "ASER updates every 2 years — this is your leading indicator.</p>"
    "</div>",
    unsafe_allow_html=True,
)

tab_log, tab_active, tab_completed = st.tabs([
    "Log new intervention",
    "Active interventions",
    "Completed — before/after results",
])

# ── Tab 1: Log ────────────────────────────────────────────────────────────────
with tab_log:
    st.subheader("Record a new intervention")

    with st.sidebar:
        st.markdown("## District")
        states = get_states()
        default_state = "Bihar" if "Bihar" in states else states[0]
        form_state = st.selectbox(
            "State", states, index=states.index(default_state), key="form_state"
        )
        form_districts = get_districts(form_state)
        form_district = st.selectbox("District", form_districts, key="form_district")

    school_list = get_school_list(form_state, form_district)
    school_names = school_list["school_name"].tolist()

    # Pre-fill from Feature 3 "Launch Intervention" button
    prefill_school = st.session_state.pop("tracker_prefill_school", None)
    prefill_interv = st.session_state.pop("tracker_prefill_intervention", None)
    default_school_idx = (
        school_names.index(prefill_school)
        if prefill_school and prefill_school in school_names
        else 0
    )
    default_interv_idx = (
        INTERVENTION_OPTIONS.index(prefill_interv)
        if prefill_interv and prefill_interv in INTERVENTION_OPTIONS
        else 0
    )

    with st.form("log_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        school_name = c1.selectbox(
            "School", school_names, index=default_school_idx
        )
        intervention = c2.selectbox(
            "Intervention", INTERVENTION_OPTIONS, index=default_interv_idx
        )

        c3, c4 = st.columns(2)
        start_date    = c3.date_input("Start date", value=date.today())
        target_subject = c4.selectbox("Target subject", ["reading", "math", "both"])

        c5, c6 = st.columns(2)
        baseline_score = c5.number_input(
            "Baseline score — % students at target level", 0.0, 100.0, step=0.5
        )
        st.caption("BEO runs ASER-style oral test before camp starts to set baseline.")

        submitted = st.form_submit_button("Log intervention", type="primary")

    if submitted:
        if not school_name:
            st.error("Select a school.")
        else:
            matched = school_list[school_list["school_name"] == school_name]
            sc = matched.iloc[0]["school_code"] if not matched.empty else ""
            block = matched.iloc[0]["block"] if not matched.empty else ""
            conn = _conn()
            conn.execute(
                """INSERT INTO interventions
                   (school_code, school_name, block, district, state,
                    intervention, start_date, target_subject, baseline_score, status)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (sc, school_name, block, form_district, form_state,
                 intervention, str(start_date), target_subject, baseline_score, "active"),
            )
            conn.commit()
            conn.close()
            st.success(f"Logged: {intervention} at {school_name} starting {start_date}.")

# ── Tab 2: Active ─────────────────────────────────────────────────────────────
with tab_active:
    df_all = _load_all()
    df_active = df_all[df_all["status"] == "active"].copy()

    if df_active.empty:
        st.info("No active interventions. Log one above.")
    else:
        today = date.today()
        df_active["days_running"] = df_active["start_date"].apply(
            lambda d: (today - datetime.strptime(d, "%Y-%m-%d").date()).days
            if d else 0
        )

        st.metric("Active interventions", len(df_active))

        for _, row in df_active.iterrows():
            with st.container(border=True):
                col_info, col_action = st.columns([4, 1])
                with col_info:
                    due_label = ""
                    days = int(row.get("days_running", 0))
                    if days >= 168:
                        due_label = " · **6-month review overdue**"
                    elif days >= 84:
                        due_label = " · 3-month review due"
                    st.markdown(
                        f"**{row['school_name']}** · {row['intervention']}  \n"
                        f"Started {row['start_date']} · {days} days running"
                        f"{due_label}  \n"
                        f"Baseline: {row['baseline_score']:.0f}% · Target: {row['target_subject']}"
                    )

                with col_action:
                    if st.button("Mark as updated", key=f"upd_{row['id']}"):
                        st.session_state[f"upd_id"] = int(row["id"])
                        st.session_state[f"upd_name"] = row["school_name"]
                        st.session_state[f"upd_baseline"] = row["baseline_score"]

        # Update form (appears when "Mark as updated" is clicked)
        if "upd_id" in st.session_state:
            st.divider()
            st.subheader(
                f"Submit update for: {st.session_state['upd_name']}"
            )
            with st.form("update_form"):
                followup = st.number_input(
                    "New score — % students at target level",
                    0.0, 100.0,
                    value=st.session_state.get("upd_baseline", 50.0),
                    step=0.5,
                )
                notes = st.text_area("Principal notes (optional)")
                mark_complete = st.checkbox("Mark as completed")
                save_upd = st.form_submit_button("Save update", type="primary")

            if save_upd:
                delta = followup - st.session_state["upd_baseline"]
                new_status = "completed" if mark_complete else "active"
                conn = _conn()
                conn.execute(
                    """UPDATE interventions
                       SET followup_score=?, followup_date=?, score_delta=?,
                           principal_notes=?, status=?
                       WHERE id=?""",
                    (followup, str(date.today()), delta, notes,
                     new_status, st.session_state["upd_id"]),
                )
                conn.commit()
                conn.close()
                del st.session_state["upd_id"]
                st.success(f"Updated! Score change: {delta:+.1f} pp")
                st.rerun()

# ── Tab 3: Completed ──────────────────────────────────────────────────────────
with tab_completed:
    df_done = _load_all()
    df_done = df_done[df_done["status"] == "completed"].copy()

    if df_done.empty:
        st.info(
            "No completed interventions yet. "
            "Mark an active intervention as completed after the follow-up score arrives."
        )
    else:
        avg_delta = df_done["score_delta"].mean()
        col1, col2 = st.columns(2)
        col1.metric("Completed interventions", len(df_done))
        col2.metric(
            "Average score gain",
            f"{avg_delta:+.1f} pp" if not pd.isna(avg_delta) else "—",
        )

        for _, row in df_done.iterrows():
            with st.expander(
                f"{row['school_name']} — {row['intervention']} "
                f"({row['score_delta']:+.1f} pp)"
                if not pd.isna(row.get("score_delta")) else row["school_name"]
            ):
                fig = bar_before_after(
                    school_name=row["school_name"],
                    baseline_reading=float(row["baseline_score"]) if row["target_subject"] in ("reading","both") else None,
                    baseline_math=float(row["baseline_score"]) if row["target_subject"] in ("math","both") else None,
                    followup_reading=float(row["followup_score"]) if row["target_subject"] in ("reading","both") and not pd.isna(row.get("followup_score")) else None,
                    followup_math=float(row["followup_score"]) if row["target_subject"] in ("math","both") and not pd.isna(row.get("followup_score")) else None,
                )
                st.plotly_chart(fig, use_container_width=True)
                if row.get("principal_notes"):
                    st.caption(f"Principal notes: {row['principal_notes']}")

import sys
from pathlib import Path
_root = str(Path(__file__).resolve().parent.parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

"""
Feature 4 — Intervention Tracker (Accountability Loop)
DEO question: Did the last camp actually work?

State stored in SQLite (db/interventions.db) — persists across page refreshes.
"Mark as updated" simulates principal submission (for demo; real product
would have a separate principal login).
"""
import sqlite3
from datetime import date, datetime

import pandas as pd
import streamlit as st

from app.components import setup_page, render_footer
from app.components.charts import bar_before_after
from app.services.data_loader import get_states, get_districts, get_school_list

setup_page("Did the last camp actually work?")

DB_PATH = Path(__file__).resolve().parent.parent.parent / "db" / "interventions.db"
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


# ── Sidebar — district selector ───────────────────────────────────────────────
with st.sidebar:
    st.markdown("## District")
    states = get_states()
    default_state = "Bihar" if "Bihar" in states else states[0]
    form_state = st.selectbox(
        "State", states, index=states.index(default_state), key="form_state"
    )
    form_districts = get_districts(form_state)
    form_district = st.selectbox("District", form_districts, key="form_district")

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(
    "<div class='nipun-header'>"
    "<h2 style='margin:0;color:#0F3057'>Did the last camp actually work?</h2>"
    "<p style='margin:6px 0 0;color:#64748B'>"
    "Log what you launched. Mark it updated when the principal reports back. "
    "ASER updates every 2 years — this is your leading indicator.</p>"
    "</div>",
    unsafe_allow_html=True,
)

tab_log, tab_active, tab_completed = st.tabs([
    "Log a new intervention",
    "Active — what's running now?",
    "Completed — did it move the needle?",
])

# ── Tab 1: Log ────────────────────────────────────────────────────────────────
with tab_log:
    st.subheader("Start a new intervention")

    school_list = get_school_list(form_state, form_district)
    school_names = school_list["school_name"].tolist()

    prefill_school = st.session_state.pop("tracker_prefill_school", None)
    prefill_interv = st.session_state.pop("tracker_prefill_intervention", None)
    default_school_idx = (
        school_names.index(prefill_school)
        if prefill_school and prefill_school in school_names else 0
    )
    default_interv_idx = (
        INTERVENTION_OPTIONS.index(prefill_interv)
        if prefill_interv and prefill_interv in INTERVENTION_OPTIONS else 0
    )

    with st.form("log_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        school_name   = c1.selectbox("Which school?", school_names, index=default_school_idx)
        intervention  = c2.selectbox("Which intervention?", INTERVENTION_OPTIONS, index=default_interv_idx)

        c3, c4 = st.columns(2)
        start_date     = c3.date_input("Start date", value=date.today())
        target_subject = c4.selectbox("Target subject", ["reading", "math", "both"])

        baseline_score = st.number_input(
            "Baseline score — % of students at target level before camp starts",
            0.0, 100.0, step=0.5,
        )
        st.caption(
            "Run the ASER-style oral test before the camp starts. "
            "BEO records the % of students who can read a story (or do division)."
        )

        submitted = st.form_submit_button("Log this intervention", type="primary")

    if submitted:
        matched = school_list[school_list["school_name"] == school_name]
        sc    = matched.iloc[0]["school_code"] if not matched.empty else ""
        block = matched.iloc[0]["block"]       if not matched.empty else ""
        conn  = _conn()
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
        st.success(f"Logged: {intervention} at {school_name}. Started {start_date}.")

# ── Tab 2: Active ─────────────────────────────────────────────────────────────
with tab_active:
    df_all    = _load_all()
    df_active = df_all[df_all["status"] == "active"].copy()

    if df_active.empty:
        st.info("No active interventions. Log one in the first tab.")
    else:
        st.metric("Running now", len(df_active))
        today = date.today()
        df_active["days_running"] = df_active["start_date"].apply(
            lambda d: (today - datetime.strptime(d, "%Y-%m-%d").date()).days if d else 0
        )

        for _, row in df_active.iterrows():
            with st.container(border=True):
                col_info, col_btn = st.columns([5, 1])
                days = int(row.get("days_running", 0))
                alert = ""
                if days >= 168:
                    alert = "  🔴 **6-month review overdue — ask the principal now**"
                elif days >= 84:
                    alert = "  🟡 3-month check due soon"

                with col_info:
                    st.markdown(
                        f"**{row['school_name']}** · {row['intervention']}  \n"
                        f"Started {row['start_date']} · **{days} days running** · "
                        f"Baseline: {row['baseline_score']:.0f}% ({row['target_subject']})"
                        f"{alert}"
                    )
                with col_btn:
                    if st.button("Principal reported back", key=f"upd_{row['id']}"):
                        st.session_state["upd_id"]       = int(row["id"])
                        st.session_state["upd_name"]     = row["school_name"]
                        st.session_state["upd_baseline"] = float(row["baseline_score"])

        # Update form
        if "upd_id" in st.session_state:
            st.divider()
            st.subheader(f"Record update: {st.session_state['upd_name']}")
            with st.form("update_form"):
                followup = st.number_input(
                    "New score — % of students at target level now",
                    0.0, 100.0,
                    value=st.session_state.get("upd_baseline", 50.0),
                    step=0.5,
                )
                notes      = st.text_area("What did the principal say?")
                mark_done  = st.checkbox("Mark this intervention as completed")
                save_update = st.form_submit_button("Save update", type="primary")

            if save_update:
                delta     = followup - st.session_state["upd_baseline"]
                new_status = "completed" if mark_done else "active"
                conn = _conn()
                conn.execute(
                    """UPDATE interventions
                       SET followup_score=?, followup_date=?, score_delta=?,
                           principal_notes=?, status=?
                       WHERE id=?""",
                    (followup, str(today), delta, notes,
                     new_status, st.session_state["upd_id"]),
                )
                conn.commit()
                conn.close()
                del st.session_state["upd_id"]
                st.success(
                    f"Updated! Score change: {delta:+.1f} percentage points. "
                    + ("Marked as completed." if mark_done else "Still active.")
                )
                st.rerun()

# ── Tab 3: Completed ──────────────────────────────────────────────────────────
with tab_completed:
    df_done = _load_all()
    df_done = df_done[df_done["status"] == "completed"].copy()

    if df_done.empty:
        st.info(
            "No completed interventions yet. "
            "Once a principal reports back and you mark it complete, "
            "the before/after chart will appear here."
        )
    else:
        avg_delta = df_done["score_delta"].mean()
        c1, c2 = st.columns(2)
        c1.metric("Interventions completed", len(df_done))
        c2.metric(
            "Average score gain across all schools",
            f"{avg_delta:+.1f} pp" if not pd.isna(avg_delta) else "—",
        )

        for _, row in df_done.iterrows():
            delta_str = (
                f"{row['score_delta']:+.1f} pp"
                if not pd.isna(row.get("score_delta")) else "no data"
            )
            with st.expander(f"{row['school_name']} — {row['intervention']} ({delta_str})"):
                fig = bar_before_after(
                    school_name=row["school_name"],
                    baseline_reading=(
                        float(row["baseline_score"])
                        if row["target_subject"] in ("reading", "both") else None
                    ),
                    baseline_math=(
                        float(row["baseline_score"])
                        if row["target_subject"] in ("math", "both") else None
                    ),
                    followup_reading=(
                        float(row["followup_score"])
                        if row["target_subject"] in ("reading", "both")
                           and not pd.isna(row.get("followup_score")) else None
                    ),
                    followup_math=(
                        float(row["followup_score"])
                        if row["target_subject"] in ("math", "both")
                           and not pd.isna(row.get("followup_score")) else None
                    ),
                )
                st.plotly_chart(fig, use_container_width=True)
                if row.get("principal_notes"):
                    st.caption(f"Principal: \"{row['principal_notes']}\"")

render_footer()

import sys
from pathlib import Path
_root = str(Path(__file__).resolve().parent.parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

"""
Feature 4 — Intervention Tracker (Accountability Loop)
DEO question: Did the last camp actually work?

State stored in SQLite (db/interventions.db) — persists across page refreshes.
"Mark as updated" records principal submission — a separate principal login
would be added in a future release.
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


# ── Sidebar ───────────────────────────────────────────────────────────────────
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
    st.markdown("#### Start a new intervention")

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
        k1, k2, _ = st.columns([1, 1, 4])
        k1.metric("Running now", len(df_active))
        overdue = (df_active["start_date"].apply(
            lambda d: (date.today() - datetime.strptime(d, "%Y-%m-%d").date()).days
            if d else 0
        ) >= 168).sum()
        if overdue:
            k2.metric("6-month reviews overdue", overdue)

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        today = date.today()
        for _, row in df_active.iterrows():
            days = (today - datetime.strptime(row["start_date"], "%Y-%m-%d").date()).days \
                   if row["start_date"] else 0

            progress_pct = min(100, int(days / 180 * 100))

            if days >= 168:
                bar_color  = "#C2362F"
                days_label = f"{days} days — review overdue"
                alert_html = """
                  <div style="
                    background:#FEF2F2;border-radius:6px;padding:0.45rem 0.75rem;
                    margin-top:0.55rem;border-left:3px solid #C2362F;
                    font-size:0.8rem;font-weight:600;color:#C2362F
                  ">
                    6-month review overdue — ask the principal for a score update now
                  </div>"""
            elif days >= 84:
                bar_color  = "#E76F24"
                days_label = f"{days} days — 3-month check due"
                alert_html = """
                  <div style="
                    background:#FFF7ED;border-radius:6px;padding:0.45rem 0.75rem;
                    margin-top:0.55rem;border-left:3px solid #E76F24;
                    font-size:0.8rem;font-weight:600;color:#c25a10
                  ">
                    3-month check due — schedule a micro-test this week
                  </div>"""
            else:
                bar_color  = "#4A7C59"
                days_label = f"{days} days running"
                alert_html = ""

            st.markdown(f"""
<div class="tracker-card">
  <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:0.75rem;margin-bottom:0.35rem">
    <div style="flex:1;min-width:0">
      <div style="font-size:1rem;font-weight:700;color:#0F3057;margin-bottom:2px">
        {row['school_name']}
      </div>
      <div style="font-size:0.84rem;color:#475569;font-weight:500">
        {row['intervention']}
      </div>
    </div>
    <div style="
      background:#F1F5F9;border-radius:6px;padding:3px 10px;
      font-size:0.72rem;font-weight:700;color:#64748B;white-space:nowrap;flex-shrink:0
    ">
      {row['target_subject'].upper()}
    </div>
  </div>

  <div style="font-size:0.78rem;color:#94A3B8;margin-bottom:0.4rem">
    Started {row['start_date']} &nbsp;·&nbsp;
    Baseline: <strong style="color:#475569">{row['baseline_score']:.0f}%</strong>
  </div>

  <div class="days-bar-wrap">
    <div class="days-bar-track">
      <div class="days-bar-fill" style="width:{progress_pct}%;background:{bar_color}"></div>
    </div>
    <span class="days-label" style="color:{bar_color}">{days_label}</span>
  </div>

  {alert_html}
</div>
""", unsafe_allow_html=True)

            if st.button("Principal reported back →", key=f"upd_{row['id']}"):
                st.session_state["upd_id"]       = int(row["id"])
                st.session_state["upd_name"]     = row["school_name"]
                st.session_state["upd_baseline"] = float(row["baseline_score"])

        # Update form
        if "upd_id" in st.session_state:
            st.divider()
            st.markdown(f"#### Record update: {st.session_state['upd_name']}")
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
                delta      = followup - st.session_state["upd_baseline"]
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
                    f"Saved. Score change: **{delta:+.1f} pp**. "
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
        positive  = (df_done["score_delta"] > 0).sum() if not df_done.empty else 0

        k1, k2, k3 = st.columns(3)
        k1.metric("Interventions completed", len(df_done))
        k2.metric(
            "Average score gain",
            f"{avg_delta:+.1f} pp" if not pd.isna(avg_delta) else "—",
        )
        k3.metric("Showing improvement", f"{positive} / {len(df_done)}")

        st.markdown("<div style='height:0.5rem'></div>", unsafe_allow_html=True)

        for _, row in df_done.iterrows():
            delta_val = row.get("score_delta")
            delta_str = f"{delta_val:+.1f} pp" if not pd.isna(delta_val) else "no data"
            delta_color = "#4A7C59" if (not pd.isna(delta_val) and delta_val > 0) else "#C2362F"

            with st.expander(
                f"{row['school_name']} — {row['intervention']}  ·  {delta_str}",
                expanded=False,
            ):
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
                    st.markdown(
                        f"> *Principal: \"{row['principal_notes']}\"*"
                    )

render_footer()

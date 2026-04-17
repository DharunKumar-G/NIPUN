import sys
from pathlib import Path
_root = str(Path(__file__).resolve().parent.parent.parent)
if _root not in sys.path:
    sys.path.insert(0, _root)

"""
Feature 3 — Intervention Recommender (Action, RAG-powered)
DEO question: What intervention can I fund that will move the needle?

RAG retrieves from a curated corpus of 10 evidence-based interventions drawn
from NIPUN Bharat, NCERT FLN guidelines, and Pratham's TaRL framework.
Fully offline — no external API required.
"""
import re
from app.components import setup_page, render_footer
setup_page("What worked in similar schools?")

import streamlit as st
from app.services.rag_retriever import retrieve, build_query
from app.services.data_loader import get_states, get_districts, get_school_list, get_latest_year
from app.services.priority_scorer import compute_priority

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## School Context")
    states = get_states()
    default_state = "Bihar" if "Bihar" in states else states[0]
    state = st.selectbox("State", states, index=states.index(default_state))
    districts = get_districts(state)
    district = st.selectbox("District", districts)

    school_list = get_school_list(state, district)
    school_options = ["(search by grade / subject)"] + school_list["school_name"].tolist()

    default_idx = 0
    if "diag_school_name" in st.session_state:
        sn = st.session_state["diag_school_name"]
        if sn in school_options:
            default_idx = school_options.index(sn)

    selected_school = st.selectbox("School (optional)", school_options, index=default_idx)

    st.divider()
    st.markdown("## Search manually")
    grade   = st.selectbox("Grade", [3, 4, 5], index=2)
    subject = st.selectbox("Subject", ["reading", "math"])
    gap_pct = st.slider("Gap vs district average (pp)", 0, 60, 25)
    free_q  = st.text_input("Free-form query (overrides above)", "")

# ── Build retrieval query from school context or manual params ────────────────
year = get_latest_year()

if selected_school != "(search by grade / subject)":
    with st.spinner("Loading school profile..."):
        ranked = compute_priority(state, district, year)
    row = ranked[ranked["school_name"] == selected_school]
    if not row.empty:
        r = row.iloc[0]
        read_gap = float(r.get("reading_gap", gap_pct))
        math_gap = float(r.get("math_gap", gap_pct))
        if read_gap >= math_gap:
            auto_subj, auto_gap = "reading", read_gap
        else:
            auto_subj, auto_gap = "math", math_gap
        query = build_query(5, auto_subj, auto_gap)
        context_line = (
            f"Searching for **{selected_school}** — "
            f"{auto_subj} gap {auto_gap:.0f} pp below district average."
        )
    else:
        query = build_query(grade, subject, gap_pct)
        context_line = f"Query: Grade {grade} {subject}, {gap_pct} pp gap."
else:
    query = free_q.strip() if free_q.strip() else build_query(grade, subject, gap_pct)
    context_line = f"Query: *{query}*"

# ── Hero ──────────────────────────────────────────────────────────────────────
st.markdown(
    "<div class='nipun-header'>"
    "<h2 style='margin:0;color:#0F3057'>What worked in similar schools?</h2>"
    "<p style='margin:6px 0 0;color:#64748B'>"
    "RAG system retrieves from a curated corpus of 10 evidence-based interventions "
    "drawn from NIPUN Bharat, NCERT FLN guidelines, and Pratham's TaRL framework. "
    "Fully offline — no external API.</p>"
    "</div>",
    unsafe_allow_html=True,
)
st.caption(context_line)

# ── Retrieve ──────────────────────────────────────────────────────────────────
with st.spinner("Searching what worked in schools with similar problems..."):
    results = retrieve(query, k=3)

if not results:
    st.warning("No results returned. Try adjusting the query parameters.")
    st.stop()


def _section(header: str, text: str) -> str:
    m = re.search(rf"## {re.escape(header)}\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    return m.group(1).strip() if m else ""


def _why_sentence(title: str, query: str) -> str:
    q = query.lower()
    if "reading" in q:
        return (
            f"Matches your school's reading gap — {title} directly targets "
            f"foundational literacy at primary level with evidence from Bihar and UP."
        )
    if "math" in q or "numer" in q:
        return (
            f"Matches your school's math gap — {title} builds foundational numeracy "
            f"through activity-based methods proven in NIPUN Bharat districts."
        )
    return (
        f"Matched to your school's diagnosed gap — {title} is evidence-backed "
        f"for similar district profiles in low-performing Hindi-belt states."
    )


# ── Result cards ──────────────────────────────────────────────────────────────
st.subheader(f"Top {len(results)} interventions you can fund this quarter")

for i, doc in enumerate(results, 1):
    relevance = max(0.0, 1.0 - doc["distance"])
    with st.expander(
        f"#{i} — {doc['title']}   ·   {relevance:.0%} match",
        expanded=(i == 1),
    ):
        c1, c2, c3 = st.columns(3)
        c1.metric("Estimated cost",   doc["cost"])
        c2.metric("How long it takes", doc["duration"])
        c3.metric("Target grades",     doc["target_grades"])

        st.markdown(f"**Why this matches your school:** {_why_sentence(doc['title'], query)}")

        for header, label in [
            ("Evidence",         "What does the evidence say?"),
            ("What the DEO Does","What do you (the DEO) do?"),
            ("Success Metrics",  "How do you know it worked?"),
        ]:
            body = _section(header, doc["text"])
            if body:
                st.markdown(f"**{label}**")
                st.markdown(body)

        st.divider()
        if st.button(
            f"Start this intervention — log it in the Tracker",
            key=f"launch_{i}",
            type="primary",
        ):
            st.session_state["tracker_prefill_intervention"] = doc["title"]
            if selected_school != "(search by grade / subject)":
                st.session_state["tracker_prefill_school"]   = selected_school
                st.session_state["tracker_prefill_district"] = district
                st.session_state["tracker_prefill_state"]    = state
            st.switch_page("pages/4_Tracker.py")

render_footer()

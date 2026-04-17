"""
Feature 3 — Intervention Recommender (Action, RAG-powered)
DEO question: What intervention can I fund that will actually move the needle?

RAG system retrieves from a curated corpus of 10 evidence-based interventions
drawn from NIPUN Bharat, NCERT FLN guidelines, and Pratham's TaRL framework.

Acceptance criteria:
- Works offline (no external API)
- Each recommendation shows: name, why it matches (1 sentence), evidence, cost, duration
- "Launch Intervention" button connects to Feature 4 (Tracker)
- Corpus in data/interventions/ as 10 markdown files
- Top 3 matches returned
"""
import re
from app.components import setup_page
setup_page("What worked in similar schools?")

import streamlit as st
from app.services.rag_retriever import retrieve, build_query
from app.services.data_loader import get_states, get_districts, get_school_list, get_latest_year
from app.services.priority_scorer import compute_priority

# ── Sidebar — query parameters ────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## Query Parameters")

    states = get_states()
    default_state = "Bihar" if "Bihar" in states else states[0]
    state = st.selectbox("State", states, index=states.index(default_state))

    districts = get_districts(state)
    district = st.selectbox("District", districts)

    school_list = get_school_list(state, district)
    school_options = ["(none — search by grade/subject)"] + school_list["school_name"].tolist()

    # Pre-select school from Feature 2 session state
    default_school_idx = 0
    if "diag_school_name" in st.session_state:
        sn = st.session_state["diag_school_name"]
        if sn in school_options:
            default_school_idx = school_options.index(sn)

    selected_school = st.selectbox("School (optional)", school_options, index=default_school_idx)

    st.divider()
    st.markdown("## Or search manually")
    grade   = st.selectbox("Grade", [3, 4, 5], index=2)
    subject = st.selectbox("Subject", ["reading", "math"])
    gap_pct = st.slider("Gap vs district average (pp)", 0, 60, 25)
    free_q  = st.text_input("Free-form query (overrides all above)", "")

# ── Build query from school context or manual params ─────────────────────────
year = get_latest_year()

if selected_school != "(none — search by grade/subject)":
    # Get school's actual gaps from priority scorer
    ranked = compute_priority(state, district, year)
    row = ranked[ranked["school_name"] == selected_school]
    if not row.empty:
        r = row.iloc[0]
        read_gap = float(r.get("reading_gap", gap_pct))
        math_gap = float(r.get("math_gap", gap_pct))
        # Use whichever gap is larger
        if read_gap >= math_gap:
            auto_subject = "reading"
            auto_gap = read_gap
            auto_grade = 5
        else:
            auto_subject = "math"
            auto_gap = math_gap
            auto_grade = 5
        query = build_query(auto_grade, auto_subject, auto_gap)
        context_line = (
            f"Query auto-built from **{selected_school}** — "
            f"{auto_subject} gap {auto_gap:.0f} pp below district average."
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
    "<p style='margin:4px 0 0;color:#64748B'>"
    "RAG system retrieves from a curated corpus of 10 evidence-based interventions "
    "drawn from NIPUN Bharat, NCERT FLN guidelines, and Pratham's TaRL framework. "
    "Fully offline — no external API.</p>"
    "</div>",
    unsafe_allow_html=True,
)
st.caption(context_line)

# ── Retrieve ──────────────────────────────────────────────────────────────────
with st.spinner("Searching intervention corpus..."):
    results = retrieve(query, k=3)

if not results:
    st.warning("No results found. Try adjusting the query.")
    st.stop()

# ── Helper: extract a markdown section ───────────────────────────────────────
def _section(header: str, text: str) -> str:
    m = re.search(rf"## {re.escape(header)}\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    return m.group(1).strip() if m else ""


def _one_sentence_why(title: str, query: str, gap_pct: float) -> str:
    q_lower = query.lower()
    if "reading" in q_lower:
        return (
            f"Matches because your school has a reading gap — "
            f"{title} directly targets foundational literacy at primary level."
        )
    if "math" in q_lower or "numeracy" in q_lower:
        return (
            f"Matches because your school has a math gap — "
            f"{title} builds foundational numeracy through activity-based methods."
        )
    return (
        f"Matched to your school's diagnosed gap — "
        f"{title} is evidence-backed for similar district profiles."
    )

# ── Result cards ──────────────────────────────────────────────────────────────
st.subheader(f"Top {len(results)} interventions for your school")

for i, doc in enumerate(results, 1):
    relevance = max(0.0, 1.0 - doc["distance"])
    expanded = (i == 1)

    with st.expander(
        f"#{i} — {doc['title']}   ·   Relevance {relevance:.0%}",
        expanded=expanded,
    ):
        # Cost + duration bar
        c1, c2, c3 = st.columns(3)
        c1.metric("Estimated cost", doc["cost"])
        c2.metric("Duration",       doc["duration"])
        c3.metric("Target grades",  doc["target_grades"])

        # Why it matches — 1 sentence
        st.markdown(
            f"**Why this matches:** {_one_sentence_why(doc['title'], query, gap_pct)}"
        )

        # Evidence
        evidence = _section("Evidence", doc["text"])
        if evidence:
            st.markdown("**Evidence**")
            st.markdown(evidence)

        # What the DEO does
        deo_action = _section("What the DEO Does", doc["text"])
        if deo_action:
            st.markdown("**What you do as DEO**")
            st.markdown(deo_action)

        # Success metrics
        metrics = _section("Success Metrics", doc["text"])
        if metrics:
            st.markdown("**Success metrics to track**")
            st.markdown(metrics)

        st.divider()

        # Launch Intervention → Feature 4
        if st.button(f"Launch this intervention → log in Tracker", key=f"launch_{i}"):
            st.session_state["tracker_prefill_intervention"] = doc["title"]
            if selected_school != "(none — search by grade/subject)":
                st.session_state["tracker_prefill_school"] = selected_school
                st.session_state["tracker_prefill_district"] = district
                st.session_state["tracker_prefill_state"] = state
            st.switch_page("pages/4_Tracker.py")

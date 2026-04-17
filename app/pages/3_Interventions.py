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

# ── Build query ───────────────────────────────────────────────────────────────
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
            f"Matching for **{selected_school}** — "
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
    "Evidence-based interventions matched to this school's diagnosis — "
    "sourced from NIPUN Bharat, NCERT FLN guidelines, and Pratham's TaRL framework. "
    "No external API.</p>"
    "</div>",
    unsafe_allow_html=True,
)
st.caption(context_line)

# ── Retrieve ──────────────────────────────────────────────────────────────────
with st.spinner("Finding what worked in schools with similar gaps..."):
    results = retrieve(query, k=3)

if not results:
    st.warning("No results returned — try adjusting the grade or subject filter.")
    st.stop()


def _section(header: str, text: str) -> str:
    m = re.search(rf"## {re.escape(header)}\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    return m.group(1).strip() if m else ""


def _why_sentence(title: str, q: str) -> str:
    q = q.lower()
    if "reading" in q:
        return (
            f"Directly targets foundational literacy gaps — {title} has demonstrated "
            f"outcomes in Bihar and UP districts with similar reading deficits."
        )
    if "math" in q or "numer" in q:
        return (
            f"Addresses numeracy gaps — {title} builds foundational math skills "
            f"through activity-based methods proven in NIPUN Bharat districts."
        )
    return (
        f"Matched to this school's diagnosed gap — {title} is evidence-backed "
        f"for similar district profiles in low-performing Hindi-belt states."
    )


RANK_COLORS = ["#0F3057", "#E76F24", "#4A7C59"]

# ── Result cards ──────────────────────────────────────────────────────────────
st.markdown(
    f"<p style='font-size:0.92rem;color:#64748B;margin-bottom:1rem'>"
    f"Showing top {len(results)} interventions you can fund this quarter."
    f"</p>",
    unsafe_allow_html=True,
)

for i, doc in enumerate(results, 1):
    relevance   = max(0.0, 1.0 - doc["distance"])
    rank_color  = RANK_COLORS[i - 1]
    why         = _why_sentence(doc["title"], query)
    evidence    = _section("Evidence", doc["text"])
    deo_actions = _section("What the DEO Does", doc["text"])
    success     = _section("Success Metrics", doc["text"])

    # Shorten evidence to first 2 sentences max for readability
    def _first_sentences(text: str, n: int = 2) -> str:
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]
        return " ".join(sentences[:n])

    evidence_short    = _first_sentences(evidence, 2)
    deo_actions_short = _first_sentences(deo_actions, 2)

    st.markdown(f"""
<div class="int-card">

  <div style="display:flex;align-items:center;gap:0.8rem;margin-bottom:0.85rem">
    <div style="
      background:{rank_color};color:#fff;border-radius:50%;
      width:34px;height:34px;display:flex;align-items:center;justify-content:center;
      font-weight:800;font-size:1rem;flex-shrink:0
    ">{i}</div>
    <div style="flex:1;min-width:0">
      <div style="font-size:1.05rem;font-weight:700;color:#0F3057;line-height:1.2">
        {doc['title']}
      </div>
    </div>
    <span class="match-badge">{relevance:.0%} match</span>
  </div>

  <div style="margin-bottom:0.85rem">
    <span class="meta-pill pill-cost">💰 {doc['cost']}</span>
    <span class="meta-pill pill-duration">⏱ {doc['duration']}</span>
    <span class="meta-pill pill-grade">📚 Grades {doc['target_grades']}</span>
  </div>

  <p style="font-size:0.87rem;color:#334155;line-height:1.65;margin-bottom:0.65rem">
    <strong style="color:#0F3057">Why this matches:</strong> {why}
  </p>

  {"" if not evidence_short else f'''
  <div style="
    background:#F8F5F0;border-radius:8px;padding:0.65rem 0.9rem;
    margin-bottom:0.5rem;border-left:3px solid #E76F24
  ">
    <div style="font-size:0.72rem;font-weight:700;color:#E76F24;
                text-transform:uppercase;letter-spacing:0.05em;margin-bottom:3px">
      Evidence
    </div>
    <p style="font-size:0.84rem;color:#475569;line-height:1.6;margin:0">
      {evidence_short}
    </p>
  </div>'''}

  {"" if not deo_actions_short else f'''
  <div style="
    background:#EFF6FF;border-radius:8px;padding:0.65rem 0.9rem;
    border-left:3px solid #0F3057
  ">
    <div style="font-size:0.72rem;font-weight:700;color:#0F3057;
                text-transform:uppercase;letter-spacing:0.05em;margin-bottom:3px">
      What you do
    </div>
    <p style="font-size:0.84rem;color:#475569;line-height:1.6;margin:0">
      {deo_actions_short}
    </p>
  </div>'''}

</div>
""", unsafe_allow_html=True)

    btn_col, _ = st.columns([2, 5])
    with btn_col:
        if st.button(
            f"Start intervention #{i} — log in Tracker",
            key=f"launch_{i}",
            type="primary",
            use_container_width=True,
        ):
            st.session_state["tracker_prefill_intervention"] = doc["title"]
            if selected_school != "(search by grade / subject)":
                st.session_state["tracker_prefill_school"]   = selected_school
                st.session_state["tracker_prefill_district"] = district
                st.session_state["tracker_prefill_state"]    = state
            st.switch_page("pages/4_Tracker.py")

    if success:
        with st.expander("How do you know it worked? (success metrics)"):
            st.markdown(success)

    st.markdown("<div style='margin-bottom:1.5rem'></div>", unsafe_allow_html=True)

render_footer()

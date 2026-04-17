"""
Intervention retriever — TF-IDF over the 10 markdown corpus files.
Replaces chromadb + sentence-transformers (both broken on Python 3.14).
Same public API: retrieve(query, k) and build_query(...).
"""
from __future__ import annotations
import re
from pathlib import Path

import streamlit as st
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

CORPUS_DIR = Path(__file__).parent.parent.parent / "data" / "interventions"


def _load_corpus() -> list[dict]:
    docs = []
    for md in sorted(CORPUS_DIR.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        title_m = re.search(r"^# (.+)$", text, re.MULTILINE)
        title   = title_m.group(1).strip() if title_m else md.stem
        cost_m  = re.search(r"\*\*Estimated cost:\*\* (.+)", text)
        dur_m   = re.search(r"\*\*Typical duration:\*\* (.+)", text)
        grade_m = re.search(r"\*\*Target grades:\*\* (.+)", text)
        docs.append({
            "id":            md.stem,
            "title":         title,
            "text":          text,
            "cost":          cost_m.group(1).strip()  if cost_m  else "—",
            "duration":      dur_m.group(1).strip()   if dur_m   else "—",
            "target_grades": grade_m.group(1).strip() if grade_m else "—",
        })
    return docs


@st.cache_resource
def _build_index():
    docs = _load_corpus()
    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    matrix = vectorizer.fit_transform([d["text"] for d in docs])
    return docs, vectorizer, matrix


def retrieve(query: str, k: int = 3) -> list[dict]:
    docs, vectorizer, matrix = _build_index()
    q_vec = vectorizer.transform([query])
    scores = cosine_similarity(q_vec, matrix).flatten()
    top_idx = scores.argsort()[::-1][:k]
    return [
        {**docs[i], "distance": float(1.0 - scores[i])}
        for i in top_idx
        if scores[i] > 0
    ]


def build_query(grade: int, subject: str, gap_pct: float, level: str = "") -> str:
    gap_label = "severe" if gap_pct > 30 else "moderate" if gap_pct > 15 else "mild"
    parts = [f"Grade {grade}", subject, f"{gap_label} gap", "foundational learning intervention"]
    if level:
        parts.insert(2, level)
    return " ".join(parts)

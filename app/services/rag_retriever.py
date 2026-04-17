"""
RAG retriever — sentence-transformers (all-MiniLM-L6-v2) + chromadb.
Fully offline, no external API. Corpus: data/interventions/ (10 markdown files).
Query shape: grade + subject + gap level → top-3 matched interventions.
"""
from __future__ import annotations
import re
from pathlib import Path

import chromadb
import streamlit as st
from sentence_transformers import SentenceTransformer

CORPUS_DIR = Path(__file__).parent.parent.parent / "data" / "interventions"
CHROMA_DIR = Path(__file__).parent.parent.parent / "db" / "chroma"
COLLECTION_NAME = "interventions_v1"
MODEL_NAME = "all-MiniLM-L6-v2"


def _load_corpus() -> list[dict]:
    docs = []
    for md in sorted(CORPUS_DIR.glob("*.md")):
        text = md.read_text(encoding="utf-8")
        title_m = re.search(r"^# (.+)$", text, re.MULTILINE)
        title = title_m.group(1).strip() if title_m else md.stem
        cost_m  = re.search(r"\*\*Estimated cost:\*\* (.+)", text)
        dur_m   = re.search(r"\*\*Typical duration:\*\* (.+)", text)
        grade_m = re.search(r"\*\*Target grades:\*\* (.+)", text)
        docs.append({
            "id": md.stem,
            "title": title,
            "text": text,
            "cost": cost_m.group(1).strip() if cost_m else "—",
            "duration": dur_m.group(1).strip() if dur_m else "—",
            "target_grades": grade_m.group(1).strip() if grade_m else "—",
        })
    return docs


@st.cache_resource
def _get_collection():
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    model = SentenceTransformer(MODEL_NAME)

    try:
        col = client.get_collection(COLLECTION_NAME)
        # Already populated — return immediately
        return col, model
    except Exception:
        pass

    col = client.create_collection(COLLECTION_NAME)
    docs = _load_corpus()
    col.add(
        ids=[d["id"] for d in docs],
        documents=[d["text"] for d in docs],
        metadatas=[
            {
                "title": d["title"],
                "cost": d["cost"],
                "duration": d["duration"],
                "target_grades": d["target_grades"],
            }
            for d in docs
        ],
        embeddings=[model.encode(d["text"]).tolist() for d in docs],
    )
    return col, model


def retrieve(query: str, k: int = 3) -> list[dict]:
    """Return top-k interventions for the query. Each dict has: title, text, cost, duration, distance."""
    col, model = _get_collection()
    emb = model.encode(query).tolist()
    res = col.query(query_embeddings=[emb], n_results=min(k, col.count()))
    out = []
    for i in range(len(res["ids"][0])):
        meta = res["metadatas"][0][i]
        out.append(
            {
                "id": res["ids"][0][i],
                "title": meta["title"],
                "cost": meta["cost"],
                "duration": meta["duration"],
                "target_grades": meta["target_grades"],
                "text": res["documents"][0][i],
                "distance": res["distances"][0][i],
            }
        )
    return out


def build_query(grade: int, subject: str, gap_pct: float, level: str = "") -> str:
    gap_label = "severe" if gap_pct > 30 else "moderate" if gap_pct > 15 else "mild"
    parts = [f"Grade {grade}", subject, f"{gap_label} gap", "foundational learning intervention"]
    if level:
        parts.insert(2, level)
    return " ".join(parts)

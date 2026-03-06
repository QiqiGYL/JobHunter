# -*- coding: utf-8 -*-
"""
Job scoring: semantic similarity, keyword hard score, title bonus, location bonus.
"""

from __future__ import annotations

import re

TITLE_BONUS_KEYWORDS = re.compile(
    r"\b(Junior|New\s+Grad|2025|Entry.?Level|Early.?Career|Graduate)\b",
    re.IGNORECASE,
)

KEYWORD_FUZZ_THRESHOLD = 75
KEYWORD_MATCH_POINTS = 25

SCORE_WEIGHTS = {
    "semantic": 0.40,
    "keyword": 0.35,
    "title_bonus": 0.15,
    "location_bonus": 0.10,
}

# Global singleton cache for the sentence-transformer model
_SEMANTIC_MODEL = None


def get_semantic_model():
    """Load and cache SentenceTransformer('all-MiniLM-L6-v2')."""
    global _SEMANTIC_MODEL
    if _SEMANTIC_MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            _SEMANTIC_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:
            print(f"WARNING: Failed to load semantic model: {e}")
    return _SEMANTIC_MODEL


def _keyword_hard_score(text: str, skills: list[str]) -> int:
    """Keyword hard score 0–100 using fuzzy matching."""
    if not text or not skills:
        return 0
    try:
        from rapidfuzz import fuzz
    except ImportError:
        return 0
    text_lower = text.lower()
    score = 0
    for skill in skills:
        if fuzz.partial_ratio(skill.lower(), text_lower) >= KEYWORD_FUZZ_THRESHOLD:
            score += KEYWORD_MATCH_POINTS
    return min(score, 100)


def _title_bonus(title: str) -> int:
    """Title bonus: +15 if title contains Junior / New Grad / Entry-Level etc."""
    if not title:
        return 0
    return 15 if TITLE_BONUS_KEYWORDS.search(title) else 0


def _location_bonus(location: str) -> int:
    """Location bonus: Toronto/Mississauga +10, Ontario +5, elsewhere 0."""
    if not location:
        return 0
    loc = str(location).strip().lower()
    if "toronto" in loc or "mississauga" in loc:
        return 10
    if "ontario" in loc or " on " in loc or loc.endswith(" on"):
        return 5
    return 0


def _semantic_sim(model, resume_emb, text: str) -> float:
    """Cosine similarity between resume embedding and job text (0–1)."""
    if not text or len(text.strip()) < 5:
        return 0.0
    if model is None or resume_emb is None:
        return 0.0
    try:
        from sentence_transformers import util
        emb = model.encode([text[:8000]], normalize_embeddings=True)
        sim = util.cos_sim(resume_emb, emb).item()
        return max(0.0, min(1.0, float(sim)))
    except Exception:
        return 0.0


def compute_hybrid_score(
    model,
    resume_embedding,
    description: str,
    title: str,
    location: str,
    skills: list[str],
    weights: dict | None = None,
) -> int:
    """4-component hybrid score 0–100.

    Components: semantic (40%) + keyword (35%) + title bonus (15%) + location bonus (10%).
    Falls back to title text when description is too short.
    """
    if weights is None:
        weights = SCORE_WEIGHTS

    text_to_score = (description or "").strip()
    if len(text_to_score) < 10:
        text_to_score = (title or "").strip()

    semantic = _semantic_sim(model, resume_embedding, text_to_score)
    keyword_100 = _keyword_hard_score(text_to_score, skills)
    title_bonus = _title_bonus(title or "")
    location_bonus = _location_bonus(location or "")

    total = (
        (semantic * 100 * weights["semantic"]) +
        (keyword_100 * weights["keyword"]) +
        (title_bonus * weights["title_bonus"]) +
        (location_bonus * weights["location_bonus"])
    )
    return min(100, int(total + 0.5))

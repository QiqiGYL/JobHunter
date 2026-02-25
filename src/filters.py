# -*- coding: utf-8 -*-
"""
职位过滤规则：经验年限、Intern/Co-op、毕业年份等。
"""

from __future__ import annotations

import re

import pandas as pd

# Intern / Co-op / Student
EXCLUDE_TITLE_DESC = re.compile(
    r"\b(Intern(ship)?|Co-?op|Student|University\s+Student|Campus\s+Hire|Rotational\s+Program)\b",
    re.IGNORECASE,
)

# 4 年及以上经验
SENIOR_PATTERNS = re.compile(
    r"\b([4-9]\+?\s*years?|[3-9]-[5-9]\s*years?|10\+?\s*years?|Senior|Staff|Principal|Tech\s+Lead|Engineering\s+Lead|Lead\s+Engineer)\b",
    re.IGNORECASE,
)

# 2026 毕业要求
EXCLUDE_2026_GRAD = re.compile(
    r"\b(Class\s+of\s+2026|2026\s+Grad(uate)?|Graduation\s+(by\s+)?2026|December\s+2025\s+Grad)\b",
    re.IGNORECASE,
)

GRAD_MUST_BY_DATE = re.compile(
    r"graduat(e|ion)\s+by\s+(\w+\s+\d{4})",
    re.IGNORECASE,
)

GRAD_FRIENDLY = re.compile(
    r"\b(Recent\s+Graduate|Class\s+of\s+202[45]|New\s+Graduate|Graduate\s+202[45])\b",
    re.IGNORECASE,
)

ENTRY_LEVEL = re.compile(
    r"\b(0\-?\s*2\s*years?|Entry\s+Level|Junior|No\s+experience|Graduate\s+role)\b",
    re.IGNORECASE,
)


def classify_job(row: pd.Series, skills: list[str]) -> tuple[str, str]:
    """返回 (target_level, rejection_reason)。"""
    title = str(row.get("title") or "")
    desc = str(row.get("description") or "")
    combined = f"{title} {desc}"

    if EXCLUDE_TITLE_DESC.search(combined):
        return "Too Senior", "Exclude: Intern/Co-op/Student in title or description"
    if EXCLUDE_2026_GRAD.search(combined):
        return "Too Senior", "Exclude: Position requires 2026 graduation (we graduate June 2025)"
    if SENIOR_PATTERNS.search(combined):
        return "Too Senior", "Exclude: 4+ years / Senior / Staff / Lead"

    grad_unlikely = bool(GRAD_MUST_BY_DATE.search(combined))
    grad_friendly = bool(GRAD_FRIENDLY.search(combined))
    entry_ok = bool(ENTRY_LEVEL.search(combined)) or not SENIOR_PATTERNS.search(combined)

    if grad_unlikely:
        return "Unlikely", "Graduation: job mentions must graduate by a date (e.g. Oct 2025)"
    if grad_friendly and entry_ok:
        return "Perfect Match", ""
    if entry_ok:
        return "Possible", ""
    return "Too Senior", "Exclude: experience level not entry/junior and no friendly wording"


def location_score(location: str) -> int:
    """地理优先级打分：Toronto/Mississauga 100, Ontario 50, 其他 0。"""
    if not location:
        return 0
    loc = str(location).strip().lower()
    if "toronto" in loc or "mississauga" in loc:
        return 100
    if "ontario" in loc or " on " in loc or loc.endswith(" on"):
        return 50
    return 0

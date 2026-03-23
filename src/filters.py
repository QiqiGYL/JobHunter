# -*- coding: utf-8 -*-
"""
Job filtering rules: experience level, intern/co-op, graduation year, non-software roles.
Supports optional FilterOptions for dynamic rules from the frontend.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd


# Role IDs for job type filter (frontend sends these; we match title/description against keywords)
JOB_ROLE_KEYWORDS: dict[str, list[str]] = {
    "software_developer": [
        "software developer", "software engineer", "developer", "full stack", "fullstack",
        "backend", "frontend", "front-end", "back-end", "application developer",
    ],
    "quality_assurance": [
        "quality assurance", "qa engineer", "test engineer", "testing", "sdet",
        "quality engineer", "automation engineer",
    ],
    "data_analyst": [
        "data analyst", "data scientist", "data analytics", "business intelligence",
        "bi analyst", "analytics engineer",
    ],
}


@dataclass
class FilterOptions:
    """Dynamic filter settings from the frontend (API only; hunt.py uses defaults via None)."""
    years_min: int = 0
    years_max: int = 2
    graduation_year: Optional[int] = None  # None = any (new grad & non-new grad)
    exclude_intern_coop: bool = True
    job_roles: list[str] = field(default_factory=list)  # empty = any role; else e.g. ["software_developer", "data_analyst"]
    location_country: Optional[str] = None  # "Canada" | "United States" | None = any

# Intern / Co-op / Student — checked against title only to avoid
# false positives like "preferred co-op experience" in description
EXCLUDE_TITLE_DESC = re.compile(
    r"\b(Intern(ship)?|Co-?op|Student|University\s+Student|Campus\s+Hire|Rotational\s+Program)\b",
    re.IGNORECASE,
)

# 4+ years experience; also catches XXX Lead titles (Test Lead, QA Lead, Team Lead, etc.)
SENIOR_PATTERNS = re.compile(
    r"\b([4-9]\+?\s*years?|[3-9]-[5-9]\s*years?|10\+?\s*years?|Senior|Staff|Principal|"
    r"Tech\s+Lead|Engineering\s+Lead|Lead\s+Engineer|\w+\s+Lead\b)\b",
    re.IGNORECASE,
)

# Explicit seniority levels in title: Level 2–9, Roman numerals II/III/IV+ (e.g. Programmer III)
SENIOR_LEVEL_IN_TITLE = re.compile(
    r"\bLevel\s+[2-9]\b|\s+(II|III|IV|V|VI|VII|VIII|IX)\b",
    re.IGNORECASE,
)

# Requires 2026 graduation (user graduates June 2025) — used when filter_options is None
EXCLUDE_2026_GRAD = re.compile(
    r"\b(Class\s+of\s+2026|2026\s+Grad(uate)?|Graduation\s+(by\s+)?2026|December\s+2025\s+Grad)\b",
    re.IGNORECASE,
)

# Capture graduation year in context for dynamic filtering (only unambiguous degree/graduation phrasing).
# Avoid matching company history like "Since 1965" by not using a generic "any word + year" pattern.
GRAD_YEAR_PREFIX = re.compile(
    r"\b(?:Class\s+of|Graduation\s+(?:by\s+)?|Graduate\s+(?:by\s+)?|"
    r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+)"
    r"\s*(\d{4})\s*(?:Grad|Graduate|Graduation)?\b",
    re.IGNORECASE,
)
GRAD_YEAR_SUFFIX = re.compile(
    r"\b(\d{4})\s*(?:Grad|Graduate|Graduation)\b",
    re.IGNORECASE,
)
# Degree/graduation year range: "degree ... between September 2025 to September 2026" -> capture 2025, 2026
GRAD_YEAR_RANGE = re.compile(
    r"(?:degree|graduat|bachelor).{0,80}?\b(\d{4})\s*(?:to|and|-)\s*(?:\w+\s+)?(\d{4})\b",
    re.IGNORECASE | re.DOTALL,
)

# Experience range: "X+ years", "X-Y years", "X years" to extract minimum required years
REQUIRED_YEARS_PATTERN = re.compile(
    r"\b(\d+)\s*\+\s*years?\b|\b(\d+)\s*-\s*\d+\s*years?\b|\b(\d+)\s+years?\s+experience\b",
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
    r"\b(0\-?\s*2\s*years?|Entry\s+Level|Junior|Associate|No\s+experience|Graduate\s+role)\b",
    re.IGNORECASE,
)

# Job titles clearly unrelated to software / development
NON_SOFTWARE_TITLE = re.compile(
    r"\b("
    # Construction, civil, estimation
    r"Construction\s+Estimator|Estimator\s*-\s*Construction|CAD\s+Technician|"
    r"Drafting\s+Technician|Civil\s+Engineer|Structural\s+Engineer|"
    r"Mechanical\s+Engineer|Electrical\s+Engineer|Electrical\s+Estimator|"
    r"Project\s+Estimator|Quantity\s+Surveyor|"
    # Environmental, geological, natural sciences
    r"Hydrologist|Hydrogeologist|Geologist|Geophysicist|Geoscientist|"
    r"Environmental\s+Scientist|Environmental\s+Engineer|Environmental\s+Technician|"
    r"Environmental\s+Consultant|Ecologist|Biologist|Microbiologist|"
    r"Chemist|Biochemist|Lab\s+Technician|Laboratory\s+Technician|"
    r"Field\s+Technician|Soil\s+Scientist|"
    # Healthcare
    r"Nurse|Nursing|Pharmacist|Physician|Dentist|Physiotherapist|"
    r"Occupational\s+Therapist|Radiologist|Veterinarian|"
    # Accounting, finance (non-technical)
    r"Accountant|Bookkeeper|Auditor|Tax\s+Specialist|Payroll\s+Specialist|"
    # Marketing, sales (non-technical)
    r"Sales\s+Representative|Account\s+Executive|Marketing\s+Coordinator|"
    r"Social\s+Media\s+Manager|Copywriter|Graphic\s+Designer|"
    # Trades and manual labour
    r"Electrician|Plumber|HVAC\s+Technician|Welder|Machinist|"
    r"Truck\s+Driver|Warehouse\s+Associate|Forklift\s+Operator"
    r")\b",
    re.IGNORECASE,
)


def _parse_required_years(text: str) -> Optional[int]:
    """Return the minimum years of experience explicitly required in text, or None.
    E.g. '3+ years' -> 3, '1-2 years' -> 1, '5 years experience' -> 5.
    If multiple matches, returns the maximum (strictest requirement).
    """
    if not text:
        return None
    found = []
    for m in REQUIRED_YEARS_PATTERN.finditer(text):
        # Group 1: X+ years, Group 2: X-Y years, Group 3: X years experience
        val = m.group(1) or m.group(2) or m.group(3)
        if val:
            found.append(int(val))
    return max(found) if found else None


def _grad_years_mentioned(text: str) -> list[int]:
    """Return list of 4-digit years mentioned in graduation/degree context.
    Includes: Class of YYYY, YYYY Grad, Month YYYY Grad, and degree ranges (e.g. between 2025 to 2026).
    Excludes: generic phrases like 'Since 1965' (company history).
    """
    if not text:
        return []
    years = []
    for m in GRAD_YEAR_PREFIX.finditer(text):
        if m.group(1):
            years.append(int(m.group(1)))
    for m in GRAD_YEAR_SUFFIX.finditer(text):
        if m.group(1):
            years.append(int(m.group(1)))
    for m in GRAD_YEAR_RANGE.finditer(text):
        y1, y2 = m.group(1), m.group(2)
        if y1:
            years.append(int(y1))
        if y2:
            years.append(int(y2))
    return years


def classify_job(
    row: pd.Series,
    skills: list[str],
    filter_options: Optional[FilterOptions] = None,
) -> tuple[str, str]:
    """Return (target_level, rejection_reason) for a job row.
    When filter_options is None, uses hardcoded rules (hunt.py). When provided, uses dynamic rules (API).
    """
    title = str(row.get("title") or "")
    desc = str(row.get("description") or "")
    combined = f"{title} {desc}"

    if filter_options is not None:
        # Dynamic path: apply frontend options first
        if filter_options.exclude_intern_coop and EXCLUDE_TITLE_DESC.search(title):
            return "Too Senior", "Exclude: Intern/Co-op/Student in title (description 'preferred' ignored)"
        # Optional graduation year: only filter when user set a specific year
        if filter_options.graduation_year is not None:
            grad_years = _grad_years_mentioned(combined)
            if grad_years and not any(y == filter_options.graduation_year for y in grad_years):
                bad = next((y for y in grad_years if y != filter_options.graduation_year), grad_years[0])
                return "Too Senior", f"Exclude: Position requires {bad} graduation (filter: {filter_options.graduation_year})"
        # Job type / role: if user selected any roles, keep only jobs matching those roles
        if filter_options.job_roles:
            keywords = []
            for role_id in filter_options.job_roles:
                keywords.extend(JOB_ROLE_KEYWORDS.get(role_id, []))
            if keywords:
                combined_lower = combined.lower()
                if not any(kw in combined_lower for kw in keywords):
                    return "Too Senior", "Exclude: job type not in selected roles"
        req_years = _parse_required_years(combined)
        if req_years is not None and req_years > filter_options.years_max:
            return "Too Senior", f"Exclude: job requires {req_years}+ years (max {filter_options.years_max})"
    else:
        # Original hardcoded path (hunt.py)
        if EXCLUDE_TITLE_DESC.search(title):
            return "Too Senior", "Exclude: Intern/Co-op/Student in title (description 'preferred' ignored)"
        if EXCLUDE_2026_GRAD.search(combined):
            return "Too Senior", "Exclude: Position requires 2026 graduation (we graduate June 2025)"

    if NON_SOFTWARE_TITLE.search(title):
        return "Too Senior", "Exclude: job title not software/tech related (e.g. Construction, CAD-only)"
    if SENIOR_LEVEL_IN_TITLE.search(title):
        return "Too Senior", "Exclude: Level 2+ or III/IV in title (too senior)"

    # If the title itself signals entry-level (Junior/Associate/Entry-Level), do not exclude
    # based on senior keywords that appear in context (e.g. "work with senior engineers")
    title_entry = bool(ENTRY_LEVEL.search(title))
    if not title_entry and SENIOR_PATTERNS.search(combined):
        if filter_options is not None:
            threshold = int(filter_options.years_max) + 1
            return "Too Senior", f"Exclude: {threshold}+ years / Senior / Staff / Lead (max {filter_options.years_max})"
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
    """Location priority score: Toronto/Mississauga 100, Ontario 50, elsewhere 0."""
    if not location:
        return 0
    loc = str(location).strip().lower()
    if "toronto" in loc or "mississauga" in loc:
        return 100
    if "ontario" in loc or " on " in loc or loc.endswith(" on"):
        return 50
    return 0

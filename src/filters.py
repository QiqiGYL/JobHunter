# -*- coding: utf-8 -*-
"""
职位过滤规则：经验年限、Intern/Co-op、毕业年份等。
"""

from __future__ import annotations

import re

import pandas as pd

# Intern / Co-op / Student（仅看标题，避免 "Preferred: co-op experience" 误杀）
EXCLUDE_TITLE_DESC = re.compile(
    r"\b(Intern(ship)?|Co-?op|Student|University\s+Student|Campus\s+Hire|Rotational\s+Program)\b",
    re.IGNORECASE,
)

# 4 年及以上经验；含 XXX Lead（Test Lead, QA Lead, Team Lead 等）
SENIOR_PATTERNS = re.compile(
    r"\b([4-9]\+?\s*years?|[3-9]-[5-9]\s*years?|10\+?\s*years?|Senior|Staff|Principal|"
    r"Tech\s+Lead|Engineering\s+Lead|Lead\s+Engineer|\w+\s+Lead\b)\b",
    re.IGNORECASE,
)

# 标题中的 senior 级别：Level 2–9、罗马数字 II/III/IV 等（Programmer III = Level 3）
SENIOR_LEVEL_IN_TITLE = re.compile(
    r"\bLevel\s+[2-9]\b|\s+(II|III|IV|V|VI|VII|VIII|IX)\b",
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
    r"\b(0\-?\s*2\s*years?|Entry\s+Level|Junior|Associate|No\s+experience|Graduate\s+role)\b",
    re.IGNORECASE,
)

# 标题明显与软件/开发无关，排除
NON_SOFTWARE_TITLE = re.compile(
    r"\b("
    # 建筑、土木、估算
    r"Construction\s+Estimator|Estimator\s*-\s*Construction|CAD\s+Technician|"
    r"Drafting\s+Technician|Civil\s+Engineer|Structural\s+Engineer|"
    r"Mechanical\s+Engineer|Electrical\s+Engineer|Electrical\s+Estimator|"
    r"Project\s+Estimator|Quantity\s+Surveyor|"
    # 环境、地质、水文、自然科学
    r"Hydrologist|Hydrogeologist|Geologist|Geophysicist|Geoscientist|"
    r"Environmental\s+Scientist|Environmental\s+Engineer|Environmental\s+Technician|"
    r"Environmental\s+Consultant|Ecologist|Biologist|Microbiologist|"
    r"Chemist|Biochemist|Lab\s+Technician|Laboratory\s+Technician|"
    r"Field\s+Technician|Soil\s+Scientist|"
    # 医疗、护理
    r"Nurse|Nursing|Pharmacist|Physician|Dentist|Physiotherapist|"
    r"Occupational\s+Therapist|Radiologist|Veterinarian|"
    # 会计、金融（非技术岗）
    r"Accountant|Bookkeeper|Auditor|Tax\s+Specialist|Payroll\s+Specialist|"
    # 市场、销售（非技术岗）
    r"Sales\s+Representative|Account\s+Executive|Marketing\s+Coordinator|"
    r"Social\s+Media\s+Manager|Copywriter|Graphic\s+Designer|"
    # 其他明显非软件岗
    r"Electrician|Plumber|HVAC\s+Technician|Welder|Machinist|"
    r"Truck\s+Driver|Warehouse\s+Associate|Forklift\s+Operator"
    r")\b",
    re.IGNORECASE,
)


def classify_job(row: pd.Series, skills: list[str]) -> tuple[str, str]:
    """返回 (target_level, rejection_reason)。"""
    title = str(row.get("title") or "")
    desc = str(row.get("description") or "")
    combined = f"{title} {desc}"

    if EXCLUDE_TITLE_DESC.search(title):
        return "Too Senior", "Exclude: Intern/Co-op/Student in title (description 'preferred' ignored)"
    if NON_SOFTWARE_TITLE.search(title):
        return "Too Senior", "Exclude: job title not software/tech related (e.g. Construction, CAD-only)"
    if SENIOR_LEVEL_IN_TITLE.search(title):
        return "Too Senior", "Exclude: Level 2+ or III/IV in title (too senior)"
    if EXCLUDE_2026_GRAD.search(combined):
        return "Too Senior", "Exclude: Position requires 2026 graduation (we graduate June 2025)"
    # 标题已明确为初级（Junior/Entry/0-2 years）时，不因 description 里出现 Senior/Lead 等就排除（如 "work with senior engineers"）
    title_entry = bool(ENTRY_LEVEL.search(title))
    if not title_entry and SENIOR_PATTERNS.search(combined):
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

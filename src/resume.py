# -*- coding: utf-8 -*-
"""
Resume processing: PDF text extraction, text cleaning, keyword extraction and comparison.
"""

from __future__ import annotations

import os
import re

try:
    import pdfplumber
    HAS_PDFPLUMBER = True
except ImportError:
    HAS_PDFPLUMBER = False


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract raw text from a PDF using pdfplumber."""
    if not pdf_path or not os.path.isfile(pdf_path):
        return ""
    if not HAS_PDFPLUMBER:
        return ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            parts = []
            for page in pdf.pages:
                raw = page.extract_text()
                if raw:
                    parts.append(raw)
            return "\n".join(parts) if parts else ""
    except Exception:
        return ""


def clean_resume_text(text: str) -> str:
    """Strip non-ASCII characters while preserving English, digits, and symbols like C++."""
    if not text:
        return ""
    allowed_extra = "+-."
    kept = "".join(
        c for c in text
        if ord(c) < 128 and (c.isalnum() or c.isspace() or c in allowed_extra)
    )
    return re.sub(r"\s+", " ", kept).strip()


def get_resume_text(resume_pdf_path: str) -> str:
    """Read and clean the full resume text from a PDF file."""
    if not resume_pdf_path or not os.path.isfile(resume_pdf_path):
        return ""
    raw = extract_text_from_pdf(resume_pdf_path)
    text = clean_resume_text(raw)
    print(f"DEBUG: first 100 chars of cleaned resume: {text[:100]}")
    return text


def extract_keywords_from_resume(
    pdf_path: str,
    keyword_dict: dict[str, list[str]],
) -> dict:
    """Extract and count tech keywords from a resume PDF, grouped by category.

    For keywords containing '.' or '/' (e.g. React.js, CI/CD), plain substring
    matching is used instead of word boundaries to avoid regex edge cases.

    Returns:
        {
            "全部关键词": {category: {keyword: count, ...}, ...},
            "缺失关键词": [keywords not found],
            "简历文本": "cleaned resume text"
        }
    """
    raw = extract_text_from_pdf(pdf_path)
    resume_text = clean_resume_text(raw)

    if not resume_text:
        return {"全部关键词": {}, "缺失关键词": [], "简历文本": ""}

    found_keywords = {}
    for category, keywords in keyword_dict.items():
        found_keywords[category] = {}
        for keyword in keywords:
            kw_escaped = re.escape(keyword.lower())
            if re.search(r'[./]', keyword):
                pattern = re.compile(kw_escaped, re.IGNORECASE)
            else:
                pattern = re.compile(r"\b" + kw_escaped + r"\b", re.IGNORECASE)
            matches = len(pattern.findall(resume_text.lower()))
            if matches > 0:
                found_keywords[category][keyword] = matches

    found_set = set()
    for kw_dict in found_keywords.values():
        found_set.update(kw_dict.keys())

    all_keywords = set()
    for keywords in keyword_dict.values():
        all_keywords.update(keywords)

    return {
        "全部关键词": found_keywords,
        "缺失关键词": sorted(all_keywords - found_set),
        "简历文本": resume_text,
    }


def compare_with_resume_skills(
    keywords_result: dict,
    resume_skills: list[str],
) -> dict:
    """Compare keywords found in the resume against the RESUME_SKILLS list."""
    found_in_resume = set()
    for category_dict in keywords_result["全部关键词"].values():
        found_in_resume.update(category_dict.keys())

    resume_skills_set = set(resume_skills)
    return {
        "在简历中但不在RESUME_SKILLS": sorted(found_in_resume - resume_skills_set),
        "在RESUME_SKILLS中但不在简历": sorted(resume_skills_set - found_in_resume),
        "都有": sorted(found_in_resume & resume_skills_set),
    }

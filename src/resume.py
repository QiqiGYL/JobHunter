# -*- coding: utf-8 -*-
"""
简历处理：PDF 提取、文本清洗、关键词提取与对比。
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
    """使用 pdfplumber 从 PDF 提取正文。"""
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
    """过滤非 ASCII 乱码，保留英文、数字及 C++ 等符号。"""
    if not text:
        return ""
    allowed_extra = "+-."
    kept = "".join(
        c for c in text
        if ord(c) < 128 and (c.isalnum() or c.isspace() or c in allowed_extra)
    )
    return re.sub(r"\s+", " ", kept).strip()


def get_resume_text(resume_pdf_path: str) -> str:
    """读取并清洗简历全文。"""
    if not resume_pdf_path or not os.path.isfile(resume_pdf_path):
        return ""
    raw = extract_text_from_pdf(resume_pdf_path)
    text = clean_resume_text(raw)
    print(f"DEBUG: 清洗后简历前100字符: {text[:100]}")
    return text


def extract_keywords_from_resume(
    pdf_path: str,
    keyword_dict: dict[str, list[str]],
) -> dict:
    """
    从简历 PDF 中提取所有技术关键词，并按类别统计。

    Returns:
        {
            "全部关键词": {category: {keyword: 出现次数, ...}, ...},
            "缺失关键词": [keywords not found],
            "简历文本": "清洗后的简历全文"
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
            # 对含 . 或 / 的关键词（如 React.js、CI/CD）不加词边界，用简单子串匹配
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
    """对比简历中发现的关键词和 RESUME_SKILLS 列表。"""
    found_in_resume = set()
    for category_dict in keywords_result["全部关键词"].values():
        found_in_resume.update(category_dict.keys())

    resume_skills_set = set(resume_skills)
    return {
        "在简历中但不在RESUME_SKILLS": sorted(found_in_resume - resume_skills_set),
        "在RESUME_SKILLS中但不在简历": sorted(resume_skills_set - found_in_resume),
        "都有": sorted(found_in_resume & resume_skills_set),
    }

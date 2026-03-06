# -*- coding: utf-8 -*-
"""
Salary extraction: parse salary information from job description text.
"""

from __future__ import annotations

import re


def extract_salary_from_text(text: str) -> str:
    """Extract a salary string from JD text (e.g. $80k-$100k, CA$46K/yr, $25/hour)."""
    if not text or not text.strip():
        return ""

    # CA$/CAD$ annual range: CA$46K/yr - CA$74K/yr
    ca_range_yr = re.search(
        r"(?:CA|CAD)\s*\$?\s*(\d{1,3}(?:,\d{3})*)\s*[kK]?\s*/\s*yr\s*[-–to]+\s*(?:CA|CAD)\s*\$?\s*(\d{1,3}(?:,\d{3})*)\s*[kK]?\s*/\s*yr",
        text, re.IGNORECASE,
    )
    if ca_range_yr:
        lo, hi = ca_range_yr.group(1).replace(",", ""), ca_range_yr.group(2).replace(",", "")
        return f"CA${lo}K/yr - CA${hi}K/yr"

    ca_range_k = re.search(
        r"(?:CA|CAD)\s*\$?\s*(\d{1,3}(?:,\d{3})*)\s*[kK]\s*[-–to]+\s*(?:CA|CAD)\s*\$?\s*(\d{1,3}(?:,\d{3})*)\s*[kK]",
        text, re.IGNORECASE,
    )
    if ca_range_k:
        lo, hi = ca_range_k.group(1).replace(",", ""), ca_range_k.group(2).replace(",", "")
        return f"CA${lo}K - CA${hi}K"

    # $XXk/yr - $YYk/yr
    range_yr = re.search(
        r"\$?\s*(\d{1,3}(?:,\d{3})*)\s*[kK]?\s*/\s*yr\s*[-–to]+\s*\$?\s*(\d{1,3}(?:,\d{3})*)\s*[kK]?\s*/\s*yr",
        text, re.IGNORECASE,
    )
    if range_yr:
        lo, hi = range_yr.group(1).replace(",", ""), range_yr.group(2).replace(",", "")
        return f"${lo}K/yr - ${hi}K/yr"

    # Hourly with context keyword (salary/pay/rate/etc.)
    hourly = re.search(
        r"(?:salary|pay|rate|compensation|wage)[\s:]*\$?\s*(\d{1,3}(?:,\d{3})*)\s*/\s*(?:hour|hr|h)\b",
        text, re.IGNORECASE,
    )
    if hourly:
        return f"${hourly.group(1).replace(',', '')}/hour"

    # Hourly without context keyword
    hourly2 = re.search(
        r"\$?\s*(\d{1,3}(?:,\d{3})*)\s*/\s*(?:hour|hr|h)\b",
        text, re.IGNORECASE,
    )
    if hourly2:
        return f"${hourly2.group(1).replace(',', '')}/hour"

    # Annual range $80k-$100k
    range_k = re.search(
        r"\$?\s*(\d{1,3}(?:,\d{3})*)\s*[kK]\s*[-–to]+\s*\$?\s*(\d{1,3}(?:,\d{3})*)\s*[kK]?",
        text, re.IGNORECASE,
    )
    if range_k:
        lo, hi = range_k.group(1).replace(",", ""), range_k.group(2).replace(",", "")
        return f"${lo}k - ${hi}k"

    # Annual range $80,000 - $100,000
    range_full = re.search(
        r"\$?\s*(\d{1,3}(?:,\d{3}){0,2})\s*[-–to]+\s*\$?\s*(\d{1,3}(?:,\d{3}){0,2})\s*(?:per\s+year|/year|annually|CAD|USD)?",
        text, re.IGNORECASE,
    )
    if range_full:
        lo, hi = range_full.group(1).replace(",", ""), range_full.group(2).replace(",", "")
        if len(lo) <= 3 and len(hi) <= 3:
            return f"${lo}-${hi}k"
        return f"${int(lo):,} - ${int(hi):,}"

    # Single salary $90k
    single_k = re.search(
        r"(?:salary|pay|up to|range)[\s:]*\$?\s*(\d{1,3}(?:,\d{3})*)\s*[kK]\b",
        text, re.IGNORECASE,
    )
    if single_k:
        return f"${single_k.group(1).replace(',', '')}k"

    single_full = re.search(
        r"(?:salary|pay|up to)[\s:]*\$?\s*(\d{1,3}(?:,\d{3}){1,2})\s*(?:per\s+year|/year)?",
        text, re.IGNORECASE,
    )
    if single_full:
        return f"${single_full.group(1)}"

    return ""

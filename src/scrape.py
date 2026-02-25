# -*- coding: utf-8 -*-
"""
职位抓取：调用 jobspy。
"""

from __future__ import annotations

import pandas as pd


def run_scrape(
    search_term: str = "Software Engineer",
    location: str = "Canada",
    results_wanted: int = 100,
    site_name: list[str] | None = None,
) -> pd.DataFrame:
    """调用 jobspy 抓取职位，hours_old=24。"""
    from jobspy import scrape_jobs
    if site_name is None:
        site_name = ["indeed", "linkedin"]
    return scrape_jobs(
        site_name=site_name,
        search_term=search_term,
        location=location,
        results_wanted=results_wanted,
        hours_old=24,
    )

# -*- coding: utf-8 -*-
"""
职位抓取：调用 jobspy。按站点分别抓取后合并，某一站失败不影响其他站结果。
"""

from __future__ import annotations

import pandas as pd


def run_scrape(
    search_term: str = "Software Engineer",
    location: str = "Canada",
    results_wanted: int = 100,
    site_name: list[str] | None = None,
    country_indeed: str = "Canada",
) -> pd.DataFrame:
    """按站点分别抓取后合并；某站失败（如 Indeed 断连）时保留其他站数据。hours_old=24，Indeed 用 country_indeed。"""
    from jobspy import scrape_jobs
    if site_name is None:
        site_name = ["indeed", "linkedin"]
    frames = []
    for site in site_name:
        print(f"正在抓取 {site}（最多 {results_wanted} 条）… 若久无输出属正常，请勿 kill。")
        try:
            df = scrape_jobs(
                site_name=[site],
                search_term=search_term,
                location=location,
                results_wanted=results_wanted,
                hours_old=24,
                country_indeed=country_indeed,
            )
            if df is not None and not df.empty:
                frames.append(df)
                print(f"  → {site} 完成，得到 {len(df)} 条。")
            else:
                print(f"  → {site} 返回 0 条。")
        except Exception as e:
            print(f"WARNING: 抓取 {site} 失败 ({e!r})，已跳过该站点。")
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)

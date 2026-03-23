# -*- coding: utf-8 -*-
"""
Job scraping: calls jobspy per site and merges results.
If one site fails (e.g. Indeed connection error), other sites still complete normally.
"""

from __future__ import annotations

import pandas as pd


def run_scrape(
    search_term: str = "Software Engineer",
    location: str = "Canada",
    results_wanted: int = 100,
    site_name: list[str] | None = None,
    site_results_wanted: dict[str, int] | None = None,
    country_indeed: str = "Canada",
) -> pd.DataFrame:
    """Scrape each site separately and concatenate results.

    Per-site result counts are controlled by results_wanted.
    LinkedIn uses linkedin_fetch_description=True for full JD text (slower).
    """
    from jobspy import scrape_jobs
    if site_name is None:
        site_name = ["indeed", "linkedin"]
    per_site = {}
    if site_results_wanted:
        for k, v in site_results_wanted.items():
            try:
                per_site[str(k).strip().lower()] = max(1, int(v))
            except Exception:
                continue
    frames = []
    for site in site_name:
        site_key = str(site).strip().lower()
        n = per_site.get(site_key, max(1, int(results_wanted)))
        print(f"Scraping {site} (up to {n} results)… this may take a while, please wait.")
        try:
            df = scrape_jobs(
                site_name=[site],
                search_term=search_term,
                location=location,
                results_wanted=n,
                hours_old=24,
                country_indeed=country_indeed,
                ###Important:
                #####Turn it off when debuging or linkedin results > 30####
                linkedin_fetch_description=True,
            )
            if df is not None and not df.empty:
                frames.append(df)
                print(f"  → {site} done: {len(df)} results.")
            else:
                print(f"  → {site} returned 0 results.")
        except Exception as e:
            print(f"WARNING: Failed to scrape {site} ({e!r}), skipping.")
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)

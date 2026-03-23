#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Job scraping and filtering entry point — optimised for June 2025 graduates targeting junior roles.
Core logic lives in the src/ package; this file is the CLI entry point only.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

import pandas as pd

from src.config import (
    DATA_DIR,
    RESUME_PDF_PATH,
    auto_update_resume_skills,
    load_skill_config,
    DEFAULT_RESUME_SKILLS,
)
from src.resume import get_resume_text
from src.scoring import get_semantic_model, compute_hybrid_score, SCORE_WEIGHTS
from src.filters import location_score
from src.salary import extract_salary_from_text
from src.scrape import run_scrape
from src import db as db_module


def main():
    parser = argparse.ArgumentParser(
        description="Job scraping & scoring (4-component: semantic 40% + keyword 35% + title 15% + location 10%)"
    )
    parser.add_argument("--search", default="Junior Software Engineer", help="Job search query")
    parser.add_argument("--search-terms", default="", help="Comma-separated search queries; if set, overrides --search")
    parser.add_argument("--location", default="Canada", help="Job location")
    parser.add_argument("--results", type=int, default=30, help="Results per site")
    parser.add_argument("--results-indeed", type=int, default=None, help="Indeed results override")
    parser.add_argument("--results-linkedin", type=int, default=None, help="LinkedIn results override")
    parser.add_argument("--sites", default="indeed,linkedin", help="Comma-separated site list")
    parser.add_argument("--resume-pdf", default=RESUME_PDF_PATH, help="Path to resume PDF")
    parser.add_argument("--out", default="data/job_hunt_results.xlsx", help="Output Excel path")
    parser.add_argument("--csv", action="store_true", help="Also write a CSV copy")
    parser.add_argument("--config", default="", help="YAML/JSON config file path")
    parser.add_argument("--position", default="", help="Position name in config")
    parser.add_argument(
        "--analyze-top", type=int, default=0, metavar="N",
        help="Run ATS analysis on top N jobs after scraping (0 = skip, default)",
    )
    parser.add_argument("--deepseek-key", default="", help="DeepSeek API key")
    parser.add_argument("--export-xlsx", action="store_true", help="Export DB to xlsx after upsert (for backup or ATS)")
    args = parser.parse_args()

    # 1) Load semantic model
    print("Loading semantic model (all-MiniLM-L6-v2)...")
    model = get_semantic_model()

    # 2) Load skills and weights
    weights = SCORE_WEIGHTS
    if args.config and args.position:
        pos_config = load_skill_config(args.config)
        if pos_config and args.position in pos_config:
            pos_data = pos_config[args.position]
            skills = pos_data.get("skills", DEFAULT_RESUME_SKILLS)
            if "skills" in pos_data:
                print(f"Loaded skills for position '{args.position}': {skills}")
            if "weights" in pos_data:
                weights = pos_data["weights"]
                print(f"Loaded weights for position '{args.position}': {weights}")
        else:
            skills = auto_update_resume_skills(args.resume_pdf)
    else:
        skills = auto_update_resume_skills(args.resume_pdf)
    if args.config and not args.position:
        print("WARNING: --config specified without --position; using default config")

    # 3) Encode resume into embedding vector
    resume_text = get_resume_text(args.resume_pdf)
    resume_embedding = None
    if model is not None and resume_text and len(resume_text.strip()) >= 20:
        resume_embedding = model.encode([resume_text[:8000]], normalize_embeddings=True)
        print("Resume embedding ready.")
    else:
        print("Semantic scoring unavailable; using keyword + title scoring only.")

    # 4) Scrape jobs
    print("Scraping jobs (hours_old=24)...")
    search_terms = [s.strip() for s in str(args.search_terms).split(",") if s.strip()]
    if not search_terms:
        search_terms = [args.search]
    site_results_wanted = {}
    if args.results_indeed is not None:
        site_results_wanted["indeed"] = max(1, int(args.results_indeed))
    if args.results_linkedin is not None:
        site_results_wanted["linkedin"] = max(1, int(args.results_linkedin))
    frames = []
    for term in search_terms:
        print(f"Search term: {term}")
        one_df = run_scrape(
            search_term=term,
            location=args.location,
            results_wanted=args.results,
            site_name=[s.strip() for s in args.sites.split(",") if s.strip()] or None,
            site_results_wanted=site_results_wanted or None,
        )
        if one_df is not None and not one_df.empty:
            frames.append(one_df)
    if not frames:
        print("No jobs found.")
        return
    df = pd.concat(frames, ignore_index=True)
    if df.empty:
        print("No jobs found.")
        return
    total_scraped = len(df)
    requested_per_site = args.results
    by_site = {}
    if "site" in df.columns:
        for site, count in df["site"].value_counts().items():
            site_key = str(site).strip().lower()
            requested = site_results_wanted.get(site_key, requested_per_site)
            by_site[str(site)] = {"requested": int(requested), "got": int(count)}
        print("Results by site:", df["site"].value_counts().to_dict())

    # 5) Score each job (no hardcoded classification — API + filter bar do that from sheet "All")
    match_scores = []
    for _, row in df.iterrows():
        score = compute_hybrid_score(
            model, resume_embedding,
            str(row.get("description") or ""),
            str(row.get("title") or ""),
            str(row.get("location") or ""),
            skills, weights,
        )
        match_scores.append(score)
    df["Match_Score"] = match_scores

    # --- Previously: classify_job(row, skills) and split into Jobs / Filtered_Out (kept for reference) ---
    # from src.filters import classify_job
    # target_levels, rejection_reasons = [], []
    # for _, row in df.iterrows():
    #     level, reason = classify_job(row, skills)
    #     target_levels.append(level)
    #     rejection_reasons.append(reason)
    # df["Target Level"] = target_levels
    # df["Rejection_Reason"] = rejection_reasons
    # kept = df[df["Target Level"].isin(["Perfect Match", "Possible", "Unlikely"])].copy()
    # filtered = df[df["Target Level"] == "Too Senior"].copy()
    # ... dedupe kept, write kept → Jobs, filtered → Filtered_Out

    # 6) Extract salary range
    def _salary_range(row: pd.Series) -> str:
        lo, hi = row.get("min_amount"), row.get("max_amount")
        cur = str(row.get("currency") or "USD").strip()
        if pd.notna(lo) and pd.notna(hi):
            return f"{int(lo):,} - {int(hi):,} {cur}"
        if pd.notna(lo):
            return f"{int(lo):,}+ {cur}"
        desc = str(row.get("description") or "")
        return extract_salary_from_text(desc)

    df["salary_range"] = df.apply(_salary_range, axis=1)

    ALL_COLUMNS = [
        "title", "company", "location", "job_url", "date_posted",
        "Match_Score", "is_remote", "salary_range", "site", "description",
    ]

    # 7) Deduplicate by (company, title), keep row with best location score
    df["location_score"] = df["location"].map(
        lambda x: location_score(str(x) if pd.notna(x) else "")
    )
    df = df.sort_values(["company", "title", "location_score"], ascending=[True, True, False])
    # Save removed duplicates so you can review (same company+title, different site/link)
    removed = df[df.duplicated(subset=["company", "title"], keep="first")].copy()
    df = df.drop_duplicates(subset=["company", "title"], keep="first")
    df = df.drop(columns=["location_score"], errors="ignore")
    if not removed.empty:
        removed = removed.drop(columns=["location_score"], errors="ignore")
        removed = removed[[c for c in ALL_COLUMNS if c in removed.columns]]
        n_removed = db_module.save_dedup_removed(removed)
        print(f"Saved {n_removed} duplicate rows (removed by company+title) to DB table jobs_dedup_removed ({db_module.DB_PATH})")

    out_df = df[[c for c in ALL_COLUMNS if c in df.columns]].copy()
    out_df = out_df.sort_values("Match_Score", ascending=False).reset_index(drop=True)

    total_after_dedup = len(out_df)
    dedup_removed_count = len(removed) if not removed.empty else 0
    scrape_stats = {
        "results_wanted_per_site": requested_per_site,
        "site_overrides": site_results_wanted,
        "search_terms": search_terms,
        "by_site": by_site,
        "total_scraped": total_scraped,
        "total_after_dedup": total_after_dedup,
        "dedup_removed": dedup_removed_count,
        "at": datetime.utcnow().isoformat() + "Z",
    }
    stats_path = DATA_DIR / "last_scrape_stats.json"
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(stats_path, "w", encoding="utf-8") as f:
        json.dump(scrape_stats, f, ensure_ascii=False, indent=2)
    print(f"Scrape stats written to {stats_path}")

    # 8) Upsert to SQLite (source of truth); optionally export to xlsx
    out_path = Path(args.out)
    n = db_module.upsert_jobs(out_df)
    print(f"Upserted {n} jobs to DB ({db_module.DB_PATH})")
    if getattr(args, "export_xlsx", False) or args.analyze_top > 0:
        db_module.export_to_xlsx(out_path)
        print(f"Exported to {out_path.absolute()}")
    if args.csv:
        all_jobs = db_module.get_all_jobs()
        if all_jobs:
            export_cols = ["title", "company", "location", "job_url", "date_posted", "Match_Score", "is_remote", "salary_range", "site", "description"]
            csv_df = pd.DataFrame([{k: j.get(k) for k in export_cols} for j in all_jobs])
            csv_path = out_path.with_suffix(".csv")
            csv_df.to_csv(csv_path, index=False, encoding="utf-8-sig")
            print(f"CSV: {csv_path.absolute()}")

    # 9) Optional ATS analysis on top N jobs by Match_Score (slow — calls DeepSeek API)
    if args.analyze_top > 0 and out_df.shape[0] > 0:
        n_analyze = min(args.analyze_top, len(out_df))
        print(f"Running ATS analysis on top {n_analyze} jobs (DeepSeek API, may take several minutes)…")
        try:
            from src.ats import run_ats_analysis
            report_path = run_ats_analysis(
                excel_path=str(out_path),
                resume_pdf_path=args.resume_pdf,
                top_n=n_analyze,
                api_key=args.deepseek_key or None,
                output_path=str(out_path.parent / "ats_analysis_report.md"),
            )
            if report_path:
                print(f"ATS analysis complete. Report: {report_path}")
        except Exception as e:
            print(f"WARNING: ATS analysis failed: {e}")


if __name__ == "__main__":
    main()

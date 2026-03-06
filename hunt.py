#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Job scraping and filtering entry point — optimised for June 2025 graduates targeting junior roles.
Core logic lives in the src/ package; this file is the CLI entry point only.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

import pandas as pd

from src.config import (
    RESUME_PDF_PATH,
    auto_update_resume_skills,
    load_skill_config,
    DEFAULT_RESUME_SKILLS,
)
from src.resume import get_resume_text
from src.scoring import get_semantic_model, compute_hybrid_score, SCORE_WEIGHTS
from src.filters import classify_job, location_score
from src.salary import extract_salary_from_text
from src.scrape import run_scrape


def main():
    parser = argparse.ArgumentParser(
        description="Job scraping & scoring (4-component: semantic 40% + keyword 35% + title 15% + location 10%)"
    )
    parser.add_argument("--search", default="Junior Software Engineer", help="Job search query")
    parser.add_argument("--location", default="Canada", help="Job location")
    parser.add_argument("--results", type=int, default=30, help="Results per site")
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
    df = run_scrape(
        search_term=args.search,
        location=args.location,
        results_wanted=args.results,
        site_name=[s.strip() for s in args.sites.split(",") if s.strip()] or None,
    )
    if df.empty:
        print("No jobs found.")
        return
    if "site" in df.columns:
        print("Results by site:", df["site"].value_counts().to_dict())

    # 5) Score and classify each job
    target_levels, rejection_reasons, match_scores = [], [], []
    for _, row in df.iterrows():
        level, reason = classify_job(row, skills)
        score = compute_hybrid_score(
            model, resume_embedding,
            str(row.get("description") or ""),
            str(row.get("title") or ""),
            str(row.get("location") or ""),
            skills, weights,
        )
        target_levels.append(level)
        rejection_reasons.append(reason)
        match_scores.append(score)

    df["Target Level"] = target_levels
    df["Rejection_Reason"] = rejection_reasons
    df["Match_Score"] = match_scores

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

    OUTPUT_COLUMNS = [
        "title", "company", "location", "job_url", "date_posted",
        "Target Level", "Match_Score", "Rejection_Reason",
        "is_remote", "salary_range", "site", "description",
    ]

    def _keep_columns(frame: pd.DataFrame) -> pd.DataFrame:
        cols = [c for c in OUTPUT_COLUMNS if c in frame.columns]
        return frame[cols].copy()

    # 7) Deduplicate and group results
    kept = df[df["Target Level"].isin(["Perfect Match", "Possible", "Unlikely"])].copy()
    kept["location_score"] = kept["location"].map(
        lambda x: location_score(str(x) if pd.notna(x) else "")
    )
    kept = kept.sort_values(["company", "title", "location_score"], ascending=[True, True, False])
    duplicate_mask = kept.duplicated(subset=["company", "title"], keep="first")
    n_dupes = int(duplicate_mask.sum())

    dupes = kept[duplicate_mask].copy()
    dupes["Target Level"] = "Filtered"
    dupes["Rejection_Reason"] = "Duplicate Posting (Preferred higher priority location)"
    kept = kept[~duplicate_mask].drop(columns=["location_score"], errors="ignore")
    dupes = dupes.drop(columns=["location_score"], errors="ignore")

    kept = _keep_columns(kept).sort_values("Match_Score", ascending=False).reset_index(drop=True)

    filtered = df[df["Target Level"] == "Too Senior"].copy()
    filtered = _keep_columns(filtered)
    if n_dupes > 0:
        filtered = pd.concat([filtered, _keep_columns(dupes)], ignore_index=True)
    filtered = filtered.sort_values("Match_Score", ascending=False).reset_index(drop=True)

    # 8) Write Excel output
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        kept.to_excel(writer, sheet_name="Jobs", index=False)
        filtered.to_excel(writer, sheet_name="Filtered_Out", index=False)

    print(f"Kept {len(kept)} jobs → sheet 'Jobs' (sorted by Match_Score)")
    print(f"Filtered {len(filtered)} jobs → sheet 'Filtered_Out'")
    print(f"Written to: {out_path.absolute()}")
    if n_dupes > 0:
        print(f"Deduplication moved {n_dupes} duplicate posting(s) to Filtered_Out.")

    if args.csv:
        csv_path = out_path.with_suffix(".csv")
        kept.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"CSV written to: {csv_path.absolute()}")

    # 9) Optional ATS analysis on top N jobs (slow — calls DeepSeek API)
    if args.analyze_top > 0 and kept.shape[0] > 0:
        n_analyze = min(args.analyze_top, len(kept))
        print(f"Running ATS analysis on top {n_analyze} jobs (DeepSeek API, may take several minutes)…")
        try:
            from src.ats import run_ats_analysis
            report_path = run_ats_analysis(
                excel_path=str(out_path),
                resume_pdf_path=args.resume_pdf,
                top_n=min(args.analyze_top, len(kept)),
                api_key=args.deepseek_key or None,
                output_path=str(out_path.parent / "ats_analysis_report.md"),
            )
            if report_path:
                print(f"ATS analysis complete. Report: {report_path}")
        except Exception as e:
            print(f"WARNING: ATS analysis failed: {e}")

    if not filtered.empty:
        print("\n--- Rejection reason summary ---")
        for reason, cnt in filtered["Rejection_Reason"].value_counts().items():
            print(f"  [{cnt}] {reason}")


if __name__ == "__main__":
    main()

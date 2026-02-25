#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
职位抓取与筛选入口 — 针对 2025 年 6 月毕业、初级岗位精准过滤。
核心逻辑位于 src/ 包内，此文件仅做命令行入口。
"""

from __future__ import annotations

import argparse
from pathlib import Path

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
        description="职位抓取与筛选（四路打分：语义40%+关键词35%+标题15%+位置10%）"
    )
    parser.add_argument("--search", default="Software Engineer", help="搜索职位关键词")
    parser.add_argument("--location", default="Canada", help="工作地点")
    parser.add_argument("--results", type=int, default=100, help="每个站点抓取数量")
    parser.add_argument("--sites", default="indeed,linkedin", help="站点，逗号分隔")
    parser.add_argument("--resume-pdf", default=RESUME_PDF_PATH, help="简历 PDF 路径")
    parser.add_argument("--out", default="data/job_hunt_results.xlsx", help="输出 Excel 路径")
    parser.add_argument("--csv", action="store_true", help="同时输出 CSV")
    parser.add_argument("--config", default="", help="YAML/JSON 配置文件路径")
    parser.add_argument("--position", default="", help="配置中职位名称")
    parser.add_argument(
        "--analyze-top", type=int, default=20, metavar="N",
        help="对 Jobs 表前 N 名高分职位做 ATS 分析（0=不分析）",
    )
    parser.add_argument("--deepseek-key", default="", help="DeepSeek API Key")
    args = parser.parse_args()

    # 1) 加载语义模型
    print("正在加载语义模型 (all-MiniLM-L6-v2)...")
    model = get_semantic_model()

    # 2) 加载技能与权重
    weights = SCORE_WEIGHTS
    if args.config and args.position:
        pos_config = load_skill_config(args.config)
        if pos_config and args.position in pos_config:
            pos_data = pos_config[args.position]
            skills = pos_data.get("skills", DEFAULT_RESUME_SKILLS)
            if "skills" in pos_data:
                print(f"已加载职位 '{args.position}' 的技能配置: {skills}")
            if "weights" in pos_data:
                weights = pos_data["weights"]
                print(f"已加载职位 '{args.position}' 的权重配置: {weights}")
        else:
            skills = auto_update_resume_skills(args.resume_pdf)
    else:
        skills = auto_update_resume_skills(args.resume_pdf)
    if args.config and not args.position:
        print("WARNING: 指定了 --config 但未指定 --position，使用默认配置")

    # 3) 简历向量
    resume_text = get_resume_text(args.resume_pdf)
    resume_embedding = None
    if model is not None and resume_text and len(resume_text.strip()) >= 20:
        resume_embedding = model.encode([resume_text[:8000]], normalize_embeddings=True)
        print("简历向量已生成。")
    else:
        print("将仅使用关键词+标题打分（无语义分）。")

    # 4) 抓取
    print("正在抓取职位 (hours_old=24)...")
    df = run_scrape(
        search_term=args.search,
        location=args.location,
        results_wanted=args.results,
        site_name=[s.strip() for s in args.sites.split(",") if s.strip()] or None,
    )
    if df.empty:
        print("未抓到任何职位。")
        return

    # 5) 打分 + 分类
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

    # 6) 薪资
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
        "is_remote", "salary_range", "description",
    ]

    def _keep_columns(frame: pd.DataFrame) -> pd.DataFrame:
        cols = [c for c in OUTPUT_COLUMNS if c in frame.columns]
        return frame[cols].copy()

    # 7) 去重与分组
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

    # 8) 写 Excel
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        kept.to_excel(writer, sheet_name="Jobs", index=False)
        filtered.to_excel(writer, sheet_name="Filtered_Out", index=False)

    print(f"已保留 {len(kept)} 条职位 → 工作表 'Jobs'（按 Match_Score 降序）")
    print(f"已过滤 {len(filtered)} 条 → 工作表 'Filtered_Out'")
    print(f"已写入: {out_path.absolute()}")
    if n_dupes > 0:
        print(f"去重逻辑已将 {n_dupes} 个重复岗位移至 Filtered_Out 表格。")

    if args.csv:
        csv_path = out_path.with_suffix(".csv")
        kept.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"CSV 已写入: {csv_path.absolute()}")

    # 9) ATS 分析
    if args.analyze_top > 0 and kept.shape[0] > 0:
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
                print(f"ATS 分析完成，报告: {report_path}")
        except Exception as e:
            print(f"WARNING: ATS 分析失败: {e}")

    if not filtered.empty:
        print("\n--- 拒绝理由统计 ---")
        for reason, cnt in filtered["Rejection_Reason"].value_counts().items():
            print(f"  [{cnt}] {reason}")


if __name__ == "__main__":
    main()

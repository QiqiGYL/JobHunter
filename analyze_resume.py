#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简历关键词分析入口。
核心逻辑位于 src/resume.py 和 src/config.py。
"""

from __future__ import annotations

import os
import sys
import json
import io
from pathlib import Path
from datetime import datetime

if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

from src.resume import extract_keywords_from_resume, compare_with_resume_skills
from src.config import (
    ROOT_DIR,
    CONFIG_DIR,
    RESUME_PDF_PATH,
    DEFAULT_RESUME_SKILLS,
    load_tech_keywords,
)

OUTPUT_REPORT = str(ROOT_DIR / "data" / "resume_analysis_report.txt")
OUTPUT_JSON = str(ROOT_DIR / "data" / "resume_analysis_report.json")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="简历技术关键词分析工具")
    parser.add_argument("--resume", default=RESUME_PDF_PATH, help="简历 PDF 路径")
    parser.add_argument("--skills", default="", help="RESUME_SKILLS 列表（逗号分隔）")
    parser.add_argument("--output", default=OUTPUT_REPORT, help="分析报告输出路径")
    args = parser.parse_args()

    print("=" * 80)
    print("简历技术关键词分析工具")
    print("=" * 80)
    print()

    tech_keywords = load_tech_keywords()
    if not tech_keywords:
        print("ERROR: 无法加载关键词库")
        return
    total_keywords = sum(len(v) for v in tech_keywords.values())
    print(f"加载成功，共 {total_keywords} 个关键词，{len(tech_keywords)} 个类别")
    print()

    if not os.path.isfile(args.resume):
        print(f"ERROR: 简历文件不存在 {args.resume}")
        return

    result = extract_keywords_from_resume(args.resume, tech_keywords)
    if not result["全部关键词"]:
        print("ERROR: 无法从简历提取关键词，请检查 PDF 文件")
        return

    found_count = sum(len(v) for v in result["全部关键词"].values())
    print(f"提取成功，发现 {found_count} 个不同的技术关键词")
    print()

    resume_skills = [s.strip() for s in args.skills.split(",")] if args.skills else list(DEFAULT_RESUME_SKILLS)
    print(f"当前 RESUME_SKILLS ({len(resume_skills)} 个): {', '.join(resume_skills)}")
    print()

    comparison = compare_with_resume_skills(result, resume_skills)

    # 文本报告
    report_lines = [
        "=" * 80,
        "简历技术关键词分析报告",
        "=" * 80,
        f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"简历文件: {args.resume}",
        f"\n当前 RESUME_SKILLS ({len(resume_skills)} 项):",
        f"  {', '.join(resume_skills)}",
        "\n" + "=" * 80,
        "\n【简历中发现的技术关键词统计】\n",
    ]

    for category in sorted(result["全部关键词"].keys()):
        kw_dict = result["全部关键词"][category]
        if kw_dict:
            report_lines.append(f"{category} ({len(kw_dict)} 个):")
            for keyword in sorted(kw_dict, key=lambda x: kw_dict[x], reverse=True):
                report_lines.append(f"  {keyword:30} (出现 {kw_dict[keyword]:3} 次)")
            report_lines.append("")

    report_lines.extend([
        f"总计发现: {found_count} 个不同关键词",
        "\n" + "=" * 80,
        "\n【关键词对比分析】\n",
        f"在简历中且在RESUME_SKILLS中: {len(comparison['都有'])} 项",
    ])
    for kw in sorted(comparison["都有"]):
        report_lines.append(f"  {kw}")

    report_lines.append(f"\n在简历中但不在RESUME_SKILLS中: {len(comparison['在简历中但不在RESUME_SKILLS'])} 项")
    for kw in sorted(comparison["在简历中但不在RESUME_SKILLS"]):
        report_lines.append(f"  {kw}")

    report_lines.append(f"\n在RESUME_SKILLS中但不在简历中: {len(comparison['在RESUME_SKILLS中但不在简历'])} 项")
    for kw in sorted(comparison["在RESUME_SKILLS中但不在简历"]):
        report_lines.append(f"  {kw}")

    report_text = "\n".join(report_lines)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(report_text)
    print(f"文本报告已保存: {args.output}")

    # JSON 报告
    json_data = {
        "生成时间": datetime.now().isoformat(),
        "简历文件": args.resume,
        "当前RESUME_SKILLS": resume_skills,
        "关键词统计": result["全部关键词"],
        "对比结果": {
            "都有": comparison["都有"],
            "在简历中但不在RESUME_SKILLS": comparison["在简历中但不在RESUME_SKILLS"],
            "在RESUME_SKILLS中但不在简历": comparison["在RESUME_SKILLS中但不在简历"],
        },
        "统计": {
            "简历中发现的总关键词数": found_count,
            "当前RESUME_SKILLS数": len(resume_skills),
            "覆盖率": f"{len(comparison['都有']) * 100 // len(resume_skills)}%" if resume_skills else "N/A",
        },
    }
    Path(OUTPUT_JSON).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f"JSON 数据已保存: {OUTPUT_JSON}")


if __name__ == "__main__":
    main()

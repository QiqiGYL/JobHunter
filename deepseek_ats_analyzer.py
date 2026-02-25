#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DeepSeek ATS 深度分析入口（可单独运行）。
核心逻辑位于 src/ats.py。
"""

from __future__ import annotations

import os
import argparse
from pathlib import Path

from src.ats import run_ats_analysis
from src.config import RESUME_PDF_PATH

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="DeepSeek ATS 深度分析")
    parser.add_argument("--excel", default="data/job_hunt_results.xlsx", help="Jobs Excel 路径")
    parser.add_argument("--resume", default=RESUME_PDF_PATH, help="简历 PDF 路径")
    parser.add_argument("--top", type=int, default=20, help="分析前 N 个职位")
    parser.add_argument("--deepseek-key", default="", help="DeepSeek API Key")
    parser.add_argument("--out", default="data/ats_analysis_report.md", help="报告输出路径")
    args = parser.parse_args()

    run_ats_analysis(
        excel_path=args.excel,
        resume_pdf_path=args.resume,
        top_n=args.top,
        api_key=args.deepseek_key or None,
        output_path=args.out,
    )

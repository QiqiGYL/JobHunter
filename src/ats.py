# -*- coding: utf-8 -*-
"""
DeepSeek ATS 深度分析：调用 API 模拟 ATS，生成简历优化建议。
"""

from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime

import pandas as pd

from src.resume import extract_text_from_pdf, clean_resume_text

ATS_SYSTEM_PROMPT = """你是一个专业的 ATS（Applicant Tracking System）系统和招聘专家。
你的任务是分析候选人的简历与职位描述的匹配度，并提供针对性的简历优化建议。

请从以下角度分析：
1. **关键词匹配**：职位要求的技能中，简历覆盖了哪些？缺少哪些？
2. **经验匹配**：候选人的项目经验是否与职位需求相符？
3. **简历优化建议**：针对这个职位，应该如何调整简历的措辞和重点？
4. **Cover Letter 要点**：应聘这个职位时，Cover Letter 应该强调哪些亮点？

请用中文回答，简洁明了，直接给出可操作的建议。"""

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-chat"


def _get_resume_text(resume_pdf_path: str) -> str:
    if not resume_pdf_path or not os.path.isfile(resume_pdf_path):
        return ""
    raw = extract_text_from_pdf(resume_pdf_path)
    return clean_resume_text(raw)


def _call_deepseek(api_key: str, system_prompt: str, user_message: str) -> str:
    try:
        import requests
    except ImportError:
        return "[错误: 未安装 requests，请执行 pip install requests]"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
        "temperature": 0.3,
        "max_tokens": 1500,
    }

    try:
        resp = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        choices = data.get("choices", [])
        if choices and isinstance(choices[0].get("message", {}).get("content"), str):
            return choices[0]["message"]["content"].strip()
        return "[API 返回格式异常]"
    except Exception as e:
        return f"[请求失败: {e}]"


def run_ats_analysis(
    excel_path: str,
    resume_pdf_path: str,
    top_n: int = 20,
    api_key: str | None = None,
    output_path: str | None = None,
) -> str:
    """读取 Excel Jobs 表前 top_n 条高分职位，调用 DeepSeek 做 ATS 分析。"""
    key = api_key or os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        print("WARNING: 未设置 DEEPSEEK_API_KEY，跳过 ATS 深度分析")
        return ""

    if output_path is None:
        output_path = str(Path(excel_path).parent / "ats_analysis_report.md")

    if not os.path.isfile(excel_path):
        print(f"WARNING: Excel 不存在 {excel_path}，跳过 ATS 分析")
        return ""

    try:
        df = pd.read_excel(excel_path, sheet_name="Jobs")
    except Exception as e:
        print(f"WARNING: 读取 Excel 失败: {e}")
        return ""

    if df.empty:
        print("WARNING: Jobs 表为空，跳过 ATS 分析")
        return ""

    if "Match_Score" in df.columns:
        df = df.sort_values("Match_Score", ascending=False).head(top_n).reset_index(drop=True)
    else:
        df = df.head(top_n)

    resume_text = _get_resume_text(resume_pdf_path)
    if not resume_text or len(resume_text.strip()) < 50:
        print("WARNING: 简历内容过短或无法读取，ATS 分析可能不准确")

    lines = [
        "# ATS 深度分析报告", "",
        f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "", "---", "",
    ]

    for i, row in df.iterrows():
        title = str(row.get("title", ""))
        company = str(row.get("company", ""))
        job_url = str(row.get("job_url", ""))
        score = row.get("Match_Score", "")
        description = str(row.get("description", ""))[:6000]

        user_message = (
            f"请分析以下职位与候选人简历的匹配度，并给出简历优化建议。\n\n"
            f"【职位标题】{title}\n【公司】{company}\n【职位描述】\n{description}\n\n"
            f"【候选人简历】\n{resume_text[:5000]}\n"
        )

        lines.append(f"## 职位 {i + 1}: {title} @ {company}")
        lines.append("")
        lines.append(f"**匹配分数**: {score}/100")
        if job_url:
            lines.append(f"**职位链接**: {job_url}")
        lines.append("")
        lines.append("### ATS 分析与建议")
        lines.append("")
        lines.append(_call_deepseek(key, ATS_SYSTEM_PROMPT, user_message))
        lines.extend(["", "---", ""])

    report_text = "\n".join(lines)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"ATS 深度分析报告已生成: {os.path.abspath(output_path)}")
    return os.path.abspath(output_path)

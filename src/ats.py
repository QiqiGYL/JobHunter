# -*- coding: utf-8 -*-
"""
DeepSeek ATS 深度分析：调用 API 模拟 ATS，生成简历优化建议。
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from datetime import datetime

import pandas as pd

from src.resume import extract_text_from_pdf, clean_resume_text

ATS_SYSTEM_PROMPT = """Role: 你是一位在大厂（如 Google, Stripe, Meta）工作多年的资深技术校招 HR 兼 ATS 算法专家。

Task: 请对比提供的 [Resume] 和 [Job Description]，进行一次深度 ATS 兼容性审计。

Output Requirements (请按以下结构输出):

1. **ATS Match Score**: 给出一个 0-100 的分数（考虑硬性技能、经验年限、教育背景）。
2. **Gap Analysis (缺啥补啥)**: 
   - 找出 JD 中强调了但简历中完全没有出现的 3-5 个关键技术词或软技能。
3. **Resume Surgery (简历手术)**:
   - 针对本项目，请提供 2-3 条“直接可复制”的简历描述优化。
   - 格式：[原描述] -> [优化后描述（加入量化成果和 JD 关键词）]。
4. **ATS Red Flags**: 检查简历是否有排版问题、无法解析的字符或过于复杂的格式。
5. **Interview Prediction**: 简短评估：这个申请人拿到 OA/面试的概率是多少？核心阻碍是什么？

请用中文回答。回答完成后，在最后单独用一行输出一个 JSON 块（便于程序解析），格式如下，不要省略字段：
```json
{"ats_match_score": 数字0到100, "missing_keywords": ["关键词1", "关键词2"], "resume_edits": [{"original": "原描述", "optimized": "优化后描述"}], "ats_red_flags": "红色风险说明", "interview_prediction": "面试概率与阻碍说明"}
```"""

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-chat"


def _parse_analysis_json(raw: str) -> dict | None:
    """从 DeepSeek 回复中提取 ```json ... ``` 块并解析。"""
    if not raw or not isinstance(raw, str):
        return None
    match = re.search(r"```json\s*([\s\S]*?)\s*```", raw)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass
    # 尝试整段解析
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        return None


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
        "max_tokens": 2500,
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


def _build_user_message(resume_text: str, job_title: str, job_company: str, job_description: str) -> str:
    jd_text = f"【职位标题】{job_title}\n【公司】{job_company}\n【职位描述】\n{job_description}"
    return f"---\n[Resume]:\n{resume_text}\n---\n[Job Description]:\n{jd_text}"


def analyze_one_job(
    resume_pdf_path: str,
    job_title: str,
    job_company: str,
    job_description: str,
    api_key: str | None = None,
) -> dict:
    """对单个职位做 ATS 分析，返回结构化结果或带 raw 的降级结果。"""
    key = (api_key or os.environ.get("DEEPSEEK_API_KEY", "")).strip()
    if not key:
        return {"ok": False, "error": "DEEPSEEK_API_KEY not set", "analysis": None, "raw": None}

    resume_text = _get_resume_text(resume_pdf_path)
    if not resume_text or len(resume_text.strip()) < 50:
        return {"ok": False, "error": "resume empty or too short", "analysis": None, "raw": None}

    jd_snippet = (job_description or "")[:6000]
    user_message = _build_user_message(resume_text[:5000], job_title or "", job_company or "", jd_snippet)
    raw = _call_deepseek(key, ATS_SYSTEM_PROMPT, user_message)

    parsed = _parse_analysis_json(raw)
    if parsed and isinstance(parsed, dict):
        analysis = {
            "ats_match_score": parsed.get("ats_match_score"),
            "missing_keywords": parsed.get("missing_keywords") or [],
            "resume_edits": parsed.get("resume_edits") or [],
            "ats_red_flags": parsed.get("ats_red_flags") or "",
            "interview_prediction": parsed.get("interview_prediction") or "",
        }
        return {"ok": True, "analysis": analysis, "raw": raw}
    return {"ok": True, "analysis": None, "raw": raw}


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

        user_message = _build_user_message(resume_text[:5000], title, company, description)
        reply = _call_deepseek(key, ATS_SYSTEM_PROMPT, user_message)
        parsed = _parse_analysis_json(reply)

        lines.append(f"## 职位 {i + 1}: {title} @ {company}")
        lines.append("")
        lines.append(f"**匹配分数**: {score}/100")
        if job_url:
            lines.append(f"**职位链接**: {job_url}")
        lines.append("")
        lines.append("### ATS 分析与建议")
        lines.append("")
        lines.append(reply)
        if parsed and isinstance(parsed, dict):
            lines.append("")
            lines.append("### 结构化摘要")
            lines.append("")
            lines.append(f"- **ATS 分数**: {parsed.get('ats_match_score', '—')}")
            lines.append(f"- **缺失关键词**: {', '.join(parsed.get('missing_keywords') or [])}")
            lines.append(f"- **面试预测**: {parsed.get('interview_prediction', '—')}")
        lines.extend(["", "---", ""])

    report_text = "\n".join(lines)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"ATS 深度分析报告已生成: {os.path.abspath(output_path)}")
    return os.path.abspath(output_path)

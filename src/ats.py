# -*- coding: utf-8 -*-
"""
DeepSeek ATS deep analysis: calls the API to simulate ATS scoring and generate resume improvement suggestions.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from datetime import datetime

import pandas as pd

from src.resume import extract_text_from_pdf, clean_resume_text

ATS_SYSTEM_PROMPT = """Role: You are a senior technical recruiter and ATS algorithm expert with years of experience at top tech companies (Google, Stripe, Meta).

Task: Compare the provided [Resume] and [Job Description], and perform a deep ATS compatibility audit.

Output Requirements (follow this structure exactly):

1. **ATS Match Score**: Give a score from 0–100 (considering hard skills, years of experience, and educational background).
2. **Gap Analysis**: Identify 3–5 key technical terms or soft skills emphasized in the JD but completely absent from the resume.
3. **Resume Surgery**: Provide 2–3 "copy-paste ready" resume bullet improvements tailored to this job.
   Format: [Original] -> [Optimized (with quantified results and JD keywords)]
4. **ATS Red Flags**: Check for formatting issues, unparseable characters, or overly complex layouts.
5. **Interview Prediction**: Brief assessment — what is the probability of getting an OA/interview? What are the main blockers?

After your analysis, output a single JSON block on its own line for programmatic parsing. Do not omit any fields:
```json
{"ats_match_score": 0-100, "missing_keywords": ["keyword1", "keyword2"], "resume_edits": [{"original": "original text", "optimized": "optimized text"}], "ats_red_flags": "red flag description", "interview_prediction": "prediction and blockers"}
```"""

DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEFAULT_MODEL = "deepseek-chat"


def _parse_analysis_json(raw: str) -> dict | None:
    """Extract and parse the ```json ... ``` block from the DeepSeek response."""
    if not raw or not isinstance(raw, str):
        return None
    match = re.search(r"```json\s*([\s\S]*?)\s*```", raw)
    if match:
        try:
            return json.loads(match.group(1).strip())
        except json.JSONDecodeError:
            pass
    # Attempt to parse the entire response as JSON
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
        return "[Error: 'requests' package not installed. Run: pip install requests]"

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
        return "[Unexpected API response format]"
    except Exception as e:
        return f"[Request failed: {e}]"


def _build_user_message(resume_text: str, job_title: str, job_company: str, job_description: str) -> str:
    jd_text = f"[Job Title] {job_title}\n[Company] {job_company}\n[Job Description]\n{job_description}"
    return f"---\n[Resume]:\n{resume_text}\n---\n[Job Description]:\n{jd_text}"


def analyze_one_job(
    resume_pdf_path: str,
    job_title: str,
    job_company: str,
    job_description: str,
    api_key: str | None = None,
) -> dict:
    """Run ATS analysis for a single job. Returns structured result or raw fallback."""
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
    """Read top_n highest-scoring jobs from the Excel and run DeepSeek ATS analysis on each."""
    key = api_key or os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if not key:
        print("WARNING: DEEPSEEK_API_KEY not set, skipping ATS analysis")
        return ""

    if output_path is None:
        output_path = str(Path(excel_path).parent / "ats_analysis_report.md")

    if not os.path.isfile(excel_path):
        print(f"WARNING: Excel file not found: {excel_path}, skipping ATS analysis")
        return ""

    try:
        df = pd.read_excel(excel_path, sheet_name="Jobs")
    except Exception:
        try:
            df = pd.read_excel(excel_path, sheet_name="All")
        except Exception as e:
            print(f"WARNING: Failed to read Excel (Jobs or All): {e}")
            return ""

    if df.empty:
        print("WARNING: Jobs/All sheet is empty, skipping ATS analysis")
        return ""

    if "Match_Score" in df.columns:
        df = df.sort_values("Match_Score", ascending=False).head(top_n).reset_index(drop=True)
    else:
        df = df.head(top_n)

    resume_text = _get_resume_text(resume_pdf_path)
    if not resume_text or len(resume_text.strip()) < 50:
        print("WARNING: Resume content is too short or unreadable; ATS analysis may be inaccurate")

    lines = [
        "# ATS Deep Analysis Report", "",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
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

        lines.append(f"## Job {i + 1}: {title} @ {company}")
        lines.append("")
        lines.append(f"**Match Score**: {score}/100")
        if job_url:
            lines.append(f"**Job URL**: {job_url}")
        lines.append("")
        lines.append("### ATS Analysis & Suggestions")
        lines.append("")
        lines.append(reply)
        if parsed and isinstance(parsed, dict):
            lines.append("")
            lines.append("### Structured Summary")
            lines.append("")
            lines.append(f"- **ATS Score**: {parsed.get('ats_match_score', '—')}")
            lines.append(f"- **Missing Keywords**: {', '.join(parsed.get('missing_keywords') or [])}")
            lines.append(f"- **Interview Prediction**: {parsed.get('interview_prediction', '—')}")
        lines.extend(["", "---", ""])

    report_text = "\n".join(lines)
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(report_text)

    print(f"ATS analysis report saved: {os.path.abspath(output_path)}")
    return os.path.abspath(output_path)

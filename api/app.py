#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JobHunter API：提供职位列表（读 xlsx）与简历上传。
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

# 项目根目录（api 的上一级），供 import src 使用
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import pandas as pd
from flask import Flask, jsonify, request, send_file
from src.ats import analyze_one_job

DEFAULT_XLSX = ROOT / "data" / "job_hunt_results.xlsx"
UPLOAD_DIR = ROOT / "data" / "uploads"
RESUME_PDF_NAME = "current_resume.pdf"
ATS_CACHE_FILE = ROOT / "data" / "ats_analysis_cache.json"

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20MB
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _job_cache_key(job: dict) -> str:
    """稳定缓存键：优先 job_url，否则用 title+company+description 的哈希。"""
    url = (job.get("job_url") or "").strip()
    if url:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]
    raw = "|".join([
        (job.get("title") or "").strip(),
        (job.get("company") or "").strip(),
        ((job.get("description") or "")[:1000]).strip(),
    ])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _load_ats_cache() -> dict:
    """读取 ATS 分析缓存。"""
    if not ATS_CACHE_FILE.is_file():
        return {}
    try:
        with open(ATS_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_ats_cache(cache: dict) -> None:
    """写入 ATS 分析缓存。"""
    ATS_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ATS_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def _read_jobs_xlsx(path: Path) -> tuple[list, list]:
    """读取 xlsx，返回 (jobs, filtered_out)，均按 Match_Score 降序。"""
    if not path.is_file():
        return [], []
    try:
        jobs_df = pd.read_excel(path, sheet_name="Jobs")
        filtered_df = pd.read_excel(path, sheet_name="Filtered_Out")
    except Exception:
        return [], []
    # 转为可 JSON 序列化的列表，NaN/NaT -> None（JSON 不接受 NaN）
    def to_records(df: pd.DataFrame) -> list:
        if df.empty:
            return []
        if "Match_Score" in df.columns:
            df = df.sort_values("Match_Score", ascending=False, na_position="last")
        records = df.to_dict(orient="records")
        for r in records:
            for k, v in list(r.items()):
                if pd.isna(v):
                    r[k] = None
        return records
    return to_records(jobs_df), to_records(filtered_df)


@app.route("/api/jobs/analyze", methods=["POST"])
def jobs_analyze():
    """对单个职位做 ATS 分析；结果按 job 持久化到 data/ats_analysis_cache.json。"""
    if not os.environ.get("DEEPSEEK_API_KEY", "").strip():
        return jsonify({"ok": False, "error": "no_api_key"}), 403
    resume_path = UPLOAD_DIR / RESUME_PDF_NAME
    if not resume_path.is_file():
        return jsonify({"ok": False, "error": "no resume uploaded"}), 400
    data = request.get_json(silent=True) or {}
    job = data.get("job") or {}
    title = job.get("title") or ""
    company = job.get("company") or ""
    description = job.get("description") or ""

    cache_key = _job_cache_key(job)
    cache = _load_ats_cache()
    if cache_key in cache:
        entry = cache[cache_key]
        return jsonify({
            "ok": True,
            "analysis": entry.get("analysis"),
            "raw": entry.get("raw"),
            "cached": True,
        })

    try:
        result = analyze_one_job(
            resume_pdf_path=str(resume_path),
            job_title=title,
            job_company=company,
            job_description=description,
        )
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    if not result.get("ok"):
        return jsonify({"ok": False, "error": result.get("error", "analysis failed")}), 400

    cache[cache_key] = {
        "analysis": result.get("analysis"),
        "raw": result.get("raw"),
    }
    _save_ats_cache(cache)
    return jsonify({
        "ok": True,
        "analysis": result.get("analysis"),
        "raw": result.get("raw"),
    })


@app.route("/api/jobs", methods=["GET"])
def get_jobs():
    """返回 { jobs: [...], filteredOut: [...] }，按 Match_Score 降序。"""
    xlsx = request.args.get("xlsx", str(DEFAULT_XLSX))
    path = Path(xlsx)
    if not path.is_absolute():
        path = ROOT / path
    jobs, filtered_out = _read_jobs_xlsx(path)
    return jsonify({"jobs": jobs, "filteredOut": filtered_out})


@app.route("/api/resume", methods=["POST"])
def upload_resume():
    """上传 PDF 简历，保存为 data/uploads/current_resume.pdf。"""
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "no file"}), 400
    f = request.files["file"]
    if f.filename == "":
        return jsonify({"ok": False, "error": "empty filename"}), 400
    if not f.filename.lower().endswith(".pdf"):
        return jsonify({"ok": False, "error": "only PDF allowed"}), 400
    dest = UPLOAD_DIR / RESUME_PDF_NAME
    try:
        f.save(str(dest))
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
    return jsonify({"ok": True, "path": str(dest)})


@app.route("/api/resume/status", methods=["GET"])
def resume_status():
    """返回当前是否已有上传的简历。"""
    p = UPLOAD_DIR / RESUME_PDF_NAME
    resp = jsonify({"uploaded": p.is_file()})
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return resp


@app.route("/api/resume/file", methods=["GET"])
def resume_file():
    """返回当前简历 PDF 供预览（新窗口打开）。"""
    p = UPLOAD_DIR / RESUME_PDF_NAME
    if not p.is_file():
        r404 = app.make_response(("", 404))
        r404.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        return r404
    r = send_file(
        str(p),
        mimetype="application/pdf",
        as_attachment=False,
        download_name=RESUME_PDF_NAME,
    )
    r.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return r


@app.after_request
def _cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin") or "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


@app.route("/api/resume", methods=["OPTIONS"])
@app.route("/api/jobs", methods=["OPTIONS"])
@app.route("/api/jobs/analyze", methods=["OPTIONS"])
def _cors_preflight():
    return "", 204


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

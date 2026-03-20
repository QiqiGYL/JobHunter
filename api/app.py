#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JobHunter API: serves job listings (from xlsx) and handles resume upload / ATS analysis.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

# Add project root to sys.path so `src` package can be imported
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import pandas as pd
from flask import Flask, jsonify, request, send_file

from src.ats import analyze_one_job
from src.config import DEFAULT_RESUME_SKILLS
from src.filters import FilterOptions, classify_job
from src.resume import get_resume_text
from src import db as db_module

DEFAULT_XLSX = ROOT / "data" / "job_hunt_results.xlsx"
UPLOAD_DIR = ROOT / "data" / "uploads"
RESUME_PDF_NAME = "current_resume.pdf"
ATS_CACHE_FILE = ROOT / "data" / "ats_analysis_cache.json"

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024  # 20 MB
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def _job_cache_key(job: dict) -> str:
    """Stable cache key: prefer job_url hash; fall back to title+company+description hash."""
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
    """Load ATS analysis cache from disk."""
    if not ATS_CACHE_FILE.is_file():
        return {}
    try:
        with open(ATS_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_ats_cache(cache: dict) -> None:
    """Persist ATS analysis cache to disk."""
    ATS_CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ATS_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache, f, ensure_ascii=False, indent=2)


def _to_records(df: pd.DataFrame) -> list:
    """Convert DataFrame to list of dicts, NaN -> None, sorted by Match_Score if present."""
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


def _read_jobs_xlsx(path: Path) -> tuple[list, list]:
    """Read xlsx and return (jobs, filtered_out), each sorted by Match_Score descending."""
    if not path.is_file():
        return [], []
    try:
        jobs_df = pd.read_excel(path, sheet_name="Jobs")
        filtered_df = pd.read_excel(path, sheet_name="Filtered_Out")
    except Exception:
        return [], []
    return _to_records(jobs_df), _to_records(filtered_df)


def _read_all_jobs_merged(path: Path) -> list:
    """Read job list for re-filtering: prefer sheet 'All' (single source of truth); fallback to Jobs + Filtered_Out merge (legacy xlsx)."""
    if not path.is_file():
        return []
    try:
        all_df = pd.read_excel(path, sheet_name="All")
        return _to_records(all_df)
    except Exception:
        pass
    try:
        jobs_df = pd.read_excel(path, sheet_name="Jobs")
        filtered_df = pd.read_excel(path, sheet_name="Filtered_Out")
        combined = pd.concat([jobs_df, filtered_df], ignore_index=True)
        return _to_records(combined)
    except Exception:
        return []


def _parse_filter_options(request) -> FilterOptions:
    """Build FilterOptions from GET query string; use defaults when missing."""
    def _int(key: str, default: int) -> int:
        val = request.args.get(key)
        if val is None or val == "":
            return default
        try:
            return int(val)
        except ValueError:
            return default

    def _int_optional(key: str) -> Optional[int]:
        val = request.args.get(key)
        if val is None or (isinstance(val, str) and val.strip() == ""):
            return None
        try:
            return int(val)
        except ValueError:
            return None

    def _bool(key: str, default: bool) -> bool:
        val = request.args.get(key)
        if val is None or val == "":
            return default
        return str(val).strip().lower() in ("1", "true", "yes", "on")

    def _job_roles_list(key: str = "job_roles") -> list:
        val = request.args.get(key)
        if val is None or (isinstance(val, str) and val.strip() == ""):
            return []
        return [s.strip() for s in str(val).split(",") if s.strip()]

    def _location_country_optional(key: str = "location_country") -> Optional[str]:
        val = request.args.get(key)
        if val is None or (isinstance(val, str) and val.strip() == ""):
            return None
        return str(val).strip()

    y_min = _int("years_min", 0)
    y_max = _int("years_max", 2)
    if y_min > y_max:
        y_min, y_max = y_max, y_min
    return FilterOptions(
        years_min=y_min,
        years_max=y_max,
        graduation_year=_int_optional("graduation_year"),
        exclude_intern_coop=_bool("exclude_intern_coop", True),
        job_roles=_job_roles_list(),
        location_country=_location_country_optional(),
    )


@app.route("/api/jobs/analyze", methods=["POST"])
def jobs_analyze():
    """Run ATS analysis for a single job; cache result in data/ats_analysis_cache.json."""
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


def _location_matches_country(location: str, location_country: Optional[str]) -> bool:
    """True if job location matches filter country (Canada / United States)."""
    if not location_country or not location_country.strip():
        return True
    loc = (location or "").strip().lower()
    country = location_country.strip().lower()
    if country == "canada":
        return "canada" in loc
    if country in ("united states", "united states of america", "usa", "us"):
        return "united states" in loc or "usa" in loc or " u.s." in loc or loc.endswith(" us") or " (us)" in loc
    return country in loc


def _load_scrape_stats():
    """Read last scrape stats from data/last_scrape_stats.json if present."""
    path = ROOT / "data" / "last_scrape_stats.json"
    if not path.is_file():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


@app.route("/api/jobs", methods=["GET"])
def get_jobs():
    """Return { jobs: [...], filteredOut: [...], appliedCount: N [, scrapeStats ] } from DB.
    tab=applied: return only applied jobs. Otherwise use status=new, filter by location_country and filter_options, then classify into jobs/filteredOut.
    """
    scrape_stats = _load_scrape_stats()
    tab = request.args.get("tab", "").strip().lower()
    if tab == "applied":
        applied = db_module.get_jobs_by_status(status="applied")
        return jsonify({"jobs": applied, "filteredOut": [], "appliedCount": len(applied), "scrapeStats": scrape_stats})

    filter_options = _parse_filter_options(request)
    all_records = db_module.get_all_new_jobs()
    xlsx_path = ROOT / "data" / "job_hunt_results.xlsx"
    if not all_records and xlsx_path.is_file():
        try:
            db_module.import_from_xlsx(xlsx_path)
            all_records = db_module.get_all_new_jobs()
        except Exception:
            all_records = []

    if filter_options.location_country:
        all_records = [r for r in all_records if _location_matches_country(r.get("location") or "", filter_options.location_country)]

    if not all_records:
        applied_count = db_module.get_applied_count()
        return jsonify({"jobs": [], "filteredOut": [], "appliedCount": applied_count, "scrapeStats": scrape_stats})

    skills = DEFAULT_RESUME_SKILLS
    jobs = []
    filtered_out = []
    for rec in all_records:
        level, reason = classify_job(rec, skills, filter_options)
        rec["Target Level"] = level
        rec["Rejection_Reason"] = reason
        if level == "Too Senior":
            filtered_out.append(rec)
        else:
            jobs.append(rec)

    jobs.sort(key=lambda r: (r.get("Match_Score") is None, -(r.get("Match_Score") or 0)))
    filtered_out.sort(key=lambda r: (r.get("Match_Score") is None, -(r.get("Match_Score") or 0)))
    applied_count = db_module.get_applied_count()
    return jsonify({"jobs": jobs, "filteredOut": filtered_out, "appliedCount": applied_count, "scrapeStats": scrape_stats})


@app.route("/api/jobs/<job_id>/status", methods=["PATCH", "PUT"])
def update_job_status_route(job_id: str):
    """Set job status to 'applied' or 'ignored'. Body: { \"status\": \"applied\" | \"ignored\" }."""
    data = request.get_json(silent=True) or {}
    status = (data.get("status") or "").strip().lower()
    if status not in ("applied", "ignored"):
        return jsonify({"ok": False, "error": "status must be 'applied' or 'ignored'"}), 400
    updated = db_module.update_job_status(job_id, status)
    if updated is None:
        return jsonify({"ok": False, "error": "job not found"}), 404
    return jsonify({"ok": True, "job": updated})


@app.route("/api/jobs/refresh", methods=["POST"])
def jobs_refresh():
    """Run hunt.py to scrape jobs and upsert into DB. May take 1–5 minutes. Returns { ok, message, jobsCount }."""
    try:
        result = subprocess.run(
            [sys.executable, str(ROOT / "hunt.py")],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            timeout=600,
            env={**os.environ},
        )
        if result.returncode != 0:
            stderr = (result.stderr or "").strip()
            stdout = (result.stdout or "").strip()
            # Show end of both: traceback usually in stderr, but some libs print to stdout
            parts = []
            if stderr:
                tail = stderr[-2200:] if len(stderr) > 2200 else stderr
                parts.append("--- stderr ---\n" + tail)
            if stdout:
                tail = stdout[-1500:] if len(stdout) > 1500 else stdout
                parts.append("--- stdout ---\n" + tail)
            detail = "\n".join(parts) if parts else None
            return jsonify({
                "ok": False,
                "error": "hunt.py failed",
                "detail": detail,
            }), 500
        jobs_count = len(db_module.get_all_jobs()) if getattr(db_module, "get_all_jobs", None) else 0
        return jsonify({
            "ok": True,
            "message": "Jobs refreshed",
            "jobsCount": jobs_count,
        })
    except subprocess.TimeoutExpired:
        return jsonify({"ok": False, "error": "Refresh timed out (max 10 min)"}), 504
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/resume", methods=["POST"])
def upload_resume():
    """Upload a PDF resume and save it as data/uploads/current_resume.pdf."""
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
    """Return whether a resume has been uploaded."""
    p = UPLOAD_DIR / RESUME_PDF_NAME
    resp = jsonify({"uploaded": p.is_file()})
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    return resp


@app.route("/api/resume/file", methods=["GET"])
def resume_file():
    """Stream the current resume PDF for in-browser preview."""
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


def _suggest_filter_from_resume(resume_path: Path) -> dict:
    """Parse uploaded resume text and suggest filter options (e.g. graduation year). graduation_year is None when not detected (optional filter)."""
    out = {"graduation_year": None, "years_min": 0, "years_max": 2}
    if not resume_path.is_file():
        return out
    text = get_resume_text(str(resume_path)) or ""
    if len(text.strip()) < 20:
        return out
    # Look for graduation year: "Expected graduation 2025", "Class of 2025", "May 2025", "2025 Graduate", etc.
    year_match = re.search(
        r"\b(?:graduation|graduate|grad|expected|class\s+of|degree)\s*(?:\))?\s*[:\s]*\s*(\d{4})\b",
        text,
        re.IGNORECASE,
    )
    if year_match:
        y = int(year_match.group(1))
        if 2020 <= y <= 2030:
            out["graduation_year"] = y
    return out


@app.route("/api/resume/filter-suggestions", methods=["GET"])
def resume_filter_suggestions():
    """Suggest filter bar values from the uploaded resume (e.g. graduation year). Call after upload to pre-fill filters."""
    p = UPLOAD_DIR / RESUME_PDF_NAME
    suggestions = _suggest_filter_from_resume(p)
    return jsonify(suggestions)


@app.after_request
def _cors(resp):
    resp.headers["Access-Control-Allow-Origin"] = request.headers.get("Origin") or "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, POST, PATCH, PUT, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return resp


@app.route("/api/resume", methods=["OPTIONS"])
@app.route("/api/resume/filter-suggestions", methods=["OPTIONS"])
@app.route("/api/jobs", methods=["OPTIONS"])
@app.route("/api/jobs/analyze", methods=["OPTIONS"])
@app.route("/api/jobs/refresh", methods=["OPTIONS"])
@app.route("/api/jobs/<job_id>/status", methods=["OPTIONS"])
def _cors_preflight(job_id=None):
    return "", 204


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

# JobHunter — Development Progress

A chronological log of features and changes, so I can look back and see what was done on any given day.

---

## I. Module Status

| Module | Status | Notes |
|--------|--------|-------|
| Job scraping & scoring (hunt.py) | ✅ Done | jobspy scraping, 4-component scoring, filtering, xlsx output |
| Position config (job_positions.yaml) | ✅ Done | Multi-position skills & weights, --config / --position |
| Resume parsing & keywords (src/resume) | ✅ Done | PDF extraction, keyword analysis, tech_keywords.yaml |
| ATS deep analysis (src/ats) | ✅ Done | DeepSeek single-job analysis, structured output, CLI batch report |
| Backend API (api/app.py) | ✅ Done | /api/jobs, /api/resume, /api/jobs/analyze, resume preview |
| Frontend (ui/) | ✅ Done | Job list, pagination, resume upload & preview, per-job ATS drawer |
| ATS result caching | ✅ Done | data/ats_analysis_cache.json; cache-first before calling API |

---

## II. Changelog (newest first)

- **2026-03-07**
  - Cleaned up repo: removed `CHANGELOG.md`, `IMPROVEMENTS.md`, `.github/copilot-instructions.md`; updated `.gitignore` to exclude `.cursor/` and generated `data/` files.
  - Translated all code comments and docstrings to English across `src/`, `api/app.py`, and `hunt.py`.
  - UI: bilingual EN/CN toggle button (fixed top-right corner, segmented `[EN|CN]` style); graceful "no API key" message when DeepSeek key is missing instead of a raw error.
  - Added `README_CN.md` (Chinese version) and rewrote `README.md` in English.

- **2026-03-07** (earlier)
  - Git: committed all Mar 5 changes; updated progress log.
  - Progress log updated with full historical summary.

- **2026-03-05**
  - Scraping: LinkedIn now fetches full descriptions (`linkedin_fetch_description=True`); per-site result counts via `RESULTS_PER_SITE` (indeed=100, linkedin=30); default `--results` lowered to 30.
  - Scoring: `tech_keywords.yaml` expanded from 77 to 160+ keywords (frontend, backend, cloud/DevOps, AI/ML, tools); fixed React.js / CI/CD matching in `resume.py` for keywords containing `.` or `/`.
  - Filters: `Associate` added to `ENTRY_LEVEL` (fixes TD Associate SWE being filtered out); `Mechanical Engineer` and `Electrical Engineer` added to `NON_SOFTWARE_TITLE`; expanded non-software exclusions (environmental, medical, accounting, trades, etc.).
  - Config: resume auto-selects uploaded PDF (`data/uploads/current_resume.pdf`) over fallback `Grace_cs3.pdf`.
  - UI: header redesigned with green gradient + resume upload bar; removed emojis from title/buttons; job card score circle fixed to right side with consistent vertical alignment; source badge (indeed/linkedin) and Remote badge added to each card.

- **2026-03-04** (cont.)
  - Frontend: `JobCard` gains source badge (indeed/linkedin green tag) and Remote blue badge; `hunt.py` `OUTPUT_COLUMNS` now includes `site` field so next xlsx will carry source info.

- **2026-03-04**
  - Scraping: per-site progress messages; `country_indeed='Canada'` passed in `run_scrape`.
  - Filters: Intern/Co-op checked against title only (avoids false-positive on "Preferred: co-op experience"); exclude non-software roles (Construction Estimator, CAD Technician, etc.); exclude Level 2+ / III/IV; exclude XXX Lead (Test Lead, QA Lead, etc.); entry-level title protects against senior keywords in description.
  - hunt: `--analyze-top` defaults to 0 (ATS batch analysis off by default).

- **2026-03-01**
  - Scraping robustness: `run_scrape` now iterates sites individually; a `RemoteDisconnected` / `ConnectionError` on one site logs a WARNING and skips that site rather than crashing the whole run.

- **2026-02-26**
  - ATS result persistence: cache written to `data/ats_analysis_cache.json`; cache key prefers `job_url` hash, falls back to title+company+description hash; analyze endpoint checks cache first and returns `cached: true` on hit.
  - Added `progress.md` to track development history.

- **2026-02-09**
  - Scoring system upgraded: 3-component → 4-component. Weight comparison:

    | Component | Old (3-component) | New (4-component) | Change |
    |-----------|-------------------|-------------------|--------|
    | Semantic similarity | 60% | 40% | ↓ 20% |
    | Keyword matching | 30% | 35% | ↑ 5% |
    | Title bonus | 10% | 15% | ↑ 5% |
    | Location bonus | — | 10% | ✨ New |

  - Keyword matching: threshold lowered 80% → 75%, points raised 20 → 25.
  - Title keywords expanded: added "Entry-Level", "Early-Career", "Graduate".
  - Location bonus added: Toronto/Mississauga +10, Ontario +5.
  - Added `job_positions.yaml` config with `--config` / `--position` CLI flags for backend/frontend/data presets.
  - New helpers: `_load_config_file()`, `_location_bonus()`, `load_skill_config()`.
  - Version tag: v2 (4-component scoring + config support).

- **Project Initialization**
  - Job scraping from Indeed / LinkedIn via `jobspy`, output to `job_hunt_results.xlsx`.
  - Hybrid scoring: `sentence-transformers` (all-MiniLM-L6-v2) for semantic similarity, `rapidfuzz` for keyword fuzzy matching.
  - Resume parsing: `pdfplumber` extracts text; keyword extraction against `tech_keywords.yaml`.
  - DeepSeek ATS analysis: single-job structured output and CLI batch report.
  - Flask API (`api/app.py`): `/api/jobs`, `/api/resume`, `/api/jobs/analyze`, resume PDF preview.
  - React + Vite + Ant Design frontend: job list, pagination, resume upload & preview, per-job ATS Analysis drawer.

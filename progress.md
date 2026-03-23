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
- **2026-03-23**
  - Quick roles compact style: switched quick-role pills to a single-line horizontal row with smaller typography/padding; added horizontal overflow support so layout stays clean on narrow widths.
  - Search Roles micro-interaction: quick-role presets reduced to three junior-focused options (`Junior Software Developer`, `Junior Data Analyst`, `Junior Quality Assurance`).
  - Enter-hint behavior: “Press ↵ Enter to add ...” is now conditionally shown only while the Search Roles input is focused and non-empty, rendered directly below the input as a subtle rounded hint.
  - Search box UI deep refactor: Search Roles container now uses fixed max width (`500px`) with wrapped inline chips; tags no longer stretch the filter panel and remain vertically centered inside the input area.
  - Quick roles redesign: moved quick-role pills directly below the Search Roles input; changed to subtle gray pill buttons with selected-state highlighting, and clicking pills toggles their role chips in the main search container.
  - Search Roles unification: merged Search input, quick tags, and selected tags into one multi-select search box; selected role chips now live inside the input container for consistent visual and state behavior.
  - Interaction polish: quick role tags now directly add roles, suggestion clicks add-and-clear input, and selected chips can be removed inline.
  - Search UI simplification: removed the overlapping Job Type selector and merged query selection into a single Search Roles workflow (type-ahead suggestions + Enter to add custom role + quick role tags).
  - Layout update: filter bar now prioritizes `[Location] [Search Roles] [Graduation year] [Years of experience]` for faster scan and less clutter.
  - Query suggestion MVP: added search-keyword-based suggested scrape queries in the UI (select up to 5 tags), with role-based fallback query generation when no tags are selected.
  - Refresh pipeline: `POST /api/jobs/refresh` now accepts `searchTerms`; backend validates them and forwards to `hunt.py --search-terms`, which scrapes per term and merges results before dedup/upsert.
  - Filter constraints: graduation year range is now constrained to 2020–2026 in both frontend input and backend parsing/suggestions.

- **2026-03-20**
  - Frontend UX: filter changes no longer auto-trigger `/api/jobs`; job list refresh is now manual via the Run button (initial page load still fetches once).
  - Refresh UI/API: added independent scrape count inputs for Indeed and LinkedIn; backend refresh now forwards per-site counts to `hunt.py` via `--results-indeed` and `--results-linkedin`.
  - Filter reason precision: senior-keyword rejection reason is now dynamic in API mode and reflects the user's selected `years_max` (e.g. max=5 -> reason shows 6+ / Senior / Staff / Lead).
  - Refresh customization: added optional `sites` (`indeed`/`linkedin`) and `resultsPerSite` parameters to `POST /api/jobs/refresh`; backend now validates and forwards them to `hunt.py` (`--sites`, `--results`) in async refresh tasks.
  - Frontend filter bar: when "Refresh jobs from web first" is enabled, users can choose scrape sites and set results-per-site directly in UI before clicking Run.
  - Scraping behavior: `src/scrape.py` now consistently honors `results_wanted` for each selected site instead of using hardcoded per-site defaults.
  - Backend API: changed job refresh from synchronous blocking execution to asynchronous tasks; `POST /api/jobs/refresh` now returns a `taskId`, and `GET /api/jobs/refresh/<task_id>` returns task status (`running/succeeded/failed`) with error details when available.
  - Frontend: updated Run flow to poll refresh task status every 2 seconds, handle timeout/failure gracefully, and fetch latest jobs only after refresh succeeds.

- **2026-03-15**
  - Architecture: introduced SQLite as the single source of truth for jobs; added `status` (new/applied/ignored) and `applied_at`; upsert keeps user-updated status and supports 90-day “same company + same job title => treated as applied” dedup logic.
  - Backend/Scraping: added `POST /api/jobs/refresh` to scrape and upsert into DB; `/api/jobs` supports the Applied tab with proper counts; improved refresh error reporting by surfacing the relevant tail output from `hunt.py`.
  - Frontend UI: added Location (Canada / United States) filtering and an Applied (N) tab; JobCard supports “Mark as applied”; Job Type changed to multi-select scrollable dropdown; added debounce for filter inputs; Run can optionally refresh first; UI displays per-site scrape counts and dedup results.

- **2026-03-20**
  - Release v1.0: migrated job persistence from CSV outputs to SQLite; introduced `status` (new/applied/ignored) and `applied_at` for “applied work” tracking.
  - UI: enhanced the filter bar for more flexible matching (including debounced inputs) and added an Applied tab with correct applied counts.


- **2026-03-07**
  - UI: improved resume upload area — after choosing a file, a filename tag (with a × dismiss button) appears next to "Choose PDF" so users can see and cancel their selection at any time.
  - Fix: error messages in `ResumeUpload` (e.g. "please select a PDF") were still hardcoded in Chinese even in the English UI; all strings are now bilingual and follow the active language toggle.
  - Cleaned up repo: removed `CHANGELOG.md`, `IMPROVEMENTS.md`, `.github/copilot-instructions.md`; updated `.gitignore` to exclude generated `data/` files.
  - Translated all code comments and docstrings to English across `src/`, `api/app.py`, and `hunt.py`.
  - UI: bilingual EN/CN toggle button (fixed top-right corner, segmented `[EN|CN]` style); graceful "no API key" message when DeepSeek key is missing instead of a raw error.
  - Added `README_CN.md` (Chinese version) and rewrote `README.md` in English.

- **2026-03-07** (earlier)
  - Scraping: LinkedIn now fetches full description (`linkedin_fetch_description=True`); per-site result counts via `RESULTS_PER_SITE` (indeed=100, linkedin=30); default `--results` lowered to 30.  
  - Scoring: `tech_keywords.yaml` expanded from 77 to 160+ keywords (frontend, backend, cloud/DevOps, AI/ML, tools); fixed React.js / CI/CD matching in `resume.py` for keywords containing `.` or `/`.  
  - Filters: `Associate` added to `ENTRY_LEVEL` (fixes TD Associate SWE being filtered out); `Mechanical Engineer` and `Electrical Engineer` added to `NON_SOFTWARE_TITLE`; expanded non-software exclusions (environmental, medical, accounting, trades, etc.).  
  - Config: resume auto-selects uploaded PDF (`data/uploads/current_resume.pdf`) over fallback `Grace_cs3.pdf`.  
  - UI: header redesigned with green gradient + resume upload bar; removed emojis from title/buttons; job card score circle fixed to right side with consistent vertical alignment; source badge (indeed/linkedin) and Remote badge added to each card.

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

- **2026-02-2?**
  - Don't rememeber when did I do this
  - Scraping: `added country_indeed='Canada'` to  `run_scrape` so Indeed returns Canadian jobs; prints `df["site"].value_counts()` after scraping to help debug whether Indeed results are being deduplicated away.

- **2026-02-26**
  - Saved current progress to git.
  - Next steps: (1) LinkedIn has no description — add `linkedin_fetch_description=True` to `scrape_jobs` call in `src/scrape.py`; (2) Indeed jobs not appearing in xlsx — investigate deduplication logic (keep only one per company+title) and whether `country_indeed` needs to be passed.

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

# AI Coding Agent Instructions

## Project Overview
This is a job hunting automation script (`hunt.py`) that scrapes job postings from Indeed/LinkedIn, scores them against a resume PDF using hybrid semantic/keyword matching, and filters out unsuitable positions for new graduates.

## Architecture & Data Flow
- **Single-file design**: All logic in `hunt.py` (~450 lines) - no separate modules
- **Four-stage scoring pipeline** (improved):
  1. Job scraping via `jobspy.scrape_jobs()` (Indeed/LinkedIn, 24h old max)
  2. Hybrid scoring: semantic (40%) + keyword fuzzy matching (35%) + title bonus (15%) + location bonus (10%)
  3. Classification: "Perfect Match"/"Possible"/"Unlikely" vs "Too Senior" filtering
  4. Output: Excel file with "Jobs" (kept) and "Filtered_Out" sheets

## Key Patterns & Conventions

### Improved Scoring Algorithm (`compute_hybrid_score`)
**Four-component system (v2)**:
- **Semantic similarity** (40%): Resume vs JD full text. Falls back to job title if JD too short (<10 chars)
- **Keyword fuzzy matching** (35%): `rapidfuzz.partial_ratio >= 75` (lowered from 80) against `RESUME_SKILLS`, +25 points per match (max 100)
- **Title bonuses** (15%): +15 if title contains "Junior|New Grad|2025|Entry|Early Career|Graduate" (expanded keywords)
- **Location bonus** (10%): +10 for Toronto/Mississauga, +5 for Ontario

**Why the changes**:
- Reduced semantic weight (60%→40%): Resume text ≠ JD wording
- Increased keyword weight (30%→35%) + lowered threshold + higher points: Technical skills are primary signal
- Expanded title keywords: "Early Career" and "Entry-Level" are key signals
- Added location bonus: Prioritizes preferred locations without filtering

### Configuration File Support (New)
Load job-specific skills & weights from YAML/JSON:
```bash
python hunt.py --config job_positions.yaml --position backend
```

**Config structure** (`job_positions.yaml`):
```yaml
positions:
  backend:
    skills: ["Java", "Python", "SQL", "Spring"]
    weights:
      semantic: 0.40
      keyword: 0.35
      title_bonus: 0.15
      location_bonus: 0.10
```

### Filtering Logic (`classify_job`)
- **Exclude patterns**: Intern/Co-op/Student positions, 3+/5+ years experience, Senior/Staff/Lead roles
- **Location prioritization**: Toronto/Mississauga (100) > Ontario (50) > others (0) for deduplication
- **Duplicate handling**: Remove duplicates by (company, title), keep highest location score

### Data Processing
- **Resume text extraction**: `pdfplumber` → clean non-ASCII → embed first 8000 chars
- **Column selection**: Fixed `OUTPUT_COLUMNS` list for consistent Excel output
- **Sorting**: Kept jobs by `Match_Score` DESC, filtered jobs by same for debugging

## Development Workflow

### Running the Script
```bash
# Default (uses RESUME_SKILLS)
python hunt.py --search "Software Engineer" --location "Canada" --results 30

# With custom position config
python hunt.py --search "Backend Engineer" \
  --config job_positions.yaml --position backend

# Custom output path
python hunt.py --out "results_custom.xlsx"
```

### Dependencies & Environment
- **Python 3.x** with packages from `requirements.txt`
- **Resume PDF**: `Grace_cs3.pdf` in script directory (or set `RESUME_PDF` env var)
- **Configuration file** (optional): `job_positions.yaml` for job-specific skills/weights
- **PyYAML** (optional): For YAML config support; auto-degrades to JSON if missing

### Testing & Validation
- **Output validation**: Check Excel sheets have correct columns and Match_Score sorting
- **Scoring verification**: Top jobs should have "Junior" in title or be in Ontario/Toronto
- **Configuration testing**: Verify `--config` and `--position` flags load correctly
- **Location bonus**: Toronto jobs should score 10 points higher than equivalents

## Code Style Notes
- **Mixed language**: Chinese docstrings/comments, English variable names
- **Global caching**: Semantic model loaded once at startup, configuration loaded once per run
- **Graceful degradation**: Keyword-only scoring if semantic model fails; default config if YAML missing
- **Regex patterns**: Pre-compiled at module level for performance
- **Type hints**: Python 3.10+ union syntax (`dict | None`)

## Common Modification Patterns
- **Update skills**: Modify `RESUME_SKILLS` or create new position in `job_positions.yaml`
- **Adjust scoring weights**: Edit `SCORE_WEIGHTS` dict or `weights` section in YAML
- **Add filters**: Extend `EXCLUDE_TITLE_DESC` or `SENIOR_PATTERNS` regexes
- **Change location priority**: Modify `location_score()` or `_location_bonus()` functions
- **Add new position profile**: Append to `positions:` section in YAML config

## Recent Improvements (v2)
- ✓ Four-component scoring (was 3-component)
- ✓ Lowered keyword threshold 80%→75% for broader matching
- ✓ Increased keyword points 20→25 per match
- ✓ Expanded title keywords (added Entry-Level, Early Career, Graduate)
- ✓ Added location bonus (Toronto +10, Ontario +5)
- ✓ YAML/JSON configuration support for quick position switching
- ✓ See `IMPROVEMENTS.md` for detailed before/after analysis</content>
<parameter name="filePath">c:\Users\16475\Documents\Grace Yue Li\life\2025 China\Find Job\cursor\.github\copilot-instructions.md
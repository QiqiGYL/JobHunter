# -*- coding: utf-8 -*-
"""
Global configuration and helpers: resume path selection, skill loading, YAML/JSON config.
"""

from __future__ import annotations

import os
import json
from pathlib import Path

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False

ROOT_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT_DIR / "config"
DATA_DIR = ROOT_DIR / "data"

DEFAULT_RESUME_SKILLS = [
    "C++", "Java", "Springboot", "SQLite", "Statistics", "Python",
    "MySQL", "MongoDB", "MariaDB", "Redis", "GitHub", "R",
]

RESUME_FILENAME = "Grace_cs3.pdf"
_UPLOADED_RESUME = DATA_DIR / "uploads" / "current_resume.pdf"
_FALLBACK_RESUME = ROOT_DIR / RESUME_FILENAME

# Priority: RESUME_PDF env var > uploaded via UI > fallback Grace_cs3.pdf
RESUME_PDF_PATH = (
    os.environ.get("RESUME_PDF")
    or (str(_UPLOADED_RESUME) if _UPLOADED_RESUME.is_file() else str(_FALLBACK_RESUME))
)

DEFAULT_TECH_KEYWORDS = {
    "编程语言": ["Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "Go", "Rust"],
    "Web框架": ["Spring", "Springboot", "Django", "Flask", "React", "Vue", "Angular", "Express"],
    "数据库": ["SQLite", "MySQL", "PostgreSQL", "MongoDB", "Redis", "MariaDB"],
    "云平台与容器": ["Docker", "Kubernetes", "AWS", "Azure", "Google Cloud", "GitHub"],
    "数据与分析": ["Statistics", "Machine Learning", "Data Analysis", "Pandas", "NumPy", "R"],
}


def load_config_file(config_path: str) -> dict:
    """Load configuration from a YAML or JSON file."""
    if not config_path or not os.path.isfile(config_path):
        return {}
    try:
        if config_path.endswith(".yaml") or config_path.endswith(".yml"):
            if not HAS_YAML:
                print(f"WARNING: PyYAML not installed, skipping YAML config {config_path}")
                return {}
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        elif config_path.endswith(".json"):
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"WARNING: Failed to read config file {config_path}: {e}")
    return {}


def load_skill_config(config_path: str) -> dict | None:
    """Load position/skill configuration from a YAML or JSON file."""
    config = load_config_file(config_path)
    if not config:
        return None
    return config.get("positions", {})


def load_tech_keywords() -> dict:
    """Load the tech keyword library (prefers config/tech_keywords.yaml)."""
    path = CONFIG_DIR / "tech_keywords.yaml"
    if path.is_file() and HAS_YAML:
        try:
            with open(path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config.get("tech_keywords", {}) or {}
        except Exception:
            pass
    # Fall back to legacy root-level location
    old_path = ROOT_DIR / "tech_keywords.yaml"
    if old_path.is_file() and HAS_YAML:
        try:
            with open(old_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config.get("tech_keywords", {}) or {}
        except Exception:
            pass
    return DEFAULT_TECH_KEYWORDS


def auto_update_resume_skills(resume_pdf_path: str) -> list[str]:
    """Auto-extract tech keywords from the resume PDF; falls back to DEFAULT_RESUME_SKILLS."""
    if not resume_pdf_path or not os.path.isfile(resume_pdf_path):
        return list(DEFAULT_RESUME_SKILLS)
    try:
        from src.resume import extract_keywords_from_resume
        tech_keywords = load_tech_keywords()
        if not tech_keywords:
            return list(DEFAULT_RESUME_SKILLS)
        result = extract_keywords_from_resume(resume_pdf_path, tech_keywords)
        found = []
        for category_dict in result.get("全部关键词", {}).values():
            found.extend(category_dict.keys())
        if found:
            skills = sorted(set(found))
            print(f"Auto-extracted {len(skills)} skill keywords from resume: {', '.join(skills)}")
            return skills
    except Exception as e:
        print(f"WARNING: Failed to auto-extract resume keywords, using defaults: {e}")
    return list(DEFAULT_RESUME_SKILLS)

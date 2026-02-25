# -*- coding: utf-8 -*-
"""
全局配置与工具函数：简历路径、技能列表、YAML/JSON 加载。
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
RESUME_PDF_PATH = os.environ.get("RESUME_PDF") or str(ROOT_DIR / RESUME_FILENAME)

DEFAULT_TECH_KEYWORDS = {
    "编程语言": ["Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "Go", "Rust"],
    "Web框架": ["Spring", "Springboot", "Django", "Flask", "React", "Vue", "Angular", "Express"],
    "数据库": ["SQLite", "MySQL", "PostgreSQL", "MongoDB", "Redis", "MariaDB"],
    "云平台与容器": ["Docker", "Kubernetes", "AWS", "Azure", "Google Cloud", "GitHub"],
    "数据与分析": ["Statistics", "Machine Learning", "Data Analysis", "Pandas", "NumPy", "R"],
}


def load_config_file(config_path: str) -> dict:
    """从 YAML/JSON 读取配置。"""
    if not config_path or not os.path.isfile(config_path):
        return {}
    try:
        if config_path.endswith(".yaml") or config_path.endswith(".yml"):
            if not HAS_YAML:
                print(f"WARNING: PyYAML 未安装，跳过 YAML 配置 {config_path}")
                return {}
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        elif config_path.endswith(".json"):
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"WARNING: 读取配置文件失败 {config_path}: {e}")
    return {}


def load_skill_config(config_path: str) -> dict | None:
    """从 YAML/JSON 加载职位和技能配置。"""
    config = load_config_file(config_path)
    if not config:
        return None
    return config.get("positions", {})


def load_tech_keywords() -> dict:
    """加载技术关键词库（优先读 config/tech_keywords.yaml）。"""
    path = CONFIG_DIR / "tech_keywords.yaml"
    if path.is_file() and HAS_YAML:
        try:
            with open(path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config.get("tech_keywords", {}) or {}
        except Exception:
            pass
    # 兼容旧位置
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
    """自动从简历 PDF 提取技术关键词作为 RESUME_SKILLS；失败时返回默认值。"""
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
            print(f"已从简历自动提取 {len(skills)} 个技能关键词: {', '.join(skills)}")
            return skills
    except Exception as e:
        print(f"WARNING: 自动提取简历关键词失败，使用默认 RESUME_SKILLS: {e}")
    return list(DEFAULT_RESUME_SKILLS)

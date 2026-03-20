# -*- coding: utf-8 -*-
"""
SQLite-backed job storage: Job model, upsert with dedup (90-day company+title applied), status (new/applied/ignored).
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import declarative_base, Session
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

from src.config import DATA_DIR

Base = declarative_base() if HAS_SQLALCHEMY else None
DB_PATH = DATA_DIR / "jobhunter.db"


def _job_id_from_row(row: dict | pd.Series) -> str:
    """Stable 32-char hex id: hash of job_url, or title+company+description."""
    url = (row.get("job_url") if hasattr(row, "get") else getattr(row, "job_url", None)) or ""
    url = str(url).strip()
    if url:
        return hashlib.sha256(url.encode("utf-8")).hexdigest()[:32]
    title = str((row.get("title") if hasattr(row, "get") else getattr(row, "title", None)) or "").strip()
    company = str((row.get("company") if hasattr(row, "get") else getattr(row, "company", None)) or "").strip()
    desc = (row.get("description") if hasattr(row, "get") else getattr(row, "description", None)) or ""
    desc = str(desc)[:1000].strip()
    raw = "|".join([title, company, desc])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


if HAS_SQLALCHEMY:
    from sqlalchemy import Column, DateTime, Float, Integer, String

    class Job(Base):
        __tablename__ = "jobs"
        job_id = Column(String(32), primary_key=True)
        title = Column(String(1024))
        company = Column(String(512))
        location = Column(String(512))
        job_url = Column(String(2048))
        date_posted = Column(String(128))
        Match_Score = Column(Float)
        is_remote = Column(Integer)  # 0/1 for SQLite
        salary_range = Column(String(256))
        site = Column(String(64))
        description = Column(String(65536))
        status = Column(String(32), default="new", nullable=False)  # new | applied | ignored
        applied_at = Column(DateTime, nullable=True)
        created_at = Column(DateTime, default=datetime.utcnow)
        updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    class DedupRemoved(Base):
        """Rows removed by (company, title) dedup; for review in same DB."""
        __tablename__ = "jobs_dedup_removed"
        id = Column(Integer, primary_key=True, autoincrement=True)
        job_id = Column(String(32))
        title = Column(String(1024))
        company = Column(String(512))
        location = Column(String(512))
        job_url = Column(String(2048))
        date_posted = Column(String(128))
        Match_Score = Column(Float)
        is_remote = Column(Integer)
        salary_range = Column(String(256))
        site = Column(String(64))
        description = Column(String(65536))
        saved_at = Column(DateTime, default=datetime.utcnow)


def get_engine():
    if not HAS_SQLALCHEMY:
        raise RuntimeError("SQLAlchemy is required for database support. pip install sqlalchemy")
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return create_engine(f"sqlite:///{DB_PATH}", future=True)


def init_db(engine=None):
    if engine is None:
        engine = get_engine()
    if Base is not None:
        Base.metadata.create_all(engine)


def save_dedup_removed(df: pd.DataFrame, engine=None) -> int:
    """Replace jobs_dedup_removed table with rows from df (those removed by company+title dedup). Returns count saved."""
    if not HAS_SQLALCHEMY or Base is None:
        return 0
    if df.empty:
        return 0
    if engine is None:
        engine = get_engine()
    init_db(engine)
    with Session(engine) as session:
        session.query(DedupRemoved).delete()
        for _, row in df.iterrows():
            rec = DedupRemoved(
                job_id=_job_id_from_row(row),
                title=row.get("title"),
                company=row.get("company"),
                location=row.get("location"),
                job_url=row.get("job_url"),
                date_posted=row.get("date_posted"),
                Match_Score=row.get("Match_Score"),
                is_remote=1 if row.get("is_remote") in (True, 1, "True", "true") else 0,
                salary_range=row.get("salary_range"),
                site=row.get("site"),
                description=row.get("description"),
            )
            session.add(rec)
        session.commit()
    return len(df)


def _row_to_dict(row) -> dict:
    """Convert SQLAlchemy Job row to dict for API/JSON."""
    d = {
        "job_id": row.job_id,
        "title": row.title,
        "company": row.company,
        "location": row.location,
        "job_url": row.job_url,
        "date_posted": row.date_posted,
        "Match_Score": row.Match_Score,
        "is_remote": bool(row.is_remote) if row.is_remote is not None else None,
        "salary_range": row.salary_range,
        "site": row.site,
        "description": row.description,
        "status": row.status or "new",
        "applied_at": row.applied_at.isoformat() if row.applied_at else None,
    }
    return d


def _has_applied_same_role_in_90_days(session: Session, company: str, title: str) -> bool:
    """True if DB has (company, title) with status=applied and applied_at within 90 days."""
    since = datetime.utcnow() - timedelta(days=90)
    q = session.query(Job).filter(
        Job.company == company,
        Job.title == title,
        Job.status == "applied",
        Job.applied_at >= since,
    ).limit(1)
    return session.scalars(q).first() is not None


def upsert_jobs(df: pd.DataFrame, engine=None) -> int:
    """Insert or update jobs from DataFrame. New rows: if (company, title) applied in 90d, set status=applied. Returns count of rows processed."""
    if not HAS_SQLALCHEMY or Base is None:
        raise RuntimeError("SQLAlchemy required")
    if engine is None:
        engine = get_engine()
    init_db(engine)
    count = 0
    with Session(engine) as session:
        for _, row in df.iterrows():
            job_id = _job_id_from_row(row)
            rec = session.get(Job, job_id)
            now = datetime.utcnow()
            if rec is not None:
                # Update data columns; do not overwrite status or applied_at
                rec.title = row.get("title")
                rec.company = row.get("company")
                rec.location = row.get("location")
                rec.job_url = row.get("job_url")
                rec.date_posted = row.get("date_posted")
                rec.Match_Score = row.get("Match_Score")
                rec.is_remote = 1 if row.get("is_remote") in (True, 1, "True", "true") else 0
                rec.salary_range = row.get("salary_range")
                rec.site = row.get("site")
                rec.description = row.get("description")
                rec.updated_at = now
            else:
                company = str(row.get("company") or "").strip()
                title = str(row.get("title") or "").strip()
                status = "new"
                applied_at = None
                if company and title and _has_applied_same_role_in_90_days(session, company, title):
                    status = "applied"
                    applied_at = now
                rec = Job(
                    job_id=job_id,
                    title=row.get("title"),
                    company=row.get("company"),
                    location=row.get("location"),
                    job_url=row.get("job_url"),
                    date_posted=row.get("date_posted"),
                    Match_Score=row.get("Match_Score"),
                    is_remote=1 if row.get("is_remote") in (True, 1, "True", "true") else 0,
                    salary_range=row.get("salary_range"),
                    site=row.get("site"),
                    description=row.get("description"),
                    status=status,
                    applied_at=applied_at,
                )
                session.add(rec)
            count += 1
        session.commit()
    return count


def get_jobs_by_status(engine=None, status: str = "new") -> list[dict]:
    """Return list of job dicts for given status. For status='new' use for Matched/Filtered; for 'applied' order by applied_at desc."""
    if not HAS_SQLALCHEMY or Base is None:
        return []
    if engine is None:
        engine = get_engine()
    init_db(engine)
    with Session(engine) as session:
        q = session.query(Job).filter(Job.status == status)
        if status == "applied":
            q = q.order_by(Job.applied_at.desc())
        else:
            q = q.order_by(Job.Match_Score.desc())
        rows = q.all()
        return [_row_to_dict(r) for r in rows]


def get_all_jobs(engine=None) -> list[dict]:
    """Return all jobs (for xlsx export). Order by Match_Score desc."""
    if not HAS_SQLALCHEMY or Base is None:
        return []
    if engine is None:
        engine = get_engine()
    init_db(engine)
    with Session(engine) as session:
        rows = session.query(Job).order_by(Job.Match_Score.desc()).all()
        return [_row_to_dict(r) for r in rows]


def get_all_new_jobs(engine=None) -> list[dict]:
    """Return all jobs with status='new' (for API to run classify_job and split jobs/filteredOut)."""
    return get_jobs_by_status(engine=engine, status="new")


def get_applied_count(engine=None) -> int:
    """Return count of jobs with status='applied' for tab label."""
    if not HAS_SQLALCHEMY or Base is None:
        return 0
    if engine is None:
        engine = get_engine()
    init_db(engine)
    with Session(engine) as session:
        return session.query(Job).filter(Job.status == "applied").count()


def update_job_status(job_id: str, status: str, engine=None) -> Optional[dict]:
    """Set job status to 'applied' or 'ignored'. If applied, set applied_at=now. Return updated job dict or None if not found."""
    if not HAS_SQLALCHEMY or Base is None:
        return None
    if engine is None:
        engine = get_engine()
    init_db(engine)
    with Session(engine) as session:
        rec = session.get(Job, job_id)
        if rec is None:
            return None
        rec.status = status
        rec.updated_at = datetime.utcnow()
        if status == "applied":
            rec.applied_at = datetime.utcnow()
        elif status == "ignored":
            rec.applied_at = None
        session.commit()
        session.refresh(rec)
        return _row_to_dict(rec)


def export_to_xlsx(path: Path, engine=None) -> int:
    """Export all jobs from DB to xlsx sheet 'All'. Returns count exported."""
    jobs = get_all_jobs(engine=engine)
    if not jobs:
        return 0
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Remove DB-only fields for xlsx
    cols = ["job_id", "title", "company", "location", "job_url", "date_posted", "Match_Score",
            "is_remote", "salary_range", "site", "description", "status", "applied_at"]
    rows = [{k: j.get(k) for k in cols if k in j} for j in jobs]
    for r in rows:
        if "job_id" in r:
            del r["job_id"]
        if "status" in r:
            del r["status"]
        if "applied_at" in r:
            del r["applied_at"]
    df = pd.DataFrame(rows)
    df.to_excel(path, sheet_name="All", index=False)
    return len(jobs)


def import_from_xlsx(path: Path, engine=None) -> int:
    """One-time import: read xlsx sheet 'All' (or Jobs+Filtered_Out), insert into DB with status='new'. Returns count imported."""
    if not HAS_SQLALCHEMY or Base is None:
        return 0
    if not path.is_file():
        return 0
    try:
        all_df = pd.read_excel(path, sheet_name="All")
    except Exception:
        try:
            j = pd.read_excel(path, sheet_name="Jobs")
            f = pd.read_excel(path, sheet_name="Filtered_Out")
            all_df = pd.concat([j, f], ignore_index=True)
        except Exception:
            return 0
    if all_df.empty:
        return 0
    # Normalize column names (Match_Score etc. may exist)
    all_df = all_df.rename(columns=lambda c: c.strip() if isinstance(c, str) else c)
    return upsert_jobs(all_df, engine=engine)

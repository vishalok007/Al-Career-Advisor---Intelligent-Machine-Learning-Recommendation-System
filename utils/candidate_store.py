"""SQLite Candidate Persistence & Analytics Store.

Provides structured relational persistence for candidates in Data/candidates.db
with automated legacy JSON migration, SQL indexing, and export utilities.
"""
from __future__ import annotations

import csv
import io
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_DIR = ROOT / "Data"
DB_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DB_DIR / "candidates.db"

# Legacy JSON store location for auto-migration
LEGACY_DIR = Path(os.environ.get("CANDIDATE_STORE_DIR", str(ROOT / ".cache" / "candidates")))


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize database tables, indexes, and migrate legacy JSON files."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS candidates (
                id TEXT PRIMARY KEY,
                saved_at TEXT NOT NULL,
                candidate_name TEXT,
                domain TEXT,
                education TEXT,
                experience_years INTEGER,
                top_job TEXT,
                overall_pct REAL,
                jd_overall_pct REAL,
                data_json TEXT NOT NULL
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_domain ON candidates(domain)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_saved_at ON candidates(saved_at DESC)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_candidates_overall_pct ON candidates(overall_pct DESC)")
        conn.commit()

    _migrate_legacy_json_files()


def _migrate_legacy_json_files() -> None:
    """Automatically import existing .json candidate files into SQLite."""
    if not LEGACY_DIR.exists():
        return

    json_files = list(LEGACY_DIR.glob("*.json"))
    if not json_files:
        return

    with get_db_connection() as conn:
        cursor = conn.cursor()
        for path in json_files:
            try:
                with open(path, "r", encoding="utf-8") as fh:
                    record = json.load(fh)
                cid = record.get("id") or path.stem
                record["id"] = cid
                record.setdefault("saved_at", _now_iso())

                top_job = ""
                if record.get("top_jobs"):
                    tj = record["top_jobs"][0]
                    top_job = tj.get("title", "") if isinstance(tj, dict) else str(tj)

                cursor.execute(
                    """
                    INSERT OR REPLACE INTO candidates (
                        id, saved_at, candidate_name, domain, education,
                        experience_years, top_job, overall_pct, jd_overall_pct, data_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        cid,
                        record["saved_at"],
                        record.get("candidate_name", "Anonymous"),
                        record.get("domain", ""),
                        record.get("education", ""),
                        int(record.get("experience_years") or 0),
                        top_job,
                        float(record.get("overall_pct") or 0.0),
                        float((record.get("jd_match") or {}).get("overall_match_pct") or 0.0),
                        json.dumps(record, ensure_ascii=False),
                    ),
                )
            except Exception:
                continue
        conn.commit()


# Initialize database schema on module import
init_db()


def save_candidate(record: dict) -> str:
    """Persist a candidate record to SQLite; returns assigned ID."""
    cid = record.get("id") or datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") + "-" + uuid.uuid4().hex[:6]
    record["id"] = cid
    saved_at = record.setdefault("saved_at", _now_iso())

    top_job = ""
    if record.get("top_jobs"):
        tj = record["top_jobs"][0]
        top_job = tj.get("title", "") if isinstance(tj, dict) else str(tj)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO candidates (
                id, saved_at, candidate_name, domain, education,
                experience_years, top_job, overall_pct, jd_overall_pct, data_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                cid,
                saved_at,
                record.get("candidate_name", "Anonymous"),
                record.get("domain", ""),
                record.get("education", ""),
                int(record.get("experience_years") or 0),
                top_job,
                float(record.get("overall_pct") or 0.0),
                float((record.get("jd_match") or {}).get("overall_match_pct") or 0.0),
                json.dumps(record, ensure_ascii=False),
            ),
        )
        conn.commit()

    return cid


def list_candidates(domain: str | None = None, min_exp: int | None = None) -> list[dict]:
    """Return all stored candidates, newest first."""
    query = "SELECT data_json FROM candidates WHERE 1=1"
    params = []
    if domain:
        query += " AND domain = ?"
        params.append(domain)
    if min_exp is not None:
        query += " AND experience_years >= ?"
        params.append(min_exp)
    query += " ORDER BY saved_at DESC"

    out: list[dict] = []
    with get_db_connection() as conn:
        cursor = conn.cursor()
        for row in cursor.execute(query, params):
            try:
                data = json.loads(row["data_json"])
                out.append(data)
            except Exception:
                continue
    return out


def load_candidate(cid: str) -> dict | None:
    """Load candidate dict by ID from SQLite."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        row = cursor.execute("SELECT data_json FROM candidates WHERE id = ?", (cid,)).fetchone()
        if row:
            try:
                return json.loads(row["data_json"])
            except Exception:
                return None
    return None


def delete_candidate(cid: str) -> bool:
    """Delete candidate by ID from SQLite."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM candidates WHERE id = ?", (cid,))
        conn.commit()
        return cursor.rowcount > 0


def record_candidate_from_session(
    *,
    candidate_name: str,
    education: str,
    experience_years: int,
    validated_skills: list[str],
    ignored_skills: list[str],
    domain: str,
    top_jobs: list[dict],
    missing_skills: list[str],
    matched_skills: list[str],
    proficiency_map: dict,
    resume_text: str = "",
    jd_text: str = "",
    jd_match: dict | None = None,
    roadmap_total_weeks: int | None = None,
    overall_pct: float | None = None,
) -> str:
    """Build candidate dictionary and persist to SQLite."""
    record = {
        "candidate_name": candidate_name or "Anonymous",
        "education": education,
        "experience_years": int(experience_years or 0),
        "validated_skills": list(validated_skills or []),
        "ignored_skills": list(ignored_skills or []),
        "domain": domain,
        "top_jobs": list(top_jobs or []),
        "missing_skills": list(missing_skills or []),
        "matched_skills": list(matched_skills or []),
        "proficiency_map": dict(proficiency_map or {}),
        "resume_text": resume_text,
        "jd_text": jd_text,
        "jd_match": jd_match or {},
        "roadmap_total_weeks": roadmap_total_weeks,
        "overall_pct": overall_pct,
    }
    return save_candidate(record)


# Export Helpers
CSV_KEYS = [
    "id", "saved_at", "candidate_name", "domain", "education", "experience_years",
    "top_job", "overall_pct", "jd_overall_pct",
    "skills_count", "missing_count", "matched_count",
]


def _flatten_for_csv(c: dict) -> dict:
    top_job = ""
    if c.get("top_jobs"):
        tj = c["top_jobs"][0]
        top_job = tj.get("title", "") if isinstance(tj, dict) else str(tj)
    return {
        "id": c.get("id", ""),
        "saved_at": c.get("saved_at", ""),
        "candidate_name": c.get("candidate_name", ""),
        "domain": c.get("domain", ""),
        "education": c.get("education", ""),
        "experience_years": c.get("experience_years", ""),
        "top_job": top_job,
        "overall_pct": c.get("overall_pct", ""),
        "jd_overall_pct": (c.get("jd_match") or {}).get("overall_match_pct", ""),
        "skills_count": len(c.get("validated_skills") or []),
        "missing_count": len(c.get("missing_skills") or []),
        "matched_count": len(c.get("matched_skills") or []),
    }


def export_csv_bytes(candidates: list[dict]) -> bytes:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=CSV_KEYS, extrasaction="ignore")
    writer.writeheader()
    for c in candidates:
        writer.writerow(_flatten_for_csv(c))
    return buf.getvalue().encode("utf-8")


def export_json_bytes(candidates: list[dict]) -> bytes:
    cleaned = [{k: v for k, v in c.items() if k != "__path__"} for c in candidates]
    return json.dumps(cleaned, indent=2, ensure_ascii=False).encode("utf-8")

"""Unit tests for Candidate Store SQLite persistence and exports."""
from __future__ import annotations
import pytest
from utils.candidate_store import (
    record_candidate_from_session,
    list_candidates,
    load_candidate,
    export_csv_bytes,
    export_json_bytes,
    delete_candidate,
    DB_PATH,
)

def test_sqlite_database_exists():
    assert DB_PATH.exists()

def test_candidate_store_lifecycle():
    # 1. Record candidate
    cid = record_candidate_from_session(
        candidate_name="Pytest SQLite Candidate",
        education="Master's",
        experience_years=5,
        validated_skills=["Python", "PyTorch", "AWS"],
        ignored_skills=["unknown"],
        domain="AI & Data Science",
        top_jobs=[{"title": "Senior ML Engineer", "confidence": 88.5}],
        missing_skills=["Kubernetes"],
        matched_skills=["Python", "PyTorch"],
        proficiency_map={"Python": {"label": "Expert", "weight": 1.0}},
        resume_text="Sample text",
        overall_pct=88.5,
    )
    assert cid is not None
    assert isinstance(cid, str)

    # 2. List & Filter candidates
    candidates = list_candidates(domain="AI & Data Science", min_exp=3)
    assert len(candidates) > 0
    found = any(c.get("id") == cid for c in candidates)
    assert found

    # 3. Load candidate
    loaded = load_candidate(cid)
    assert loaded.get("candidate_name") == "Pytest SQLite Candidate"
    assert loaded.get("education") == "Master's"

    # 4. Exports
    csv_bytes = export_csv_bytes(candidates)
    json_bytes = export_json_bytes(candidates)
    assert len(csv_bytes) > 0
    assert len(json_bytes) > 0

    # 5. Cleanup
    deleted = delete_candidate(cid)
    assert deleted is True

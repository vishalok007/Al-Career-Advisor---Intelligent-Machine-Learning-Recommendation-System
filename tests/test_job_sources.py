"""Unit tests for live job sources and semantic matching."""
from __future__ import annotations
import pytest
from utils.job_sources import provider_status_rows
from utils.semantic_matching import rank_job_matches, get_scorer

def test_provider_status_rows():
    status = provider_status_rows()
    assert isinstance(status, list)
    assert len(status) >= 4
    names = {p["Provider"] for p in status}
    assert "Remotive" in names
    assert "Arbeitnow" in names

def test_rank_job_matches(mock_job_postings, sample_skills):
    results = rank_job_matches(
        predicted_role="Machine Learning Engineer",
        skills=sample_skills,
        experience_years=5,
        jobs=mock_job_postings,
        education="Master's",
        domain="AI & Data Science",
        scorer_name="cosine",
        top_k=5,
    )
    assert len(results) == 2
    top = results[0]
    assert "fit_score" in top
    assert top["title"] == "Senior Machine Learning Engineer"
    assert top["fit_score"] > 0

def test_get_scorer():
    cosine_scorer = get_scorer("cosine")
    assert cosine_scorer.name == "cosine"
    
    dense_scorer = get_scorer("embeddings")
    assert dense_scorer.name == "embeddings"

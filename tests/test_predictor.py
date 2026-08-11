"""Unit tests for ML Predictor service layer."""
from __future__ import annotations
import pytest
from utils.predictor import (
    load_models,
    predict_job_role,
    validate_skills,
    summarize_profile,
    skill_gap,
    matched_skills,
)

def test_load_models():
    pkg = load_models()
    assert "classifier" in pkg
    assert "skills_encoder" in pkg
    assert "label_encoder" in pkg
    assert "education_encoder" in pkg

def test_validate_skills():
    pkg = load_models()
    valid, invalid = validate_skills(["Python", "PyTorch", "NonExistentSkill123"], pkg["skills_encoder"])
    assert "Python" in valid
    assert "PyTorch" in valid
    assert "NonExistentSkill123" in invalid

def test_predict_job_role(sample_skills):
    jobs, scores, details = predict_job_role(
        education="Master's",
        experience=5,
        skills=sample_skills,
        user_domain="AI & Data Science",
        return_details=True,
    )
    assert len(jobs) >= 3
    assert len(scores) == len(jobs)
    assert jobs[0] in details
    assert "matched_skills" in details[jobs[0]]

def test_skill_gap_and_matched():
    required = ["Python", "PyTorch", "Kubernetes", "Airflow"]
    user_skills = ["Python", "PyTorch"]
    
    gap = skill_gap(required, user_skills)
    matched = matched_skills(required, user_skills)
    
    assert set(gap) == {"Kubernetes", "Airflow"}
    assert set(matched) == {"Python", "PyTorch"}

def test_summarize_profile(sample_skills):
    summary = summarize_profile(sample_skills)
    assert isinstance(summary, dict)
    assert len(summary) > 0

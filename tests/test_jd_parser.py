"""Unit tests for Job Description parser and match scorer."""
from __future__ import annotations
import pytest
from utils.jd_parser import parse_jd_text
from utils.jd_match import jd_overall_score
from utils.skill_proficiency import infer_proficiency_from_text

def test_parse_jd_text():
    raw_jd = (
        "Job Title: Senior ML Engineer\n"
        "Skills: Python, PyTorch, Docker, Kubernetes, AWS, SQL, FastAPI.\n"
        "Requirements: 3 to 5 years of experience.\n"
    )
    parsed = parse_jd_text(raw_jd)
    assert parsed["title"] == "Senior ML Engineer"
    assert "Python" in parsed["skills"]
    assert "PyTorch" in parsed["skills"]
    assert parsed["min_years"] == 3
    assert parsed["max_years"] == 5

def test_jd_overall_score(sample_resume_text):
    prof = infer_proficiency_from_text(sample_resume_text)
    jd_skills = ["Python", "PyTorch", "Kubernetes", "AWS", "Airflow"]
    
    score = jd_overall_score(
        candidate_proficiency=prof,
        jd_skills=jd_skills,
        candidate_exp=5,
        jd_min_years=3,
        jd_max_years=7,
        education="Master's",
    )
    
    assert "overall_match_pct" in score
    assert "skill_pct" in score
    assert "experience_pct" in score
    assert score["overall_match_pct"] > 50
    assert "Python" in score["matched"]
    assert "Airflow" in score["missing"]

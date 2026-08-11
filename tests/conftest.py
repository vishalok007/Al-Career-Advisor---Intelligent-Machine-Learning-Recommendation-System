"""Shared Pytest Configuration, Fixtures, and Mock Data."""
from __future__ import annotations
import sys
from pathlib import Path
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def sample_resume_text() -> str:
    return (
        "Senior Data Scientist with 5 years experience using Python, "
        "Machine Learning, PyTorch, SQL, Pandas, NumPy, Docker, AWS, "
        "TensorFlow, FastAPI. Master's in Computer Science."
    )


@pytest.fixture
def sample_skills() -> list[str]:
    return ["Python", "Machine Learning", "PyTorch", "SQL", "Docker", "AWS", "FastAPI"]


@pytest.fixture
def sample_candidate_profile(sample_skills) -> dict:
    return {
        "candidate_name": "Test Candidate",
        "education": "Master's",
        "experience_years": 5,
        "valid_skills": sample_skills,
        "domain": "AI & Data Science",
        "predicted_role": "Machine Learning Engineer",
    }


@pytest.fixture
def mock_job_postings() -> list[dict]:
    return [
        {
            "id": "remotive-101",
            "title": "Senior Machine Learning Engineer",
            "company": "AI Tech Corp",
            "location": "Remote",
            "url": "https://remotive.com/job/101",
            "apply_url": "https://remotive.com/job/101",
            "source": "Remotive",
            "source_key": "remotive",
            "description": "Looking for a Senior ML Engineer with 4+ years of PyTorch, Python, and AWS experience.",
            "tags": ["python", "pytorch", "aws"],
            "employment_type": "Full-time",
            "published_at": "2026-08-01",
            "salary": "$140,000 - $170,000",
        },
        {
            "id": "arbeitnow-202",
            "title": "Data Scientist",
            "company": "Analytics Cloud",
            "location": "Berlin",
            "url": "https://arbeitnow.com/job/202",
            "apply_url": "https://arbeitnow.com/job/202",
            "source": "Arbeitnow",
            "source_key": "arbeitnow",
            "description": "We need a Data Scientist experienced in SQL, Pandas, and Python.",
            "tags": ["python", "sql", "pandas"],
            "employment_type": "Full-time",
            "published_at": "2026-08-05",
            "salary": "€75,000",
        },
    ]

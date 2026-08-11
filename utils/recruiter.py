"""Recruiter helpers — score stored candidates against a single JD."""
from __future__ import annotations

from typing import Iterable

from utils.jd_match import jd_overall_score
from utils.jd_parser import parse_jd_text
from utils.skill_proficiency import infer_proficiency_from_text


def rank_candidates_for_jd(jd_text: str, candidates: Iterable[dict]) -> list[dict]:
    """Score each stored candidate against ``jd_text`` and return them ranked.

    Each row contains the original candidate id + name and the JD-match dict so
    the UI can render a comparison table without recomputing.
    """
    parsed = parse_jd_text(jd_text or "")
    jd_skills = parsed.get("skills") or []
    jd_min = parsed.get("min_years")
    jd_max = parsed.get("max_years")

    rows: list[dict] = []
    for c in candidates or []:
        prof = c.get("proficiency_map") or infer_proficiency_from_text(c.get("resume_text", ""))
        result = jd_overall_score(
            candidate_proficiency=prof,
            jd_skills=jd_skills,
            candidate_exp=int(c.get("experience_years") or 0),
            jd_min_years=jd_min,
            jd_max_years=jd_max,
            education=c.get("education") or "Bachelor's",
        )
        rows.append({
            "candidate_id": c.get("id"),
            "candidate_name": c.get("candidate_name", "Anonymous"),
            "domain": c.get("domain", ""),
            "experience_years": c.get("experience_years", 0),
            "education": c.get("education", ""),
            "result": result,
            "saved_at": c.get("saved_at", ""),
        })

    rows.sort(
        key=lambda row: (
            row["result"]["overall_match_pct"],
            row["result"]["skill_pct"],
            row["result"]["experience_pct"],
        ),
        reverse=True,
    )
    return rows

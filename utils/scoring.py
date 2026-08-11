from __future__ import annotations
from typing import Iterable
def _norm(skills: Iterable[str]) -> set[str]:
    return {s.strip().lower() for s in skills if s and s.strip()}

def _clamp_score(score_pct: float) -> float:
    return max(8.0, min(100.0, score_pct))

def explain_job_score(user_skills, job, model_score=None, model_rank=None, candidate_pool_size=None):
    """Return an explainable score breakdown for one job."""
    from utils.job_skills import required_skills_for

    required_display = list(required_skills_for(job))
    required_norm = _norm(required_display)

    user_display = []
    seen_user = set()
    for skill in user_skills:
        key = str(skill).strip().lower()
        if key and key not in seen_user:
            seen_user.add(key)
            user_display.append(str(skill).strip())
    user_norm = {s.lower() for s in user_display}
    n_user = max(len(user_norm), 1)

    if not required_display:
        model_pct = float(model_score or 0.0) * 100.0
        score_pct = round(_clamp_score(model_pct), 1)
        return {
            "job": job,
            "required_skills": [],
            "matched_skills": [],
            "missing_skills": [],
            "matched_count": 0,
            "required_count": 0,
            "user_skill_count": len(user_norm),
            "coverage_pct": 0.0,
            "breadth_pct": 0.0,
            "model_score_pct": round(model_pct, 1),
            "model_rank": model_rank,
            "candidate_pool_size": candidate_pool_size,
            "match_score_pct": score_pct,
        }

    matched_skills = [skill for skill in required_display if skill.lower() in user_norm]
    missing_skills = [skill for skill in required_display if skill.lower() not in user_norm]
    matched_count = len(matched_skills)
    required_count = len(required_norm)

    coverage = matched_count / required_count if required_count else 0.0
    breadth = matched_count / n_user if n_user else 0.0
    score_pct = _clamp_score((0.85 * coverage + 0.15 * breadth) * 100.0)
    model_pct = float(model_score or 0.0) * 100.0

    return {
        "job": job,
        "required_skills": required_display,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "matched_count": matched_count,
        "required_count": required_count,
        "user_skill_count": len(user_norm),
        "coverage_pct": round(coverage * 100.0, 1),
        "breadth_pct": round(breadth * 100.0, 1),
        "model_score_pct": round(model_pct, 1),
        "model_rank": model_rank,
        "candidate_pool_size": candidate_pool_size,
        "match_score_pct": round(score_pct, 1),
    }


def score_jobs_for_user(user_skills, jobs, model_scores=None, model_ranks=None, return_details=False):
    model_scores = model_scores or {}
    model_ranks = model_ranks or {}
    candidate_pool_size = len(list(jobs)) if jobs is not None else 0

    scored = []
    details = {}
    for job in jobs:
        breakdown = explain_job_score(
            user_skills,
            job,
            model_score=model_scores.get(job, 0.0) or 0.0,
            model_rank=model_ranks.get(job),
            candidate_pool_size=candidate_pool_size,
        )
        score_pct = breakdown["match_score_pct"]
        scored.append((job, score_pct))
        details[job] = breakdown

    scored.sort(
        key=lambda x: (x[1], model_scores.get(x[0], 0.0) or 0.0),
        reverse=True,
    )

    if return_details:
        return scored, details
    return scored


def top_n(user_skills, jobs, n=3, model_scores=None, model_ranks=None, return_details=False):
    """Return top jobs, scores, and optional explainability details."""
    ranked, details = score_jobs_for_user(
        user_skills,
        jobs,
        model_scores=model_scores,
        model_ranks=model_ranks,
        return_details=True,
    )
    if not ranked:
        return ([], [], {}) if return_details else ([], [])

    top_jobs = [j for j, _ in ranked[:n]]
    top_scores = [s for _, s in ranked[:n]]
    if return_details:
        return top_jobs, top_scores, {job: details[job] for job in top_jobs if job in details}
    return top_jobs, top_scores

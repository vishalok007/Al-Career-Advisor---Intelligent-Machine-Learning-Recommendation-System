from __future__ import annotations
from typing import Mapping
from utils.skill_proficiency import PRO_BY_NAME

# Helpers
EDUCATION_BENCHMARK = {
    "High School": 60.0,
    "Diploma":     72.0,
    "Bachelor's":  85.0,
    "Master's":    95.0,
    "PhD":         100.0,
}


def _clamp(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    return max(lo, min(hi, x))


def _experience_fit(candidate_years: int, jd_min: int | None, jd_max: int | None) -> float:
    if jd_min is None and jd_max is None:
        return 85.0  # neutral — no tenure preference stated
    if jd_min is not None and jd_max is not None:
        if jd_min <= candidate_years <= jd_max:
            return 100.0
        if candidate_years < jd_min:
            return _clamp(85.0 - 15.0 * (jd_min - candidate_years), 20.0, 100.0)
        return _clamp(90.0 - 8.0 * (candidate_years - jd_max), 50.0, 100.0)
    if jd_min is not None:
        if candidate_years >= jd_min:
            return 100.0
        return _clamp(85.0 - 15.0 * (jd_min - candidate_years), 20.0, 100.0)
    if candidate_years <= (jd_max or candidate_years):
        return 100.0
    return _clamp(90.0 - 8.0 * (candidate_years - (jd_max or candidate_years)), 50.0, 100.0)

# Main scorer
def jd_overall_score(
    candidate_proficiency: Mapping[str, dict],
    jd_skills: list[str],
    candidate_exp: int,
    jd_min_years: int | None,
    jd_max_years: int | None,
    education: str,
) -> dict:
    matched: dict[str, float] = {}
    missing: list[str] = []
    raw = 0.0
    denom = max(len(jd_skills), 1)

    # index proficiency by lower-cased key for case-insensitive matching
    prof_idx = {k.lower(): v for k, v in candidate_proficiency.items()}

    for js in jd_skills:
        info = prof_idx.get(js.lower())
        if not info:
            # even a Beginner-level signal beats zero
            for k, v in prof_idx.items():
                if k == js.lower():
                    info = v
                    break
        if info:
            matched[js] = float(info.get("weight", 0.0))
            raw += matched[js]
        else:
            missing.append(js)

    skill_pct = _clamp((raw / denom) * 100.0)
    exp_pct = _experience_fit(int(candidate_exp or 0), jd_min_years, jd_max_years)
    edu_pct = EDUCATION_BENCHMARK.get(education, 80.0)

    # Weighted blend tuned so the JD skills dominate but experience & education
    # still move the needle for borderline candidates.
    overall = 0.70 * skill_pct + 0.20 * exp_pct + 0.10 * edu_pct
    overall = round(_clamp(overall), 1)

    return {
        "overall_match_pct": overall,
        "skill_pct": round(skill_pct, 1),
        "experience_pct": round(exp_pct, 1),
        "education_pct": round(edu_pct, 1),
        "matched": list(matched.keys()),
        "missing": missing,
        "matched_detail": matched,
    }

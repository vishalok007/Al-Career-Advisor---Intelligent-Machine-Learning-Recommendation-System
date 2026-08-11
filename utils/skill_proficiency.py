from __future__ import annotations
import re
from typing import Iterable

PRO_LEVELS = [
    {"name": "None",         "weight": 0.00, "summary": "Not detected"},
    {"name": "Beginner",     "weight": 0.25, "summary": "Familiar with basics"},
    {"name": "Intermediate", "weight": 0.55, "summary": "Hands-on, real projects"},
    {"name": "Advanced",     "weight": 0.80, "summary": "Production-level depth"},
    {"name": "Expert",       "weight": 1.00, "summary": "Principal / specialist"},
]

PRO_BY_NAME = {lvl["name"]: lvl for lvl in PRO_LEVELS}

# Keyword evidence per level (case-insensitive substring match in window).
EVIDENCE = {
    "Beginner":     ["learning", "familiar with", "exposure", "introductory",
                     "introduction", "foundation", "basics", "started"],
    "Intermediate": ["hands-on", "hands on", "1+ year", "1 year", "2 years",
                     "2+ years", "worked on", "built", "project", "coursework"],
    "Advanced":     ["3 years", "3+ years", "4 years", "5 years", "5+ years",
                     "production", "led ", "lead ", "advanced", "deep ",
                     "scalable", "optimized", "optimised", "end-to-end"],
    "Expert":       ["expert", "principal", "6+ years", "7+ years", "8+ years",
                     "9+ years", "10+ years", "authored", "speaker",
                     "conference", "patent", "published"],
}

# Skill catalog — union of the existing SKILL_CATEGORIES and JOB_REQUIRED_SKILLS.
def _build_catalog() -> list[str]:
    from utils.constants import SKILL_CATEGORIES
    from utils.job_skills import JOB_REQUIRED_SKILLS

    seen, out = set(), []
    for bucket in SKILL_CATEGORIES.values():
        for s in bucket:
            k = s.strip().lower()
            if k and k not in seen:
                seen.add(k)
                out.append(s)
    for bucket in JOB_REQUIRED_SKILLS.values():
        for s in bucket:
            k = s.strip().lower()
            if k and k not in seen:
                seen.add(k)
                out.append(s)
    for s in [
        "LLM", "Generative AI", "Prompt Engineering", "LangGraph",
        "Vector Database", "PostgreSQL", "Redis", "FastAPI", "Flask",
        "Django", "REST API", "CI/CD", "Airflow", "Snowflake",
        "MLOps", "ETL", "Spark", "Hadoop", "Tableau", "Power BI",
        "Problem Solving", "Analysis", "Reporting",
    ]:
        if s.lower() not in seen:
            seen.add(s.lower())
            out.append(s)
    return out


KNOWN_SKILLS = _build_catalog()


def _window(text_lower: str, pos: int, span: int = 80) -> str:
    return text_lower[max(0, pos - span): min(len(text_lower), pos + span)]


def infer_proficiency_from_text(text: str) -> dict[str, dict]:
    """Return a {skill_canonical: {label, weight, evidence}} map.

    Skills absent from the text are omitted (caller decides whether to fill
    ``None`` for unseen entries).
    """
    if not text:
        return {}
    text_lower = text.lower()
    out: dict[str, dict] = {}
    for skill in KNOWN_SKILLS:
        s_low = skill.lower()
        best_label = "Beginner"
        best_weight = PRO_BY_NAME["Beginner"]["weight"]
        evidence_hits: list[str] = []
        for match in re.finditer(re.escape(s_low), text_lower):
            window = _window(text_lower, match.start(), 80)
            for label, words in EVIDENCE.items():
                if any(w in window for w in words):
                    wgt = PRO_BY_NAME[label]["weight"]
                    if wgt >= best_weight:
                        best_weight = wgt
                        best_label = label
                        evidence_hits.append(label)
        if best_label != "None" and evidence_hits:
            out[skill] = {
                "label": best_label,
                "weight": best_weight,
                "evidence": sorted(set(evidence_hits)),
            }
    return out


def attach_manual_proficiency(
    detected: dict[str, dict],
    overrides: Iterable[tuple[str, str]],
) -> dict[str, dict]:
    """Merge explicit user-selected levels (from a selectbox) on top of
    the inferred map. Returns a new dict, never mutates the input.
    """
    out = {skill: dict(info) for skill, info in detected.items()}
    for skill, label in overrides:
        if not skill:
            continue
        level = PRO_BY_NAME.get(label)
        if not level:
            continue
        out[skill] = {
            "label": label,
            "weight": level["weight"],
            "evidence": out.get(skill, {}).get("evidence", []) + ["user-set"],
        }
    return out


def proficiency_to_score_rows(proficiency: dict[str, dict]) -> list[tuple[str, float]]:
    """Convert a proficiency map into ``(skill, weight)`` rows used by legacy
    consumers like ``score_jobs_for_user`` via ``required_proficiency``.
    """
    return [(s, info["weight"]) for s, info in proficiency.items()]


def describe_level(label: str) -> str:
    return PRO_BY_NAME.get(label, PRO_BY_NAME["None"]).get("summary", "")

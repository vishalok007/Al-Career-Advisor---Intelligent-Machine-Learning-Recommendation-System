from __future__ import annotations
from collections import Counter, defaultdict
from typing import Iterable
from utils.job_skills import JOB_REQUIRED_SKILLS
import pandas as pd

SKILL_ALIASES = {
    "html/css": {"html/css", "html", "css"},
    "c/c++": {"c/c++", "c++", "c"},
    "rest api": {"rest api", "api development"},
    "ui/ux design": {"ui/ux design", "design", "user experience", "user interface"},
    "react native": {"react native", "react"},
    "technical problem solving": {"technical problem solving", "problem solving"},
    "cloud platforms": {"cloud platforms", "cloud"},
}


def normalize_skill(skill: str) -> str:
    return str(skill).strip().lower()

def split_skills(raw_skills: str) -> list[str]:
    return [skill.strip() for skill in str(raw_skills).split("|") if skill and skill.strip()]

def _expanded_alias_set(skill: str) -> set[str]:
    norm = normalize_skill(skill)
    return set(SKILL_ALIASES.get(norm, {norm}))

def curated_allowed_skills(role: str) -> set[str]:
    allowed: set[str] = set()
    for skill in JOB_REQUIRED_SKILLS.get(role, []):
        allowed.update(_expanded_alias_set(skill))
    return allowed

def recurring_role_skills(df: pd.DataFrame) -> dict[str, set[str]]:
    role_counts = df["Job Role"].value_counts().to_dict()
    role_skill_freq: dict[str, Counter] = defaultdict(Counter)

    for _, row in df.iterrows():
        role = row["Job Role"]
        if role not in JOB_REQUIRED_SKILLS:
            continue
        for skill in set(map(normalize_skill, split_skills(row["Skills"]))):
            role_skill_freq[role][skill] += 1

    out: dict[str, set[str]] = {}
    for role, counter in role_skill_freq.items():
        role_count = role_counts.get(role, 0)
        if role_count >= 12:
            out[role] = {skill for skill, freq in counter.items() if freq >= 3}
        elif role_count >= 6:
            out[role] = {skill for skill, freq in counter.items() if freq >= 2}
        else:
            out[role] = set()
    return out

def clean_skills_for_role(skills: Iterable[str], role: str, frequent_skills: set[str] | None = None) -> list[str]:
    if role not in JOB_REQUIRED_SKILLS:
        # Leave uncovered roles untouched until a curated profile is added.
        seen = set()
        kept = []
        for skill in skills:
            norm = normalize_skill(skill)
            if norm and norm not in seen:
                seen.add(norm)
                kept.append(str(skill).strip())
        return kept

    allowed = curated_allowed_skills(role) | set(frequent_skills or set())
    kept: list[str] = []
    seen = set()
    for skill in skills:
        norm = normalize_skill(skill)
        if not norm or norm in seen:
            continue
        keep = norm in allowed
        if not keep:
            for expanded in SKILL_ALIASES.values():
                if norm in expanded and expanded & allowed:
                    keep = True
                    break
        if keep:
            seen.add(norm)
            kept.append(str(skill).strip())
    return kept


def clean_training_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Return ``(clean_df, stats)`` after removing off-role skills."""
    work = df.copy()
    frequent_map = recurring_role_skills(work)

    cleaned_rows = []
    dropped_rows = 0
    rewritten_rows = 0
    removed_skills = 0

    for _, row in work.iterrows():
        role = row["Job Role"]
        original_skills = split_skills(row["Skills"])
        cleaned_skills = clean_skills_for_role(
            original_skills,
            role,
            frequent_skills=frequent_map.get(role, set()),
        )

        if role in JOB_REQUIRED_SKILLS and not cleaned_skills:
            dropped_rows += 1
            continue

        if cleaned_skills != original_skills:
            rewritten_rows += 1
            removed_skills += max(len(original_skills) - len(cleaned_skills), 0)
            row = row.copy()
            row["Skills"] = "|".join(cleaned_skills)

            resume_text = str(row.get("Resume Text", "") or "")
            if resume_text:
                row["Resume Text"] = resume_text.replace(
                    "Skills: " + ", ".join(original_skills),
                    "Skills: " + ", ".join(cleaned_skills),
                )

        cleaned_rows.append(row)

    clean_df = pd.DataFrame(cleaned_rows).reset_index(drop=True)
    stats = {
        "input_rows": int(len(df)),
        "output_rows": int(len(clean_df)),
        "dropped_rows": int(dropped_rows),
        "rewritten_rows": int(rewritten_rows),
        "removed_skills": int(removed_skills),
        "roles_with_curated_profiles": int(sum(df["Job Role"].isin(JOB_REQUIRED_SKILLS))),
    }
    return clean_df, stats

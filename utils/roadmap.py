"""Weekly learning-roadmap generator.
For every skill gap, we assign a duration proportional to how far the
candidate needs to climb. Starting levels come from the proficiency map:

- None         -> 4 weeks (start from scratch)
- Beginner     -> 3 weeks
- Intermediate -> 2 weeks
- Advanced     -> 1 week (light brushing-up)
- Expert       -> 0 weeks (nothing to learn)

Each week ships with a milestone tag and an estimated hour budget. The total
weekly plan, the cumulative week count, and per-skill subtotals are returned
so the UI can render both a timeline view and a totals card.
"""
from __future__ import annotations
from typing import Mapping
from utils.skill_proficiency import PRO_BY_NAME


WEEKS_PER_LEVEL = {
    "None":         4,
    "Beginner":     3,
    "Intermediate": 2,
    "Advanced":     1,
    "Expert":       0,
}

WEEKLY_MILESTONES = [
    "Foundations & environment setup",
    "Hands-on tutorials & exercises",
    "Mini project end-to-end",
    "Production-grade capstone",
    "Mock interview / portfolio review",
]


def build_weekly_roadmap(
    gap_skills: list[str],
    candidate_proficiency: Mapping[str, dict],
    weekly_hours: int = 8,
) -> dict:
    """Return a per-week study plan that climbs each gap skill toward Expert.

    Output:
        {
            "total_weeks": int,
            "total_hours": int,
            "items": [
                {"week": int, "skill": str, "milestone": str,
                 "hours": int, "start_level": str},
                ...
            ],
            "per_skill": [{"skill": str, "weeks": int, "start_level": str}, ...]
        }
    """
    items: list[dict] = []
    per_skill: list[dict] = []
    week_cursor = 1

    for skill in gap_skills:
        start_label = candidate_proficiency.get(skill, {}).get("label", "None")
        weeks = WEEKS_PER_LEVEL.get(start_label, 4)
        per_skill.append({"skill": skill, "weeks": weeks, "start_level": start_label})

        for w_offset in range(weeks):
            milestone = WEEKLY_MILESTONES[min(w_offset, len(WEEKLY_MILESTONES) - 1)]
            items.append({
                "week": week_cursor,
                "skill": skill,
                "milestone": milestone,
                "hours": weekly_hours,
                "start_level": start_label,
            })
            week_cursor += 1

    total_weeks = max(week_cursor - 1, 0)
    total_hours = total_weeks * weekly_hours
    return {
        "total_weeks": total_weeks,
        "total_hours": total_hours,
        "items": items,
        "per_skill": per_skill,
    }

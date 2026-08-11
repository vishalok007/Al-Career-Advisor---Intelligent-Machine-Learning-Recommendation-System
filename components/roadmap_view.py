"""Weekly Skill Roadmap Component.

Renders missing-skill weekly learning roadmaps with timeline progress,
milestones, and weekly hour allocations.
"""
from __future__ import annotations
import streamlit as st

def render_weekly_roadmap(roadmap: dict) -> None:
    """Render structured weekly roadmap timeline and skill milestones."""
    if not roadmap or not roadmap.get("items"):
        st.success("No missing skill gaps detected! Your profile meets requirements.")
        return

    total_weeks = roadmap.get("total_weeks", 0)
    total_hours = roadmap.get("total_hours", 0)

    st.markdown(
        f'<div class="card fade-up" style="background:rgba(36,75,65,.18);border-color:rgba(122,165,151,.38)">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.5rem">'
        f'<div>'
        f'<div class="card-t">Personalized Weekly Learning Plan</div>'
        f'<div class="card-s">Sequential roadmap to bridge missing skills based on your current proficiency ladder.</div>'
        f'</div>'
        f'<div>'
        f'<span class="pill brand" style="padding:.4rem .8rem">{total_weeks} Weeks Total ({total_hours} hrs)</span>'
        f'</div>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    items = roadmap.get("items", [])
    for item in items[:12]:
        week_num = item.get("week", 1)
        skill = item.get("skill", "Skill")
        milestone = item.get("milestone", "Milestone")
        hours = item.get("hours", 8)

        st.markdown(
            f'<div class="card fade-up" style="margin-bottom:.5rem;padding:.7rem 1rem;display:flex;align-items:center;gap:1rem">'
            f'<div style="background:#244b41;color:#f1c161;font-weight:700;font-size:.9rem;padding:.3rem .7rem;border-radius:.3rem;min-width:75px;text-align:center">'
            f'Week {week_num}'
            f'</div>'
            f'<div style="flex:1">'
            f'<div style="font-weight:600;font-size:.95rem;color:#f4f7f5">{skill} — <span style="color:#a4c2b0">{milestone}</span></div>'
            f'</div>'
            f'<div style="color:#7aa597;font-size:.85rem;font-weight:600">'
            f'⏱️ {hours} hrs'
            f'</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

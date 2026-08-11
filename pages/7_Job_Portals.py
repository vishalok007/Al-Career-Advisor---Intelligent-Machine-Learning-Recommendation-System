from __future__ import annotations
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from utils.job_portals import recommend_portals, primary_recommendation, PORTALS
from utils.constants import BRAND, DOMAIN_COLORS
from utils.job_sources import provider_status_rows
from utils.helpers import (
    inject_css, page_header, kpi_card, empty_state,
)
from components import render_sidebar


SAMPLE_ROLES = [
    "Machine Learning Engineer",
    "Data Scientist",
    "AI Engineer",
    "Software Engineer",
    "Backend Developer",
    "Full Stack Developer",
    "DevOps Engineer",
    "Cloud Engineer",
    "Data Analyst",
    "Cybersecurity Analyst",
]

SAMPLE_LOCATIONS = [
    "Bangalore", "Hyderabad", "Pune", "Mumbai", "Delhi",
    "India", "USA", "Remote", "London", "Singapore",
]


inject_css("assets/styles.css")
render_sidebar("Job Portals")
page_header(
    "Job Portals",
    "Pre-filled live search links for the four biggest free job portals — "
    "Naukri, Hirist, Wellfound and Dice. The portal returns real-time postings "
    "in a new tab.",
    eyebrow="Free public portals · live deep-links",
)

st.markdown(
    "<div class='card fade-up' style='background:linear-gradient(135deg,"
    "rgba(212,153,102,.10),rgba(164,194,176,.06))'>"
    "<div class='card-t'>How this works</div>"
    "<div class='card-s'>These portals do not expose free public APIs for live "
    "job listings. We build a pre-filled <strong>search URL</strong> for each "
    "portal using your role, top skills, location and experience — when you "
    "click a card, the portal's own search-results page opens with those "
    "filters applied. Counts and matches you see are the portal's own "
    "live results.</div></div>",
    unsafe_allow_html=True,
)

st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)

# Inputs 
left, right = st.columns([1, 1])
with left:
    st.markdown(
        '<div class="card fade-up"><div class="card-t">Candidate intent</div>'
        '<div class="card-s">What you want recruiters to find</div></div>',
        unsafe_allow_html=True,
    )
    role = st.selectbox("Target role", SAMPLE_ROLES, index=0)
    experience = st.slider("Experience (years)", 0, 30, 3)
    skills_text = st.text_input(
        "Top skills (comma-separated)",
        value="Python, SQL, Docker",
        placeholder="Python, Machine Learning, AWS",
        help="First 3 skills are forwarded to the search query.",
    )

with right:
    st.markdown(
        '<div class="card fade-up"><div class="card-t">Location</div>'
        '<div class="card-s">Where you want to work</div></div>',
        unsafe_allow_html=True,
    )
    location = st.selectbox("Pick a location", SAMPLE_LOCATIONS, index=0)
    custom_loc = st.text_input("\u2026or type your own", placeholder="e.g. Berlin, Toronto")
    domain = st.selectbox(
        "Career domain",
        list(DOMAIN_COLORS.keys()),
        index=0,
        help="Used to bias portal ranking (startups vs enterprise vs India vs global).",
    )

if custom_loc.strip():
    location = custom_loc.strip()

skills_list = [s.strip() for s in skills_text.split(",") if s.strip()]
effective_loc = location or "India"

# KPI strip 
recs = recommend_portals(
    role=role,
    skills=skills_list,
    location=effective_loc,
    experience=experience,
    domain=domain,
    location_hint=effective_loc,
)
primary = primary_recommendation(recs) or {}

k1, k2, k3, k4 = st.columns(4)
with k1: kpi_card("Portals covered", "4", "free + public", icon=None)
with k2: kpi_card("Skills query", str(len(skills_list)), "into the URL", icon=None)
with k3: kpi_card("Top portal", primary.get("name", "\u2014"), None, icon=None)
with k4: kpi_card("Top fit score", f"{primary.get('fit_score', 0)}%", "model-driven", icon=None)

st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

st.markdown(
    "<div class='eyebrow' style='margin-top:.8rem'>Live provider registry</div>"
    "<h2 style='margin:.1rem 0 .6rem'>Semantic engine data sources</h2>",
    unsafe_allow_html=True,
)
provider_df = pd.DataFrame(provider_status_rows())
reg_left, reg_right = st.columns([1.15, 1.85])
with reg_left:
    st.dataframe(provider_df, use_container_width=True, hide_index=True)
with reg_right:
    st.markdown(
        "<div class='card'><div class='card-t'>Architecture note</div>"
        "<div class='card-s'>Remotive is live out of the box. Adzuna and JSearch stay in standby until API credentials are added, but the registry and ranking pipeline are already wired, so the UI does not need to change when those providers go live.</div></div>",
        unsafe_allow_html=True,
    )

# Top recommendation banner 
if primary:
    st.markdown(
        f'<div class="card fade-up" style="display:flex;gap:1rem;flex-wrap:wrap;'
        f'align-items:center;background:linear-gradient(135deg,'
        f'rgba(212,153,102,.12),rgba(164,194,176,.08))">'
        f'<div style="flex:1;min-width:240px">'
        f'<div class="card-s">Primary recommendation</div>'
        f'<div style="font-size:1.2rem;font-weight:650;margin-top:.2rem">'
        f'Search <strong>{role}</strong> on {primary["name"]}</div>'
        f'<div class="card-s" style="margin-top:.2rem">{primary["region"]} &middot; '
        f'fit score {primary["fit_score"]}%</div>'
        f'<div style="margin-top:.4rem;color:var(--text-soft);font-size:.9rem">'
        f'{primary["fit_reason"]}</div></div>'
        f'<a href="{primary["url"]}" target="_blank" rel="noopener noreferrer">'
        f'<button class="apply-cta">Open live results &rarr;</button></a></div>',
        unsafe_allow_html=True,
    )

# Ranked portal cards 
st.markdown(
    "<div class='eyebrow' style='margin-top:1.4rem'>All four portals &middot; ranked</div>"
    "<h2 style='margin:.1rem 0 .6rem'>Pick where to apply first</h2>",
    unsafe_allow_html=True,
)

cols = st.columns(len(recs))
for col, r in zip(cols, recs):
    with col:
        st.markdown(
            f'<div class="card portal-card fade-up" style="height:100%">'
            f'<div style="display:flex;justify-content:flex-end;'
            f'align-items:center;margin-bottom:.4rem">'
            f'<span class="pill" style="font-size:.74rem;font-weight:650">'
            f'Fit {r["fit_score"]}%</span></div>'
            f'<div style="font-weight:650;font-size:1.05rem;margin-top:.2rem">'
            f'{r["name"]}</div>'
            f'<div class="card-s" style="margin-top:.15rem">{r["region"]}</div>'
            f'<div style="margin-top:.6rem;color:var(--text-soft);'
            f'font-size:.88rem;line-height:1.55;min-height:80px">'
            f'{r["fit_reason"]}</div>'
            f'<div class="card-s" style="margin-top:.5rem;font-weight:600">'
            f'Best for:</div>'
            f'<div style="margin-top:.15rem;font-size:.85rem">'
            f'{r["apply_hint"]}</div>'
            f'<a href="{r["url"]}" target="_blank" rel="noopener noreferrer" '
            f'style="display:inline-block;margin-top:1rem;text-decoration:none">'
            f'<button class="apply-btn">Open live search &rarr;</button></a>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.markdown(
    "<div class='eyebrow' style='margin-top:1.2rem'>What gets sent to each portal</div>"
    "<h2 style='margin:.1rem 0 .6rem'>URL parameters used</h2>",
    unsafe_allow_html=True,
)

url_rows = []
for p in PORTALS:
    info = p.build(role, skills_list, effective_loc, experience)
    url_rows.append({
        "Portal": p.name,
        "Region": info["region"],
        "Search URL": info["url"],
        "Format": info["format"],
    })
st.dataframe(pd.DataFrame(url_rows), use_container_width=True, hide_index=True)

st.markdown(
    "<div class='eyebrow' style='margin-top:1.2rem'>Ranking factors</div>"
    "<h2 style='margin:.1rem 0 .6rem'>Why this order</h2>",
    unsafe_allow_html=True,
)
factor_items = [
    "<strong>Domain bias</strong> &mdash; startup/domain-leaning roles boost Wellfound &amp; Dice; "
    "general roles favour Naukri &amp; Hirist.",
    "<strong>Location bias</strong> &mdash; Indian cities lift Naukri &amp; Hirist; USA / Remote "
    "lifts Dice &amp; Wellfound.",
    "<strong>Experience</strong> &mdash; senior candidates (&ge; 5 yrs) get a small Dice / Wellfound "
    "boost; junior profiles get a Naukri / Hirist boost.",
    "<strong>Skill density</strong> &mdash; more skills forwarded = richer search query = "
    "higher listing precision.",
]
for item in factor_items:
    st.markdown(
        f'<div class="card" style="margin-bottom:.5rem">'
        f'<div class="card-s" style="font-size:.92rem;line-height:1.55">{item}</div></div>',
        unsafe_allow_html=True,
    )

st.caption(
    f"&copy; 2026 {BRAND['name']} &middot; Job-portal deep-links open the portal's own "
    f"live search-results page in a new tab."
)

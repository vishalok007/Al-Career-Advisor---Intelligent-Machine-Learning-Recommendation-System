
from __future__ import annotations
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import hashlib
import io
import pandas as pd
import streamlit as st

from utils.resume_utils import (
    extract_text_from_pdf,
    extract_skills_from_text,
    extract_location_from_text,
    location_country_hint,
)
from utils.job_portals import recommend_portals, primary_recommendation
from career.recommendations import CAREER_RECOMMENDATIONS
from career.career_domains import detect_domain
from utils.constants import BRAND, EDUCATION_LEVELS
from utils.helpers import (
    inject_css, page_header, kpi_card, prediction_card, coverage_card,
    empty_state, read_csv_cached, pill, progress_bar,
)
from utils.predictor import (
    load_models, predict_job_role, validate_skills, summarize_profile,
    skill_gap, matched_skills, normalize_education_label,
)
from utils.chart_helper import build_top3_chart
from utils.job_sources import fetch_live_jobs, provider_status_rows
from utils.semantic_matching import rank_job_matches
from utils.taxonomy import resolve_hierarchical_role, get_taxonomy_breadcrumbs
from utils.llm_extractor import extract_profile_with_nlp
from utils.skill_proficiency import (
    infer_proficiency_from_text,
    attach_manual_proficiency,
    PRO_LEVELS,
    PRO_BY_NAME,
    describe_level,
)
from utils.jd_parser import parse_jd_pdf, parse_jd_text
from utils.jd_match import jd_overall_score
from utils.roadmap import build_weekly_roadmap
from utils.candidate_store import record_candidate_from_session
from components import render_sidebar, render_live_job_cards, render_weekly_roadmap


inject_css("assets/styles.css")
render_sidebar("Predict")
page_header(
    "Predict Job Role",
    "Upload a resume or paste skills to receive ranked predictions, "
    "a graded proficiency ladder, JD match, weekly learning roadmap, "
    "and a persistent candidate history.",
    eyebrow="Live model · graded skills · JD match · roadmap",
)

models_pkg = load_models()
skills_encoder = models_pkg["skills_encoder"]

# Defaults so reads before writes don't KeyError.
st.session_state.setdefault("prediction", None)
st.session_state.setdefault("resume_parse", None)   # {"key": hash, "text": ..., "skills": [...]}
st.session_state.setdefault("save_msg", None)        # {"kind": success|info|error, "text": ..., "ts": ...}


left, right = st.columns([1, 1])
with left:
    st.markdown(
        '<div class="card fade-up">'
        '<div class="card-t">Candidate profile</div>'
        '<div class="card-s">Education & experience</div></div>',
        unsafe_allow_html=True,
    )
    candidate_name = st.text_input("Candidate name", placeholder="e.g. Priya Sharma", key="in_candidate_name")
    education = st.selectbox("Education", EDUCATION_LEVELS, index=2, key="in_education")
    experience = st.slider("Experience (years)", 0, 30, 2, key="in_experience")
    location_input = st.text_input(
        "Preferred location",
        placeholder="e.g. Bangalore, USA, Remote",
        help="Used for portal ranking and live job matching.",
        key="in_location",
    )
    uploaded = st.file_uploader(
        "Resume (PDF)", type=["pdf"],
        help="Optional — skills are extracted automatically.",
        key="in_uploaded",
    )

with right:
    st.markdown(
        '<div class="card fade-up">'
        '<div class="card-t">Skills</div>'
        '<div class="card-s">Comma-separated list</div></div>',
        unsafe_allow_html=True,
    )
    manual = st.text_area(
        "Enter skills", placeholder="Python, SQL, Machine Learning, Docker",
        height=140, label_visibility="collapsed", key="in_manual",
    )
    cnt = len([s for s in (manual or "").split(",") if s.strip()])
    st.caption(f"{cnt} skills entered")


resume_text: str | None = None
detected_skills: list[str] = []
if uploaded is not None:
    raw_bytes = uploaded.getvalue()
    upload_key = f"{(uploaded.name or '')}::{uploaded.size or len(raw_bytes)}::{hashlib.md5(raw_bytes).hexdigest()[:12]}"
    cached = st.session_state.get("resume_parse")
    if not cached or cached.get("key") != upload_key:
        with st.spinner("Parsing your resume..."):
            resume_text = extract_text_from_pdf(io.BytesIO(raw_bytes))
            detected_skills = extract_skills_from_text(resume_text, skills_encoder.classes_)
        st.session_state["resume_parse"] = {
            "key": upload_key,
            "name": uploaded.name,
            "text": resume_text,
            "skills": detected_skills,
        }
    else:
        resume_text = cached.get("text") or ""
        detected_skills = cached.get("skills") or []
    st.success(f"Extracted {len(detected_skills)} skill(s) from your resume.")

if detected_skills:
    pills = "".join(
        f'<span class="pill accent" style="margin:.2rem;display:inline-block">{s}</span>'
        for s in detected_skills[:24]
    )
    st.markdown(
        f'<div class="card fade-up" style="margin-top:.5rem">'
        f'<div class="card-t">Detected skills</div>'
        f'<div class="card-s">Pulled from your PDF resume</div>'
        f'<div style="margin-top:.6rem">{pills}</div></div>',
        unsafe_allow_html=True,
    )
    if resume_text:
        with st.expander("View parsed text"):
            st.text(resume_text[:1500] + ("…" if len(resume_text) > 1500 else ""))

proficiency = infer_proficiency_from_text(resume_text or "")
proficiency_overrides: dict[str, str] = {}
skills_for_picker: list[str] = []
seen_lower: set[str] = set()
for s in (detected_skills or [s.strip() for s in (manual or "").split(",") if s.strip()]):
    add = s.strip()
    if add and add.lower() not in seen_lower:
        seen_lower.add(add.lower())
        skills_for_picker.append(add)

if skills_for_picker:
    with st.expander("Grade your skills (optional)", expanded=False):
        st.caption(
            "The skill ladder replaces a binary match with five levels "
            "(None → Expert). Each row nudges the JD score, weekly "
            "roadmap length, and the record exported to history."
        )
        columns = st.columns(2)
        for idx, skill in enumerate(skills_for_picker[:20]):
            current_label = proficiency.get(skill, {}).get("label", "Beginner")
            with columns[idx % 2]:
                proficiency_overrides[skill] = st.selectbox(
                    skill,
                    [lvl["name"] for lvl in PRO_LEVELS],
                    index=[lvl["name"] for lvl in PRO_LEVELS].index(current_label),
                    key=f"pro_{skill}",
                )

proficiency = attach_manual_proficiency(
    proficiency,
    [(skill, label) for skill, label in proficiency_overrides.items()],
)

st.markdown(
    "<div class='eyebrow' style='margin-top:1rem'>Job description</div>"
    "<h2 style='margin:.1rem 0 .5rem'>Match the resume against a specific JD</h2>",
    unsafe_allow_html=True,
)
jd_left, jd_right = st.columns([1, 1])
with jd_left:
    jd_pdf = st.file_uploader(
        "Upload JD (PDF)", type=["pdf"], key="in_jd_pdf",
        help="Optional — paste is preferred for pasted JDs.",
    )
with jd_right:
    jd_text_input = st.text_area(
        "…or paste JD text",
        height=160,
        placeholder="Paste the JD here (skills, tenure, responsibilities)",
        key="in_jd_text",
    )

weekly_hours = st.slider(
    "Hours per week you can study", 2, 24, 8, key="in_weekly_hours",
    help="Drives the weekly learning roadmap length.",
)

# Parse JD inputs (independent of Run so we can show detected skills live).
parsed_jd_input: dict | None = None
if jd_pdf is not None:
    try:
        with st.spinner("Parsing JD PDF..."):
            parsed_jd_input = parse_jd_pdf(jd_pdf)
    except Exception as exc:                                   # pragma: no cover
        st.warning(f"Could not parse JD PDF: {exc}")
elif (jd_text_input or "").strip():
    parsed_jd_input = parse_jd_text(jd_text_input)

if parsed_jd_input and (parsed_jd_input.get("raw_text") or "").strip():
    chips = "".join(
        pill(s) for s in (parsed_jd_input.get("skills") or [])[:18]
    ) or '<span class="pill">No recognised skills in JD yet</span>'
    sub_parts: list[str] = []
    if parsed_jd_input.get("title"):
        sub_parts.append(f"<b>{parsed_jd_input['title']}</b>")
    if parsed_jd_input.get("min_years") or parsed_jd_input.get("max_years"):
        rng = []
        if parsed_jd_input.get("min_years") is not None:
            rng.append(f"min {parsed_jd_input['min_years']}y")
        if parsed_jd_input.get("max_years") is not None:
            rng.append(f"max {parsed_jd_input['max_years']}y")
        sub_parts.append(" · ".join(rng))
    sub_html = " &middot; ".join(sub_parts)
    st.markdown(
        f'<div class="card fade-up" style="margin-top:.5rem">'
        f'<div class="card-t">Parsed JD preview</div>'
        f'<div class="card-s">{sub_html or "Title / tenure not detected"}</div>'
        f'<div style="margin-top:.6rem">{chips}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


st.markdown("")
predict_clicked = st.button(
    "Run Prediction", type="primary", use_container_width=True, key="btn_run",
)



def _segments(items: list[dict]) -> str:
    palette = ["#d49966", "#e3b389", "#a4c2b0", "#7fb88b", "#6cd0e4"]
    out = []
    for idx, row in enumerate(items):
        weeks = row["weeks"]
        color = palette[idx % len(palette)]
        out.append(
            f'<div title="{row["skill"]} · {row["start_level"]} → Expert ({weeks}w)" '
            f'style="background:{color};width:max(.6rem,{weeks*1.6}rem);height:.65rem;'
            f'margin-right:.18rem;border-radius:.5rem"></div>'
        )
    return "".join(out)


def _compute_prediction() -> dict | None:
    """Compute the full prediction bundle and return it. Returns None on
    unrecoverable input errors (and renders the empty state inline)."""
    if uploaded is not None:
        skills_list = detected_skills or [s.strip() for s in (manual or "").split(",") if s.strip()]
    else:
        skills_list = [s.strip() for s in (manual or "").split(",") if s.strip()]
        detected_skills_local = []
    if not skills_list:
        empty_state("🛠", "No skills yet", "Add skills in the textarea or upload a resume to continue.")
        return None

    valid, invalid = validate_skills(skills_list, skills_encoder)
    if not valid:
        empty_state(
            "", "No recognised skills",
            "Try common terms like Python, SQL, React, Docker.",
        )
        return None

    local_prof = attach_manual_proficiency(
        proficiency,
        [(skill, label) for skill, label in proficiency_overrides.items()],
    )

    user_domain = detect_domain(valid)
    jobs, scores, job_explanations = predict_job_role(
        education,
        experience,
        valid,
        user_domain,
        return_details=True,
    )
    if len(jobs) < 3:
        empty_state(
            "", "Prediction unavailable",
            "The model could not rank enough roles for this profile.",
        )
        return None

    rec = CAREER_RECOMMENDATIONS.get(user_domain, {}) or {}
    gap = skill_gap(rec.get("required_skills", []) or [], valid)
    matched = matched_skills(rec.get("required_skills", []) or [], valid)
    summary = summarize_profile(valid)

    detected_loc = extract_location_from_text(resume_text or "")
    effective_loc = (location_input or detected_loc or "India").strip()
    effective_country = location_country_hint(effective_loc) or effective_loc

    # JD match (recompute from current inputs).
    jd_payload = None
    parsed_jd = parsed_jd_input
    if parsed_jd and (parsed_jd.get("raw_text") or "").strip():
        overall = jd_overall_score(
            candidate_proficiency=local_prof,
            jd_skills=parsed_jd["skills"],
            candidate_exp=experience,
            jd_min_years=parsed_jd.get("min_years"),
            jd_max_years=parsed_jd.get("max_years"),
            education=education,
        )
        jd_payload = {
            "parsed": {
                "title": parsed_jd.get("title"),
                "skills": parsed_jd.get("skills"),
                "min_years": parsed_jd.get("min_years"),
                "max_years": parsed_jd.get("max_years"),
                "raw_text": parsed_jd.get("raw_text") or "",
            },
            "overall": overall,
        }

    target_skills = jd_payload["overall"]["missing"] if jd_payload else gap
    roadmap = build_weekly_roadmap(
        gap_skills=target_skills,
        candidate_proficiency=local_prof,
        weekly_hours=weekly_hours,
    )

    return {
        "candidate_name": candidate_name or "Anonymous",
        "education": education,
        "experience_years": experience,
        "valid": valid,
        "invalid": invalid,
        "proficiency": local_prof,
        "domain": user_domain,
        "jobs": jobs,
        "scores": scores,
        "job_explanations": job_explanations,
        "resume_text": resume_text or "",
        "rec": rec,
        "gap": gap,
        "matched_skills": matched,
        "summary": summary,
        "jd_payload": jd_payload,
        "roadmap": roadmap,
        "effective_loc": effective_loc,
        "effective_country": effective_country,
        "weekly_hours": weekly_hours,
    }


if predict_clicked:
    computed = _compute_prediction()
    if computed is not None:
        st.session_state["prediction"] = computed
        st.session_state["save_msg"] = None
    


pred = st.session_state.get("prediction")

# If the user wants to re-run, they press Run again — meanwhile we always
# render whatever's cached so frequent interactions don't lose the view.
if pred is None:
    st.markdown(
        '<div class="card fade-up" style="background:rgba(127,184,139,.16);'
        'border-color:rgba(127,184,139,.38);color:#dff3e4">'
        'Fill in the profile, optionally drop in a JD, then press '
        '<b>Run Prediction</b>. The result stays visible across every '
        'interaction — including clicking <b>Save this candidate to history</b>.'
        '</div>',
        unsafe_allow_html=True,
    )
    st.stop()

valid = pred["valid"]
invalid = pred["invalid"]
proficiency = pred["proficiency"]
user_domain = pred["domain"]
jobs = pred["jobs"]
scores = pred["scores"]
job_explanations = pred.get("job_explanations") or {}
resume_text_cached = pred.get("resume_text") or ""
rec = pred["rec"]
gap = pred["gap"]
matched = pred["matched_skills"]
summary = pred["summary"]
jd_payload = pred["jd_payload"]
roadmap = pred["roadmap"]
effective_loc = pred["effective_loc"]
effective_country = pred["effective_country"]
weekly_hours = pred["weekly_hours"]

# Save banner (sticky across reruns).
msg = st.session_state.get("save_msg")
if isinstance(msg, dict):
    cls = "success" if msg["kind"] == "success" else ("error" if msg["kind"] == "error" else "info")
    bg = "rgba(127,184,139,.16)" if cls == "success" else (
        "rgba(216,122,106,.18)" if cls == "error" else "rgba(212,153,102,.16)"
    )
    border = "rgba(127,184,139,.38)" if cls == "success" else (
        "rgba(216,122,106,.4)" if cls == "error" else "rgba(212,153,102,.38)"
    )
    color = "#dff3e4" if cls == "success" else ("#ffd9d3" if cls == "error" else "#f1dfc6")
    st.markdown(
        f'<div class="card fade-up" style="background:{bg};border-color:{border};'
        f'color:{color};margin-bottom:.4rem">{msg["text"]}</div>',
        unsafe_allow_html=True,
    )

k1, k2, k3, k4 = st.columns(4)
with k1: kpi_card("Skills matched", str(len(valid)), None, icon="✅")
with k2: kpi_card("Skills ignored", str(len(invalid)), None, icon="⚠️")
with k3: kpi_card("Experience", f"{experience} yrs", None, icon="💼")
with k4: kpi_card("Top match", jobs[0] if jobs else "—", None, icon="🏆")

st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)

tax_node = resolve_hierarchical_role(jobs[0] if jobs else "")
st.markdown(
    f'<div class="card fade-up" style="display:flex;align-items:center;gap:1rem;flex-wrap:wrap">'
    f'<div><div class="card-s">Hierarchical Taxonomy & Domain</div>'
    f'<div style="font-size:1.15rem;font-weight:650;margin-top:.2rem">{user_domain} › {tax_node["family"]}</div>'
    f'<div style="font-size:.85rem;color:#7aa597;margin-top:.1rem">O*NET SOC {tax_node["onet_code"]} · {tax_node["level"]}</div>'
    f'</div>'
    f'<div style="flex:1;min-width:240px"><div class="card-s">Candidate embedding summary</div>'
    f'<div style="margin-top:.2rem">{get_taxonomy_breadcrumbs(jobs[0] if jobs else "")}. Profile vector encodes role, 384d dense embeddings / skills, experience, and education.</div>'
    f'</div></div>',
    unsafe_allow_html=True,
)


st.markdown(
    "<div class='eyebrow' style='margin-top:1.2rem'>Top job predictions</div>"
    "<h2 style='margin:.1rem 0 .6rem'>Your top three matches</h2>",
    unsafe_allow_html=True,
)
p1, p2, p3 = st.columns(3)
for col, (rank, job, score_pct) in zip(
    [p1, p2, p3],
    [(1, jobs[0], scores[0]), (2, jobs[1], scores[1]), (3, jobs[2], scores[2])],
):
    with col:
        prediction_card(rank, job, score_pct / 100.0)
        explain = job_explanations.get(job) or {}
        with st.expander("Why this match"):
            matched_skill_pills = "".join(
                pill(skill, "success") for skill in explain.get("matched_skills", [])
            ) or pill("No matched skills detected yet")
            missing_skill_pills = "".join(
                pill(skill, "warn") for skill in explain.get("missing_skills", [])
            ) or pill("No missing skills", "success")
            st.markdown(
                f'<div class="card" style="margin-bottom:.5rem">'
                f'<div class="card-t">Matched skills</div>'
                f'<div style="margin-top:.45rem">{matched_skill_pills}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="card" style="margin-bottom:.5rem">'
                f'<div class="card-t">Missing skills</div>'
                f'<div style="margin-top:.45rem">{missing_skill_pills}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            model_rank = explain.get("model_rank")
            pool_size = explain.get("candidate_pool_size")
            model_rank_text = (
                f'#{model_rank} of {pool_size}' if model_rank and pool_size else 'n/a'
            )
            st.caption(
                f"Coverage {explain.get('coverage_pct', 0.0):.1f}% · "
                f"Breadth {explain.get('breadth_pct', 0.0):.1f}% · "
                f"Model rank {model_rank_text}"
            )

st.plotly_chart(build_top3_chart(jobs, scores), use_container_width=True, theme=None)

# Career paths
if rec:
    st.markdown(
        "<div class='eyebrow' style='margin-top:1rem'>Suggested roles</div>"
        "<h2 style='margin:.1rem 0 .6rem'>Recommended career paths</h2>",
        unsafe_allow_html=True,
    )
    primary_cols = st.columns(len(rec.get("primary", [])) or 1)
    for col, item in zip(primary_cols, rec.get("primary", [])):
        with col:
            st.markdown(
                f'<div class="card" style="text-align:center;padding:1.3rem .75rem">'
                f'<div style="font-weight:600;margin-top:.3rem">{item}</div></div>',
                unsafe_allow_html=True,
            )
    if rec.get("secondary"):
        pills_html = "".join(
            f'<span class="pill" style="margin:.2rem;display:inline-block">{c}</span>'
            for c in rec["secondary"]
        )
        st.markdown(
            f'<div class="card" style="margin-top:.5rem"><div class="card-s">Other suitable careers</div>'
            f'<div style="margin-top:.5rem">{pills_html}</div></div>',
            unsafe_allow_html=True,
        )

# Skill coverage 
st.markdown(
    "<div class='eyebrow' style='margin-top:1rem'>Coverage</div>"
    "<h2 style='margin:.1rem 0 .6rem'>Skill coverage by category</h2>",
    unsafe_allow_html=True,
)
cols = st.columns(len(summary))
for col, (cat, info) in zip(cols, summary.items()):
    with col:
        coverage_card(cat, info["matched"], info["total"])

# Skill gap 
st.markdown(
    "<div class='eyebrow' style='margin-top:1rem'>Skill gap</div>"
    "<h2 style='margin:.1rem 0 .6rem'>What to learn vs. strengths</h2>",
    unsafe_allow_html=True,
)
g1, g2 = st.columns(2)
with g1:
    st.markdown(
        '<div class="card"><div class="card-t">Skills to learn</div>'
        '<div class="card-s">Fills the gap for your target domain</div>'
        '<div style="margin-top:.5rem">'
        + (
            "".join(
                f'<span class="pill warn" style="margin:.2rem;display:inline-block">{s}</span>'
                for s in gap
            )
            if gap else
            '<span class="pill success" style="margin:.2rem;display:inline-block">You already have everything.</span>'
        )
        + '</div></div>',
        unsafe_allow_html=True,
    )
with g2:
    st.markdown(
        '<div class="card"><div class="card-t">Strengths</div>'
        '<div class="card-s">Skills already in your toolkit</div>'
        '<div style="margin-top:.5rem">'
        + (
            "".join(
                f'<span class="pill success" style="margin:.2rem;display:inline-block">{s}</span>'
                for s in matched
            )
            if matched else
            '<span class="pill" style="margin:.2rem;display:inline-block">Add more skills to see strengths</span>'
        )
        + '</div></div>',
        unsafe_allow_html=True,
    )

# Proficiency ladder 
st.markdown(
    "<div class='eyebrow' style='margin-top:1.2rem'>Proficiency ladder</div>"
    "<h2 style='margin:.1rem 0 .6rem'>Graded skill proficiency (not just present/absent)</h2>",
    unsafe_allow_html=True,
)
ladder_rows = []
detected_set = {s.lower() for s in valid}
for skill in valid[:20]:
    info = proficiency.get(skill, {})
    ladder_rows.append({
        "Skill": skill,
        "Detected": "Yes" if skill.lower() in detected_set else "—",
        "Initial signal": info.get("label", "Beginner"),
        "Weight": round(float(info.get("weight", 0.0)), 2),
        "Evidence": ", ".join(info.get("evidence", [])[:3]) or "no explicit signal",
    })
if ladder_rows:
    st.dataframe(pd.DataFrame(ladder_rows), use_container_width=True, hide_index=True, height=320)
st.caption("Scale: None → Beginner (0.25) → Intermediate (0.55) → Advanced (0.80) → Expert (1.00)")

# JD match 
st.markdown(
    "<div class='eyebrow' style='margin-top:1.2rem'>JD match</div>"
    "<h2 style='margin:.1rem 0 .6rem'>Resume ↔ specific job description</h2>",
    unsafe_allow_html=True,
)

if jd_payload:
    overall = jd_payload["overall"]
    k1, k2, k3, k4 = st.columns(4)
    with k1: kpi_card("Overall match", f"{overall['overall_match_pct']:.1f}%", "blended", icon="🎯")
    with k2: kpi_card("Skill fit", f"{overall['skill_pct']:.1f}%", "weighted", icon="🛠")
    with k3: kpi_card("Experience fit", f"{overall['experience_pct']:.1f}%", f"{experience} yrs", icon="⏱")
    with k4: kpi_card("Education fit", f"{overall['education_pct']:.1f}%", education, icon="🎓")

    col_a, col_b = st.columns(2)
    matched_pills = "".join(pill(s, "success") for s in overall["matched"]) or pill("No overlap")
    missing_pills = "".join(pill(s, "warn") for s in overall["missing"]) or '<span class="pill success">No missing skills</span>'
    with col_a:
        st.markdown(
            f'<div class="card"><div class="card-t">Covered ({len(overall["matched"])})</div>'
            f'<div class="card-s">Weighted by proficiency</div>'
            f'<div style="margin-top:.5rem">{matched_pills}</div></div>',
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            f'<div class="card"><div class="card-t">Gap ({len(overall["missing"])})</div>'
            f'<div class="card-s">Candidate is missing these JD skills</div>'
            f'<div style="margin-top:.5rem">{missing_pills}</div></div>',
            unsafe_allow_html=True,
        )

    if (jd_payload.get("parsed") or {}).get("title"):
        st.caption(f"Detected JD title: {jd_payload['parsed']['title']}")
    if (jd_payload.get("parsed") or {}).get("min_years") or (jd_payload.get("parsed") or {}).get("max_years"):
        yr = []
        if (jd_payload["parsed"].get("min_years") is not None): yr.append(f"min {jd_payload['parsed']['min_years']}")
        if (jd_payload["parsed"].get("max_years") is not None): yr.append(f"max {jd_payload['parsed']['max_years']}")
        st.caption("Tenure: " + " · ".join(yr) + " yrs")
else:
    st.markdown(
        '<div class="card fade-up" style="background:rgba(212,153,102,.12);'
        'border-color:rgba(212,153,102,.32);color:#f1dfc6">'
        'No JD provided — paste or upload one above, then press '
        '<b>Run Prediction</b> again to see a tailored match score.</div>',
        unsafe_allow_html=True,
    )

# Weekly learning roadmap 
st.markdown(
    "<div class='eyebrow' style='margin-top:1.2rem'>Learning roadmap</div>"
    "<h2 style='margin:.1rem 0 .6rem'>Weekly plan to fill the skill gap</h2>",
    unsafe_allow_html=True,
)
rm1, rm2, rm3 = st.columns(3)
with rm1: kpi_card("Total weeks", str(roadmap["total_weeks"]), "to close the gap", icon="🗓")
with rm2: kpi_card("Total hours", str(roadmap["total_hours"]), f"{weekly_hours}h / week", icon="⏳")
with rm3: kpi_card("Skills covered", str(len(roadmap["per_skill"])), "in your plan", icon="📘")

if roadmap["per_skill"]:
    segments = _segments(roadmap["per_skill"])
    st.markdown(
        f'<div class="card" style="margin-top:.6rem">'
        f'<div class="card-t">Skill budget</div>'
        f'<div class="card-s">Each block = weeks allocated per skill (colour rotated)</div>'
        f'<div style="display:flex;flex-wrap:wrap;margin-top:.7rem">{segments}</div>'
        f'<div style="margin-top:.7rem;display:flex;flex-wrap:wrap;gap:.6rem;font-size:.78rem;color:var(--text-soft)">'
        + "".join(
            f'<span><span style="display:inline-block;width:.55rem;height:.55rem;background:{["#d49966","#e3b389","#a4c2b0","#7fb88b","#6cd0e4"][i % 5]};border-radius:50%;margin-right:.25rem"></span>{row["skill"]} <span style="opacity:.75">({row["weeks"]}w)</span></span>'
            for i, row in enumerate(roadmap["per_skill"])
        )
        + '</div></div>',
        unsafe_allow_html=True,
    )

    week_df = pd.DataFrame(roadmap["items"])
    week_df.columns = ["Week", "Skill", "Milestone", "Hours", "Starting level"]
    st.dataframe(week_df, use_container_width=True, hide_index=True, height=320)


st.markdown(
    "<div class='eyebrow' style='margin-top:1.2rem'>Save candidate</div>"
    "<h2 style='margin:.1rem 0 .6rem'>Persist to recruiter-visible history</h2>",
    unsafe_allow_html=True,
)
st.caption(
    "Save reads from the cached prediction above — it never re-runs or "
    "collapses the result. After saving, open the Recruiter Mode tab to "
    "compare this candidate against any JD."
)

if st.button(
    "Save this candidate to history",
    type="primary",
    use_container_width=True,
    key="btn_save_candidate",
):
    try:
        cid = record_candidate_from_session(
            candidate_name=pred["candidate_name"],
            education=pred["education"],
            experience_years=pred["experience_years"],
            validated_skills=pred["valid"],
            ignored_skills=pred["invalid"],
            domain=pred["domain"],
            top_jobs=[{"title": j, "confidence": float(s)} for j, s in zip(pred["jobs"], pred["scores"])],
            missing_skills=pred["gap"],
            matched_skills=pred["matched_skills"],
            proficiency_map=pred["proficiency"],
            resume_text=pred.get("resume_text") or "",
            jd_text=(pred.get("jd_payload") or {}).get("parsed", {}).get("raw_text", ""),
            jd_match=(pred.get("jd_payload") or {}).get("overall", {}),
            roadmap_total_weeks=pred["roadmap"]["total_weeks"],
            overall_pct=float(
                (pred.get("jd_payload") or {}).get("overall", {}).get("overall_match_pct")
                or pred["scores"][0]
            ),
        )
        st.session_state["save_msg"] = {
            "kind": "success",
            "text": f"✅ Saved — candidate id <code>{cid}</code>. Open "
                    f"<b>Recruiter Mode</b> in the sidebar to compare this "
                    f"candidate against any JD.",
        }
    except Exception as exc:                                     # pragma: no cover
        st.session_state["save_msg"] = {
            "kind": "error",
            "text": f"❌ Save failed: {exc}",
        }

# Career info 
best = jobs[0]
try:
    _career_info = read_csv_cached("career/career_info.csv")
except Exception:
    _career_info = pd.DataFrame()
if not _career_info.empty:
    row_info = _career_info[_career_info["Job Role"] == best]
    if not row_info.empty:
        st.markdown(
            "<div class='eyebrow' style='margin-top:1rem'>Career info</div>"
            "<h2 style='margin:.1rem 0 .6rem'>Recommended role details</h2>",
            unsafe_allow_html=True,
        )
        c1, c2 = st.columns([1.6, 1])
        with c1:
            st.markdown(
                f'<div class="card">'
                f'<div class="card-s">Recommended role</div>'
                f'<h2 style="margin:.2rem 0">{best}</h2>'
                f'<div class="card-s" style="margin-top:.6rem">Description</div>'
                f'<p style="margin:.2rem 0;line-height:1.6">{row_info.iloc[0]["Description"]}</p>'
                f'<div class="card-s" style="margin-top:.6rem">Recommended skills</div>'
                f'<p style="margin:.2rem 0">{row_info.iloc[0]["Recommended Skills"]}</p>'
                f'<div class="card-s" style="margin-top:.6rem">Career path</div>'
                f'<p style="margin:.2rem 0">{row_info.iloc[0]["Career Path"]}</p></div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown('<div class="card"><div class="card-t">Profile snapshot</div>', unsafe_allow_html=True)
            st.markdown(f"**Education:** {education}")
            st.markdown(f"**Experience:** {experience} years")
            st.markdown(f"**Domain:** {user_domain}")
            st.markdown(f"**Recognised skills:** {', '.join(valid) or '—'}")
            if invalid:
                st.markdown(f"**Ignored:** {', '.join(invalid)}")
            st.markdown("</div>", unsafe_allow_html=True)

# Job portals 
recs = recommend_portals(
    role=jobs[0],
    skills=valid,
    location=effective_loc,
    experience=experience,
    domain=user_domain,
    location_hint=effective_loc,
)
primary = primary_recommendation(recs)

st.markdown(
    "<div class='eyebrow' style='margin-top:1.2rem'>Where to apply</div>"
    "<h2 style='margin:.1rem 0 .4rem'>Recommended free job portals</h2>"
    f"<div class='card-s'>Pre-filled live search links for <strong>{jobs[0]}</strong> in <strong>{effective_loc}</strong> — open each portal to see real-time postings.</div>",
    unsafe_allow_html=True,
)

if primary:
    st.markdown(
        f'<div class="card fade-up" style="display:flex;gap:1rem;flex-wrap:wrap;align-items:center;background:linear-gradient(135deg,rgba(212,153,102,.12),rgba(164,194,176,.08))">'
        f'<div style="flex:1;min-width:220px">'
        f'<div class="card-s">Top recommendation</div>'
        f'<div style="font-size:1.15rem;font-weight:650;margin-top:.2rem">Apply on {primary["name"]}</div>'
        f'<div class="card-s" style="margin-top:.25rem">{primary["region"]} &middot; fit score {primary["fit_score"]}%</div>'
        f'<div style="margin-top:.4rem;color:var(--text-soft);font-size:.88rem">{primary["fit_reason"]}</div></div>'
        f'<a href="{primary["url"]}" target="_blank" rel="noopener noreferrer">'
        f'<button class="apply-cta">Open on {primary["name"]} &rarr;</button></a>'
        f'</div>',
        unsafe_allow_html=True,
    )

portal_cols = st.columns(len(recs))
for col, r in zip(portal_cols, recs):
    with col:
        st.markdown(
            f'<div class="card portal-card" style="height:100%">'
            f'<div style="display:flex;justify-content:flex-end;align-items:center;margin-bottom:.4rem">'
            f'<span class="pill" style="font-size:.72rem">Fit {r["fit_score"]}%</span></div>'
            f'<div style="font-weight:650;font-size:1rem">{r["name"]}</div>'
            f'<div class="card-s" style="margin-top:.15rem">{r["region"]}</div>'
            f'<div style="margin-top:.55rem;color:var(--text-soft);font-size:.86rem;line-height:1.5;min-height:62px">{r["fit_reason"]}</div>'
            f'<div class="card-s" style="margin-top:.5rem"><strong>Best for:</strong> {r["apply_hint"]}</div>'
            f'<a href="{r["url"]}" target="_blank" rel="noopener noreferrer" style="display:inline-block;margin-top:.8rem;text-decoration:none">'
            f'<button class="apply-btn">Open live search &rarr;</button></a>'
            f'</div>',
            unsafe_allow_html=True,
        )

context_chips = "".join([
    f'<span class="pill accent" style="margin:.2rem;display:inline-block">{len(valid)} skills</span>',
    f'<span class="pill" style="margin:.2rem;display:inline-block">Location: {effective_loc} ({effective_country or "global"})</span>',
    f'<span class="pill" style="margin:.2rem;display:inline-block">Experience: {experience} yrs</span>',
    f'<span class="pill" style="margin:.2rem;display:inline-block">Domain: {user_domain}</span>',
])
st.markdown(
    f'<div class="card" style="margin-top:.6rem"><div class="card-s">Ranking factors</div>'
    f'<div style="margin-top:.5rem">{context_chips}</div></div>',
    unsafe_allow_html=True,
)
st.caption("Free portal deep-links · Live listings opened in a new tab. Counts and exact matches are shown on each portal's live page.")

# Semantic job matching 
st.markdown(
    "<div class='eyebrow' style='margin-top:1.3rem'>Semantic engine</div>"
    "<h2 style='margin:.1rem 0 .5rem'>Ranked live job postings by fit score</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "<div class='card fade-up' style='background:linear-gradient(135deg,rgba(164,194,176,.10),rgba(212,153,102,.08))'>"
    "<div class='card-t'>How matching works</div>"
    "<div class='card-s'>We build a candidate embedding from validated skills, predicted role, education, and experience. "
    "We score live postings using dense 384-dimensional vector embeddings (SentenceTransformers 'all-MiniLM-L6-v2') or TF-IDF, "
    "blended with title alignment, skill overlap, and experience fit signals.</div>"
    "</div>",
    unsafe_allow_html=True,
)

scorer_choice = st.selectbox(
    "Semantic Scorer Engine",
    ["Dense Vector Embeddings (all-MiniLM-L6-v2)", "TF-IDF Vectorizer"],
    index=0,
    help="Dense vector embeddings evaluate 384d semantic similarity; TF-IDF evaluates n-gram term frequency.",
)
scorer_key = "embeddings" if "Embeddings" in scorer_choice else "cosine"

with st.spinner("Fetching live jobs and computing semantic fit scores..."):
    live_jobs = fetch_live_jobs(
        role=jobs[0],
        skills=valid,
        location=effective_loc,
        limit_per_provider=12,
    )
    semantic_matches = rank_job_matches(
        predicted_role=jobs[0],
        skills=valid,
        experience_years=experience,
        jobs=live_jobs,
        education=education,
        domain=user_domain,
        scorer_name=scorer_key,
        top_k=8,
    )

provider_df = pd.DataFrame(provider_status_rows())
p1, p2, p3, p4 = st.columns(4)
with p1: kpi_card("Providers", str(len(provider_df)), "4 zero-key feeds live", icon=None)
with p2: kpi_card("Live postings", str(len(live_jobs)), "deduplicated", icon=None)
with p3: kpi_card("Top fit", f"{semantic_matches[0]['fit_score']:.1f}%" if semantic_matches else "—", "blended score", icon=None)
with p4: kpi_card("Top-job gaps", str(len(semantic_matches[0]["missing_skills"])) if semantic_matches else "0", "skills to add", icon=None)

if semantic_matches:
    st.markdown(
        "<div class='eyebrow' style='margin-top:1rem'>Top live matches</div>"
        "<h2 style='margin:.1rem 0 .6rem'>Explainable ranking breakdown</h2>",
        unsafe_allow_html=True,
    )

    
    st.markdown(
        '<div class="card fade-up" style="margin-bottom:.6rem">'
        '<div class="card-t">Live feeds</div>'
        '<div class="card-s">Each card below shows the real hiring company and a '
        'verified Apply link pulled straight from a live job board.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    chips = "".join(
        f'<span class="pill accent" style="margin:.2rem">{r["Provider"]} <strong>·</strong> {r["Status"]}</span>'
        for r in provider_status_rows()
    )
    st.markdown(f'<div class="card" style="padding:.55rem .9rem">{chips}</div>', unsafe_allow_html=True)

    # ----- Compare table for the math-transparency view -----
    match_table = pd.DataFrame([
        {
            "Rank": idx,
            "Job": m["title"],
            "Company": m["company"],
            "Location": m["location"],
            "Source": m["source"],
            "Fit Score": f"{m['fit_score']:.1f}%",
            "Semantic": f"{m['semantic_score']:.1f}%",
            "Title Align": f"{m['title_alignment_score']:.1f}%",
            "Overlap": f"{m['skill_overlap_ratio']:.1f}%",
            "Experience": f"{m['experience_score']:.1f}%",
            "Salary": m["salary"] or "—",
        }
        for idx, m in enumerate(semantic_matches, start=1)
    ])
    st.dataframe(match_table, use_container_width=True, hide_index=True)

    
    render_live_job_cards(semantic_matches)

st.caption(f"{BRAND['name']} · Predictions powered by 7 trained classifiers")

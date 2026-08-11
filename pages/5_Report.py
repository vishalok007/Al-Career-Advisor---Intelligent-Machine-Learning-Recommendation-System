"""Report page — exec summary + multi-format export."""
from __future__ import annotations
from pathlib import Path
import sys, json

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from utils.constants import BRAND, EDUCATION_LEVELS
from utils.helpers import (
    inject_css, page_header, kpi_card, read_csv_cached,
)
from utils.predictor import (
    load_models, predict_job_role, validate_skills, summarize_profile,
    skill_gap, matched_skills,
)
from career.recommendations import CAREER_RECOMMENDATIONS
from career.career_domains import detect_domain
from components import render_sidebar

inject_css("assets/styles.css")
render_sidebar("Report")
page_header(
    "Career Report",
    "Generate an executive summary you can share with mentors or recruiters.",
    eyebrow="One-click exports · recruiter-ready",
)

models_pkg = load_models()
skills_encoder = models_pkg["skills_encoder"]

# Inputs — form for cleanliness
with st.form("report_form"):
    ic1, ic2 = st.columns(2)
    with ic1: education = st.selectbox("Education", EDUCATION_LEVELS, index=2)
    with ic2: experience = st.slider("Experience (years)", 0, 30, 3)
    manual = st.text_area("Skills (comma-separated)", placeholder="Python, SQL, Docker")
    cand = st.text_input("Candidate name", placeholder="e.g. Priya Sharma")
    submitted = st.form_submit_button("Generate Report", type="primary",
                                       use_container_width=True)

if not submitted:
    st.markdown(
        '<div class="card fade-up" style="background:rgba(127,184,139,.16);border-color:rgba(127,184,139,.38);color:#dff3e4">'
        'Fill in the form and tap <b>Generate Report</b> above.</div>',
        unsafe_allow_html=True,
    )
    st.stop()

raw = [s.strip() for s in manual.split(",") if s.strip()]
valid, invalid = validate_skills(raw, skills_encoder)
if not valid:
    st.error("Please enter at least one recognised skill.")
    st.stop()

domain = detect_domain(valid)
jobs, scores = predict_job_role(education, experience, valid, domain)
rec = CAREER_RECOMMENDATIONS.get(domain, {})
gap = skill_gap(rec.get("required_skills", []), valid)
matched = matched_skills(rec.get("required_skills", []), valid)
candidate_name = cand or "Candidate"

# Exec summary KPI strip
st.markdown(f"## Executive Summary — {candidate_name}")
k1, k2, k3, k4, k5 = st.columns(5)
with k1: kpi_card("Detected Domain", domain, None, icon="🧭")
with k2: kpi_card("Top Match", jobs[0], f"{scores[0]:.1f}%", icon="🏆")
with k3: kpi_card("Skills Validated", str(len(valid)), None, icon="✅")
with k4: kpi_card("Skills to Learn", str(len(gap)), None, icon="📘")
with k5: kpi_card("Strengths", str(len(matched)), None, icon="💪")

st.markdown(
    f'<div class="card fade-up">'
    f'<div class="card-t">Narrative</div>'
    f'<p style="margin:.35rem 0 0;line-height:1.6">{candidate_name} is best aligned with the '
    f'<b>{domain}</b> domain after {experience} years of experience. Their top recommendation is '
    f'<b>{jobs[0]}</b> ({scores[0]:.1f}% confidence), supported by {len(matched)} matching skills '
    f'and an opportunity to up-skill in {len(gap)} additional capabilities.</p></div>',
    unsafe_allow_html=True,
)

# Skill gap L→R
import pandas as pd
st.markdown("<div class='eyebrow' style='margin-top:1.2rem'>Skill analysis</div>"
            "<h2 style='margin:.1rem 0 .6rem'>Skill gap and coverage</h2>",
            unsafe_allow_html=True)
c1, c2 = st.columns([1.3, 1])
with c1:
    st.markdown('<div class="card"><div class="card-t">Gap / strengths</div>', unsafe_allow_html=True)
    df_gap = pd.DataFrame({
        "Status": ["Strength"] * len(matched) + ["To Learn"] * len(gap),
        "Skill": matched + gap,
    })
    st.dataframe(df_gap, use_container_width=True, hide_index=True, height=300)
    st.markdown("</div>", unsafe_allow_html=True)
with c2:
    st.markdown('<div class="card"><div class="card-t">Coverage by category</div>', unsafe_allow_html=True)
    summary = summarize_profile(valid)
    df_cov = pd.DataFrame([
        {"Category": k, "Matched": v["matched"], "Total": v["total"]}
        for k, v in summary.items()
    ])
    st.dataframe(df_cov, use_container_width=True, hide_index=True, height=300)
    st.markdown("</div>", unsafe_allow_html=True)

# Exports 
profile = {
    "candidate": candidate_name,
    "education": education,
    "experience_years": experience,
    "skills_validated": valid,
    "skills_ignored": invalid,
    "domain": domain,
    "top_predictions": [{"job": j, "confidence": float(s)}
                        for j, s in zip(jobs, scores)],
    "skill_gap": gap,
    "matched_skills": matched,
}

st.markdown("<div class='eyebrow' style='margin-top:1.4rem'>Exports</div>"
            "<h2 style='margin:.1rem 0 .6rem'>Share with recruiters</h2>",
            unsafe_allow_html=True)

slug = (candidate_name or "candidate").lower().replace(" ", "_")
dt1, dt2 = st.columns(2)
with dt1:
    st.download_button(
        label="JSON Profile",
        data=json.dumps(profile, indent=2).encode("utf-8"),
        file_name=f"{slug}_report.json", mime="application/json",
        use_container_width=True,
    )

text_lines = [
    f"AI CAREER ADVISOR — REPORT",
    f"Generated for: {profile['candidate']}",
    "",
    f"EDUCATION       : {profile['education']}",
    f"EXPERIENCE (yrs): {profile['experience_years']}",
    f"DOMAIN          : {profile['domain']}",
    "",
    "TOP PREDICTIONS", "-" * 40,
]
for i, row in enumerate(profile["top_predictions"]):
    text_lines.append(f"  #{i+1}  {row['job']:<32} {row['confidence']:5.1f}%")
text_lines.append("")
text_lines.append("SKILLS VALIDATED   : " + ", ".join(profile["skills_validated"]))
if profile["skills_ignored"]:
    text_lines.append("SKILLS IGNORED     : " + ", ".join(profile["skills_ignored"]))
text_lines.append("MATCHED SKILLS     : " + ", ".join(profile["matched_skills"]))
text_lines.append("SKILL GAP          : " + ", ".join(profile["skill_gap"]))
text_report = "\n".join(text_lines)
with dt2:
    st.download_button(
        label="Text Report",
        data=text_report.encode("utf-8"),
        file_name=f"{slug}_report.txt", mime="text/plain",
        use_container_width=True,
    )

# HTML print-to-PDF 
html = f"""<!doctype html>
<html><head><meta charset=utf-8><title>{candidate_name} — Career Report</title>
<style>
  body{{font-family:-apple-system,Inter,'Segoe UI',sans-serif;background:#0d1f1b;color:#f5ede0;margin:0;padding:2rem}}
  .wrap{{max-width:760px;margin:0 auto;background:#15342e;padding:2rem 2.2rem;border:1px solid #2c564c;border-radius:18px;box-shadow:0 12px 32px rgba(0,0,0,.4)}}
  h1{{margin:0 0 .2rem;font-size:1.8rem;letter-spacing:-.02em}}
  h2{{margin:1.4rem 0 .4rem;font-size:1.1rem;color:#a4c2b0;border-bottom:1px solid #2c564c;padding-bottom:.4rem}}
  .meta{{color:#a5b3ad;font-size:.9rem}}
  .pill{{display:inline-block;background:#1c4138;color:#f5ede0;padding:.2rem .6rem;border-radius:999px;font-size:.78rem;margin:.15rem .2rem;border:1px solid #2c564c}}
  .match{{background:#243b30;color:#9fd0a7;border-color:#3e6e60}}
  .gap{{background:#3a2a18;color:#e3b389;border-color:#5a4022}}
  table{{border-collapse:collapse;width:100%;margin-top:.5rem;font-size:.88rem}}
  th,td{{text-align:left;padding:.6rem .5rem;border-bottom:1px solid #2c564c}}
  th{{color:#a5b3ad;text-transform:uppercase;letter-spacing:.04em;font-size:.72rem}}
  .footer{{margin-top:2rem;color:#5a6660;font-size:.72rem;text-align:center}}
</style></head><body><div class=wrap>
<h1>{candidate_name}</h1>
<div class=meta>AI Career Advisor · Executive Report · v{BRAND['version']}</div>
<h2>Profile</h2>
<p><b>Education:</b> {profile['education']}<br>
<b>Experience:</b> {profile['experience_years']} years<br>
<b>Detected Domain:</b> {profile['domain']}</p>
<h2>Top Predictions</h2>
<table><tr><th>Rank</th><th>Job Role</th><th>Confidence</th></tr>
{"".join(f"<tr><td>{i+1}</td><td>{row['job']}</td><td>{row['confidence']:.1f}%</td></tr>" for i,row in enumerate(profile['top_predictions']))}
</table>
<h2>Match Strength</h2>
{"".join(f'<span class="pill match">{s}</span>' for s in profile['matched_skills']) or '<span class=meta>—</span>'}
<h2>Skill Gap</h2>
{"".join(f'<span class="pill gap">{s}</span>' for s in profile['skill_gap']) or '<span class=meta>None — perfect match.</span>'}
<div class=footer>Generated by {BRAND['name']} · {BRAND['tagline']}</div>
</div></body></html>"""
d3, d4 = st.columns(2)
with d3:
    st.download_button(
        label="HTML Report",
        data=html.encode("utf-8"),
        file_name=f"{slug}_report.html", mime="text/html",
        use_container_width=True,
    )
with d4:
    st.markdown(
        '<a class="pill brand" href="javascript:window.print()">Print / Save as PDF</a>',
        unsafe_allow_html=True,
    )

st.caption(f"{BRAND['name']} · Reports · Share with confidence")

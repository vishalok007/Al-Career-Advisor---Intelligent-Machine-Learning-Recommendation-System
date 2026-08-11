from __future__ import annotations
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import streamlit as st

from components import render_sidebar
from utils.constants import BRAND
from utils.helpers import inject_css, page_header, kpi_card, empty_state, pill, progress_bar
from utils.candidate_store import (
    list_candidates,
    load_candidate,
    delete_candidate,
    export_csv_bytes,
    export_json_bytes,
)
from utils.jd_parser import parse_jd_text, parse_jd_pdf
from utils.recruiter import rank_candidates_for_jd

inject_css("assets/styles.css")
render_sidebar("Recruiter")

page_header(
    "Recruiter Mode",
    "Rank every saved candidate against one job description — side-by-side "
    "fit scores, skill gaps and weekly roadmaps. The recruiter supplies the JD; "
    "the engine grades each candidate.",
    eyebrow="Compare many candidates · one JD",
)

candidates = list_candidates()

if not candidates:
    st.markdown(
        '<div class="card fade-up" style="background:rgba(127,184,139,.16);'
        'border-color:rgba(127,184,139,.38);color:#dff3e4">'
        "No saved candidates yet. Predict a profile on the <b>Predict</b> page "
        "and tap <b>Save this candidate to history</b> to populate this view."
        "</div>",
        unsafe_allow_html=True,
    )
    st.stop()

c1, c2, c3 = st.columns(3)
with c1: kpi_card("Candidates stored", str(len(candidates)), "on disk", icon="🗂")
with c2: kpi_card("Domains covered", str(len({c.get("domain") for c in candidates})), "unique", icon="🧭")
with c3: kpi_card("Top saved fit", f"{max((c.get('overall_pct') or 0) for c in candidates):.1f}%", "across history", icon="🏆")

st.caption("Files live in `.cache/candidates/` as JSON so recruiters can ship them by email.")

st.markdown(
    "<div class='eyebrow' style='margin-top:1rem'>Job description</div>"
    "<h2 style='margin:.1rem 0 .6rem'>Paste or upload the JD to rank candidates</h2>",
    unsafe_allow_html=True,
)

jd_left, jd_right = st.columns([1, 1])
with jd_left:
    jd_pdf = st.file_uploader("JD (PDF)", type=["pdf"], key="recruiter_jd_pdf")
with jd_right:
    jd_text_input = st.text_area(
        "…or paste JD text",
        height=160,
        placeholder="Paste the JD here — title, skills, tenure. We'll rank every saved candidate.",
    )

parsed_jd = None
if jd_pdf is not None:
    with st.spinner("Parsing JD PDF..."):
        parsed_jd = parse_jd_pdf(jd_pdf)
elif jd_text_input.strip():
    parsed_jd = parse_jd_text(jd_text_input)

if not parsed_jd or not (parsed_jd.get("raw_text") or "").strip():
    empty_state(
        "📄", "No JD parsed yet",
        "Upload or paste a JD. We use the detected skills and tenure to grade "
        "every saved candidate against the same yardstick.",
    )
    st.stop()

# Show parsed JD summary
jd_skills = parsed_jd.get("skills") or []
jd_title = parsed_jd.get("title")
min_y = parsed_jd.get("min_years")
max_y = parsed_jd.get("max_years")

chips = "".join(pill(s) for s in jd_skills[:18]) or '<span class="pill">No recognised skills in JD</span>'
sub = []
if jd_title: sub.append(f"<b>{jd_title}</b>")
if min_y or max_y:
    rng = []
    if min_y is not None: rng.append(f"min {min_y}y")
    if max_y is not None: rng.append(f"max {max_y}y")
    sub.append(" · ".join(rng))
sub_html = " &middot; ".join(sub) if sub else ""
st.markdown(
    f'<div class="card fade-up" style="margin-top:.5rem">'
    f'<div class="card-t">Parsed JD</div>'
    f'<div class="card-s">{sub_html}</div>'
    f'<div style="margin-top:.6rem">{chips}</div>'
    f'</div>',
    unsafe_allow_html=True,
)


ranked = rank_candidates_for_jd(parsed_jd.get("raw_text", ""), candidates)

st.markdown(
    "<div class='eyebrow' style='margin-top:1rem'>Ranked candidates</div>"
    "<h2 style='margin:.1rem 0 .6rem'>Best fit for this JD</h2>",
    unsafe_allow_html=True,
)

if not ranked:
    st.warning("No candidates could be scored against this JD.")
    st.stop()

# Side-by-side score table.
table_rows = []
for idx, row in enumerate(ranked, start=1):
    res = row["result"]
    table_rows.append({
        "Rank": idx,
        "Candidate": row["candidate_name"],
        "Domain": row["domain"] or "—",
        "Experience (yrs)": row["experience_years"],
        "Education": row["education"],
        "Overall fit": f"{res['overall_match_pct']:.1f}%",
        "Skill fit": f"{res['skill_pct']:.1f}%",
        "Experience fit": f"{res['experience_pct']:.1f}%",
        "Education fit": f"{res['education_pct']:.1f}%",
        "Matched": len(res["matched"]),
        "Missing": len(res["missing"]),
    })
st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True, height=320)

# Highlight the top three with detailed cards
top3 = ranked[:3]
cols = st.columns(len(top3))
for col, row in zip(cols, top3):
    res = row["result"]
    matched_html = "".join(pill(s, "success") for s in res["matched"][:8]) or pill("No overlap")
    missing_html = "".join(pill(s, "warn") for s in res["missing"][:8]) or '<span class="pill success">No gap</span>'
    overall = res["overall_match_pct"]
    cls = "medal g" if overall >= 75 else ("medal s" if overall >= 55 else "medal b")
    with col:
        st.markdown(
            f'<div class="prediction-card fade-up">'
            f'<div class="{cls}">{row["candidate_name"][:2].upper() if row["candidate_name"] else "—"}</div>'
            f'<div style="flex:1">'
            f'<div style="font-weight:600;font-size:1.02rem">{row["candidate_name"]}</div>'
            f'<div style="font-size:.78rem;color:var(--text-soft);margin-top:.15rem">Overall fit {overall:.1f}%</div>'
            f'<div class="score-bar"><div style="width:{overall:.1f}%"></div></div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

# Detailed comparison rows
for idx, row in enumerate(ranked, start=1):
    res = row["result"]
    matched_html = "".join(pill(s, "success") for s in res["matched"][:10]) or pill("No overlap")
    missing_html = "".join(pill(s, "warn") for s in res["missing"][:10]) or '<span class="pill success">No gap</span>'
    st.markdown(
        f'<div class="card portal-card fade-up" style="margin-bottom:.7rem">'
        f'<div style="display:flex;justify-content:space-between;gap:1rem;flex-wrap:wrap;align-items:flex-start">'
        f'<div style="flex:1;min-width:240px">'
        f'<div class="card-s">#{idx} · {row["candidate_name"]}</div>'
        f'<div style="font-size:1.08rem;font-weight:650;margin-top:.15rem">'
        f'{row["candidate_name"]} &middot; {row["domain"] or "Unspecified domain"}</div>'
        f'<div class="card-s" style="margin-top:.2rem">{row["experience_years"]} yrs · '
        f'{row["education"]} · saved {row["saved_at"]}</div>'
        f'</div>'
        f'<div style="display:flex;gap:.4rem;flex-wrap:wrap;justify-content:flex-end">'
        f'<span class="pill accent">Overall {res["overall_match_pct"]:.1f}%</span>'
        f'<span class="pill">Skill {res["skill_pct"]:.1f}%</span>'
        f'<span class="pill">Exp {res["experience_pct"]:.1f}%</span>'
        f'<span class="pill">Edu {res["education_pct"]:.1f}%</span>'
        f'</div></div>'
        f'<div class="card-s" style="margin-top:.8rem">Matched skills</div>'
        f'<div style="margin-top:.3rem">{matched_html}</div>'
        f'<div class="card-s" style="margin-top:.8rem">Missing skills</div>'
        f'<div style="margin-top:.3rem">{missing_html}</div>'
        f'<div class="card-s" style="margin-top:.8rem">Each component</div>'
        f'<div class="coverage"><div style="width:{res["skill_pct"]:.1f}%"></div></div>'
        f'<div style="font-size:.78rem;color:var(--text-soft);margin-top:.2rem">Skills</div>'
        f'<div class="coverage"><div style="width:{res["experience_pct"]:.1f}%"></div></div>'
        f'<div style="font-size:.78rem;color:var(--text-soft);margin-top:.2rem">Experience</div>'
        f'<div class="coverage"><div style="width:{res["education_pct"]:.1f}%"></div></div>'
        f'<div style="font-size:.78rem;color:var(--text-soft);margin-top:.2rem">Education</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

st.markdown(
    "<div class='eyebrow' style='margin-top:1.2rem'>History</div>"
    "<h2 style='margin:.1rem 0 .6rem'>Manage saved candidates</h2>",
    unsafe_allow_html=True,
)

ids = [c.get("id", "?") for c in candidates]
default_label = "Select a candidate to inspect"
choice = st.selectbox("Open saved record", [default_label] + ids)
if choice and choice != default_label:
    loaded = load_candidate(choice) or {}
    if loaded:
        info_cols = st.columns(2)
        with info_cols[0]:
            st.markdown(
                f'<div class="card"><div class="card-t">{loaded.get("candidate_name", "Anonymous")}</div>'
                f'<div class="card-s">{loaded.get("domain", "")} · {loaded.get("education", "")} · '
                f'{loaded.get("experience_years", 0)} yrs</div>'
                f'<div style="margin-top:.5rem">'
                f'<div class="coverage"><div style="width:{(loaded.get("overall_pct") or 0):.1f}%"></div></div>'
                f'<div style="font-size:.78rem;color:var(--text-soft);margin-top:.2rem">Latest overall fit</div>'
                f'<div style="margin-top:.5rem;color:var(--text-soft);font-size:.88rem">Saved {loaded.get("saved_at","—")}</div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )
        with info_cols[1]:
            skills_pills = "".join(pill(s) for s in (loaded.get("validated_skills") or [])[:18])
            st.markdown(
                f'<div class="card"><div class="card-t">Validated skills</div>'
                f'<div class="card-s">{len(loaded.get("validated_skills") or [])} validated across history</div>'
                f'<div style="margin-top:.5rem">{skills_pills or "<span class=muted>none captured</span>"}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

        if st.button(f"Delete candidate {choice}", key=f"del_{choice}"):
            delete_candidate(choice)
            st.success(f"Deleted {choice}. Refresh to update the table.")
            st.rerun() if hasattr(st, "rerun") else None

exp_cols = st.columns(2)
with exp_cols[0]:
    st.download_button(
        "Export history (CSV)",
        data=export_csv_bytes(candidates),
        file_name="candidate_history.csv",
        mime="text/csv",
        use_container_width=True,
    )
with exp_cols[1]:
    st.download_button(
        "Export history (JSON)",
        data=export_json_bytes(candidates),
        file_name="candidate_history.json",
        mime="application/json",
        use_container_width=True,
    )

st.caption(
    f"{BRAND['name']} · Recruiter Mode · Side-by-side JD comparison & exports"
)

"""Platform Brief page — architecture, technical specifications, layout map."""
from __future__ import annotations
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from utils.constants import BRAND
from utils.helpers import inject_css, page_header, kpi_card, read_json
from components import render_sidebar
from utils.model_paths import REPORT_PATHS, validate_runtime_artifacts

inject_css("assets/styles.css")
render_sidebar("About")

missing_runtime_files = validate_runtime_artifacts()
if missing_runtime_files:
    st.error("Missing runtime model files: " + ", ".join(missing_runtime_files))
    st.stop()

page_header(
    "Platform Brief",
    f"{BRAND['name']} — AI Career Advisor is an enterprise artificial intelligence application designed to automate career role forecasting, skill-gap analysis, live job market alignment, and candidate screening.",
    eyebrow="System Overview & Architecture",
)

summary = read_json(REPORT_PATHS["evaluation_summary"])
models = summary["models"]
winner = next(m for m in models if m["name"] == summary["winner"])
top3_acc = winner.get("top3_accuracy", 0.8255)

k1, k2, k3, k4 = st.columns(4)
with k1: kpi_card("Modules", "8", "SaaS routing", icon="📄")
with k2: kpi_card("Champion Model", winner["name"], f"{winner['accuracy']*100:.1f}% Top-1 Acc", icon="🧠")
with k3: kpi_card("Top-3 Accuracy", f"{top3_acc*100:.1f}%", "in top-3 predictions", icon="🥇")
with k4: kpi_card("Database", "SQLite3", "Data/candidates.db", icon="💾")

st.markdown("")

left, right = st.columns([1, 1])
with left:
    st.markdown(
        '<div class="card">'
        '<div class="card-t">System Mission & Purpose</div>'
        '<p style="margin:.5rem 0;line-height:1.6">AI Career Advisor helps candidates and hiring teams translate skill profiles into data-backed career paths and match evaluations. By combining a 324-class machine learning classifier with 384-dimensional dense vector embeddings, the platform generates explainable job recommendations, personalized weekly learning roadmaps, and candidate candidate analytics.</p>'
        '</div>',
        unsafe_allow_html=True,
    )
with right:
    st.markdown(
        '<div class="card">'
        '<div class="card-t">Pipeline Architecture</div>'
        '<p style="margin:.5rem 0;line-height:1.6;font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.82rem;color:var(--accent)">'
        'Candidate Resume (PDF/Text)<br>'
        '↓ Multi-Provider LLM Extractor (Gemini / OpenAI / Ollama / NLP)<br>'
        '↓ 3-Tier Taxonomy & O*NET-SOC Mapper<br>'
        '↓ Random Forest Champion Classifier (324 Roles)<br>'
        '↓ Dense Vector Matcher (SentenceTransformers 384d)<br>'
        '↓ SQLite Candidates Database & Live Job Registries'
        '</p>'
        '</div>',
        unsafe_allow_html=True,
    )

st.markdown("<div class='eyebrow' style='margin-top:1.4rem'>Platform Engineering</div>"
            "<h2 style='margin:.1rem 0 .6rem'>Technical Specifications & Highlights</h2>",
            unsafe_allow_html=True)
highlights = [
    "384-dimensional SentenceTransformers dense vector embeddings (all-MiniLM-L6-v2) for contextual semantic job matching.",
    "Multi-provider zero-shot LLM resume parser supporting Google Gemini API, OpenAI API, Local Ollama, and offline Heuristic NLP.",
    "3-tier hierarchical taxonomy mapped to U.S. Bureau of Labor Statistics O*NET-SOC occupation codes.",
    "Embedded relational SQLite database (Data/candidates.db) with index-backed SQL query filtering.",
    "Live provider registry for Remotive, Arbeitnow, RemoteOK, and The Muse with round-robin result interleaving.",
    "Automated 15-test Pytest suite with GitHub Actions CI/CD pipeline integration."
]
for line in highlights:
    st.markdown(
        f'<div class="card" style="padding:.7rem 1rem;margin:.3rem 0;display:flex;'
        f'gap:.6rem;align-items:flex-start">'
        f'<div style="flex:1">{line}</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("<div class='eyebrow' style='margin-top:1.4rem'>Repository Architecture</div>"
            "<h2 style='margin:.1rem 0 .6rem'>Project Directory Map</h2>",
            unsafe_allow_html=True)
folders = {
    "app.py": "Streamlit SaaS application entry point",
    "pages/": "Eight routed application pages (Dashboard, Predict, Recruiter, etc.)",
    "components/": "Modular UI component blocks (job cards, roadmap view)",
    "utils/": "Service layer, predictors, dense vector matchers, candidate store",
    "assets/": "CSS design system & stylesheets",
    "models/runtime/": "Persisted production classifier pickles & encoders",
    "models/reports/": "Classification reports & evaluation summary JSON",
    "Data/": "Relational SQLite database (candidates.db) & training CSVs",
    "career/": "Taxonomy definitions, IT job roles, and domain mappings",
    "training/": "Re-runnable multi-model training & benchmarking pipeline",
    "tests/": "Automated 15-test Pytest verification test suite",
    "scripts/": "Diagnostic utilities & verification tools",
}
c1, c2 = st.columns([1, 1])
items = list(folders.items())
mid = (len(items) + 1) // 2
left_items, right_items = items[:mid], items[mid:]
for col, batch in zip([c1, c2], [left_items, right_items]):
    with col:
        rows = "".join(
            f'<div style="display:flex;gap:1rem;padding:.45rem 0;'
            f'border-bottom:1px dashed var(--border)">'
            f'<b style="min-width:140px;color:var(--accent)">{k}</b>'
            f'<span style="color:var(--text-soft)">{v}</span></div>'
            for k, v in batch
        )
        st.markdown(f'<div class="card">{rows}</div>', unsafe_allow_html=True)

st.markdown("<div class='eyebrow' style='margin-top:1.4rem'>Credits & Engineering</div>", unsafe_allow_html=True)
st.markdown(
    f'<div class="card" style="padding:1.2rem 1.4rem">'
    f'<p style="margin:0;line-height:1.6">Developed by <b>Vishal Kumar</b> as an end-to-end machine learning and software engineering application demonstrating advanced data preprocessing, multi-model evaluation, dense semantic embeddings, and automated candidate analytics.</p></div>',
    unsafe_allow_html=True,
)

st.caption(f"{BRAND['name']} · Platform Brief")

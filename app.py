"""AI Career Advisor — entry point with side-by-side hero and shortcuts."""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import pandas as pd
import streamlit as st

from components import render_sidebar
from utils.constants import BRAND
from utils.helpers import inject_css, page_header, kpi_card, read_json
from utils.model_paths import REPORT_PATHS, RUNTIME_MODEL_PATHS, validate_runtime_artifacts

st.set_page_config(
    page_title=f"{BRAND['name']} — {BRAND['tagline']}",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css("assets/styles.css")
render_sidebar("Dashboard")

missing_runtime_files = validate_runtime_artifacts()
if missing_runtime_files:
    st.error(
        "Missing runtime model files: " + ", ".join(missing_runtime_files)
    )
    st.stop()

# Load evaluation summary once (cached)
summary = read_json(REPORT_PATHS["evaluation_summary"])
models = summary["models"]
winner = next(m for m in models if m["name"] == summary["winner"])
label_encoder = joblib.load(RUNTIME_MODEL_PATHS["label_encoder"])
job_role_count = len(label_encoder.classes_)
resume_count = int(summary.get("dataset_rows", 0))
feature_count = int(summary.get("feature_count", 0))

page_header(
    "Command Center",
    "Your workspace for predictions, analytics, model comparison, and career reporting.",
    eyebrow="Career intelligence workspace",
)

# KPI strip 
c1, c2, c3, c4 = st.columns(4)
with c1: kpi_card("Resumes scored", f"{resume_count:,}", "from evaluation summary", delta_dir="up", icon="📄")
with c2: kpi_card("Active model", winner["name"], f"{winner['accuracy']*100:.1f}% hold-out", icon="🧠")
with c3: kpi_card("Job roles", f"{job_role_count:,}", "label encoder classes", icon="🎯")
with c4: kpi_card("Skill vectors", f"{feature_count:,}", "feature dims", icon="🛠")

st.markdown("")

# Two-column layout: live model list on the left, navigation on the right
left, right = st.columns([1.4, 1])

with left:
    st.markdown(
        '<div class="card fade-up">'
        '<div class="card-t">All trained models</div>'
        '<div class="card-s">Hold-out accuracy + cross-validation · click a name to view on Models</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    table = pd.DataFrame([
        {
            "Model": m["name"],
            "Hold-out acc.": f"{m['accuracy']*100:.1f}%",
            "CV (5-fold)": f"{m['cv_mean']*100:.1f}% ± {m['cv_std']*100:.1f}",
            "F1 (weighted)": f"{m['f1']*100:.1f}%",
            "Precision": f"{m['precision']*100:.1f}%",
            "Recall": f"{m['recall']*100:.1f}%",
            "Train time": f"{m['train_seconds']:.1f}s",
        }
        for m in models
    ])
    st.dataframe(table, use_container_width=True, hide_index=True)

with right:
    st.markdown(
        '<div class="card fade-up" style="height:100%;padding:1.15rem 1.15rem 1rem">'
        '<div class="card-t">Workspace Summary</div>'
        '<div class="card-s">Core platform capabilities in one view</div>'
        '<div style="margin-top:1rem;display:grid;gap:.7rem">'
        '<div style="padding:.8rem .9rem;border:1px solid var(--border);border-radius:14px;background:rgba(255,255,255,.02)">Prediction workflows for resume and skill-based matching.</div>'
        '<div style="padding:.8rem .9rem;border:1px solid var(--border);border-radius:14px;background:rgba(255,255,255,.02)">Dataset analytics for skills, domains, and education trends.</div>'
        '<div style="padding:.8rem .9rem;border:1px solid var(--border);border-radius:14px;background:rgba(255,255,255,.02)">Model monitoring with comparison metrics and performance summaries.</div>'
        '<div style="padding:.8rem .9rem;border:1px solid var(--border);border-radius:14px;background:rgba(255,255,255,.02)">Structured reporting for recruiter-ready candidate reviews.</div>'
        '</div></div>',
        unsafe_allow_html=True,
    )

st.markdown("---")
st.caption(
    f"© 2026 {BRAND['name']} · {BRAND['tagline']} · "
    f"Active classifier: {winner['name']} ({winner['accuracy']*100:.1f}% hold-out accuracy)"
)

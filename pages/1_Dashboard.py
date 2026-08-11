"""Dashboard — L→R KPI row + chart row + recent previews."""
from __future__ import annotations
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import joblib
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.helpers import (
    inject_css, page_header, kpi_card, read_csv_cached, read_json,
)
from components import render_sidebar
from utils.model_paths import REPORT_PATHS, RUNTIME_MODEL_PATHS

inject_css("assets/styles.css")
render_sidebar("Dashboard")
page_header(
    "Command Center",
    "Live overview of your career-intelligence workspace.",
    eyebrow="Career intelligence · real-time",
)

# Load artefacts
df = read_csv_cached("Data/training_data.csv")
summary = read_json(REPORT_PATHS["evaluation_summary"])
top_model = next(m for m in summary["models"] if m["name"] == summary["winner"])
label_encoder = joblib.load(RUNTIME_MODEL_PATHS["label_encoder"])
job_role_count = len(label_encoder.classes_)
resume_count = int(summary.get("dataset_rows", len(df)))
feature_count = int(summary.get("feature_count", 0))
median_experience = float(df["Experience Years"].median())

KPI_DATA = [
    ("Resumes scored", f"{resume_count:,}", "evaluation summary", "📄", "up"),
    ("Job roles", f"{job_role_count:,}", "label encoder classes", "🎯", "up"),
    ("Avg. experience", f"{df['Experience Years'].mean():.1f} yrs", f"median {median_experience:.0f}", "💼", "up"),
    ("Hold-out accuracy", f"{top_model['accuracy']*100:.1f}%", top_model["name"], "🧠", "up"),
]
kpi_cols = st.columns(len(KPI_DATA))
for col, (label, val, delta, icon, direction) in zip(kpi_cols, KPI_DATA):
    with col:
        kpi_card(label, val, delta, delta_dir=direction, icon=icon)

st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

# Charts row (left + right, never stacked)
left, right = st.columns([1.4, 1])
with left:
    st.markdown(
        '<div class="card fade-up">'
        '<div class="card-t">Top job categories</div>'
        '<div class="card-s">Distribution across the training set</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    counts = (
        df["Category"].fillna("Other").value_counts().head(12).reset_index()
    )
    counts.columns = ["Category", "Count"]
    fig = px.bar(
        counts, x="Count", y="Category", orientation="h",
        color_discrete_sequence=["#a4c2b0"],
    )
    fig.update_traces(marker_line_color="#7aa597", marker_line_width=1)
    fig.update_layout(
        showlegend=False, height=380, margin=dict(l=200, r=20, t=8, b=20),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="-apple-system,Inter,Segoe UI", color="#cfd8d2"),
    )
    fig.update_xaxes(showgrid=True, gridcolor="rgba(255,255,255,.08)")
    fig.update_yaxes(showgrid=False, autorange="reversed", automargin=True, title=None)
    st.plotly_chart(fig, use_container_width=True, theme=None)

with right:
    st.markdown(
        '<div class="card fade-up">'
        '<div class="card-t">Experience distribution</div>'
        '<div class="card-s">Years of experience across resumes</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    fig2 = go.Figure(
        data=[go.Histogram(
            x=df["Experience Years"], nbinsx=20,
            marker_color="#d49966", opacity=.9,
            hovertemplate="Years: %{x}<br>Resumes: %{y}<extra></extra>",
        )]
    )
    fig2.update_layout(
        height=380, margin=dict(l=10, r=10, t=8, b=20),
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="-apple-system,Inter,Segoe UI", color="#cfd8d2"),
        bargap=.06,
    )
    fig2.update_xaxes(title="Years", showgrid=True,
                      gridcolor="rgba(255,255,255,.08)",
                      zerolinecolor="rgba(255,255,255,.08)")
    fig2.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,.08)",
                      title="Resumes")
    st.plotly_chart(fig2, use_container_width=True, theme=None)

st.markdown("<div style='height:.7rem'></div>", unsafe_allow_html=True)

# Wide table --------------------------------------------------------------
st.markdown(
    '<div class="card fade-up">'
    '<div class="card-t">Latest resumes</div>'
    '<div class="card-s">Recently scored candidate profiles</div>'
    '</div>',
    unsafe_allow_html=True,
)
preview = (
    df[["Resume ID", "Education", "Experience Years", "Job Role", "Category"]]
    .head(10)
    .reset_index(drop=True)
)
preview.columns = ["Resume", "Education", "Experience (yrs)", "Predicted Role", "Domain"]
st.dataframe(preview, use_container_width=True, hide_index=True, height=320)

st.caption("AI Career Advisor · Command Center · Updated live")

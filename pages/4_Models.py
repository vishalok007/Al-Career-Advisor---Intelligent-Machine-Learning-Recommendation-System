"""Models page — show ALL trained classifiers, Top-1/Top-3/Top-5 accuracies, and benchmark matrix."""
from __future__ import annotations
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from utils.constants import BRAND
from utils.helpers import (
    inject_css, page_header, kpi_card, progress_bar, read_json,
)
from components import render_sidebar
from utils.model_paths import REPORT_PATHS, RUNTIME_MODEL_PATHS, validate_runtime_artifacts

inject_css("assets/styles.css")
render_sidebar("Models")

missing_runtime_files = validate_runtime_artifacts()
if missing_runtime_files:
    st.error("Missing runtime model files: " + ", ".join(missing_runtime_files))
    st.stop()

summary = read_json(REPORT_PATHS["evaluation_summary"])
page_header(
    "ML Models & Model Comparison",
    "Empirical benchmarks across multi-class algorithms evaluated on unseen test data.",
    eyebrow=f"{len(summary['models'])} classifiers evaluated on unseen test set",
)
models = summary["models"]
winner_name = summary["winner"]
winner = next(m for m in models if m["name"] == winner_name)

top3_val = winner.get("top3_accuracy", winner["accuracy"])
top5_val = winner.get("top5_accuracy", winner["accuracy"])
macro_f1_val = winner.get("macro_f1", winner.get("f1", 0.0))

# Champion banner
st.markdown(
    f'<div class="hero fade-up" style="background:linear-gradient(135deg,#0a1814 0%,#244b41 60%,#7aa597 100%);'
    f'display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:1.4rem">'
    f'<div>'
    f'<div class="eyebrow" style="color:#f1c161">Active production champion model</div>'
    f'<h1 style="margin:.25rem 0">{winner["name"]}</h1>'
    f'<p>Unseen Test Top-1 <b>{winner["accuracy"]*100:.1f}%</b> · Top-3 <b>{top3_val*100:.1f}%</b> · Top-5 <b>{top5_val*100:.1f}%</b> · '
    f'3-fold CV <b>{winner["cv_mean"]*100:.1f}% ± {winner["cv_std"]*100:.1f}</b> · '
    f'<b>{winner["features"]:,}</b> features · <b>{winner["classes"]:,}</b> classes</p>'
    f'</div>'
    f'<div style="display:flex;gap:.5rem;flex-wrap:wrap">'
    f'<span class="pill accent" style="padding:.45rem .8rem">Top-1 {winner["accuracy"]*100:.1f}%</span>'
    f'<span class="pill brand" style="padding:.45rem .8rem">Top-3 {top3_val*100:.1f}%</span>'
    f'<span class="pill" style="padding:.45rem .8rem;background:rgba(255,255,255,.1)">Macro F1 {macro_f1_val*100:.1f}%</span>'
    f'</div>'
    f'</div>',
    unsafe_allow_html=True,
)

st.markdown("")

# Metric KPI summary cards
m1, m2, m3, m4 = st.columns(4)
with m1: kpi_card("Top-1 Accuracy", f"{winner['accuracy']*100:.1f}%", "exact match", icon="🎯")
with m2: kpi_card("Top-3 Accuracy", f"{top3_val*100:.1f}%", "in top-3 predictions", icon="🥇")
with m3: kpi_card("Top-5 Accuracy", f"{top5_val*100:.1f}%", "in top-5 predictions", icon="🏆")
with m4: kpi_card("Macro F1", f"{macro_f1_val*100:.1f}%", "unweighted class avg", icon="⚖️")

st.markdown("<div style='height:.8rem'></div>", unsafe_allow_html=True)

st.markdown(
    '<div class="card fade-up">'
    '<div class="card-t">Unseen test-set accuracy comparison</div>'
    '<div class="card-s">Top-1 Accuracy evaluated on 20% hold-out test set</div>'
    '</div>',
    unsafe_allow_html=True,
)
df_models = pd.DataFrame(models).sort_values("accuracy", ascending=False)
fig = px.bar(
    df_models,
    x="name",
    y="accuracy",
    color="accuracy",
    text=df_models["accuracy"].map(lambda x: f"{x*100:.1f}%"),
    color_continuous_scale=["#7aa597", "#a4c2b0", "#d49966"],
    range_color=[df_models["accuracy"].min() * 0.9, 1.0],
)
fig.update_traces(
    textposition="outside",
    marker_line_color="#0d1f1b",
    cliponaxis=False,
    textfont=dict(size=12),
)
fig.update_layout(
    height=430,
    margin=dict(l=92, r=20, t=28, b=100),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="-apple-system,Inter,Segoe UI", color="#cfd8d2", size=14),
    coloraxis_showscale=False,
)
fig.update_xaxes(
    title=None,
    tickangle=0,
    tickfont=dict(size=12, color="#d9e3dd"),
    automargin=True,
)
fig.update_yaxes(
    title="Test accuracy (%)",
    tickformat=".0%",
    gridcolor="rgba(255,255,255,.08)",
    tickfont=dict(size=13, color="#d9e3dd"),
    automargin=True,
    range=[0, 1],
)
st.plotly_chart(fig, use_container_width=True, theme=None)

# Model Comparison Matrix Table
st.markdown("<div class='eyebrow' style='margin-top:1rem'>Empirical Benchmark Matrix</div>"
            "<h2 style='margin:.1rem 0 .6rem'>Every model evaluated on unseen test data</h2>",
            unsafe_allow_html=True)
table_data = []
for m in sorted(models, key=lambda x: -x["accuracy"]):
    t3 = m.get("top3_accuracy", m["accuracy"])
    t5 = m.get("top5_accuracy", m["accuracy"])
    mf1 = m.get("macro_f1", m.get("f1", 0.0))
    table_data.append({
        "Model": m["name"],
        "Top-1 Accuracy": f"{m['accuracy']*100:.1f}%",
        "Top-3 Accuracy": f"{t3*100:.1f}%",
        "Top-5 Accuracy": f"{t5*100:.1f}%",
        "Macro F1": f"{mf1*100:.1f}%",
        "Weighted F1": f"{m['f1']*100:.1f}%",
        "3-Fold CV": f"{m['cv_mean']*100:.1f}% ± {m['cv_std']*100:.2f}",
        "Train Time": f"{m['train_seconds']:.1f}s",
        "Status": "Active Champion" if m["name"] == winner_name else "Evaluated Candidate",
    })
table = pd.DataFrame(table_data)
st.dataframe(table, use_container_width=True, hide_index=True, height=280)


st.markdown("<div class='eyebrow' style='margin-top:1.4rem'>Pipeline</div>"
            "<h2 style='margin:.1rem 0 .6rem'>Academic training & evaluation workflow</h2>",
            unsafe_allow_html=True)
steps = [
    ("1", "Data Ingestion", "10,000 resume rows + cleaned skill columns"),
    ("2", "Preprocessing", "Label-encode roles, split skills into clean vectors"),
    ("3", "Feature Matrix", "OneHot education · MultiLabelBinarizer skills · numeric experience"),
    ("4", "Train/Test Split", "80% Train · 20% Unseen Test Set (stratified)"),
    ("5", "Model Benchmarks", "Random Forest, Extra Trees, Decision Tree, Logistic Regression"),
    ("6", "Evaluation", "Unseen Test Top-1, Top-3, Top-5 Acc, Macro/Weighted F1, 3-fold CV"),
]
pipe_cols = st.columns(len(steps))
for col, (num, title, desc) in zip(pipe_cols, steps):
    with col:
        st.markdown(
            f'<div class="card" style="text-align:center;padding:1rem .6rem">'
            f'<div style="width:30px;height:30px;border-radius:50%;background:#d49966;'
            f'color:#241509;display:inline-grid;place-items:center;font-weight:700">{num}</div>'
            f'<div style="font-weight:600;margin-top:.45rem;font-size:.9rem">{title}</div>'
            f'<div style="font-size:.74rem;color:var(--text-soft);margin-top:.3rem;line-height:1.45">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

st.subheader("Download model artifacts")
d1, d2, d3 = st.columns(3)
files = [
    ("Classifier", RUNTIME_MODEL_PATHS["classifier"]),
    ("Skills encoder", RUNTIME_MODEL_PATHS["skills_encoder"]),
    ("Education encoder", RUNTIME_MODEL_PATHS["education_encoder"]),
]
for col, (name, path) in zip([d1, d2, d3], files):
    with open(path, "rb") as fh:
        with col:
            st.download_button(
                label=name,
                data=fh.read(),
                file_name=Path(path).name,
                use_container_width=True,
            )

st.caption(f"{BRAND['name']} · Model Card · Academic Evaluation Standard")

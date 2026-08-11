"""Analytics page — readable stacked charts for skills, domains, and education."""
from __future__ import annotations
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from utils.constants import BRAND
from utils.helpers import inject_css, page_header, kpi_card, read_csv_cached
from components import render_sidebar

inject_css("assets/styles.css")
render_sidebar("Analytics")
page_header(
    "Analytics",
    "Explore skill, domain and education trends with clearer, easier-to-read charts.",
    eyebrow="Insights · per-resume statistics",
)


df = read_csv_cached("Data/training_data.csv").copy()

if "Skills" in df.columns:
    df["Skill Count"] = df["Skills"].fillna("").apply(
        lambda s: len([t for t in s.split("|") if t.strip()])
    )

if "Experience Years" in df.columns:
    df["Experience Years"] = pd.to_numeric(df["Experience Years"], errors="coerce")

if "Category" in df.columns:
    df["Category"] = df["Category"].fillna("Other")

if "Education" in df.columns:
    df["Education"] = df["Education"].fillna("Unknown")

PALETTE = ["#a4c2b0", "#d49966", "#e3b389", "#6cd0e4", "#9d6cf2", "#d87a6a"]
CHART_FONT = dict(family="-apple-system,Inter,Segoe UI", color="#cfd8d2", size=14)
AXIS_STYLE = dict(
    showgrid=True,
    gridcolor="rgba(207,216,210,0.16)",
    zeroline=False,
    title_font=dict(size=15, color="#f4f7f5"),
    tickfont=dict(size=13, color="#d9e3dd"),
)


def apply_readable_layout(fig, height: int = 540, left_margin: int = 240, bottom_margin: int = 60):
    fig.update_layout(
        height=height,
        margin=dict(l=left_margin, r=50, t=30, b=bottom_margin),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=CHART_FONT,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="left",
            x=0,
            bgcolor="rgba(0,0,0,0)",
            font=dict(size=12, color="#cfd8d2"),
        ),
    )
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(
        showgrid=True,
        gridcolor="rgba(207,216,210,0.16)",
        zeroline=False,
        title=None,  # Suppress redundant vertical label to prevent overlapping
        tickfont=dict(size=13, color="#f4f7f5"),
        automargin=True,
    )
    return fig


k1, k2, k3, k4 = st.columns(4)
top_domain = df["Category"].value_counts().index[0] if "Category" in df else "Technology"
with k1:
    kpi_card("Domains", f"{df['Category'].nunique() if 'Category' in df else 0}", "across the set", icon="🌐")
with k2:
    kpi_card("Top domain", top_domain, "highest volume", icon="🧭")
with k3:
    kpi_card("Avg. skills / resume", f"{df['Skill Count'].mean():.1f}", "median stable", icon="📦")
with k4:
    kpi_card("Total rows", f"{len(df):,}", "scored", icon="📄")

st.markdown("")

tab1, tab2, tab3 = st.tabs(["Skills", "Domains", "Education"])


with tab1:
    st.markdown(
        '<div class="card fade-up">'
        '<div class="card-t">Top skills across the dataset</div>'
        '<div class="card-s">Most frequently mentioned skills in resumes</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    flat = pd.Series(
        [s.strip() for line in df["Skills"].dropna() for s in line.split("|") if s.strip()]
    )
    top_skills = flat.value_counts().head(10).reset_index()
    top_skills.columns = ["Skill", "Resume count"]

    fig_top_skills = px.bar(
        top_skills.sort_values("Resume count", ascending=True),
        x="Resume count",
        y="Skill",
        orientation="h",
        text="Resume count",
        color="Resume count",
        color_continuous_scale=[[0, "#5d8578"], [1, "#bfd6c9"]],
    )
    fig_top_skills.update_traces(textposition="outside", cliponaxis=False)
    fig_top_skills.update_coloraxes(showscale=False)
    fig_top_skills.update_xaxes(title="Number of resumes")
    apply_readable_layout(fig_top_skills, height=520, left_margin=180, bottom_margin=50)
    st.plotly_chart(fig_top_skills, use_container_width=True, theme=None)

    st.markdown(
        '<div class="card fade-up">'
        '<div class="card-t">Skill vs. experience</div>'
        '<div class="card-s">Average number of skills listed at each experience level</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    skill_exp = (
        df.dropna(subset=["Experience Years", "Skill Count"])
        .groupby("Experience Years", as_index=False)["Skill Count"]
        .mean()
        .sort_values("Experience Years")
    )
    skill_exp = skill_exp[skill_exp["Experience Years"] >= 0].head(25)

    fig_skill_exp = px.line(
        skill_exp,
        x="Experience Years",
        y="Skill Count",
        markers=True,
    )
    fig_skill_exp.update_traces(
        line=dict(color="#d49966", width=4),
        marker=dict(size=9, color="#a4c2b0", line=dict(width=1, color="#f5efe6")),
        hovertemplate="Experience: %{x} years<br>Avg. listed skills: %{y:.1f}<extra></extra>",
    )
    fig_skill_exp.update_xaxes(title="Experience years")
    fig_skill_exp.update_yaxes(title="Average listed skills")
    apply_readable_layout(fig_skill_exp, height=460, left_margin=80, bottom_margin=70)
    st.plotly_chart(fig_skill_exp, use_container_width=True, theme=None)


with tab2:
    st.markdown(
        '<div class="card fade-up">'
        '<div class="card-t">Domain distribution</div>'
        '<div class="card-s">Resume volume by domain</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    dom = df["Category"].value_counts().head(15).reset_index()
    dom.columns = ["Domain", "Resumes"]

    fig_domain_dist = px.bar(
        dom.sort_values("Resumes", ascending=True),
        x="Resumes",
        y="Domain",
        orientation="h",
        text="Resumes",
        color="Resumes",
        color_continuous_scale=[[0, "#5d8578"], [1, "#bfd6c9"]],
    )
    fig_domain_dist.update_traces(textposition="outside", cliponaxis=False)
    fig_domain_dist.update_coloraxes(showscale=False)
    fig_domain_dist.update_xaxes(title="Number of resumes")
    apply_readable_layout(fig_domain_dist, height=580, left_margin=260, bottom_margin=50)
    st.plotly_chart(fig_domain_dist, use_container_width=True, theme=None)

    st.markdown(
        '<div class="card fade-up">'
        '<div class="card-t">Experience by domain</div>'
        '<div class="card-s">Average years of experience for each domain</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    exp_by_domain = (
        df.dropna(subset=["Experience Years"])
        .groupby("Category", as_index=False)["Experience Years"]
        .mean()
        .sort_values("Experience Years", ascending=False)
        .head(15)
    )

    fig_exp_domain = px.bar(
        exp_by_domain.sort_values("Experience Years", ascending=True),
        x="Experience Years",
        y="Category",
        orientation="h",
        text="Experience Years",
        color="Experience Years",
        color_continuous_scale=[[0, "#7aa597"], [1, "#d49966"]],
    )
    fig_exp_domain.update_traces(texttemplate="%{text:.1f}", textposition="outside", cliponaxis=False)
    fig_exp_domain.update_coloraxes(showscale=False)
    fig_exp_domain.update_xaxes(title="Average experience years")
    apply_readable_layout(fig_exp_domain, height=580, left_margin=260, bottom_margin=60)
    st.plotly_chart(fig_exp_domain, use_container_width=True, theme=None)


with tab3:
    st.markdown(
        '<div class="card fade-up">'
        '<div class="card-t">Education distribution</div>'
        '<div class="card-s">Number of resumes in each education group</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    edu = df["Education"].value_counts().head(15).reset_index()
    edu.columns = ["Education", "Resumes"]

    fig_edu_dist = px.bar(
        edu.sort_values("Resumes", ascending=True),
        x="Resumes",
        y="Education",
        orientation="h",
        text="Resumes",
        color="Resumes",
        color_continuous_scale=[[0, "#6c8f85"], [1, "#d4b08d"]],
    )
    fig_edu_dist.update_traces(textposition="outside", cliponaxis=False)
    fig_edu_dist.update_coloraxes(showscale=False)
    fig_edu_dist.update_xaxes(title="Number of resumes")
    apply_readable_layout(fig_edu_dist, height=620, left_margin=220, bottom_margin=60)
    st.plotly_chart(fig_edu_dist, use_container_width=True, theme=None)

    st.markdown(
        '<div class="card fade-up">'
        '<div class="card-t">Experience by education</div>'
        '<div class="card-s">Average experience years for each education level</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    top_edu_labels = edu["Education"].tolist()
    exp_by_edu = (
        df.dropna(subset=["Experience Years"])
        .groupby("Education", as_index=False)["Experience Years"]
        .mean()
    )
    exp_by_edu = exp_by_edu[exp_by_edu["Education"].isin(top_edu_labels)]

    fig_exp_edu = px.bar(
        exp_by_edu.sort_values("Experience Years", ascending=True),
        x="Experience Years",
        y="Education",
        orientation="h",
        text="Experience Years",
        color="Experience Years",
        color_continuous_scale=[[0, "#7aa597"], [1, "#d49966"]],
    )
    fig_exp_edu.update_traces(texttemplate="%{text:.1f}", textposition="outside", cliponaxis=False)
    fig_exp_edu.update_coloraxes(showscale=False)
    fig_exp_edu.update_xaxes(title="Average experience years")
    apply_readable_layout(fig_exp_edu, height=620, left_margin=220, bottom_margin=60)
    st.plotly_chart(fig_exp_edu, use_container_width=True, theme=None)

st.caption(f"{BRAND['name']} · Analytics · Updated live")

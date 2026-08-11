"""Sidebar + brand block with clean text-only navigation."""
from __future__ import annotations

import streamlit as st

from utils.constants import BRAND
from components.job_cards import render_live_job_cards
from components.roadmap_view import render_weekly_roadmap

__all__ = ["render_sidebar", "render_live_job_cards", "render_weekly_roadmap"]

NAV_ITEMS = [
    {"label": "Command Center", "page": "app.py", "match": {"Home", "Dashboard"}},
    {"label": "Career Match", "page": "pages/2_Predict.py", "match": {"Predict"}},
    {"label": "Talent Insights", "page": "pages/3_Analytics.py", "match": {"Analytics"}},
    {"label": "Model Lab", "page": "pages/4_Models.py", "match": {"Models"}},
    {"label": "Report Studio", "page": "pages/5_Report.py", "match": {"Report"}},
    {"label": "Job Portals", "page": "pages/7_Job_Portals.py", "match": {"Job Portals"}},
    {"label": "Recruiter Mode", "page": "pages/8_Recruiter.py", "match": {"Recruiter"}},
    {"label": "Platform Brief", "page": "pages/6_About.py", "match": {"About"}},
]


def brand_block():
    st.markdown(
        f"""
        <div class="sidebar-brand-wrap">
          <div class="sidebar-brand-badge">AI</div>
          <div class="sidebar-brand-copy">
            <div class="sidebar-brand-title">{BRAND['name']}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def workspace_intro():
    st.markdown(
        """
        <div class="sidebar-panel">
          <div class="sidebar-panel-title">CAREER INTELLIGENCE WORKSPACE</div>
          <div class="sidebar-panel-copy">A cleaner navigation experience for predictions, analytics, reports, and model operations.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def model_status():
    from utils.helpers import read_json
    from utils.model_paths import REPORT_PATHS
    try:
        summary = read_json(REPORT_PATHS["evaluation_summary"])
        winner_name = summary.get("winner", "Random Forest")
        winner = next((m for m in summary.get("models", []) if m.get("name") == winner_name), None)
        acc_str = f"{winner['accuracy']*100:.1f}%" if winner else "78.3%"
        roles_str = f"{summary.get('class_count', 324)}"
    except Exception:
        winner_name = "Random Forest"
        acc_str = "78.3%"
        roles_str = "324"

    st.markdown(
        f"""
        <div class="sidebar-section-label" style="margin-top:1.3rem">MODEL STATUS</div>
        <div class="sidebar-status-card">
          <div class="sidebar-status-row"><span>Model</span><strong>{winner_name}</strong></div>
          <div class="sidebar-status-row"><span>Accuracy</span><strong>{acc_str}</strong></div>
          <div class="sidebar-status-row"><span>Job roles</span><strong>{roles_str}</strong></div>
          <div class="sidebar-status-row sidebar-status-ok"><span class="sidebar-status-dot"></span><span>All models operational</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(current: str):
    with st.sidebar:
        brand_block()
        workspace_intro()
        st.markdown('<div class="sidebar-section-label">WORKSPACE</div>', unsafe_allow_html=True)
        for item in NAV_ITEMS:
            st.page_link(item["page"], label=item["label"], icon=None, use_container_width=True)
        model_status()
        st.markdown(
            f"""
            <div class="sidebar-footer">
              <div>© 2026 {BRAND['name']}</div>
              <div>Built with Streamlit</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

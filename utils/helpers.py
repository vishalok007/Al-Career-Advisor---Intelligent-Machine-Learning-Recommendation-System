"""Reusable UI helpers (all left-aligned, dark-theme safe)."""
from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from utils.constants import DOMAIN_COLORS


def inject_css(path: str = "assets/styles.css"):
    try:
        with open(path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        pass


def page_header(title: str, subtitle: str | None = None, icon: str | None = None,
                eyebrow: str | None = None):
    """Render a wide hero-style header aligned left-to-right."""
    eyebrow_html = f'<div class="eyebrow">{eyebrow}</div>' if eyebrow else ""
    sub_html = f'<p>{subtitle}</p>' if subtitle else ""
    st.markdown(
        f'<div class="hero fade-up">{eyebrow_html}<h1>{title}</h1>{sub_html}</div>',
        unsafe_allow_html=True,
    )


def section_title(text: str, eyebrow: str | None = None):
    eyebrow_html = (
        f'<div class="eyebrow" style="margin:.5rem 0 .2rem">{eyebrow}</div>' if eyebrow else ""
    )
    st.markdown(f'{eyebrow_html}<h2 style="margin:.2rem 0 .6rem">{text}</h2>', unsafe_allow_html=True)


def kpi_card(label: str, value: str, delta: str | None = None,
             delta_dir: str = "up", icon: str | None = None):
    """Render a KPI card without decorative icons."""
    arrow = "▲" if delta_dir == "up" else "▼"
    delta_html = (
        f'<div class="kpi-d" style="color:{"#7fb88b" if delta_dir=="up" else "#d87a6a"}">{arrow} {delta}</div>'
        if delta else ""
    )
    st.markdown(
        f'<div class="card fade-up" style="display:flex;justify-content:space-between;align-items:flex-start">'
        f'<div class="kpi"><div class="kpi-l">{label}</div><div class="kpi-v">{value}</div>{delta_html}</div></div>',
        unsafe_allow_html=True,
    )


def prediction_card(rank: int, job: str, score: float):
    """Top-K job card with numeric rank badge and score bar."""
    badge_cls = {1: "medal g", 2: "medal s", 3: "medal b"}.get(rank, "medal s")
    pct = max(0.0, min(1.0, score)) * 100
    st.markdown(
        f'<div class="prediction-card fade-up">'
        f'<div class="{badge_cls}">{rank}</div>'
        f'<div style="flex:1"><div style="font-weight:600;font-size:1.02rem">{job}</div>'
        f'<div style="font-size:.78rem;color:var(--text-soft);margin-top:.15rem">Confidence {pct:.1f}%</div>'
        f'<div class="score-bar"><div style="width:{pct:.1f}%"></div></div></div></div>',
        unsafe_allow_html=True,
    )


def pill(text: str, kind: str = "default", icon: str | None = None):
    """Render a horizontal stream of pills in a single block."""
    cls = "pill" + (f" {kind}" if kind and kind != "default" else "")
    return f'<span class="{cls}" style="display:inline-block;margin:.18rem .3rem .18rem 0">{text}</span>'


def empty_state(icon: str, title: str, hint: str):
    st.markdown(
        f'<div class="card fade-up" style="text-align:center;padding:2.2rem 1rem">'
        f'<div style="font-weight:600;font-size:1.05rem;margin-top:.2rem">{title}</div>'
        f'<div style="color:var(--text-soft);font-size:.9rem;margin-top:.4rem">{hint}</div></div>',
        unsafe_allow_html=True,
    )


def progress_bar(value: float, label: str | None = None):
    pct = max(0.0, min(1.0, value)) * 100
    label_html = (
        f'<div style="display:flex;justify-content:space-between;font-size:.82rem;color:var(--text-soft);margin-bottom:.25rem">'
        f'<span>{label}</span><span>{pct:.0f}%</span></div>' if label else ""
    )
    st.markdown(f"{label_html}<div class='coverage'><div style='width:{pct:.1f}%'></div></div>", unsafe_allow_html=True)


def coverage_card(label: str, matched: int, total: int):
    pct = (matched / total * 100) if total else 0
    st.markdown(
        f'<div class="card">'
        f'<div class="card-t">{label}</div>'
        f'<div class="card-s">{matched} of {total} skills matched</div>'
        f'<div class="coverage" style="margin-top:.6rem"><div style="width:{pct:.1f}%"></div></div>'
        f'<div style="text-align:right;color:var(--text-soft);font-size:.78rem;margin-top:.3rem">{pct:.0f}% covered</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def domain_pill(domain: str) -> str:
    color = DOMAIN_COLORS.get(domain, DOMAIN_COLORS["General"])
    return f'<span class="pill" style="background:{color}22;color:{color};border-color:{color}55;font-weight:600">{domain}</span>'


@st.cache_resource(show_spinner=False)
def read_json(path: str):
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


@st.cache_data(show_spinner=False)
def read_csv_cached(path: str) -> pd.DataFrame:
    return pd.read_csv(path)

"""Live Job Match Cards Component.

Renders ranked live job postings with fit score meters, verified company links,
dynamic board Apply buttons, location/salary badges, and skill overlap breakdowns.
"""
from __future__ import annotations
import html as _html
import streamlit as st
from utils.helpers import pill

def _esc(text: str) -> str:
    return _html.escape(str(text or ""), quote=True)

def render_live_job_cards(semantic_matches: list[dict]) -> None:
    """Render structured, premium job cards for ranked semantic matches."""
    if not semantic_matches:
        st.info("No live job matches found for this profile.")
        return

    st.markdown(
        '<div class="eyebrow" style="margin-top:1.2rem">Top live job matches</div>'
        '<h2 style="margin:.1rem 0 .4rem">Explainable live postings & verified links</h2>'
        '<div style="font-size:.88rem;color:#a4c2b0;margin-bottom:1rem">'
        'ℹ️ Each card points directly to the verified listing on partner boards (Remotive, Arbeitnow, RemoteOK, The Muse). '
        'Clicking <strong>Apply on [Provider] ↗</strong> opens the specific job description page for that position.'
        '</div>',
        unsafe_allow_html=True,
    )

    for idx, match in enumerate(semantic_matches, 1):
        fit_score = float(match.get("fit_score", 0.0))
        company = (match.get("company") or "Hiring Company").strip()
        title = (match.get("title") or "Job Title").strip()
        location = (match.get("location") or "Remote").strip()
        source = (match.get("source") or "Live Provider").strip()
        salary = (match.get("salary") or "").strip()
        apply_url = (match.get("apply_url") or match.get("url") or "").strip()
        company_url = (match.get("company_url") or "").strip()

        matched_skills = (match.get("matched_skills") or [])[:6]
        missing_skills = (match.get("missing_skills") or [])[:6]

        initials = "".join([w[:1].upper() for w in company.split()][:2]) or "JP"
        fit_badge_bg = (
            "linear-gradient(135deg, #244b41 0%, #7aa597 100%)" if fit_score >= 80 else (
                "linear-gradient(135deg, #2b3a42 0%, #4a6fa5 100%)" if fit_score >= 65 else "linear-gradient(135deg, #3d2b22 0%, #d49966 100%)"
            )
        )

        matched_pills = "".join(pill(s, "success") for s in matched_skills) or pill("General skill match")
        missing_pills = "".join(pill(s, "warn") for s in missing_skills) or pill("No critical gaps", "success")

        apply_button_html = (
            f'<a href="{_esc(apply_url)}" target="_blank" rel="noopener noreferrer" '
            f'style="display:inline-flex;align-items:center;gap:.35rem;background:#7aa597;color:#0a1814;'
            f'padding:.5rem 1.1rem;border-radius:.45rem;text-decoration:none;font-weight:700;font-size:.9rem;'
            f'box-shadow:0 2px 8px rgba(122,165,151,.35);transition:all .2s ease">Apply on {_esc(source)} ↗</a>'
            if apply_url else
            '<span style="color:#7aa597;font-size:.85rem;opacity:.7">Apply unavailable</span>'
        )

        company_button_html = (
            f'<a href="{_esc(company_url)}" target="_blank" rel="noopener noreferrer" '
            f'style="display:inline-flex;align-items:center;gap:.3rem;background:rgba(255,255,255,.08);color:#d9e3dd;'
            f'padding:.5rem .9rem;border-radius:.45rem;text-decoration:none;font-weight:600;font-size:.85rem;'
            f'border:1px solid rgba(255,255,255,.12)">Company Info ↗</a>'
            if company_url else ''
        )

        salary_html = f'<span style="color:#f1c161;font-size:.85rem;font-weight:600">💰 {_esc(salary)}</span>' if salary else ''

        card_html = (
            f'<div class="card fade-up" style="margin-bottom:1rem;background:#10221d;border:1px solid rgba(122,165,151,.25);border-radius:.75rem;padding:1.2rem">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:.8rem">'
            f'<div style="display:flex;align-items:center;gap:1rem">'
            f'<div style="width:2.8rem;height:2.8rem;border-radius:.6rem;background:#244b41;color:#f1c161;display:flex;align-items:center;justify-content:center;font-weight:800;font-size:1.1rem;border:1px solid rgba(241,193,97,.3)">{_esc(initials)}</div>'
            f'<div>'
            f'<div style="font-size:1.15rem;font-weight:700;color:#f4f7f5">{_esc(title)}</div>'
            f'<div style="color:#a4c2b0;font-size:.88rem;margin-top:.15rem">{_esc(company)} · 📍 {_esc(location)} · <span style="background:rgba(255,255,255,.08);padding:.15rem .45rem;border-radius:.3rem;font-weight:600">{_esc(source)}</span></div>'
            f'</div>'
            f'</div>'
            f'<div style="background:{fit_badge_bg};color:#ffffff;padding:.4rem .85rem;border-radius:.5rem;text-align:center;box-shadow:0 3px 10px rgba(0,0,0,.3)">'
            f'<div style="font-size:1.1rem;font-weight:800">{fit_score:.1f}%</div>'
            f'<div style="font-size:.7rem;text-transform:uppercase;letter-spacing:.05em;opacity:.9">Fit Score</div>'
            f'</div>'
            f'</div>'
            f'<div style="margin-top:1rem;padding-top:.8rem;border-top:1px solid rgba(255,255,255,.06);display:flex;gap:.8rem;align-items:center;flex-wrap:wrap">'
            f'{apply_button_html}'
            f'{company_button_html}'
            f'{salary_html}'
            f'</div>'
            f'<div style="margin-top:1rem;display:grid;gap:.5rem">'
            f'<div><span style="font-size:.78rem;color:#7aa597;font-weight:700;text-transform:uppercase;margin-right:.4rem">Matched Skills:</span>{matched_pills}</div>'
            f'<div><span style="font-size:.78rem;color:#d49966;font-weight:700;text-transform:uppercase;margin-right:.4rem">Missing Skills:</span>{missing_pills}</div>'
            f'</div>'
            f'</div>'
        )
        st.markdown(card_html, unsafe_allow_html=True)

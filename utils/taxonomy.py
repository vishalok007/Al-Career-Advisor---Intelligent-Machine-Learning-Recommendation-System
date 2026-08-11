"""Hierarchical Career Taxonomy & O*NET Standard Mapping Engine.

Provides a structured 3-tier taxonomy (Domain -> Role Family -> Seniority Level)
and standardized O*NET-SOC occupation classification for tech career roles.
"""
from __future__ import annotations
import re
from typing import TypedDict

class TaxonomyNode(TypedDict):
    domain: str
    family: str
    level: str
    onet_code: str
    onet_title: str

# 3-Tier Career Taxonomy Map: Domain -> Sub-Family -> Standard Roles & O*NET Codes
TAXONOMY_HIERARCHY: dict[str, dict[str, list[dict[str, str]]]] = {
    "AI & Data Science": {
        "Machine Learning Engineering": [
            {"title": "Machine Learning Engineer", "level": "Mid-Senior", "onet": "15-1252.00"},
            {"title": "Senior ML Engineer", "level": "Senior", "onet": "15-1252.00"},
            {"title": "AI Research Scientist", "level": "Senior/Lead", "onet": "15-1221.00"},
            {"title": "MLOps Engineer", "level": "Mid-Senior", "onet": "15-1252.00"},
            {"title": "Prompt / LLM Engineer", "level": "Mid-Senior", "onet": "15-1252.00"},
        ],
        "Data Engineering & Analytics": [
            {"title": "Data Scientist", "level": "Mid-Senior", "onet": "15-2051.00"},
            {"title": "Data Engineer", "level": "Mid-Senior", "onet": "15-1243.00"},
            {"title": "Senior Data Engineer", "level": "Senior", "onet": "15-1243.00"},
            {"title": "Data Analyst", "level": "Associate/Mid", "onet": "15-2051.01"},
            {"title": "Business Intelligence Engineer", "level": "Mid-Senior", "onet": "15-2051.02"},
        ],
    },
    "Software & Web Engineering": {
        "Backend Development": [
            {"title": "Backend Developer", "level": "Associate/Mid", "onet": "15-1252.00"},
            {"title": "Senior Backend Engineer", "level": "Senior", "onet": "15-1252.00"},
            {"title": "Python Developer", "level": "Mid-Senior", "onet": "15-1252.00"},
            {"title": "API Architect", "level": "Lead/Principal", "onet": "15-1252.00"},
        ],
        "Frontend & Fullstack": [
            {"title": "Frontend Developer", "level": "Associate/Mid", "onet": "15-1254.00"},
            {"title": "Full Stack Engineer", "level": "Mid-Senior", "onet": "15-1254.00"},
            {"title": "UI/UX Developer", "level": "Mid-Senior", "onet": "15-1255.00"},
            {"title": "React Developer", "level": "Mid-Senior", "onet": "15-1254.00"},
        ],
    },
    "Cloud & DevOps": {
        "Infrastructure & Cloud": [
            {"title": "Cloud Engineer", "level": "Mid-Senior", "onet": "15-1244.00"},
            {"title": "DevOps Engineer", "level": "Mid-Senior", "onet": "15-1244.00"},
            {"title": "Site Reliability Engineer (SRE)", "level": "Senior", "onet": "15-1244.00"},
            {"title": "Cloud Architect", "level": "Lead/Principal", "onet": "15-1241.00"},
        ],
        "Cybersecurity": [
            {"title": "Security Analyst", "level": "Mid-Senior", "onet": "15-1212.00"},
            {"title": "Cybersecurity Engineer", "level": "Mid-Senior", "onet": "15-1212.00"},
            {"title": "Penetration Tester", "level": "Mid-Senior", "onet": "15-1212.00"},
        ],
    },
    "Product & Management": {
        "Product & Agile": [
            {"title": "Product Manager", "level": "Mid-Senior", "onet": "11-9041.00"},
            {"title": "Technical Program Manager", "level": "Senior", "onet": "11-9041.00"},
            {"title": "Scrum Master", "level": "Mid-Senior", "onet": "11-9041.00"},
        ],
    },
}

ONET_DESCRIPTIONS: dict[str, str] = {
    "15-1252.00": "Software Developers & Machine Learning Engineers — Research, design, and develop software & ML algorithms.",
    "15-2051.00": "Data Scientists — Develop and implement mathematical/statistical models to derive insights from complex datasets.",
    "15-1243.00": "Database Architects & Data Engineers — Design and build data pipelines, data warehouses, and scalable schemas.",
    "15-1244.00": "Network & Cloud Engineers — Build, configure, and optimize cloud infrastructure, CI/CD, and DevOps automation.",
    "15-1254.00": "Web & Digital Interface Developers — Design, build, and optimize dynamic web and web-application interfaces.",
    "15-1212.00": "Information Security Analysts — Monitor and protect networks, systems, and cloud infrastructure from threats.",
    "11-9041.00": "Architectural and Engineering Managers — Plan, direct, and coordinate technology products, teams, and sprints.",
}


def _detect_seniority_level(title: str) -> str:
    low = title.lower()
    if any(k in low for k in ["lead", "principal", "head", "staff", "director", "architect"]):
        return "Lead / Principal"
    if any(k in low for k in ["senior", "sr.", "sr ", "5+"]):
        return "Senior Level"
    if any(k in low for k in ["junior", "jr.", "jr ", "intern", "associate", "entry"]):
        return "Entry / Associate"
    return "Mid-Senior Level"


def resolve_hierarchical_role(predicted_role: str, skills: list[str] | None = None) -> TaxonomyNode:
    """Map any target or predicted role to its 3-tier taxonomy node & O*NET SOC code."""
    title_norm = (predicted_role or "Software Engineer").strip()
    title_low = title_norm.lower()

    # Match against taxonomy tree
    for domain, families in TAXONOMY_HIERARCHY.items():
        for family, roles in families.items():
            for role in roles:
                role_title_low = role["title"].lower()
                if role_title_low in title_low or title_low in role_title_low:
                    return {
                        "domain": domain,
                        "family": family,
                        "level": _detect_seniority_level(title_norm),
                        "onet_code": role["onet"],
                        "onet_title": ONET_DESCRIPTIONS.get(role["onet"], role["title"]),
                    }

    # Keyword fallback classification
    if any(k in title_low for k in ["data sci", "ml ", "machine learning", "ai ", "deep learning", "nlp", "llm"]):
        return {
            "domain": "AI & Data Science",
            "family": "Machine Learning Engineering",
            "level": _detect_seniority_level(title_norm),
            "onet_code": "15-1252.00",
            "onet_title": ONET_DESCRIPTIONS["15-1252.00"],
        }
    if any(k in title_low for k in ["data eng", "data analyst", "bi ", "analytics", "sql"]):
        return {
            "domain": "AI & Data Science",
            "family": "Data Engineering & Analytics",
            "level": _detect_seniority_level(title_norm),
            "onet_code": "15-2051.00",
            "onet_title": ONET_DESCRIPTIONS["15-2051.00"],
        }
    if any(k in title_low for k in ["devops", "cloud", "sre", "aws", "kubernetes", "infra"]):
        return {
            "domain": "Cloud & DevOps",
            "family": "Infrastructure & Cloud",
            "level": _detect_seniority_level(title_norm),
            "onet_code": "15-1244.00",
            "onet_title": ONET_DESCRIPTIONS["15-1244.00"],
        }
    if any(k in title_low for k in ["security", "cyber", "pentest"]):
        return {
            "domain": "Cloud & DevOps",
            "family": "Cybersecurity",
            "level": _detect_seniority_level(title_norm),
            "onet_code": "15-1212.00",
            "onet_title": ONET_DESCRIPTIONS["15-1212.00"],
        }

    # Default fallback
    return {
        "domain": "Software & Web Engineering",
        "family": "Backend Development",
        "level": _detect_seniority_level(title_norm),
        "onet_code": "15-1252.00",
        "onet_title": ONET_DESCRIPTIONS["15-1252.00"],
    }


def get_taxonomy_breadcrumbs(predicted_role: str) -> str:
    """Return a formatted breadcrumb representation of the taxonomy hierarchy."""
    node = resolve_hierarchical_role(predicted_role)
    return f"{node['domain']} › {node['family']} › {node['level']} ({node['onet_code']})"

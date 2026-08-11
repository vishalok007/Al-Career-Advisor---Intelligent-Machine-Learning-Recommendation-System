from __future__ import annotations

import re
import urllib.parse
from typing import Iterable


def _slugify(value: str) -> str:
    """Lower-case, hyphen-separated slug safe for URL paths."""
    value = (value or "").strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-") or "jobs"


def _quote(value: str) -> str:
    return urllib.parse.quote_plus((value or "").strip())


def _norm_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class Portal:
    def __init__(self, name: str, base: str, region: str, build):
        self.name = name
        self.base = base
        self.region = region
        self.build = build


def _build_naukri(role: str, skills: list, location: str, experience: int):
    role_slug = _slugify(role)
    query = " ".join([role] + (skills[:3] if skills else []))
    path = f"https://www.naukri.com/{role_slug}-jobs"
    url = (
        f"{path}"
        f"?k={_quote(query)}"
        f"&experience={max(0, min(experience, 30))}"
        f"&cityType=id:{_slugify(location) if location else 'india'}"
    )
    return {
        "url": url,
        "region": "India + global remote",
        "fit_reason": "Largest Indian job portal with strong IT/tech coverage.",
        "apply_hint": "Pre-filtered by role, experience, and your top 3 skills.",
        "format": "Search results page (live)",
    }


def _build_hirist(role: str, skills: list, location: str, experience: int):
    """Hirist working URL: /search?keyword=&exp=&loc= (verified live)."""
    query = " ".join([role] + (skills[:3] if skills else []))
    loc = (location or "").strip() or "India"
    url = (
        "https://www.hirist.tech/search"
        f"?keyword={_quote(query)}"
        f"&exp={max(0, min(experience, 30))}"
        f"&loc={_quote(loc)}"
    )
    return {
        "url": url,
        "region": "India (IT niche)",
        "fit_reason": "IT-only portal — best filter-to-noise ratio for tech resumes.",
        "apply_hint": "Niche IT openings with skill-tagged listings.",
        "format": "Search results page (live)",
    }


def _build_wellfound(role: str, skills: list, location: str, experience: int):
    query = " ".join([role] + (skills[:2] if skills else []))
    url = (
        "https://wellfound.com/jobs"
        f"?q={_quote(query)}"
        f"&remote=false"
        f"&us=true"
    )
    return {
        "url": url,
        "region": "Global startups (ex-AngelList)",
        "fit_reason": "Best fit for startup / equity-heavy / product culture roles.",
        "apply_hint": "Startup-tagged listings; equity & remote filters applied.",
        "format": "Search results page (live)",
    }


def _build_dice(role: str, skills: list, location: str, experience: int):
    query = " ".join([role] + (skills[:3] if skills else []))
    url = (
        "https://www.dice.com/jobs"
        f"?q={_quote(query)}"
        f"&location={_quote(location or 'United States')}"
        f"&e={max(0, min(experience, 30))}"
    )
    return {
        "url": url,
        "region": "USA tech (enterprise)",
        "fit_reason": "Strongest US enterprise-tech — banking, defence, SaaS.",
        "apply_hint": "US tech market search with your role + skills + location.",
        "format": "Search results page (live)",
    }


PORTALS: list[Portal] = [
    Portal(
        name="Naukri.com",
        base="https://www.naukri.com",
        region="India",
        build=_build_naukri,
    ),
    Portal(
        name="Hirist",
        base="https://www.hirist.tech",
        region="India",
        build=_build_hirist,
    ),
    Portal(
        name="Wellfound",
        base="https://wellfound.com",
        region="Global",
        build=_build_wellfound,
    ),
    Portal(
        name="Dice",
        base="https://www.dice.com",
        region="USA",
        build=_build_dice,
    ),
]


_ROLE_DOMAIN_HINTS = {
    "ai & data science": ["wellfound", "dice", "hirist", "naukri"],
    "software development": ["wellfound", "dice", "hirist", "naukri"],
    "cloud & devops": ["dice", "wellfound", "hirist", "naukri"],
    "cyber security": ["dice", "wellfound", "hirist", "naukri"],
    "general": ["naukri", "wellfound", "hirist", "dice"],
}

_LOCATION_REGION = {
    "india": ["naukri", "hirist", "wellfound", "dice"],
    "indian": ["naukri", "hirist", "wellfound", "dice"],
    "bangalore": ["naukri", "hirist", "wellfound", "dice"],
    "bengaluru": ["naukri", "hirist", "wellfound", "dice"],
    "hyderabad": ["naukri", "hirist", "wellfound", "dice"],
    "pune": ["naukri", "hirist", "wellfound", "dice"],
    "delhi": ["naukri", "hirist", "wellfound", "dice"],
    "mumbai": ["naukri", "hirist", "wellfound", "dice"],
    "usa": ["dice", "wellfound", "naukri", "hirist"],
    "united states": ["dice", "wellfound", "naukri", "hirist"],
    "us": ["dice", "wellfound", "naukri", "hirist"],
    "remote": ["wellfound", "dice", "hirist", "naukri"],
    "global": ["wellfound", "dice", "naukri", "hirist"],
}


def _portal_key(portal: Portal) -> str:
    return portal.name.split(".")[0].lower().replace(" ", "")


def recommend_portals(
    role: str,
    skills: Iterable[str],
    location: str,
    experience: int,
    domain: str = "General",
    location_hint: str | None = None,
) -> list[dict]:
    """Return a list of {name, url, region, fit_score, fit_reason, ...} for each portal.

    Sorted high to low by fit_score.
    """
    skills_list = [s.strip() for s in (skills or []) if isinstance(s, str) and s.strip()]
    exp = _norm_int(experience, 0)

    domain_rank = _ROLE_DOMAIN_HINTS.get((domain or "").lower(), _ROLE_DOMAIN_HINTS["general"])
    loc = (location_hint or location or "").strip().lower()
    location_rank = _LOCATION_REGION.get(loc, _LOCATION_REGION["global"])
    skill_density = min(len(skills_list), 5)

    out = []
    for p in PORTALS:
        key = _portal_key(p)
        info = p.build(role, skills_list, location, exp)
        score = 60
        score += max(0, 30 - domain_rank.index(key) * 10) if key in domain_rank else 0
        score += max(0, 20 - location_rank.index(key) * 8) if key in location_rank else 0
        if exp >= 5 and key in {"dice", "wellfound"}:
            score += 5
        if exp <= 2 and key in {"naukri", "hirist"}:
            score += 5
        score += skill_density * 1.0

        out.append({
            "name": p.name,
            "url": info["url"],
            "region": info["region"],
            "fit_reason": info["fit_reason"],
            "apply_hint": info["apply_hint"],
            "format": info["format"],
            "fit_score": int(min(100, max(0, score))),
        })

    out.sort(key=lambda r: r["fit_score"], reverse=True)
    return out


def primary_recommendation(recs):
    return recs[0] if recs else None

from __future__ import annotations
import re
from typing import IO
import pdfplumber
from utils.skill_proficiency import KNOWN_SKILLS
from utils.semantic_matching import extract_skills_from_job_text, extract_years_required

_TITLE_PATTERNS = [
    re.compile(r"^\s*job\s*title\s*[:\-]\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*position\s*[:\-]\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*role\s*[:\-]\s*(.+)$", re.IGNORECASE | re.MULTILINE),
    re.compile(r"^\s*title\s*[:\-]\s*(.+)$", re.IGNORECASE | re.MULTILINE),
]


def parse_jd_pdf(uploaded: IO[bytes]) -> dict:
    text = ""
    with pdfplumber.open(uploaded) as pdf:
        for page in pdf.pages:
            t = page.extract_text()
            if t:
                text += t + "\n"
    return _parse_jd_text(text)


def parse_jd_text(text: str) -> dict:
    return _parse_jd_text(text)


def _parse_jd_text(text: str) -> dict:
    return {
        "raw_text": text or "",
        "title": _extract_title(text),
        "skills": extract_skills_from_job_text(text or "", []),
        "min_years": extract_years_required(text or "")[0],
        "max_years": extract_years_required(text or "")[1],
        "char_count": len(text or ""),
    }


def _extract_title(text: str) -> str | None:
    if not text:
        return None
    for pat in _TITLE_PATTERNS:
        match = pat.search(text)
        if match:
            return match.group(1).strip().split("\n")[0][:120]
    # Fallback — first non-empty line that doesn't look like a section header.
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if len(line) > 95:
            continue
        if ":" in line:
            continue
        if line.isupper() and len(line.split()) > 6:
            continue
        return line[:120]
    return None


def extract_jd_skills_only(text: str) -> list[str]:
    """Public helper — only the skills list, no other parsing."""
    return extract_skills_from_job_text(text or "", [])

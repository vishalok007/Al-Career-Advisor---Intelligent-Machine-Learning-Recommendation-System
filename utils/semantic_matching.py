"""Semantic candidate-to-job matching utilities.

Design goals
------------
1. Build a rich candidate representation from skills, predicted role, domain,
   education, and experience.
2. Score live job postings with cosine similarity over TF-IDF embeddings today.
3. Keep the scorer pluggable so a cross-encoder can be swapped in later.
4. Expose recruiter-friendly explanations: overlap, missing skills, experience fit.
5. Penalise obviously off-target results whose titles do not align with the
   predicted role, so live-provider noise does not dominate the ranking.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
import html
import re
from typing import Iterable

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from utils.constants import SKILL_CATEGORIES
from utils.job_skills import JOB_REQUIRED_SKILLS


ROLE_WORD_BLACKLIST = {
    "and", "for", "with", "the", "a", "an", "of", "to", "in", "on",
    "sr", "jr", "senior", "junior", "lead", "staff", "principal",
}


def _ordered_unique(items: Iterable[str]) -> list[str]:
    out, seen = [], set()
    for item in items or []:
        token = str(item).strip()
        if not token:
            continue
        key = token.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(token)
    return out


def _normalize_skills(skills: Iterable[str]) -> list[str]:
    return _ordered_unique(skills)


def _normalize_skill_set(skills: Iterable[str]) -> set[str]:
    return {s.lower() for s in _normalize_skills(skills)}


def _flatten_skill_catalog() -> list[str]:
    skills = []
    for bucket in SKILL_CATEGORIES.values():
        skills.extend(bucket)
    for bucket in JOB_REQUIRED_SKILLS.values():
        skills.extend(bucket)
    skills.extend([
        "LLM", "Generative AI", "Prompt Engineering", "LangGraph",
        "Vector Database", "PostgreSQL", "Redis", "FastAPI", "Flask",
        "Django", "REST API", "CI/CD", "Airflow", "Snowflake",
        "MLOps", "ETL", "Spark", "Hadoop", "Tableau", "Power BI",
    ])
    return _ordered_unique(skills)


KNOWN_SKILLS = _flatten_skill_catalog()


def strip_html(text: str) -> str:
    text = html.unescape(text or "")
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _tokenize(text: str) -> list[str]:
    return [
        token for token in re.findall(r"[a-z0-9+#.]+", (text or "").lower())
        if len(token) > 1 and token not in ROLE_WORD_BLACKLIST
    ]


def _title_alignment(predicted_role: str, title: str, description: str = "", tags: Iterable[str] | None = None) -> float:
    role_tokens = set(_tokenize(predicted_role))
    title_tokens = set(_tokenize(title))
    desc_tokens = set(_tokenize(" ".join([title, " ".join(tags or []), strip_html(description)[:500]])))

    if not role_tokens:
        return 0.5

    exact_role = predicted_role.strip().lower()
    title_low = (title or "").strip().lower()
    if exact_role and (exact_role in title_low or title_low in exact_role):
        return 1.0

    title_overlap = len(role_tokens & title_tokens) / len(role_tokens) if role_tokens else 0.0
    desc_overlap = len(role_tokens & desc_tokens) / len(role_tokens) if role_tokens else 0.0

    score = (0.75 * title_overlap) + (0.25 * desc_overlap)

    # Common live-feed noise reduction: if neither the title nor the first chunk
    # of the description mentions any role token, this posting is likely off-target.
    if title_overlap == 0 and desc_overlap == 0:
        return 0.0
    return min(1.0, score)


def extract_skills_from_job_text(text: str, tags: Iterable[str] | None = None) -> list[str]:
    haystack = f"{strip_html(text)} {' '.join(tags or [])}".lower()
    found = []
    for skill in KNOWN_SKILLS:
        pattern = rf"(?<![a-z0-9]){re.escape(skill.lower())}(?![a-z0-9])"
        if re.search(pattern, haystack):
            found.append(skill)
    return _ordered_unique(found)


def extract_years_required(text: str) -> tuple[int | None, int | None]:
    low_text = strip_html(text).lower()
    patterns = [
        r"(\d{1,2})\s*\+?\s*(?:to|-|–)\s*(\d{1,2})\s+years",
        r"(\d{1,2})\s*\+\s*years",
        r"minimum\s+of\s+(\d{1,2})\s+years",
        r"at\s+least\s+(\d{1,2})\s+years",
        r"(\d{1,2})\s+years\s+of\s+experience",
    ]
    for idx, pattern in enumerate(patterns):
        match = re.search(pattern, low_text)
        if not match:
            continue
        if idx == 0:
            return int(match.group(1)), int(match.group(2))
        value = int(match.group(1))
        return value, None
    return None, None


def candidate_profile_text(
    predicted_role: str,
    skills: Iterable[str],
    experience_years: int,
    education: str = "",
    domain: str = "",
) -> str:
    skills = _normalize_skills(skills)
    role_block = " ".join([
        f"Target role {predicted_role}.",
        f"Predicted role {predicted_role}.",
        f"Candidate is targeting {predicted_role} opportunities.",
    ])
    exp_block = (
        f"Experience {experience_years} years. "
        f"Candidate is a {experience_years}-year professional."
    )
    edu_block = f"Education {education}." if education else ""
    domain_block = f"Career domain {domain}." if domain else ""
    skill_block = " ".join(
        [
            "Core skills " + ", ".join(skills) + "." if skills else "",
            "Skill keywords " + " ".join(skills) + "." if skills else "",
            "Preferred tooling " + " ; ".join(skills[:8]) + "." if skills else "",
        ]
    ).strip()
    return " ".join([part for part in [role_block, exp_block, edu_block, domain_block, skill_block] if part]).strip()


def job_profile_text(job: dict) -> str:
    title = job.get("title", "")
    company = job.get("company", "")
    location = job.get("location", "")
    employment_type = job.get("employment_type", "")
    tags = job.get("tags", []) or []
    description = strip_html(job.get("description", ""))
    return " ".join(
        [
            f"Job title {title}.",
            f"Company {company}." if company else "",
            f"Location {location}." if location else "",
            f"Employment type {employment_type}." if employment_type else "",
            f"Tags {' '.join(tags)}." if tags else "",
            description,
        ]
    ).strip()


@dataclass
class MatchResult:
    title: str
    company: str
    location: str
    url: str
    source: str
    source_key: str
    fit_score: float
    semantic_score: float
    title_alignment_score: float
    skill_overlap_ratio: float
    experience_score: float
    matched_skills: list[str]
    missing_skills: list[str]
    extracted_job_skills: list[str]
    employment_type: str
    published_at: str
    salary: str
    summary: str
    company_url: str = ""
    apply_url: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


class CosineSimilarityScorer:
    name = "cosine"

    def score(self, candidate_text: str, job_texts: list[str]) -> list[float]:
        if not job_texts:
            return []
        vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=4000)
        matrix = vectorizer.fit_transform([candidate_text] + job_texts)
        candidate_vec = matrix[0:1]
        job_vecs = matrix[1:]
        sims = cosine_similarity(candidate_vec, job_vecs)[0]
        return [float(v) for v in sims]


class SentenceTransformerScorer:
    """Dense vector embedding scorer using SentenceTransformers ('all-MiniLM-L6-v2')."""
    name = "embeddings"
    _model = None

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name

    def _get_model(self):
        if SentenceTransformerScorer._model is None:
            from sentence_transformers import SentenceTransformer
            SentenceTransformerScorer._model = SentenceTransformer(self.model_name)
        return SentenceTransformerScorer._model

    def score(self, candidate_text: str, job_texts: list[str]) -> list[float]:
        if not job_texts:
            return []
        try:
            model = self._get_model()
            cand_emb = model.encode([candidate_text], normalize_embeddings=True)
            job_embs = model.encode(job_texts, normalize_embeddings=True)
            sims = cosine_similarity(cand_emb, job_embs)[0]
            return [float(v) for v in sims]
        except Exception:
            # Fallback to TF-IDF if SentenceTransformers is not installed or fails
            return CosineSimilarityScorer().score(candidate_text, job_texts)


def get_scorer(name: str = "embeddings"):
    name_low = (name or "embeddings").lower()
    if name_low in {"embeddings", "transformer", "sentence-transformer", "dense"}:
        try:
            return SentenceTransformerScorer()
        except Exception:
            return CosineSimilarityScorer()
    return CosineSimilarityScorer()


def _experience_fit(candidate_years: int, description_text: str) -> float:
    min_years, max_years = extract_years_required(description_text)
    if min_years is None and max_years is None:
        return 0.75
    if max_years is not None and min_years is not None:
        if min_years <= candidate_years <= max_years:
            return 1.0
        if candidate_years < min_years:
            gap = min_years - candidate_years
            return max(0.25, 1 - 0.18 * gap)
        gap = candidate_years - max_years
        return max(0.45, 1 - 0.08 * gap)
    if min_years is not None:
        if candidate_years >= min_years:
            return 1.0
        gap = min_years - candidate_years
        return max(0.2, 1 - 0.2 * gap)
    return 0.75


def _fit_label(score: float) -> str:
    if score >= 85:
        return "Excellent semantic fit"
    if score >= 72:
        return "Strong match"
    if score >= 58:
        return "Promising match"
    return "Stretch match"


def rank_job_matches(
    predicted_role: str,
    skills: Iterable[str],
    experience_years: int,
    jobs: list[dict],
    education: str = "",
    domain: str = "",
    scorer_name: str = "cosine",
    top_k: int = 10,
) -> list[dict]:
    if not jobs:
        return []

    candidate_skills = _normalize_skills(skills)
    candidate_skill_set = _normalize_skill_set(candidate_skills)
    candidate_text = candidate_profile_text(
        predicted_role=predicted_role,
        skills=candidate_skills,
        experience_years=experience_years,
        education=education,
        domain=domain,
    )
    job_texts = [job_profile_text(job) for job in jobs]
    scorer = get_scorer(scorer_name)
    semantic_scores = scorer.score(candidate_text, job_texts)

    ranked = []
    for job, semantic in zip(jobs, semantic_scores):
        extracted_skills = extract_skills_from_job_text(job.get("description", ""), job.get("tags", []))
        extracted_skill_set = {s.lower() for s in extracted_skills}
        matched = [s for s in extracted_skills if s.lower() in candidate_skill_set]
        missing = [s for s in extracted_skills if s.lower() not in candidate_skill_set]
        overlap = (len(matched) / len(extracted_skills)) if extracted_skills else 0.0
        experience_score = _experience_fit(experience_years, job.get("description", ""))
        title_alignment = _title_alignment(
            predicted_role=predicted_role,
            title=job.get("title", ""),
            description=job.get("description", ""),
            tags=job.get("tags", []),
        )

        # Final fit score uses cosine similarity as the backbone, strengthened by
        # title-role alignment, skill overlap, and experience fit.
        fit = (0.5 * semantic) + (0.2 * overlap) + (0.1 * experience_score) + (0.2 * title_alignment)

        # If a job is clearly off-target by title and has no extracted skill overlap,
        # heavily discount it so generic feed noise sinks below relevant roles.
        if title_alignment < 0.15 and overlap == 0:
            fit *= 0.45
        elif title_alignment < 0.3 and overlap == 0:
            fit *= 0.7

        fit_score = round(max(0.0, min(1.0, fit)) * 100, 1)

        summary = _fit_label(fit_score)
        if matched:
            summary += f" · overlap: {', '.join(matched[:4])}"
        elif missing:
            summary += f" · likely gaps: {', '.join(missing[:3])}"
        ranked.append(
            MatchResult(
                title=job.get("title", ""),
                company=job.get("company", ""),
                location=job.get("location", ""),
                url=job.get("url", "") or job.get("apply_url", ""),
                source=job.get("source", ""),
                source_key=job.get("source_key", ""),
                fit_score=fit_score,
                semantic_score=round(semantic * 100, 1),
                title_alignment_score=round(title_alignment * 100, 1),
                skill_overlap_ratio=round(overlap * 100, 1),
                experience_score=round(experience_score * 100, 1),
                matched_skills=matched[:10],
                missing_skills=missing[:10],
                extracted_job_skills=extracted_skills[:15],
                employment_type=job.get("employment_type", ""),
                published_at=job.get("published_at", ""),
                salary=job.get("salary", ""),
                summary=summary,
                company_url=job.get("company_url", ""),
                apply_url=job.get("apply_url", "") or job.get("url", ""),
            ).to_dict()
        )

    ranked.sort(
        key=lambda item: (
            item["fit_score"],
            item["title_alignment_score"],
            item["semantic_score"],
            item["skill_overlap_ratio"],
        ),
        reverse=True,
    )
    return ranked[:top_k]

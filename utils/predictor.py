"""Career prediction service — single inference surface for the app."""
from __future__ import annotations

import joblib
import pandas as pd
import streamlit as st

from career.career_domains import (
    CAREER_DOMAINS,
    detect_domain,
    AI_PRIORITY_JOBS,
    AI_PRIORITY_SKILLS,
)
from utils.model_paths import RUNTIME_MODEL_PATHS, validate_runtime_artifacts
from utils.scoring import score_jobs_for_user

AI_BOOST = 0.03


@st.cache_resource(show_spinner=False)
def load_models():
    missing = validate_runtime_artifacts()
    if missing:
        missing_text = ", ".join(missing)
        raise FileNotFoundError(
            "Missing required runtime model files: " + missing_text
        )

    models = {
        "classifier": joblib.load(RUNTIME_MODEL_PATHS["classifier"]),
        "education_encoder": joblib.load(RUNTIME_MODEL_PATHS["education_encoder"]),
        "skills_encoder": joblib.load(RUNTIME_MODEL_PATHS["skills_encoder"]),
        "label_encoder": joblib.load(RUNTIME_MODEL_PATHS["label_encoder"]),
        "feature_scaler": None,
    }
    scaler_path = RUNTIME_MODEL_PATHS["classifier"].with_name("feature_scaler.pkl")
    if scaler_path.exists():
        models["feature_scaler"] = joblib.load(scaler_path)
    return models


def _user_skill_set(skills):
    return {s.strip().lower() for s in skills if s and s.strip()}


def normalize_education_label(education, education_encoder):
    """Map generic UI education labels to known training categories."""
    if not education:
        return education

    categories = [str(x) for x in education_encoder.categories_[0]]
    exact_map = {c.lower(): c for c in categories}
    raw = str(education).strip()
    key = raw.lower()
    if key in exact_map:
        return exact_map[key]

    priority_rules = [
        (["phd", "doctor", "doctorate"], ["phd", "doctor"]),
        (["master"], ["master"]),
        (["bachelor"], ["bachelor"]),
        (["diploma", "cert", "certificate", "certification", "trade"], ["cert", "certificate", "certification", "diploma", "trade"]),
        (["high school", "school"], ["high school"]),
    ]

    for triggers, match_terms in priority_rules:
        if any(trigger in key for trigger in triggers):
            for category in categories:
                lowered = category.lower()
                if any(term in lowered for term in match_terms):
                    return category

    for category in categories:
        lowered = category.lower()
        if key in lowered or lowered in key:
            return category

    return raw


def validate_skills(skills, skills_encoder):
    """Return (canonical_skills, ignored_skills) for the input list."""
    skill_map = {s.lower(): s for s in skills_encoder.classes_}
    valid, invalid = [], []
    for skill in skills:
        key = skill.strip().lower()
        if key in skill_map:
            valid.append(skill_map[key])
        elif key:
            invalid.append(skill)
    seen, ordered = set(), []
    for s in valid:
        if s.lower() not in seen:
            seen.add(s.lower())
            ordered.append(s)
    return ordered, invalid


def predict_job_role(education, experience, skills, user_domain, return_details: bool = False):
    """Return ranked jobs, visible match scores, and optional explainability data.
    The classifier's raw ``predict_proba`` over hundreds of classes is kept only
    as a tiebreaker. The user-facing score is instead the explainable skill-match
    percentage produced by ``utils.scoring.score_jobs_for_user``.
    """
    models = load_models()
    edu_enc = models["education_encoder"]
    skl_enc = models["skills_encoder"]
    label_enc = models["label_encoder"]
    clf = models["classifier"]
    scaler = models.get("feature_scaler")
    normalized_education = normalize_education_label(education, edu_enc)

    edu_df = pd.DataFrame(
        edu_enc.transform(pd.DataFrame({"Education": [normalized_education]})),
        columns=edu_enc.get_feature_names_out(["Education"]),
    )
    skl_df = pd.DataFrame(skl_enc.transform([skills]), columns=skl_enc.classes_)
    exp_df = pd.DataFrame({"Experience Years": [experience]})

    user_vector = pd.concat([edu_df, exp_df, skl_df], axis=1)
    inference_input = scaler.transform(user_vector) if scaler is not None else user_vector
    probs = clf.predict_proba(inference_input)[0]
    all_jobs = label_enc.inverse_transform(range(len(probs)))
    model_results = list(zip(all_jobs, probs))

    user_skill_set = _user_skill_set(skills)
    has_ai_skills = len(user_skill_set & AI_PRIORITY_SKILLS) >= 3
    if has_ai_skills:
        model_results = [
            (job, prob + AI_BOOST) if job in AI_PRIORITY_JOBS else (job, prob)
            for job, prob in model_results
        ]

    allowed = set(CAREER_DOMAINS.get(user_domain, []))
    candidates = [job for job, _ in model_results if job in allowed]

    if candidates:
        allowed_probs = {job: prob for job, prob in model_results if job in allowed}
        max_prob = max(allowed_probs.values()) or 1.0
        model_lookup = {job: allowed_probs[job] / max_prob for job in candidates}
        ranked_by_model = sorted(allowed_probs.items(), key=lambda item: item[1], reverse=True)
        model_rank_lookup = {job: rank for rank, (job, _) in enumerate(ranked_by_model, start=1)}
    else:
        model_lookup = {}
        model_rank_lookup = {}

    ranked, details = score_jobs_for_user(
        skills,
        candidates,
        model_scores=model_lookup,
        model_ranks=model_rank_lookup,
        return_details=True,
    )
    if not ranked:
        sorted_model = sorted(model_results, key=lambda x: x[1], reverse=True)
        top_jobs = [job for job, _ in sorted_model[:3] if job in allowed]
        if not top_jobs:
            return ([], [], {}) if return_details else ([], [])
        top_scores = [50.0] * len(top_jobs)
        fallback_details = {
            job: {
                "job": job,
                "matched_skills": [],
                "missing_skills": [],
                "coverage_pct": 0.0,
                "breadth_pct": 0.0,
                "model_rank": model_rank_lookup.get(job),
                "match_score_pct": 50.0,
            }
            for job in top_jobs
        }
        return (top_jobs, top_scores, fallback_details) if return_details else (top_jobs, top_scores)

    top_jobs = [job for job, _ in ranked[:3]]
    top_scores = [score for _, score in ranked[:3]]
    top_details = {job: details[job] for job in top_jobs if job in details}
    return (top_jobs, top_scores, top_details) if return_details else (top_jobs, top_scores)


def summarize_profile(skills):
    user = _user_skill_set(skills)
    summary = {}
    buckets = {
        "Programming": ["Python", "Java", "C++", "JavaScript", "C", "R"],
        "AI / ML": ["Machine Learning", "Deep Learning", "PyTorch", "TensorFlow",
                    "Scikit-learn", "Pandas", "NumPy"],
        "Databases": ["SQL", "MySQL", "PostgreSQL", "MongoDB"],
        "Cloud / DevOps": ["Docker", "AWS", "Azure", "GCP", "Kubernetes"],
    }
    for cat, items in buckets.items():
        matched = sum(1 for s in items if s.lower() in user)
        summary[cat] = {"matched": matched, "total": len(items)}
    return summary


def skill_gap(required, user_skills):
    user = _user_skill_set(user_skills)
    return [s for s in required if s.lower() not in user]


def matched_skills(required, user_skills):
    user = _user_skill_set(user_skills)
    return [s for s in required if s.lower() in user]

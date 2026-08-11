
from __future__ import annotations
import json
import os
import re
import urllib.request
from typing import TypedDict

from utils.job_skills import JOB_REQUIRED_SKILLS
from utils.semantic_matching import KNOWN_SKILLS

class ExtractedCandidateProfile(TypedDict):
    skills: list[str]
    experience_years: int
    education: str
    target_role: str
    summary: str
    extraction_method: str

def _heuristic_nlp_extract(resume_text: str) -> ExtractedCandidateProfile:
    """Zero-cost NLP heuristic extractor for skills, experience, and education."""
    text_clean = (resume_text or "").strip()
    text_low = text_clean.lower()

    # 1. Skill Extraction using KNOWN_SKILLS taxonomy
    extracted_skills = []
    for skill in KNOWN_SKILLS:
        pattern = rf"(?<![a-z0-9]){re.escape(skill.lower())}(?![a-z0-9])"
        if re.search(pattern, text_low):
            extracted_skills.append(skill)

    # Dedup while preserving order
    seen = set()
    unique_skills = []
    for s in extracted_skills:
        if s.lower() not in seen:
            seen.add(s.lower())
            unique_skills.append(s)

    # 2. Experience Years Extraction
    exp_years = 2  # Default baseline
    years_matches = re.findall(r"(\d{1,2})\s*\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp|work)", text_low)
    if years_matches:
        try:
            exp_years = max(int(y) for y in years_matches)
        except ValueError:
            exp_years = 2
    else:
        # Check for year ranges e.g. 2018-2024
        date_matches = re.findall(r"(20\d{2})\s*[-–\to]\s*(20\d{2}|present|current)", text_low)
        if date_matches:
            total_duration = 0
            for start, end in date_matches:
                end_yr = 2026 if end in ("present", "current") else int(end)
                start_yr = int(start)
                total_duration += max(0, end_yr - start_yr)
            if total_duration > 0:
                exp_years = min(total_duration, 25)

    # 3. Education Level Extraction
    edu_level = "Bachelor's"
    if any(k in text_low for k in ["ph.d", "phd", "doctorate", "doctor of philosophy"]):
        edu_level = "Ph.D."
    elif any(k in text_low for k in ["master", "m.s.", "m.sc", "m.tech", "mba", "postgraduate"]):
        edu_level = "Master's"
    elif any(k in text_low for k in ["bachelor", "b.s.", "b.sc", "b.tech", "undergraduate"]):
        edu_level = "Bachelor's"
    elif any(k in text_low for k in ["associate", "diploma"]):
        edu_level = "Associate"

    # 4. Target Role Suggestion
    target_role = "Software Engineer"
    role_scores = {}
    for role, req_skills in JOB_REQUIRED_SKILLS.items():
        score = sum(1 for s in req_skills if s.lower() in seen)
        if score > 0:
            role_scores[role] = score

    if role_scores:
        target_role = max(role_scores, key=role_scores.get)

    summary = (
        f"Candidate with {exp_years} year(s) of experience, educated to {edu_level} level. "
        f"Demonstrated proficiency in {len(unique_skills)} technical skills including "
        f"{', '.join(unique_skills[:5]) if unique_skills else 'general engineering'}."
    )

    return {
        "skills": unique_skills or ["Python", "Problem Solving"],
        "experience_years": exp_years,
        "education": edu_level,
        "target_role": target_role,
        "summary": summary,
        "extraction_method": "Zero-Shot NLP Heuristic Engine",
    }


def extract_profile_with_nlp(resume_text: str) -> ExtractedCandidateProfile:
    """Extract candidate profile using available LLM API or fallback to NLP parser."""
    gemini_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")

    if gemini_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
            prompt = (
                "You are an expert resume parser. Extract candidate details as valid JSON with keys: "
                "\"skills\" (list of strings), \"experience_years\" (integer), \"education\" (string), "
                "\"target_role\" (string), \"summary\" (string).\n\nResume Text:\n" + resume_text[:3000]
            )
            data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=8) as response:
                res = json.loads(response.read().decode("utf-8"))
                out_text = res["candidates"][0]["content"]["parts"][0]["text"]
                # Parse JSON block
                json_match = re.search(r"\{.*\}", out_text, re.DOTALL)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    return {
                        "skills": parsed.get("skills", []),
                        "experience_years": int(parsed.get("experience_years", 2)),
                        "education": str(parsed.get("education", "Bachelor's")),
                        "target_role": str(parsed.get("target_role", "Software Engineer")),
                        "summary": str(parsed.get("summary", "")),
                        "extraction_method": "Google Gemini AI API",
                    }
        except Exception:
            pass  # Fallback to heuristic parser on API timeout/error

    if openai_key:
        try:
            url = "https://api.openai.com/v1/chat/completions"
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {
                        "role": "system",
                        "content": "Extract candidate info as JSON: skills (list), experience_years (int), education (str), target_role (str), summary (str).",
                    },
                    {"role": "user", "content": resume_text[:3000]},
                ],
                "response_format": {"type": "json_object"},
            }
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {openai_key}",
                },
            )
            with urllib.request.urlopen(req, timeout=8) as response:
                res = json.loads(response.read().decode("utf-8"))
                parsed = json.loads(res["choices"][0]["message"]["content"])
                return {
                    "skills": parsed.get("skills", []),
                    "experience_years": int(parsed.get("experience_years", 2)),
                    "education": str(parsed.get("education", "Bachelor's")),
                    "target_role": str(parsed.get("target_role", "Software Engineer")),
                    "summary": str(parsed.get("summary", "")),
                    "extraction_method": "OpenAI GPT-4o API",
                }
        except Exception:
            pass

    return _heuristic_nlp_extract(resume_text)

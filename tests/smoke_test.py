from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.skill_proficiency import (
    infer_proficiency_from_text,
    attach_manual_proficiency,
    PRO_LEVELS,
    describe_level,
)
from utils.jd_parser import parse_jd_text
from utils.jd_match import jd_overall_score
from utils.roadmap import build_weekly_roadmap
from utils.candidate_store import (
    record_candidate_from_session,
    list_candidates,
    export_csv_bytes,
    export_json_bytes,
    load_candidate,
    delete_candidate,
)
from utils.recruiter import rank_candidates_for_jd
from utils.taxonomy import resolve_hierarchical_role, get_taxonomy_breadcrumbs
from utils.llm_extractor import extract_profile_with_nlp
from utils.semantic_matching import get_scorer

print("== Hierarchical Taxonomy ==")
tax_node = resolve_hierarchical_role("Senior Machine Learning Engineer")
print("Taxonomy Node:", tax_node)
breadcrumbs = get_taxonomy_breadcrumbs("Senior Machine Learning Engineer")
print("Breadcrumbs:", breadcrumbs)
assert tax_node["domain"] == "AI & Data Science"
assert tax_node["family"] == "Machine Learning Engineering"

print("\n== LLM / Zero-Shot NLP Extractor ==")
nlp_extracted = extract_profile_with_nlp(
    "Senior ML Engineer with 5 years exp in Python, PyTorch, Docker, Kubernetes, AWS. MS degree."
)
print("Method:", nlp_extracted["extraction_method"])
print("Skills:", nlp_extracted["skills"])
print("Exp Years:", nlp_extracted["experience_years"])
print("Education:", nlp_extracted["education"])
assert nlp_extracted["experience_years"] == 5
assert "Python" in nlp_extracted["skills"]

print("\n== Vector Embedding Scorer ==")
scorer = get_scorer("embeddings")
sims = scorer.score(
    "Machine Learning Engineer with Python PyTorch AWS experience",
    ["Looking for Senior ML Engineer proficient in PyTorch and AWS", "Financial accountant with Excel skills"]
)
print("Scorer name:", scorer.name, "| Sim scores:", sims)
assert len(sims) == 2
assert sims[0] > sims[1]

print("\n== proficiency map ==")
resume = (
    "Senior Data Scientist with 4 years of experience using Python, "
    "Machine Learning, PyTorch, SQL, Pandas, NumPy. Built production "
    "pipelines on AWS and Docker. Expert in TensorFlow and modelling."
)
prof = infer_proficiency_from_text(resume)
prof = attach_manual_proficiency(prof, [("FastAPI", "Intermediate"), ("Kafka", "Beginner")])
print("Detected skills count:", len(prof))
for skill, info in prof.items():
    print(f"  {skill}: level={info['label']} weight={info['weight']:.2f} evidence={info['evidence']}")

print("\n== JD parser ==")
jd = (
    "Job Title: Senior ML Engineer\n"
    "Skills: Python, Machine Learning, Deep Learning, PyTorch, TensorFlow, "
    "AWS, Docker, Kubernetes, SQL, Spark, Airflow, FastAPI.\n"
    "Requirements: 3+ years experience.\n"
)
parsed = parse_jd_text(jd)
print("Title:", parsed["title"])
print("Skills:", parsed["skills"])
print("Tenure:", parsed["min_years"], "..", parsed["max_years"])

print("\n== JD match scorer ==")
score = jd_overall_score(
    prof, parsed["skills"], 4, parsed["min_years"], parsed["max_years"], "Bachelor's"
)
print(f"Overall: {score['overall_match_pct']}% | skill: {score['skill_pct']}% | "
      f"exp: {score['experience_pct']}% | edu: {score['education_pct']}%")
print("Matched:", score["matched"])
print("Missing:", score["missing"])

print("\n== Weekly roadmap ==")
roadmap = build_weekly_roadmap(score["missing"], prof, weekly_hours=8)
print(f"Total weeks: {roadmap['total_weeks']} | total hours: {roadmap['total_hours']}")
for row in roadmap["per_skill"]:
    print(f"  {row['skill']:>10s}: {row['weeks']}w from {row['start_level']}")
print("First 5 weekly items:")
for item in roadmap["items"][:5]:
    print(f"  week {item['week']} · {item['skill']} · {item['milestone']} · {item['hours']}h")

print("\n== Candidate persistence ==")
cid = record_candidate_from_session(
    candidate_name="Sample Candidate",
    education="Bachelor's",
    experience_years=4,
    validated_skills=list(prof.keys()),
    ignored_skills=["hackhack"],
    domain="AI & Data Science",
    top_jobs=[{"title": "Senior ML Engineer", "confidence": score["overall_match_pct"]}],
    missing_skills=score["missing"],
    matched_skills=score["matched"],
    proficiency_map=prof,
    resume_text=resume,
    jd_text=jd,
    jd_match=score,
    roadmap_total_weeks=roadmap["total_weeks"],
    overall_pct=score["overall_match_pct"],
)
print("Saved candidate id:", cid)

all_c = list_candidates()
print("Stored candidates count:", len(all_c))

loaded = load_candidate(cid)
print("Loaded name:", loaded.get("candidate_name"), "| overall:", loaded.get("overall_pct"))

print("\n== Recruiter ranking ==")
ranked = rank_candidates_for_jd(jd, all_c)
print(f"Ranked rows: {len(ranked)}")
for row in ranked[:3]:
    r = row["result"]
    print(
        f"  #{row['candidate_name']} overall={r['overall_match_pct']}% "
        f"skill={r['skill_pct']}% exp={r['experience_pct']}% edu={r['education_pct']}%"
    )

print("\n== Exports ==")
csv_bytes = export_csv_bytes(all_c)
json_bytes = export_json_bytes(all_c)
print(f"CSV bytes={len(csv_bytes)} JSON bytes={len(json_bytes)}")
print(f"CSV header: {csv_bytes.decode('utf-8').splitlines()[0]}")

print("\n== Cleanup ==")
deleted = delete_candidate(cid)
print("Deleted:", deleted, "| remaining:", len(list_candidates()))

print("\nAll feature modules verified successfully (including taxonomy, LLM zero-shot extraction, and vector embeddings).")

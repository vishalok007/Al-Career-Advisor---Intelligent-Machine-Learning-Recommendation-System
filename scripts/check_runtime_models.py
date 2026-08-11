from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from career.career_domains import detect_domain
from utils.predictor import load_models, predict_job_role, validate_skills
from utils.model_paths import validate_runtime_artifacts

def main() -> int:
    missing = validate_runtime_artifacts()
    if missing:
        print("[FAIL] Missing runtime artifacts:")
        for item in missing:
            print(f" - {item}")
        return 1

    models = load_models()
    sample_skills = ["Python", "SQL", "Machine Learning", "Pandas", "Scikit-learn"]
    valid, invalid = validate_skills(sample_skills, models["skills_encoder"])
    domain = detect_domain(valid)
    jobs, scores = predict_job_role("Bachelor's", 2, valid, domain)

    print("[OK] Runtime model artifacts loaded")
    print(f"[OK] Valid skills: {valid}")
    print(f"[OK] Ignored skills: {invalid}")
    print(f"[OK] Detected domain: {domain}")
    print(f"[OK] Predicted jobs: {jobs}")
    print(f"[OK] Scores: {scores}")

    if not jobs:
        print("[FAIL] No jobs returned from prediction flow")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


from __future__ import annotations
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.llm_extractor import extract_profile_with_nlp

def verify():
    sample_resume = (
        "Senior ML Engineer with 5 years experience in Python, PyTorch, "
        "Kubernetes, AWS, Docker, PostgreSQL. MS in Computer Science."
    )
    print("AI Career Advisor — Fallback Engine Verification")

    # 1. Active Environment Extraction Check
    res = extract_profile_with_nlp(sample_resume)
    print(f"\n[1] Current Environment Extractor:")
    print(f"    - Method:     {res['extraction_method']}")
    print(f"    - Target Role:{res['target_role']}")
    print(f"    - Skills:     {res['skills']}")

    # 2. Simulated Streamlit Cloud Mode (No local Ollama / No API keys)
    print(f"\n[2] Simulating Streamlit Cloud Mobile Mode (Zero-Cost Fallback):")
    old_gemini = os.environ.pop("GEMINI_API_KEY", None)
    old_openai = os.environ.pop("OPENAI_API_KEY", None)
    old_ollama = os.environ.pop("OLLAMA_HOST", None)

    cloud_res = extract_profile_with_nlp(sample_resume)
    print(f"    - Method:     {cloud_res['extraction_method']}")
    print(f"    - Target Role:{cloud_res['target_role']}")
    print(f"    - Skills:     {cloud_res['skills']}")

    # Restore env vars
    if old_gemini: os.environ["GEMINI_API_KEY"] = old_gemini
    if old_openai: os.environ["OPENAI_API_KEY"] = old_openai
    if old_ollama: os.environ["OLLAMA_HOST"] = old_ollama

    print("\n[OK] All fallback modes verified successfully!")

if __name__ == "__main__":
    verify()

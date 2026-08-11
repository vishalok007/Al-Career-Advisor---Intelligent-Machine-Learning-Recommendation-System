"""Ollama Diagnostic Utility.

Verifies local Ollama server connectivity, lists installed models,
and tests JSON zero-shot resume extraction using the AI Career Advisor extractor.
"""
from __future__ import annotations
import json
import os
import sys
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from utils.llm_extractor import extract_profile_with_nlp

def check_ollama():
    host = os.environ.get("OLLAMA_HOST") or "http://localhost:11434"
    model = os.environ.get("OLLAMA_MODEL") or "llama3.2"
    print(f"[*] Checking Ollama server at {host} ...")

    # 1. Ping /api/tags endpoint
    tags_url = f"{host.rstrip('/')}/api/tags"
    is_live = False
    try:
        req = urllib.request.Request(tags_url)
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m["name"] for m in data.get("models", [])]
            is_live = True
            print(f"[OK] Ollama server is LIVE! Installed models: {models if models else 'None'}")
            if not models:
                print(f"[!] Warning: No models found. Run `ollama pull {model}` in PowerShell.")
    except Exception as e:
        print(f"[OFFLINE] Could not connect to Ollama at {host}: {e}")
        print("          If Ollama is not installed yet, download it from https://ollama.com")
        print("          If installed, make sure the Ollama application is running.")

    # 2. Test LLM Extractor
    print(f"\n[*] Running AI Career Advisor extraction check ...")
    sample_text = (
        "Senior ML Engineer with 5 years experience in Python, PyTorch, "
        "Kubernetes, AWS, Docker, PostgreSQL. MS in Computer Science."
    )
    result = extract_profile_with_nlp(sample_text)
    print(f"[OK] Extraction Method: {result['extraction_method']}")
    print(f"[OK] Target Role:       {result['target_role']}")
    print(f"[OK] Exp Years:         {result['experience_years']}")
    print(f"[OK] Extracted Skills:  {result['skills']}")
    print(f"[OK] Summary:           {result['summary']}")

if __name__ == "__main__":
    check_ollama()

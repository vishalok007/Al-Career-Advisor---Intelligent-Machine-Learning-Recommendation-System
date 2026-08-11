from __future__ import annotations
import os
import sys
from pathlib import Path

print("== AI Career Advisor Setup ==")
print(f"Python Version: {sys.version}")

dirs = [
    "Data", "models/runtime", "models/reports", "notebook",
    "career", "utils", "scripts", "tests"
]
for d in dirs:
    Path(d).mkdir(parents=True, exist_ok=True)
    print(f"[OK] Directory verified: {d}")

# Verify core dependencies
required_packages = [
    "pandas", "numpy", "sklearn", "joblib",
    "streamlit", "pdfplumber", "plotly"
]
for pkg in required_packages:
    try:
        __import__(pkg)
        print(f"[OK] Package available: {pkg}")
    except ImportError:
        print(f"[!] Package missing: {pkg}")

print("\nProject setup complete.")

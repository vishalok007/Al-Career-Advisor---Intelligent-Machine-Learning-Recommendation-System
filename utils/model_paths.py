"""Centralized runtime model/report paths and validation helpers."""
from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
RUNTIME_MODELS_DIR = MODELS_DIR / "runtime"
REPORTS_DIR = MODELS_DIR / "reports"

RUNTIME_MODEL_PATHS = {
    "classifier": RUNTIME_MODELS_DIR / "final_model.pkl",
    "education_encoder": RUNTIME_MODELS_DIR / "education_encoder.pkl",
    "skills_encoder": RUNTIME_MODELS_DIR / "skills_encoder.pkl",
    "label_encoder": RUNTIME_MODELS_DIR / "label_encoder.pkl",
}
OPTIONAL_RUNTIME_MODEL_PATHS = {
    "feature_scaler": RUNTIME_MODELS_DIR / "feature_scaler.pkl",
}

REPORT_PATHS = {
    "evaluation_summary": REPORTS_DIR / "evaluation_summary.json",
    "classification_report": REPORTS_DIR / "classification_report.txt",
}


def relative_to_project(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def validate_runtime_artifacts() -> list[str]:
    """Return a list of missing required runtime artefact paths."""
    missing = []
    for path in list(RUNTIME_MODEL_PATHS.values()) + list(REPORT_PATHS.values()):
        if not path.exists():
            missing.append(relative_to_project(path))
    return missing

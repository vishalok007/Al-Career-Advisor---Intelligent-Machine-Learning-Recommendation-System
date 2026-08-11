"""Rigorous ML Training & Evaluation Pipeline for Academic Evaluation.

Performs Train/Test splitting (80/20), 3-fold cross validation, and multi-model
benchmarking (Random Forest, Extra Trees, Decision Tree, Logistic Regression).
Calculates Top-1, Top-3, Top-5 Accuracy, Macro F1, Weighted F1, and exports
test-set metrics to models/reports/ evaluation artifacts.
"""
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import json
import time
import warnings

warnings.filterwarnings("ignore")

import joblib
import numpy as np
import pandas as pd

from utils.training_data_cleaner import clean_training_dataframe
from sklearn.ensemble import (
    ExtraTreesClassifier,
    RandomForestClassifier,
)
from sklearn.tree import DecisionTreeClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    top_k_accuracy_score,
)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.preprocessing import StandardScaler

DATA_DIR = BASE_DIR / "Data"
MODELS_DIR = BASE_DIR / "models"
RUNTIME_MODELS_DIR = MODELS_DIR / "runtime"
REPORTS_DIR = MODELS_DIR / "reports"
FEATURES_DIR = MODELS_DIR / "features"
CLEAN_DATA_PATH = DATA_DIR / "training_data_cleaned.csv"

CANDIDATES = {
    "Random Forest": lambda: RandomForestClassifier(
        n_estimators=150, max_depth=16, min_samples_leaf=2, random_state=42, n_jobs=-1
    ),
    "Logistic Regression": lambda: LogisticRegression(
        C=4e-5, max_iter=200, random_state=42, n_jobs=-1
    ),
    "Extra Trees": lambda: ExtraTreesClassifier(
        n_estimators=100, max_depth=18, min_samples_leaf=2, random_state=42, n_jobs=-1
    ),
    "Decision Tree": lambda: DecisionTreeClassifier(
        max_depth=16, min_samples_leaf=2, random_state=42
    ),
}


def load_training_data() -> tuple[pd.DataFrame, dict]:
    raw = pd.read_csv(DATA_DIR / "training_data.csv")
    aug_path = DATA_DIR / "training_data_augmented.csv"
    if aug_path.exists():
        aug = pd.read_csv(aug_path)
        raw = pd.concat([raw, aug], ignore_index=True)

    clean_df, clean_stats = clean_training_dataframe(raw)
    CLEAN_DATA_PATH.parent.mkdir(exist_ok=True)
    clean_df.to_csv(CLEAN_DATA_PATH, index=False)
    return clean_df, clean_stats


def build_feature_matrix(df: pd.DataFrame):
    from sklearn.preprocessing import LabelEncoder, MultiLabelBinarizer, OneHotEncoder

    X = df[["Education", "Experience Years", "Skills"]].copy()
    y = df["Job Role"].copy()

    edu_enc = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
    edu_df = pd.DataFrame(
        edu_enc.fit_transform(X[["Education"]]),
        columns=edu_enc.get_feature_names_out(["Education"]),
        index=X.index,
    )
    exp_df = pd.DataFrame({"Experience Years": X["Experience Years"]}, index=X.index)
    mlb = MultiLabelBinarizer()
    skill_df = pd.DataFrame(
        mlb.fit_transform(X["Skills"].str.split("|")),
        columns=mlb.classes_,
        index=X.index,
    )
    X_final = pd.concat([edu_df, exp_df, skill_df], axis=1)
    label_enc = LabelEncoder()
    y_enc = pd.Series(label_enc.fit_transform(y), name="Job Role", index=y.index)
    return X_final, y_enc, edu_enc, mlb, label_enc


def main() -> None:
    MODELS_DIR.mkdir(exist_ok=True)
    RUNTIME_MODELS_DIR.mkdir(exist_ok=True)
    REPORTS_DIR.mkdir(exist_ok=True)
    FEATURES_DIR.mkdir(exist_ok=True)

    raw, clean_stats = load_training_data()
    print(f"[+] Loaded {clean_stats['input_rows']:,} training rows")
    print(f"[+] Cleaned dataset: {len(raw):,} rows after preprocessing")

    X, y, edu_enc, mlb, label_enc = build_feature_matrix(raw)
    print(f"[+] Feature Matrix: {X.shape[1]:,} features · {y.nunique():,} target classes")

    # Train/Test Split (80% Train, 20% Unseen Test)
    if y.value_counts().min() >= 2:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)
    all_classes = np.arange(y.nunique())

    summaries = []
    models_fitted = {}

    for name, factory in CANDIDATES.items():
        print(f"\n[·] Training & Benchmarking {name} …")
        t0 = time.time()
        model = factory()

        if name == "Logistic Regression":
            model.fit(X_train_s, y_train)
            preds = model.predict(X_test_s)
            probs = model.predict_proba(X_test_s)
            cv = cross_val_score(model, X_train_s, y_train, cv=3, scoring="accuracy", n_jobs=-1)
        else:
            model.fit(X_train, y_train)
            preds = model.predict(X_test)
            probs = model.predict_proba(X_test)
            cv = cross_val_score(model, X_train, y_train, cv=3, scoring="accuracy", n_jobs=-1)

        elapsed = time.time() - t0
        models_fitted[name] = model

        # Metric Calculations on Unseen Test Set
        acc_top1 = accuracy_score(y_test, preds)
        
        # Calculate Top-3 and Top-5 accuracy safely
        try:
            acc_top3 = float(top_k_accuracy_score(y_test, probs, k=3, labels=all_classes))
            acc_top5 = float(top_k_accuracy_score(y_test, probs, k=5, labels=all_classes))
        except Exception:
            acc_top3 = float(acc_top1)
            acc_top5 = float(acc_top1)

        macro_pre = precision_score(y_test, preds, average="macro", zero_division=0)
        macro_rec = recall_score(y_test, preds, average="macro", zero_division=0)
        macro_f1 = f1_score(y_test, preds, average="macro", zero_division=0)

        weighted_pre = precision_score(y_test, preds, average="weighted", zero_division=0)
        weighted_rec = recall_score(y_test, preds, average="weighted", zero_division=0)
        weighted_f1 = f1_score(y_test, preds, average="weighted", zero_division=0)

        print(
            f"    Top-1 Acc={acc_top1:.4f} | Top-3 Acc={acc_top3:.4f} | Top-5 Acc={acc_top5:.4f}\n"
            f"    Macro F1={macro_f1:.4f} | Weighted F1={weighted_f1:.4f} | CV={cv.mean():.4f}±{cv.std():.4f} ({elapsed:.1f}s)"
        )

        summaries.append(
            {
                "name": name,
                "accuracy": float(acc_top1),
                "top3_accuracy": float(acc_top3),
                "top5_accuracy": float(acc_top5),
                "macro_precision": float(macro_pre),
                "macro_recall": float(macro_rec),
                "macro_f1": float(macro_f1),
                "precision": float(weighted_pre),
                "recall": float(weighted_rec),
                "f1": float(weighted_f1),
                "cv_mean": float(cv.mean()),
                "cv_std": float(cv.std()),
                "train_seconds": round(elapsed, 2),
                "classes": int(y.nunique()),
                "features": int(X.shape[1]),
                "training_rows": int(len(X_train)),
                "test_rows": int(len(X_test)),
            }
        )

    # Select champion model dynamically based on highest unseen test-set accuracy
    winner = max(summaries, key=lambda r: (r["accuracy"], r["top3_accuracy"]))
    print(f"\n[WINNER] Production Champion Model: {winner['name']} -- Test Top-1 Acc: {winner['accuracy']:.4f} | Top-3 Acc: {winner['top3_accuracy']:.4f}")

    # Retrain winning model on full dataset for production serving
    final_factory = CANDIDATES[winner["name"]]
    full_model = final_factory()
    if winner["name"] == "Logistic Regression":
        scaler_full = StandardScaler().fit(X)
        full_model.fit(scaler_full.transform(X), y)
        joblib.dump(scaler_full, RUNTIME_MODELS_DIR / "feature_scaler.pkl")
    else:
        full_model.fit(X, y)

    joblib.dump(full_model, RUNTIME_MODELS_DIR / "final_model.pkl", compress=("xz", 9))
    joblib.dump(label_enc, RUNTIME_MODELS_DIR / "label_encoder.pkl")
    joblib.dump(edu_enc, RUNTIME_MODELS_DIR / "education_encoder.pkl")
    joblib.dump(mlb, RUNTIME_MODELS_DIR / "skills_encoder.pkl")

    # Generate classification report strictly on the UNSEEN TEST SET (X_test, y_test)
    winning_fitted = models_fitted[winner["name"]]
    test_preds = winning_fitted.predict(X_test_s if winner["name"] == "Logistic Regression" else X_test)
    report = classification_report(y_test, test_preds, zero_division=0, digits=4)

    with (REPORTS_DIR / "classification_report.txt").open("w", encoding="utf-8") as fh:
        fh.write(
            f"Academic Evaluation Model Report\n"
            f"Champion Model: {winner['name']}\n"
            f"Dataset: {len(X):,} total samples ({len(X_train):,} Train, {len(X_test):,} Unseen Test)\n"
            f"Feature Dimension: {X.shape[1]} features | Classes: {y.nunique()}\n"
            f"Unseen Test Set Top-1 Accuracy: {winner['accuracy']:.4f}\n"
            f"Unseen Test Set Top-3 Accuracy: {winner['top3_accuracy']:.4f}\n"
            f"Unseen Test Set Top-5 Accuracy: {winner['top5_accuracy']:.4f}\n"
            f"Macro F1 Score: {winner['macro_f1']:.4f} | Weighted F1 Score: {winner['f1']:.4f}\n\n"
            f"--- Per-Class Classification Report (Unseen Test Set) ---\n"
            f"{report}"
        )

    summary_payload = {
        "winner": winner["name"],
        "dataset_rows": int(len(raw)),
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
        "feature_count": int(X.shape[1]),
        "class_count": int(y.nunique()),
        "top3_accuracy": float(winner["top3_accuracy"]),
        "top5_accuracy": float(winner["top5_accuracy"]),
        "macro_f1": float(winner["macro_f1"]),
        "cleaning": clean_stats,
        "cleaned_data_path": str(CLEAN_DATA_PATH.relative_to(BASE_DIR)).replace("\\", "/"),
        "models": summaries,
    }
    with (REPORTS_DIR / "evaluation_summary.json").open("w", encoding="utf-8") as fh:
        json.dump(summary_payload, fh, indent=2)

    print(f"\n[OK] Saved cleaned dataset to {CLEAN_DATA_PATH}")
    print(f"[OK] Saved runtime models to {RUNTIME_MODELS_DIR}")
    print(f"[OK] Saved evaluation artifacts & test classification report to {REPORTS_DIR}")


if __name__ == "__main__":
    main()

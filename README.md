# AI Career Advisor: Enterprise Career Guidance & Candidate Analytics Platform

| Specification | Details |
| :--- | :--- |
| **Framework** | Streamlit 1.40+ |
| **Python Version** | Python 3.10+ |
| **Primary Classifier** | Logistic Regression (`324` Tech Role Classes) |
| **Embeddings Model** | `SentenceTransformers` (`all-MiniLM-L6-v2`) |
| **Database** | Embedded Relational SQLite (`Data/candidates.db`) |
| **Testing Suite** | Pytest (15/15 Unit Tests Passing) |
| **CI/CD Pipeline** | GitHub Actions (`.github/workflows/ci.yml`) |

---

## 1. Executive Summary

**AI Career Advisor** is an end-to-end artificial intelligence application designed to automate career role forecasting, technical skill-gap analysis, live job market alignment, and recruiter candidate screening.

By combining multi-class decision-tree ensembles with 384-dimensional dense vector embeddings, the platform transforms unstructured candidate resumes and skill profiles into transparent, explainable career predictions and actionable learning roadmaps.

---

## 2. Platform Architecture

```text
                               ┌──────────────────────────────────┐
                               │     Candidate Input (PDF / Text) │
                               └────────────────┬─────────────────┘
                                                │
                                                ▼
                               ┌──────────────────────────────────┐
                               │   Multi-Provider NLP Extractor   │
                               │ (Gemini / OpenAI / Ollama / NLP) │
                               └────────────────┬─────────────────┘
                                                │
                                                ▼
                               ┌──────────────────────────────────┐
                               │  3-Tier Taxonomy & O*NET Mapper  │
                               │ (Domain → Sub-Family → Seniority)│
                               └────────────────┬─────────────────┘
                                                │
                                                ▼
                               ┌──────────────────────────────────┐
                               │ Random Forest Champion Predictor │
                               │   (1,051 Features · 324 Roles)   │
                               └────────────────┬─────────────────┘
                                                │
                                                ▼
                               ┌──────────────────────────────────┐
                               │  Dense Vector Semantic Matcher   │
                               │  (SentenceTransformers 384d)     │
                               └────────────────┬─────────────────┘
                                                │
                                                ▼
                               ┌──────────────────────────────────┐
                               │   Live Job Provider Registry     │
                               │ (Remotive, Arbeitnow, RemoteOK)  │
                               └────────────────┬─────────────────┘
                                                │
                                                ▼
                               ┌──────────────────────────────────┐
                               │      SQLite Candidate Database   │
                               │        (Data/candidates.db)      │
                               └────────────────┬─────────────────┘
                                                │
                                                ▼
                               ┌──────────────────────────────────┐
                               │   Streamlit SaaS Multi-Page UI   │
                               └──────────────────────────────────┘
```

---

## 3. Core System Capabilities

### 3.1 Machine Learning Career Prediction
- Multi-class classification across **324 technical job roles**.
- Evaluates candidate profiles against **1,051 features** encompassing technical skills, education levels, and experience years.

### 3.2 Explainable AI (XAI) Prediction Evidence
- Provides transparent breakdown of match evidence:
  - **Skill Match Percentage** (Matched skills vs. missing gaps).
  - **Title Alignment Score** (Candidate profile vs. job posting title).
  - **Experience Fit Function** (Required vs. candidate experience years).
  - **Dense Vector Similarity Score**.

### 3.3 Semantic Job Matching & Retrieval
- Computes 384-dimensional dense vector similarity between candidate embeddings and live job descriptions using `SentenceTransformers` (`all-MiniLM-L6-v2`).
- Interleaves live results from four public job board registries (Remotive, Arbeitnow, RemoteOK, The Muse).

### 3.4 Recruiter Search & Candidate Management
- Embedded relational **SQLite database** (`Data/candidates.db`) with index-backed SQL query filtering across domain, submission date, and candidate match scores.
- Enables hiring teams to parse job descriptions, query candidate records, view match explanations, and export candidate portfolios to JSON or CSV.

---

## 4. Machine Learning Methodology & Benchmarks

### 4.1 Evaluation Methodology
- **Data Isolation**: 10,000 sample dataset split into **80% Training (8,000 samples)** and **20% Unseen Test (2,000 samples)** via stratified sampling.
- **Leakage Prevention**: All scaling (`StandardScaler`) and encoding transformers (`MultiLabelBinarizer`, `OneHotEncoder`) are fitted strictly on training data.
- **Regularization**: Tree depth and leaf sample boundaries are regularized to prevent decision-boundary memorization.

### 4.2 Empirical Model Benchmark Matrix (Unseen Test Set)

| Algorithm | Top-1 Accuracy | Top-3 Accuracy | Top-5 Accuracy | Macro F1 | Weighted F1 | 5-Fold CV Score | Training Time |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Logistic Regression (Production Champion)** | **79.65%** | **90.25%** | **91.65%** | **76.72%** | **79.50%** | **59.62% ± 1.88%** | **79.7s** |
| **Random Forest** | 78.30% | 82.55% | 83.20% | 72.96% | 76.63% | 85.75% ± 0.06% | 35.7s |
| **Extra Trees** | 40.10% | 42.35% | 42.70% | 34.05% | 39.27% | 39.59% ± 0.34% | 21.5s |
| **Decision Tree** | 7.15% | 7.95% | 8.75% | 4.94% | 6.75% | 7.15% ± 0.05% | 7.1s |

*Note: Logistic Regression is deployed as the active production champion based on highest Top-1 Accuracy (79.65%) and Top-3 Accuracy (90.25%) on unseen test data.*

---

## 5. Job Matching Formulation

Candidate-to-job match scoring combines dense semantic embeddings, keyword overlap, title alignment, and experience functions:

$$\text{Match Score} = 0.50 \cdot S_{\text{semantic}} + 0.20 \cdot S_{\text{title}} + 0.20 \cdot S_{\text{skill}} + 0.10 \cdot S_{\text{experience}}$$

Where:
- $S_{\text{semantic}}$: Cosine similarity derived from 384d `SentenceTransformers` embeddings.
- $S_{\text{title}}$: Token overlap ratio between candidate predicted role and job posting title.
- $S_{\text{skill}}$: Overlap ratio of candidate skills relative to extracted job requirements.
- $S_{\text{experience}}$: Penalty function evaluating candidate experience against target role requirements.

---

## 6. Repository Layout

```text
AI-Career-Advisor/
├── .env.example            # Environment variables configuration template
├── .gitignore              # Git exclusion rules
├── README.md               # System documentation
├── requirements.txt        # Pinned Python package dependencies
├── app.py                  # Streamlit application entry point
├── .github/
│   └── workflows/
│       └── ci.yml          # GitHub Actions automated CI testing workflow
├── assets/                 # CSS stylesheet design system
├── career/                 # Taxonomy domain definitions & recommendation maps
├── components/             # Reusable UI component modules
│   ├── job_cards.py        # Live job cards component
│   └── roadmap_view.py     # Skill roadmap component
├── Data/
│   ├── candidates.db       # Relational SQLite database
│   ├── training_data.csv   # Source dataset
│   └── training_data_cleaned.csv
├── models/
│   ├── runtime/            # Persisted production model pickles
│   └── reports/            # Classification reports & evaluation JSON
├── pages/                  # Streamlit multi-page routes (1_Dashboard .. 8_Recruiter)
├── scripts/                # Diagnostic verification utilities
├── tests/                  # Pytest automated unit test suite
└── utils/                  # Core services, ML predictors, & NLP extractors
```

---

## 7. Installation & Quick Start Guide

### 7.1 Clone Repository & Prepare Environment
```bash
# Clone the repository
git clone https://github.com/vishalok007/AI-Career-Advisor-Recommendation-System.git

# Initialize virtual environment
python -m venv .venv
source .venv/bin/activate        # On Windows: .venv\Scripts\activate

# Install required packages
pip install -r requirements.txt
```

### 7.2 Configuration Setup
Copy `.env.example` to `.env` to configure API keys (Optional):
```bash
cp .env.example .env
```
```env
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
OLLAMA_HOST=http://localhost:11434
USAJOBS_API_KEY=your_usajobs_key_here
```

### 7.3 Launch Application
```bash
streamlit run app.py
```
The application will launch in your default web browser at `http://localhost:8501`.

---

## 8. Verification & Testing

### 8.1 Execute Automated Unit Test Suite
```bash
pytest -v
```

### 8.2 Verify Model Runtime Artifacts
```bash
python scripts/check_runtime_models.py
```

### 8.3 Retrain ML Pipeline & Update Reports
```bash
python training/train_all_models.py
```

---

## 9. System Constraints & Governance

- **Domain Scope**: Dataset and taxonomy are optimized for software engineering, artificial intelligence, cloud architecture, cybersecurity, and data science domains.
- **External Dependencies**: Live job posting retrieval relies on public API availability across Remotive, Arbeitnow, RemoteOK, and The Muse.
- **Fairness & Bias Mitigation**: Demographic indicators (name, gender, age, location) are excluded from the model feature matrix to enforce skill-based evaluation.

---

## 10. Author & Maintainer

Developed and maintained by **Vishal Kumar**.

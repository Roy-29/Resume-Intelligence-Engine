# RecruiterPro — AI-Powered Resume Analyzer and Recruitment Platform

RecruiterPro is a full-stack web application that uses advanced AI/ML techniques to automatically analyze candidate resumes, score them against job roles, and provide recruiters with an intelligent applicant tracking system (ATS). It eliminates manual resume screening by automating skill extraction, candidate ranking, and interview scheduling.

---

## 2. Project Objective

**Problem:** Recruiters receive hundreds of resumes per job opening. Manually reading and ranking each one is time-consuming, inconsistent, and prone to unconscious bias.

**Solution:** RecruiterPro automatically processes a candidate's uploaded resume using a multi-layer AI pipeline. It extracts skills, calculates match scores against a selected job role, classifies the resume domain, and presents an AI-generated analysis report. Recruiters get a ranked, data-driven shortlist with XGBoost-predicted hiring probabilities.

**Key Goals:**

- Automate resume shortlisting using NLP + ML
- Provide bias-free, data-driven candidate scoring
- Give recruiters a full ATS (Applicant Tracking System) dashboard
- Enable candidates to receive intelligent feedback on their resumes

---

## 3. System Overview

The system has two portals:

1. **Candidate Portal** — Candidates can upload an existing resume, or use the **Smart Resume Builder** with AI-enhanced bullet points. They can also connect their **GitHub profile** for automated skill extraction and activity scoring. Once analyzed, candidates receive a detailed AI report including scores, job match percentage, improvement suggestions, and salary benchmarks.

2. **Recruiter Portal** — Recruiters post jobs, edit existing postings directly from the dashboard, view all applicants ranked by AI score, manage interview schedules, send messages, and use the XGBoost model to predict which candidates are most likely to be hired.

The backend processes resumes through a multi-stage AI pipeline: text extraction → NLP analysis → skill extraction → job matching → scoring → ML ranking. A WebSocket channel (Django Channels) broadcasts real-time updates to the recruiter dashboard.

> **Note on Infrastructure:** Django Channels uses an **In-Memory channel layer** (`channels.layers.InMemoryChannelLayer`). Celery is configured with `CELERY_TASK_ALWAYS_EAGER = True` and an in-memory broker, meaning tasks run synchronously in the same process without a separate Redis/broker server requirement for development.

---

## 4. Complete Project Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                    WEB BROWSER (Client)                 │
│         Candidate Portal      Recruiter ATS Portal      │
└────────────────────┬────────────────────────┬───────────┘
                     │ HTTP/HTTPS             │ WebSocket
         ┌───────────▼────────────────────────▼───────────┐
         │            Django Application Server            │
         │   (Daphne ASGI + Django 4.2 + DRF)             │
         │                                                 │
         │  ┌──────────────┐   ┌──────────────────────┐   │
         │  │ candidate app│   │    recruiter app      │   │
         │  │  views/urls  │   │   views/urls/models   │   │
         │  └──────┬───────┘   └──────────┬────────────┘   │
         │         │                      │                 │
         │  ┌──────▼──────────────────────▼────────────┐   │
         │  │           ai_core Package                 │   │
         │  │  nlp_extraction.py  (3-layer skill ext.)  │   │
         │  │  matching.py        (Hybrid Matcher)      │   │
         │  │  scoring.py         (Weighted Scorer)     │   │
         │  │  resume_classifier.py (Random Forest)     │   │
         │  │  clustering.py      (K-Means)             │   │
         │  └──────────────────────────────────────────┘   │
         │                                                 │
         │  ┌─────────────────────────────────────────┐    │
         │  │           api app / services             │    │
         │  │  ai_service.py     (Gemini + Retry logic)│    │
         │  │  ocr_service.py    (Tesseract OCR)       │    │
         │  │  adzuna_service.py (Job Market API)      │    │
         │  │  bulk_analysis_service.py                │    │
         │  └─────────────────────────────────────────┘    │
         │                                                 │
         │  ┌─────────────────────────────────────────┐    │
         │  │         ml_models / ml_pipeline          │    │
         │  │  XGBoost (candidate selection)           │    │
         │  │  Random Forest (resume classification)   │    │
         │  │  Logistic Regression (alternative)       │    │
         │  └─────────────────────────────────────────┘    │
         └───────────────────┬─────────────────────────────┘
                             │
              ┌──────────────▼──────────────────┐
              │    SQLite Database (db.sqlite3)  │
              │    Django ORM-managed tables     │
              └──────────────────────────────────┘
              ┌──────────────────────────────────┐
              │    Redis (Cache + Channels)       │
              │    Django Cache + WebSocket Layer │
              └──────────────────────────────────┘
```

**How components interact:**

- The **Django** backend handles all HTTP requests via URL routing.
- The **candidate app** contains the resume parsing `engine.py`, which orchestrates the AI pipeline.
- The **ai_core package** is a standalone module of reusable AI classes used by both portals.
- The **recruiter app** contains the `ml_pipeline.py` for XGBoost training and an ATS dashboard.
- The **api app** provides REST API endpoints and external service integrations.
- **Django Channels + Redis** handles WebSocket connections for live dashboard updates.
- The **ml_models** directory stores all `.joblib` model files on disk.

---

## 5. Detailed Project Structure

```text
antigravity cv/
│
├── manage.py                   # Django entry point
├── requirements.txt            # All Python dependencies
├── db.sqlite3                  # SQLite database (auto-created)
│
├── recruitment/                # Django project settings package
│   ├── settings.py             # Database, app list, installed apps, Celery/Channels config
│   ├── urls.py                 # Root URL dispatcher
│   ├── wsgi.py / asgi.py       # WSGI/ASGI server entry points
│   └── celery.py               # Celery app definition (runs eagerly in dev)
│
├── candidate/                  # Candidate app (core user-facing)
│   ├── models.py               # CandidateAnalysis, UserProfile, JobRole, Notification
│   ├── views.py                # All candidate views: upload, dashboard, report, auth,
│   │                           # job board, resume builder, GitHub analyzer, inbox, profile
│   ├── engine.py               # Main AI pipeline orchestrator
│   ├── urls.py                 # URL patterns for candidate portal
│   ├── forms.py                # Upload form, signup form
│   ├── data.py                 # TECHNICAL_SKILLS, SOFT_SKILLS, JOB_ROLE_SKILLS databases
│   ├── pdf_report.py           # ReportLab PDF generation for resume reports
│   ├── tasks.py                # Celery task definitions
│   ├── serializers.py          # DRF serializers
│   ├── api_urls.py / api_views.py  # REST API endpoints for candidate data
│   └── templates/candidate/   # HTML templates for candidate UI
│
├── recruiter/                  # Recruiter app (ATS features)
│   ├── models.py               # JobPosting, JobApplication, Interview, RecruiterMessage, MLModelVersion
│   ├── views.py                # ATS dashboard, job detail, interview CRUD, messages hub
│   ├── ml_pipeline.py          # XGBoost training & prediction pipeline
│   ├── urls.py                 # URL patterns for recruiter portal
│   ├── forms.py                # Job creation form
│   ├── tasks.py                # Celery background tasks
│   ├── api_urls.py / api_views.py  # Recruiter REST API endpoints
│   └── templates/recruiter/   # HTML templates for recruiter UI
│
├── ai_core/                    # Standalone AI/ML module
│   ├── engine.py               # Facade — single entry point for all AI operations
│   ├── nlp_extraction.py       # 3-layer skill extractor (keyword, ontology, semantic/SBERT)
│   ├── matching.py             # Hybrid matcher (TF-IDF + BM25 + Sentence-BERT)
│   ├── scoring.py              # Weighted composite scorer + bias removal
│   ├── resume_classifier.py    # Random Forest resume domain classifier
│   └── clustering.py           # K-Means candidate skill clustering
│
├── api/                        # REST API and external services
│   ├── views.py                # REST endpoints (bulk upload, public links, AI feedback)
│   ├── models.py               # CentralizedResume model (bulk uploads)
│   ├── urls.py                 # API URL routing
│   ├── consumers.py            # WebSocket consumer (Django Channels)
│   ├── routing.py              # WebSocket URL routing
│   ├── ml_views.py             # ML metrics API views
│   └── services/
│       ├── ai_service.py       # Google Gemini for qualitative feedback + bullet enhance
│       ├── github_service.py   # GitHub REST API profile fetching + skill extraction
│       ├── ocr_service.py      # Tesseract OCR for image-based resumes
│       ├── adzuna_service.py   # Adzuna job search & salary API integration
│       ├── bulk_analysis_service.py # Batch resume processing for recruiters
│       ├── bulk_upload_service.py   # Bulk file upload handler
│       ├── trends_service.py   # Google Trends skill demand analysis
│       └── public_link_service.py  # Shareable public resume report links
│
├── ml/                         # Standalone ML training & evaluation scripts
│   ├── fine_tune_bert.py       # Fine-tune Sentence-BERT with CosineSimilarityLoss
│   ├── fine_tune_from_csv.py   # Fine-tune from CSV dataset of resume/job pairs
│   ├── model_trainer.py        # Train XGBoost / RF models from feature sets
│   ├── model_evaluator.py      # Evaluate and compare trained model versions
│   ├── model_loader.py         # Load and serve trained models
│   ├── dataset_builder.py      # Build training datasets from DB records
│   ├── feature_engineering.py  # Feature extraction utilities for ML training
│   ├── synthetic_data_generator.py  # Generate synthetic candidate data for testing
│   └── download_dataset.py    # Download Kaggle datasets automatically
│
└── ml_models/                  # Trained model files (stored on disk)
    ├── kaggle_trainer.py       # Script to train RF + LR on Kaggle resume dataset
    ├── xgb_kaggle_*.joblib     # Multiple versioned XGBoost classifier files
    ├── rf_resume_classifier.joblib  # Trained Random Forest model
    ├── rf_tfidf_vectorizer.joblib   # TF-IDF vectorizer for RF input
    ├── logistic_regression.joblib   # Alternate LR classifier
    ├── lr_scaler.joblib             # Scaler for Logistic Regression
    └── fine_tuned_bert/             # Fine-tuned Sentence-BERT model files
```

### Most Important Files

| File | Purpose |
| :--- | :--- |
| `candidate/engine.py` | The central orchestrator. Calls pdfplumber/docx/OCR to extract text, then invokes all AI modules in sequence |
| `ai_core/nlp_extraction.py` | 3-layer skill extractor: keyword match → abbreviation normalization → Sentence-BERT semantic detection |
| `ai_core/matching.py` | Hybrid job-matching engine using TF-IDF, BM25, and Sentence-BERT cosine similarity |
| `ai_core/scoring.py` | Computes the final weighted composite score and removes gender bias terms |
| `recruiter/ml_pipeline.py` | Trains XGBoost on hiring history, saves `.joblib` file, and predicts hire probability per candidate |
| `ai_core/resume_classifier.py` | Uses pre-trained Random Forest (25 categories) to classify resume into a domain like "Data Science" |
| `api/services/ai_service.py` | Calls Google Gemini to generate natural language feedback, missing skills, and improvement suggestions |

---

## 6. Core Logic and Algorithms

### 6.1 Resume Text Extraction

When a candidate uploads a resume, the system determines the file type:

- **PDF** → `pdfplumber` extracts text page-by-page
- **Word (.docx)** → `python-docx` reads paragraphs and tables
- **Image (.png/.jpg)** → `Tesseract OCR` (via pytesseract) converts image to text

### 6.2 Three-Layer Skill Extraction (nlp_extraction.py)

The system extracts skills in three progressive layers:

**Layer 1 — Exact Keyword Match:**

- Uses regex with word boundaries (`\bhaskell\b`) to scan the resume text against a pre-defined database of 200+ `TECHNICAL_SKILLS` and `SOFT_SKILLS`
- Fast and precise for explicitly mentioned skills

**Layer 2 — Ontology / Abbreviation Normalization:**

- Maps common abbreviations to canonical forms. Example: `JS` → `JavaScript`, `k8s` → `Kubernetes`, `ML` → `Machine Learning`
- Catches skills hidden behind shorthand notation

**Layer 3 — Semantic Skill Extraction (Sentence-BERT):**

- Splits the resume into sentences, encodes them using `all-MiniLM-L6-v2` (Sentence Transformers)
- Encodes all skills not yet found by Layers 1 & 2 into the same vector space
- If cosine similarity between a sentence and a skill exceeds **0.55**, that skill is inferred as present
- Example: `"Built RESTful microservices"` → detects `REST API`, `Microservices` without explicit mention

All three layers are merged and deduplicated. The result is a clean, sorted list of extracted skills.

### 6.3 Hybrid Job Matching (matching.py)

The resume is compared against the job description using three algorithms simultaneously:

| Algorithm | Method | Weight |
| :--- | :--- | :--- |
| **Sentence-BERT** | Cosine similarity of sentence embeddings | 40% |
| **TF-IDF** | Term frequency cosine similarity | 40% |
| **BM25 (Okapi)** | Information retrieval ranking algorithm | 20% |

**Final Formula:** `Job Match % = (SBERT × 0.40) + (TF-IDF × 0.40) + (BM25 × 0.20)`

This hybrid approach captures both semantic understanding (SBERT) and precise keyword importance (TF-IDF + BM25).

### 6.4 Weighted Composite Scoring (scoring.py)

Each resume gets an overall score (0–100) computed as:

```text
Overall Score = (Skill Match % × 50%) 
              + (Experience Score × 20%) 
              + (Education Score × 10%) 
              + (Semantic Similarity × 20%)
```

- Skill score is the percentage of the job's required skills found in the resume
- Experience score is derived from regex-matched years (`5+ years of experience`)
- Education score is tiered: PhD=95, Master's=80, Bachelor's=60, Diploma=40
- The final score maps to a label: Excellent (≥80), Good (≥60), Average (≥40), Low (<40)

### 6.5 Bias Removal (scoring.py)

Before scoring, gendered pronouns and bias terms (`he/she`, `his/her`, `male/female`, etc.) are replaced with `[REDACTED]` using regex substitution. This ensures the AI evaluates candidates on skills and experience alone.

### 6.6 Resume Domain Classification (resume_classifier.py)

The pre-trained **Random Forest** classifier (trained on the Kaggle "UpdatedResumeDataSet") classifies each resume into one of **25 professional categories** (e.g., Data Science, DevOps Engineer, Java Developer).

The input features are:

1. TF-IDF text representation of the resume
2. Numerical features: skill count, keyword score, years of experience, education tier

The model outputs the predicted category + confidence %, and the **top-3 most likely categories**.

### 6.7 XGBoost Candidate Selection Model (ml_pipeline.py)

This model predicts the **probability that a specific candidate will be hired** for a given role, trained on the recruiter's own historical data.

**Training input features:**

- `skill_score` — how many required skills the candidate has
- `experience_score` — years of experience score
- `semantic_sim` — job match percentage
- `education_score` — education tier

**Target variable:** 1 if `JobApplication.status == 'hired'`, else 0

The model is trained using `XGBClassifier` with `n_estimators=100`, `max_depth=3`, `learning_rate=0.1`. The trained model is saved as a versioned `.joblib` file. **Robust Handling:** The pipeline has been optimized to handle numeric zero probabilities (0% match) explicitly, ensuring `0.0` values properly render in the UI instead of returning errors. Each new training run creates a new version and deactivates the previous one.

**At inference time**, for each new applicant, the system calls `predict_selection_probability()`, which loads the active model and returns a confidence score used to rank candidates in the ATS dashboard.

### 6.8 Handling Class Imbalance (SMOTE)

The recruitment dataset often suffers from class imbalance (e.g., more rejected candidates than hired ones). To prevent the XGBoost model from becoming biased toward the majority class, the `model_trainer.py` script implements **SMOTE** (Synthetic Minority Over-sampling Technique) via the `imblearn` library. This ensures the model learns minority patterns effectively.

### 6.9 K-Means Candidate Clustering (clustering.py)

When comparing multiple candidates, the system groups them into skill-based clusters using **K-Means (k=4)**:

1. Each candidate's skill list is converted into a TF-IDF frequency vector
2. K-Means groups similar vectors into clusters
3. Recruiters can see "skill domain groups" among applicants

### 6.9 Gemini Qualitative Feedback (ai_service.py)

After local scoring, the system sends the resume text and target role to **Gemini 1.5/3.1 Flash** via the Google Gemini API. The prompt requests a structured JSON with:

- `overall_feedback` — professional summary
- `missing_skills` — skills the candidate lacks for the target role
- `improvement_suggestions` — 2–3 actionable tips  
- `optimization_score` — AI-rated score 0–100

If the API key is unavailable, the system falls back to a pre-built static response. The `_call_gemini_with_retry` wrapper includes exponential backoff logic to handle transient 429/500 API errors gracefully.

### 6.11 Smart Resume Builder

Candidates can build a resume from scratch using a structured web form. To help them craft impactful descriptions, an **"AI Enhance"** button uses Gemini to re-write standard bullet points into action-oriented, quantifiable achievements (e.g., turning "fixed bugs" into "Resolved 50+ critical bugs, improving system uptime by 15%").

### 6.12 GitHub Analyzer

To supplement their profile, candidates can enter their GitHub username. The `github_service.py` makes calls to the GitHub REST API to fetch repositories, calculate an overall activity score, and extract programming languages and frameworks directly from the codebase.

---

## 7. File-Level Code Explanation

### `candidate/engine.py`

**Purpose:** Central AI orchestrator for a single resume analysis.

**What it does:**

1. Receives the file path and target job role
2. Detects file type and calls the appropriate parser (pdfplumber, docx, pytesseract)
3. Calls `ai_core.engine.scrub_bias()` to remove gender terms
4. Calls `ai_core.engine.extract_skills_advanced()` — the 3-layer skill extractor
5. Calls `ai_core.engine.match_resume_hybrid()` — hybrid job matching
6. Calls `ai_core.scoring.calculate_advanced_score()` — final weighted score
7. Calls `ai_core.resume_classifier.classify_resume_ml()` — domain classification
8. Calls `api/services/ai_service.py` for Gemini feedback
9. Returns a comprehensive dictionary with text, entities, skills, scores, and suggestions

### `candidate/views.py`

**Purpose:** HTTP view functions for the candidate portal.

**Key functions:**

- `upload_resume` — Handles file upload, calls the AI engine, saves a `CandidateAnalysis` database record
- `dashboard` — Shows the analysis results with score breakdown
- `report` — Full PDF-exportable report for a candidate
- `home_login` — Unified login with role selection (Candidate / Recruiter)
- `rematch_job` — Re-runs job matching when candidate selects a different role
- `resume_builder` & `ai_enhance_bullet` — Interactive CV builder with AI rewriting
- `github_analyzer` — Fetches and scores public GitHub profile activity

### `recruiter/views.py`

**Purpose:** HTTP view functions for the ATS Recruiter Portal.

**Key functions:**

- `recruiter_dashboard` — Shows all jobs and their application counts, ML metrics
- `job_detail` — Shows ranked list of candidates for a specific job using XGBoost score
- `compare_candidates` — Side-by-side candidate analysis with score bars and matched/missing skills
- `schedule_interview` — Creates `Interview` records and notifies the candidate
- `messages_hub` — Recruiter inbox for all sent messages with View/Edit/Delete
- `ml_model_metrics` — Shows accuracy, ROC AUC, and the active model version

### `recruiter/ml_pipeline.py`

**Purpose:** Trains and runs the XGBoost selection model.

**Functions:**

- `extract_features(applications)` — Converts Django ORM queryset to a pandas DataFrame
- `train_selection_model(queryset)` — Trains XGBoost, evaluates accuracy and ROC AUC, saves `.joblib`, logs version to DB
- `predict_selection_probability(...)` — Loads active model and returns hire probability for a single candidate

### `api/consumers.py`

**Purpose:** WebSocket consumer for real-time updates.

When a bulk resume analysis finishes or a new job is created, the server broadcasts a `dashboard_message` event over the `dashboard` WebSocket group. The recruiter's browser receives the update live without refreshing.

---

## 8. AI Modules and Their Responsibilities

| Module | Technology | Responsibility |
| :--- | :--- | :--- |
| **SkillExtractor** | Regex + Sentence-BERT | Extracts technical and soft skills using 3 layers |
| **HybridMatcher** | TF-IDF + BM25 + SBERT | Scores how well a resume matches a job description |
| **Scorer** | Weighted formula | Produces the final 0–100 composite score |
| **BiasRemover** | Regex | Strips gendered terms before scoring |
| **ResumeClassifier** | Random Forest (trained) | Classifies resume into 1 of 25 job categories |
| **XGBoost Pipeline** | XGBoost | Predicts hiring probability from historical data |
| **KMeansClustering** | TF-IDF + KMeans | Groups candidates into skill-based clusters |
| **Gemini Flash** | Google Gemini API | Generates qualitative improvement feedback and enhances CV bullets (with exponential backoff) |
| **GitHub Service** | GitHub API | Fetches user repositories and scores developer activity |
| **OCR Service** | Tesseract | Extracts text from image-format resumes |
| **Adzuna Service** | REST API | Fetches real job listings and salary data |

---

## 9. Workflow of the System

### Candidate Workflow

```text
1. Candidate registers/logs in at http://127.0.0.1:8000/
2. Uploads resume file (PDF / Word / Image) and selects a target job role
3. candidate/engine.py:
   a. Extracts text (pdfplumber / python-docx / Tesseract OCR)
   b. Scrubs gender bias terms
   c. Runs 3-layer skill extraction (keyword → ontology → Sentence-BERT)
   d. Runs hybrid job matching (TF-IDF + BM25 + SBERT)
   e. Calculates weighted composite score
   f. Classifies resume domain (Random Forest)
   g. Calls Gemini for qualitative feedback
4. CandidateAnalysis record is saved to SQLite database
5. Candidate is redirected to their dashboard with:
   - Overall score (0–100) with grade label
   - Matched skills vs Missing skills
   - Education and Experience scores
   - AI improvement suggestions
   - Salary benchmarks (from Adzuna API)
6. Candidate can download a PDF report or share via a public link
```

### Recruiter Workflow

```text
1. Recruiter logs in and sees the ATS Dashboard
2. Creates a Job Posting (title, description, required skills via JobRole)
3. New job creation triggers a WebSocket broadcast to all dashboard viewers
4. Candidates' CandidateAnalysis records are linked as JobApplications
5. Recruiter views Job Detail:
   - All applicants ranked by XGBoost ml_selection_probability
   - Each candidate card shows score, matched/missing skills, experience
6. Recruiter can:
   - Edit active and inactive job postings directly from the dashboard
   - Change application status (Applied → Shortlisted → Hired → Rejected)
   - Schedule an Interview (sends a Notification to the candidate)
   - Send a Message (stored in RecruiterMessage, triggers Notification)
   - Compare candidates side-by-side on the Compare page
7. With enough historical hiring data, recruiter can retrain the XGBoost model:
   - ml_pipeline.train_selection_model() runs on past JobApplications
   - New versioned .joblib file saved, MLModelVersion logged to DB
   - Future predictions use the new active model
```

---

## 10. Technologies and Libraries Used

| Technology | Purpose |
| :--- | :--- |
| **Django 4.2** | Web framework — URL routing, ORM, views, templates, authentication |
| **Django REST Framework** | REST API endpoints for external/mobile access |
| **Django Channels 4.0** | WebSocket support for real-time recruiter dashboard updates (InMemoryChannelLayer) |
| **Daphne** | ASGI server that handles both HTTP and WebSocket connections |
| **SQLite** | Default database — stores all user, analysis, job, and message records |
| **spaCy** | Optional NER for extracting names, emails, phone numbers — falls back gracefully if not loaded |
| **pdfplumber** | PDF text extraction with layout awareness |
| **python-docx** | Word (.docx) file parsing |
| **Sentence-Transformers** | `all-MiniLM-L6-v2` model for semantic skill matching and Layer 3 extraction (optional import) |
| **scikit-learn** | TF-IDF vectorizer, K-Means, Random Forest, cosine similarity |
| **XGBoost** | Gradient-boosted classifier for candidate selection prediction |
| **rank-bm25** | BM25 Okapi implementation for information retrieval scoring |
| **pandas / numpy** | Feature engineering for ML training and inference |
| **imbalanced-learn** | SMOTE implementation to balance the XGBoost training dataset |
| **joblib** | Serializing and loading trained ML models to/from disk |
| **Tesseract / pytesseract** | OCR for image-based resume text extraction |
| **Pillow** | Image pre-processing before OCR |
| **Google Gemini** | Natural language qualitative resume feedback + AI bullet enhancement |
| **Adzuna API** | Real-time job listings and salary benchmark data |
| **pytrends** | Google Trends API integration for skill demand trends |
| **reportlab** | Generating downloadable PDF analysis reports |
| **Celery** | Task queue configured in eager/synchronous mode for development (no separate broker required) |

---

## 11. Installation and Setup

### Prerequisites

- Python 3.11+
- Redis server running locally (or Docker)
- Tesseract OCR installed on the system

### Steps

```bash
# 1. Clone the repository
git clone <repository-url>
cd "antigravity cv"

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. (Optional) Download the spaCy language model for enhanced NER
# spaCy is optional — the app runs without it using regex-based entity extraction
python -m spacy download en_core_web_sm

# 5. Apply database migrations
python manage.py migrate

# 6. (Optional) Set environment variables for external APIs
# Create a .env file or set in your shell:
# GEMINI_API_KEY=your_gemini_key
# ADZUNA_APP_ID=your_adzuna_id
# ADZUNA_APP_KEY=your_adzuna_key

# 7. (Optional) Train the ML models from the Kaggle dataset
# Download UpdatedResumeDataSet.csv from Kaggle and place in ml_models/kaggle_data/
python ml_models/kaggle_trainer.py

# 8. Run the development server
# `manage.py runserver` has been configured to automatically launch the local Redis server 
# and the Celery worker in separate background console windows. 
# When you stop the server with Ctrl+C, the background services will cleanly shut down.
python manage.py runserver

# 9. Access the application
# Unified Login:    http://127.0.0.1:8000/
# Candidate Portal: http://127.0.0.1:8000/candidate/upload/
# Recruiter Portal: http://127.0.0.1:8000/recruiter/dashboard/
```

---

## 12. Example Working Scenario

**Scenario:** A software engineering student uploads their resume to apply for a Python Developer role.

1. Student visits `http://127.0.0.1:8000/`, selects **Candidate**, logs in.
2. On the Upload page, they attach their PDF resume and select "Python Developer" as the target role.
3. The system extracts the text using **pdfplumber**. It finds `{"Python", "Django", "REST API", "Git"}` explicitly (Layer 1). It infers `"Flask"` from `"built WSGI applications"` using Sentence-BERT (Layer 3).
4. The **Hybrid Matcher** compares the resume against the Python Developer job description using TF-IDF (38%), BM25 (15%), and SBERT (44%), producing a job match of **71%**.
5. The **Weighted Scorer** computes: Skills (50% weight × 85%) + Experience (20% × 60%) + Education (10% × 80%) + Semantic (20% × 71%) = **74.2 overall score** — labeled "Good Fit".
6. The **Random Forest classifier** classifies the resume as "Python Developer" with 91% confidence.
7. **Google Gemini** suggests: "Add experience with Docker and Kubernetes to strengthen your DevOps profile."
8. The student sees a dashboard showing their score, skills breakdown, and suggestions, and downloads a PDF report.
9. When the recruiter views this application in the ATS dashboard, the XGBoost model assigns it a **68% selection probability** based on historical hiring patterns.

---

## 13. Future Improvements

- **Real-time resume feedback** — Stream GPT feedback token-by-token using Server-Sent Events (SSE)
- **Video interview integration** — Embed Zoom/Google Meet links directly in interview scheduling
- **Multi-language resume support** — Add multilingual NLP models for non-English resumes
- **LinkedIn profile parsing** — Allow candidates to import their LinkedIn profile as an alternative to uploading a file
- **Mobile application** — Build a React Native app for candidates to apply on the go
- **ATS pipeline automation** — Auto-advance candidate status using configurable ML score thresholds
- **Email notifications** — Send automated emails when interview is scheduled or status changes
- **Collaborative hiring** — Allow multiple recruiters to share notes and vote on candidates
- **Model explainability** — Add SHAP values to explain why the XGBoost model assigned a particular hiring probability

---

## 14. Conclusion

RecruiterPro demonstrates the practical application of multiple AI/ML techniques in a real-world recruitment context. The system solves the genuine industry problem of resume overload by combining **rule-based NLP**, **transformer-based semantic understanding**, **classical information retrieval (BM25/TF-IDF)**, and **supervised machine learning (XGBoost, Random Forest)** into a unified pipeline.

The Candidate Portal provides applicants with transparent, actionable feedback — making the platform useful for both job seekers and recruiters. The Recruiter ATS automates shortlisting, prevents unconscious bias through text scrubbing, and continuously improves its hiring predictions as more data is collected.

The architecture follows good software engineering principles: the AI logic is isolated in a standalone `ai_core` package (Strategy and Facade patterns), models are versioned and swappable, and real-time features are handled through a proper asynchronous WebSocket layer.

---

Built with Django 4.2 · Sentence-Transformers · XGBoost · Random Forest · BM25 · Google Gemini · Redis · Django Channels

---

## 15. Database Schema and Data Models

The application uses Django ORM with a SQLite backend. Below is a full description of all core models and their relationships.

### `UserProfile`

- Links every Django `User` to a role: `candidate` or `recruiter`
- Auto-created on user registration via a Django `post_save` signal
- Has helper properties: `is_recruiter`, `is_candidate`

### `CandidateAnalysis`

The most central model in the system — one record is created per resume upload.

| Field | Type | Description |
|-------|------|-------------|
| `user` | ForeignKey | The candidate who uploaded this resume |
| `resume_file` | FileField | Stored under `media/resumes/YYYY/MM/` |
| `full_text` | TextField | Full extracted resume text |
| `candidate_name`, `email`, `phone` | CharField | NER-extracted contact info |
| `extracted_skills` | JSONField | List of all skills found across 3 layers |
| `experience_years` | FloatField | Regex-extracted years from resume |
| `education_level` | CharField | Highest degree detected (PhD, Masters, etc.) |
| `overall_score` | FloatField | Composite AI score (0–100) |
| `skill_score`, `experience_score`, `education_score`, `keyword_score` | FloatField | Individual dimension scores |
| `job_match_percentage` | FloatField | Hybrid match % against selected job role |
| `matched_skills`, `missing_skills` | JSONField | Compared against `JobRole.required_skills` |
| `suggestions`, `career_paths` | JSONField | AI-generated improvement tips |
| `share_token` | UUIDField | UUID for publicly shareable report links |

### `JobRole`

Pre-defined job templates created by system admins/recruiters.

| Field | Type | Description |
|-------|------|-------------|
| `title` | CharField | e.g., "Python Developer", "Data Scientist" |
| `required_skills` | JSONField | List of skills used to calculate skill match % |
| `avg_salary_min`, `avg_salary_max` | IntegerField | Salary range benchmarks |

### `JobPosting`

A recruiter's specific job opening, linked to a `JobRole`.

- When a new `JobPosting` is saved, it broadcasts a `new_job_created` WebSocket event to all connected dashboard users.

### `JobApplication`

The join table connecting a candidate's resume analysis to a job posting.

| Field | Type | Description |
| :--- | :--- | :--- |
| `status` | CharField | `applied → shortlisted → hired / rejected` |
| `ml_selection_probability` | FloatField | XGBoost model's predicted hire probability |

### `Interview`

Tracks interview slots with type (phone, video, onsite, technical, HR), meeting link, notes, and status (scheduled, completed, cancelled, no_show).

### `RecruiterMessage`

Stores all messages sent from recruiter to candidate, linked to a specific `JobApplication`.

### `MLModelVersion`

Tracks every XGBoost training run with version ID, accuracy, ROC AUC score, confusion matrix (JSON), and the file path to the `.joblib` model. Only one version is `is_active=True` at any time.

### `Notification`

In-app alerts for candidates (interview scheduled, status changed, new message). Stores read/unread status and an optional redirect link.

### Entity Relationship Summary

```
User ─────────── UserProfile (role: candidate/recruiter)
 │
 ├── CandidateAnalysis ──────── JobRole
 │        └── JobApplication ── JobPosting ── RecruiterMessage
 │                 └── Interview
 │
 └── Notification
```

---

## 16. REST API Endpoints

The `api` app exposes REST API endpoints using Django REST Framework. All routes are mounted under `/api/`.

### External Data APIs

| Method | Endpoint | Description |
|--------|---------|-------------|
| `GET` | `/api/external/jobs/` | Fetch live job listings from Adzuna API |
| `GET` | `/api/external/salary/` | Get salary benchmarks for a given role and city |
| `GET` | `/api/market/skill-trend/` | Skill demand trend data from Google Trends (pytrends) |

### AI Feedback APIs

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/ai/resume-feedback/` | Gemini qualitative feedback for a resume |
| `POST` | `/api/ai/skill-gap-analysis/` | Skill gap analysis between resume and a role |

### Bulk Resume Processing APIs

| Method | Endpoint | Description |
|--------|---------|-------------|
| `POST` | `/api/resumes/bulk-upload/` | Upload multiple resumes at once for batch analysis |
| `POST` | `/api/resumes/bulk-analyze/` | Run batch AI analysis on bulk-uploaded resumes |
| `POST` | `/api/jobs/<job_id>/generate-upload-link/` | Generate a public shareable upload link for a job |
| `POST` | `/api/public-upload/<token>/` | Submit a resume via a public recruiter-shared link |
| `GET` | `/api/job/<job_id>/resumes/` | Get all resumes attached to a specific job |
| `GET` | `/api/resume/<id>/analysis-report/` | Retrieve the full analysis report for a resume |
| `PATCH` | `/api/resume/<id>/<action>/` | Update resume status (shortlist, hire, reject) |

### ML Model APIs

| Method | Endpoint | Description |
|--------|---------|-------------|
| `POST` | `/api/recruiter/train-model/` | Manually trigger XGBoost model retraining |
| `GET` | `/api/recruiter/model-reports/` | List all ML model training versions |
| `GET` | `/api/recruiter/model-reports/<pk>/` | Retrieve a specific training report |
| `GET` | `/api/recruiter/best-model/` | Get the currently active (best) model version |

| Endpoint | Description |
| :--- | :--- |
| `ws://host/ws/dashboard/` | Real-time recruiter dashboard feed (InMemoryChannelLayer) |

All API responses are JSON. Authentication uses Django session auth or DRF token authentication.

---

## 17. Design Patterns Used

This project follows several established software engineering design patterns, making it modular, testable, and easy to extend.

### Facade Pattern (`ai_core/engine.py`)

The `engine.py` file is a **Facade** — it presents a single, simplified interface (`extract_skills_advanced`, `match_resume_hybrid`, `scrub_bias`) that internally coordinates multiple complex subsystems (NLP extraction, matching, scoring). External code never needs to directly import individual AI classes.

### Strategy Pattern (`ai_core/matching.py`)

The matching system uses the **Strategy** pattern. `BaseMatcher` defines an abstract `match()` interface. Three concrete strategies implement it: `TFIDFMatcher`, `BM25Matcher`, and `SemanticMatcher`. The `HybridMatcher` composes all three to produce a weighted result. Switching or adding matchers (e.g., a fine-tuned BERT model) requires no change to the rest of the system.

### Template Method Pattern (`candidate/engine.py`)

The resume analysis pipeline follows a fixed sequence of steps (extract → clean → skills → match → score → classify → feedback), with each step potentially having different implementations depending on file type or configuration.

### Observer Pattern (Django Signals)

Django's `post_save` signal on `User` automatically creates a `UserProfile` record — this is the **Observer/Event** pattern, decoupling user creation logic from profile creation logic.

### Versioned Model Artifacts

ML model files are saved with a unique version ID (UUID8) and tracked in the `MLModelVersion` database table. Only one version is active at a time. This is the **Active Record versioning** pattern — new training runs are non-destructive and the old model file is retained on disk.

### Caching Strategy (Cache-Aside)

API responses from Adzuna and Google Trends are expensive external calls. The system uses **Cache-Aside** pattern with Redis: check cache first, fetch from API if miss, write to cache with TTL. Adzuna job listings are cached for 1 hour; salary data for 24 hours.

---

## 18. User Roles and Permissions

The system has two user types, differentiated via the `UserProfile.role` field.

### Candidate

- Can register/login via the candidate login page
- Can upload resumes and receive AI analysis
- Can view their full analysis report (scores, skills, suggestions)
- Can download a PDF of their report
- Can share a public view-only link of their report
- Can view their unified Inbox (system notifications + recruiter messages)
- Can update their CandidateProfile (personal details, education, social links)
- Can browse job postings on the Job Board and apply directly
- Can use the Smart Resume Builder to create structured CVs with AI-enhanced bullets
- Can analyze any public GitHub profile for skills, activity score, and AI feedback

### Recruiter

- Can register/login via the unified homepage login (select Recruiter role)
- Can create and manage job postings
- Can edit active and inactive job postings directly from the dashboard
- Can view all applications for a job, ranked by AI score and XGBoost probability
- Can change application status (Applied / Shortlisted / Hired / Rejected)
- Can schedule, edit, and cancel interviews
- Can send messages to candidates (stored and visible in candidate's inbox)
- Can compare candidates side-by-side on the Compare page
- Can filter the Compare page by job posting
- Can view ML model metrics (accuracy, ROC AUC per version)
- Can access CEO Analytics dashboard with platform-wide statistics

### Access Control

- All candidate views use Django's `@login_required` decorator and check `request.user.profile.is_candidate`
- All recruiter views similarly check `is_recruiter`
- Role mismatches on the login page show a descriptive error (e.g., "This account is a Recruiter. Please select the Recruiter role")

---

## 19. Candidate Portal — Detailed UI Flow

The candidate portal is a multi-page web application with a consistent dark-themed, glassmorphism design.

### Page 1: Unified Login / Homepage (`/`)

- Role toggle (Candidate / Recruiter) with radio buttons
- Username + Password fields
- "Show Password" checkbox
- Dynamic login button that changes label based on role
- Links to Candidate Signup and Recruiter Signup

### Page 2: Resume Upload (`/candidate/upload/`)

- File upload area (supports PDF, DOCX, DOC, PNG, JPG)
- Job Role dropdown (lists all available `JobRole` objects)
- Submit triggers the full AI pipeline

### Page 3: Dashboard (`/candidate/dashboard/`)

- Circular overall score display with color coding
  - Green ≥ 80 (Excellent), Yellow ≥ 60 (Good), Orange ≥ 40 (Average), Red < 40 (Needs Improvement)
- Score breakdown bar chart: Skill, Experience, Education, Keyword, Completeness
- Matched skills (green chips) and Missing skills (red chips)
- AI improvement suggestions list
- Resume domain classification (e.g., "Python Developer — 91% confidence")
- Salary benchmark for the selected role (from Adzuna)

### Page 4: Full Report (`/candidate/report/<id>/`)

- All dashboard data plus full resume text
- PDF download button (uses reportlab)
- Public shareable link

### Page 5: Unified Inbox (`/candidate/inbox/`)

- Timeline of system notifications and recruiter messages sorted by date
- Type badges: 🔔 System / 📩 Message
- Mark individual items as read / Mark All Read button
- Unread count badge on sidebar nav link

### Page 6: Job Board (`/candidate/jobs/`)

- Browse all active job postings created by recruiters
- Apply to a job, which creates a `JobApplication` with immediate ML scoring

### Page 7: Smart Resume Builder (`/candidate/resume-builder/`)

- Structured 5-tab hierarchical CV editor
- Live A4-style classic paper preview
- AI bullet enhancement via Google Gemini
- ATS readiness score ring indicator
- Browser-native PDF export via `window.print()`

### Page 8: GitHub Analyzer (`/candidate/github-analyzer/`)

- Analyze any public GitHub profile by username
- Optional role comparison for skill gap analysis
- AI Feedback & Scoring panel with animated score counter and color-coded feedback cards

---

## 20. Recruiter Portal — Detailed UI Flow

### Page 1: ATS Dashboard (`/recruiter/dashboard/`)

- Summary stat cards: Total Jobs, Total Applications, Average Score, Shortlisted Count
- List of all job postings with active/inactive toggle
- Real-time WebSocket feed for new events

### Page 2: Job Detail (`/recruiter/job/<id>/`)

- All candidates who applied, sorted by `ml_selection_probability` (XGBoost score)
- Each candidate card shows: overall score, skill match %, experience, education, top extracted skills
- Status dropdown to change application status
- Action buttons: Schedule Interview, Send Message

### Page 3: Interview Calendar (`/recruiter/interviews/`)

- Upcoming interviews in chronological order, grouped by status
- Each interview shows: candidate name, job title, interview type, date/time, meeting link
- Quick actions: Edit, Cancel, Mark Complete

### Page 4: Compare Candidates (`/recruiter/compare/`)

- Job filter dropdown — select a job to show its top candidates
- Summary stat cards: Total Candidates, Average Score, Top Score, Average Experience
- Side-by-side candidate cards with:
  - Rank badges (🥇🥈🥉 for top 3)
  - Progress bars for Skill Score, Experience Score, Education Score, Semantic Match
  - Matched skills (green) and Missing skills (red) chip lists

### Page 5: Messages Hub (`/recruiter/messages/`)

- Sent messages table with recipient, subject, date
- Full CRUD: View, Edit (pre-fills compose form), Delete
- Compose new message at `/recruiter/message/<app_pk>/`

### Page 6: ML Pipeline Dashboard (`/recruiter/ml-models/`)

- Active model version, training date, accuracy %, ROC AUC score
- Retrain model button (`/recruiter/ml-models/retrain/`)
- Download model weights button
- Version history from `MLModelVersion` model

### Page 7: CEO Analytics (`/recruiter/ceo-analytics/`)

- Platform-wide hiring funnel metrics
- Application status distribution
- Skill demand heatmap

### Page 8: Recruiter Profile (`/recruiter/profile/`)

- View and edit recruiter account details

---

## 21. Skill Knowledge Base

The system's skill detection quality depends on the skill database in `candidate/data.py`. This file contains two sets:

### `TECHNICAL_SKILLS`

200+ curated technical skills spanning:

- **Programming Languages:** Python, Java, JavaScript, TypeScript, Go, Rust, C++, R, Scala, Julia
- **Web Frameworks:** Django, Flask, FastAPI, React, Angular, Vue, Next.js, Spring Boot, Node.js
- **Databases:** PostgreSQL, MySQL, MongoDB, Redis, Cassandra, Elasticsearch, BigQuery
- **Cloud Platforms:** AWS, GCP, Azure, DigitalOcean, Heroku
- **DevOps Tools:** Docker, Kubernetes, Terraform, Jenkins, GitLab CI, GitHub Actions
- **ML/AI Libraries:** TensorFlow, PyTorch, scikit-learn, Keras, Hugging Face, OpenCV, spaCy
- **Data Tools:** Spark, Hadoop, Kafka, Airflow, dbt, Tableau, Power BI
- **Concepts:** Microservices, REST API, GraphQL, gRPC, Agile, Scrum, Design Patterns

### `SOFT_SKILLS`

50+ soft skills including: Leadership, Communication, Problem Solving, Critical Thinking, Team Management, Time Management, Collaboration, Adaptability, Mentoring, Presentation.

### Ontology Map

12 common abbreviations are mapped to canonical names (`JS → JavaScript`, `k8s → Kubernetes`, `ML → Machine Learning`, etc.), preventing skills from being missed due to shorthand notation.

---

## 22. External API Integrations

### Google Gemini API

- **Used for:** (1) Qualitative resume feedback generation and (2) AI Bullet Enhancement in the Resume Builder
- **How:** The resume text and target role are sent in a structured prompt to Gemini 1.5/3.1 Flash. The API returns a strict JSON object.
- **Fallback:** If the API key is not set or the call fails, a static fallback response is returned.
- **Model chosen:** `Gemini 1.5/3.1 Flash` — chosen for its free tier, extremely fast response time, and high instruction-following quality.

### Adzuna Jobs API

- **Used for:** Real-time job listings and salary benchmarks
- **How:** Accepts `skill` and `city` as parameters, fetches 10 jobs per page with title, company, salary range, and redirect URL
- **Caching:** Results are cached locally in the application layer; Redis is listed in `requirements.txt` but the current configuration uses in-process caching
- **Salary Estimation:** The `/historystats` endpoint returns an average monthly salary; the system estimates a ±20% range around the mean

### Google Trends (pytrends)

- **Used for:** Displaying the market demand trend for specific tech skills
- **How:** `trends_service.py` queries the `TrendReq` API for a keyword (skill name) and returns time-series interest-over-time data
- **Usage:** Candidates can see if a skill they have is trending up or down in job market demand

### Tesseract OCR

- **Used for:** Extracting text from image-format resumes (.png, .jpg, .jpeg)
- **How:** `OCRService.extract_text()` opens the image with Pillow, converts to RGB, then sends it to Tesseract via pytesseract
- **Limitation:** OCR accuracy depends on image quality and formatting; scanned PDFs may have lower extraction accuracy compared to digital PDFs

---

## 23. ML Model Training — Kaggle Dataset

The `ml_models/kaggle_trainer.py` script is used to train the two main resue-related models offline:

### Dataset

- **Source:** Kaggle "UpdatedResumeDataSet" — a labeled dataset of resumes across 25 job categories
- **Size:** ~2,400 resume samples, 25 category labels
- **Stored at:** `ml_models/kaggle_data/UpdatedResumeDataSet.csv`

### Random Forest Training Process (Inline with code)

1. Load CSV, extract `Resume` (text) and `Category` (label) columns
2. Clean text — remove URLs, non-ASCII characters, whitespace
3. Build hybrid feature matrix: TF-IDF text features + numerical features (skill count, keyword score, experience, education tier)
4. Label-encode the 25 category strings to integers
5. Split: 80% train / 20% test
6. Train `RandomForestClassifier(n_estimators=200, max_depth=None)`
7. Evaluate on test set — typical accuracy: ~96–98%
8. Save model and vectorizer as `.joblib` files

### Logistic Regression (Alternate Model)

- Trained on the same dataset as a lightweight alternative
- Uses a `StandardScaler` for numerical features, separate TF-IDF vectorizer
- Useful for comparisons or when the Random Forest file is unavailable

### XGBoost (Online Training from Recruiter Data)

- Trained exclusively on the recruiter's own `JobApplication` historical data
- Not pre-trained from Kaggle — learns from real hiring decisions made inside the platform
- Improves over time as more hiring decisions are logged

---

## 24. Security Considerations

### Authentication

- Django's built-in `django.contrib.auth` handles user registration, login, logout, and password hashing (PBKDF2 + SHA256 by default)
- All sensitive views are protected with `@login_required`
- **Strict Portal Separation:** Role-based access control is enforced at the view level using decorators. Candidates cannot access recruiter views, and recruiters are restricted from candidate portals. Logout flows are independently managed per portal to ensure secure state management.
- Role-based access: each view checks `user.profile.is_recruiter` before serving recruiter data

### CSRF Protection

- All POST forms include Django's `{% csrf_token %}` template tag
- The `home_login` view includes a guard for already-authenticated users, preventing CSRF token staleness issues on repeated visits

### File Upload Security

- Uploaded resume files are stored in `media/resumes/YYYY/MM/` — served as static files in development
- **Robust Filename Handling:** PDF generation uses `django.utils.text.get_valid_filename` to sanitize candidate names, preventing `BadHeaderError` and ensuring compatibility across different operating systems.
- File type validation should be enforced before processing (recommended in production: use `python-magic` for MIME type checking)

### API Key Management

- Gemini and Adzuna credentials are loaded from environment variables (`os.environ.get(...)`)
- A dummy/fallback key is used in development so the app doesn't crash without credentials

### Data Privacy

- Resume files and extracted text are stored in the platform's SQLite database and file system
- Each analysis has a unique `share_token` (UUID4) for public links — only people with the exact UUID can view a shared report
- Bias removal (`scrub_bias()`) strips gendered pronouns before any scoring is performed

---

## 25. Project Scope and Academic Relevance

### What Problem Domain This Covers

RecruiterPro sits at the intersection of **Human-Computer Interaction**, **Natural Language Processing**, **Information Retrieval**, and **Supervised Machine Learning**. It is a practical demonstration of how multiple AI subfields can be combined into a single cohesive product.

### Academic Contributions / Techniques Demonstrated

| Area | Technique Used |
| :--- | :--- |
| NLP | Tokenization, regex pattern matching, named entity recognition (spaCy) |
| Information Retrieval | TF-IDF, BM25 Okapi relevance ranking |
| Semantic NLP | Sentence embeddings, cosine similarity (Sentence-BERT) |
| Supervised ML | Random Forest classification (multi-class), XGBoost binary classification |
| Unsupervised ML | K-Means clustering on skill vectors |
| Feature Engineering | Hybrid sparse+dense feature matrices for RF and XGBoost |
| Evaluation | Accuracy, ROC AUC, Confusion Matrix for binary classifier |
| Software Engineering | Facade pattern, Strategy pattern, Observer pattern, active model versioning |
| Real-Time Systems | WebSocket protocol, ASGI architecture (Django Channels + Daphne) |
| API Design | RESTful endpoints (Django REST Framework), external API integration with caching |

### Real-World Alignment

The system directly mirrors real ATS products used in industry (Greenhouse, Lever, Workday, LinkedIn Recruiter). Unlike those systems, RecruiterPro's full AI pipeline is transparent and directly inspectable — making it an excellent academic demonstration project.

### Dataset Used

The resume classifier is trained on the publicly available **"UpdatedResumeDataSet" from Kaggle** — a commonly used benchmark dataset in NLP/resume parsing research. The XGBoost model uses live production data, demonstrating the concept of **online learning from user behavior**.

---

## 26. Known Limitations and Tradeoffs

| Limitation | Explanation | Possible Fix |
| :--- | :--- | :--- |
| SQLite not production-ready | SQLite has write lock limitations under concurrent load | Migrate to PostgreSQL for production |
| Layer 3 (SBERT) is slow | Encoding 50 skills × 30 sentences per resume adds ~2–3 seconds | Run asynchronously via Celery; cache embeddings |
| OCR accuracy varies | Tesseract struggles with stylized resume templates | Use cloud OCR (Google Vision API, AWS Textract) |
| XGBoost requires historical data | Needs at least 10 applications with both hired and non-hired outcomes | Seed with synthetic data using `ml/synthetic_data_generator.py` |
| Gemini API Limits | Google Gemini (Free Tier) has rate limits (RPM/RPD) | Implement caching or error handling for high traffic |
| No email integration | Notifications are only in-app; no SMTP email sent | Integrate Django's email backend with SendGrid or SMTP |
| Celery runs synchronously | `CELERY_TASK_ALWAYS_EAGER=True` means all tasks block the request thread | Configure a real broker (Redis/RabbitMQ) + run `celery worker` separately |
| Django Channels is in-memory | `InMemoryChannelLayer` does not scale across multiple server processes | Switch to `channels_redis` with a running Redis instance for multi-process setups |
| GitHub API rate limit | Public API is capped at 60 requests/hour without authentication | Implement GitHub OAuth to raise the limit to 5,000 requests/hour |

---

## 27. Glossary of Key Terms

| Term | Definition |
| :--- | :--- |
| **ATS** | Applicant Tracking System — software that manages the end-to-end hiring process |
| **NLP** | Natural Language Processing — AI branch dealing with understanding text |
| **TF-IDF** | Term Frequency–Inverse Document Frequency — a numerical statistic reflecting word importance in a document |
| **BM25** | Best Match 25 — a probabilistic information retrieval ranking function, improvement over TF-IDF |
| **Sentence-BERT** | A Sentence Transformers model that converts text into dense semantic vectors for similarity comparison |
| **Cosine Similarity** | A metric measuring the angle between two vectors; used to quantify how similar two texts are |
| **Random Forest** | An ensemble of decision trees; stable, accurate, and resistant to overfitting |
| **XGBoost** | Extreme Gradient Boosting — a high-performance gradient boosted tree classifier |
| **K-Means** | An unsupervised clustering algorithm that groups data points into K clusters based on distance |
| **OCR** | Optical Character Recognition — technology that extracts text from images |
| **ASGI** | Asynchronous Server Gateway Interface — enables Django to handle WebSockets alongside HTTP |
| **Django Channels** | Django extension that adds WebSocket and async support |
| **Joblib** | Python library for serializing/deserializing large NumPy arrays and ML models efficiently |
| **Facade** | A design pattern providing a simplified interface to a complex subsystem |
| **Strategy** | A design pattern defining a family of algorithms, encapsulating each one, and making them interchangeable |
| **Feature Engineering** | The process of creating meaningful input variables from raw data for ML model training |
| **ROC AUC** | Area Under the ROC Curve — measures a classifier's ability to distinguish between classes (1.0 = perfect) |
| **Hybrid Matcher** | RecruiterPro's custom matcher combining TF-IDF + BM25 + SBERT with weighted averaging |

---

## 28. Recent Advancements & Performance Refactors

This section highlights the most recent architectural and UI improvements implemented in the platform:

### 28.1 Advanced ML: Sentence-BERT Fine-Tuning

A dedicated training script `ml/fine_tune_bert.py` has been added to allow recruiters to "specialize" the AI's semantic understanding.

- **Goal:** Adapt the general `all-MiniLM-L6-v2` model to specific industry jargon or company-specific hiring criteria.
- **Method:** Uses **CosineSimilarityLoss** on user-provided resume/job matching pairs.
- **Outcome:** Produces a specialized model in `ml_models/fine_tuned_bert/` that can be swapped into the production pipeline.

### 28.2 UI/UX Refactor: Redesigned Candidate Actions

The candidate table in the Job Detail page was overhauled for better responsiveness and visual appeal:

- **Icon-based Actions:** Replaced text buttons with compact, square icon buttons (📅, 📩, 🧠, 🤖).
- **Flexbox Layout:** Ensures buttons never overflow the table cell or overlap on smaller screens.
- **Premium "Job Controls" Panel:** A new glassmorphism card on the job detail page provides a clean, centralized hub for job-level actions like re-analyzing resumes or generating public links.

### 28.3 Stability: ML Payloads & 0.0 Handling

The API communication between the backend and ML modals was hardened:

- Fixed a bug where a `0.0%` hiring probability was treated as a falsy value, crashing the Javascript report modal.
- Explicit `is not None` checks ensure that "Worst Fit" candidates still receive a professional report instead of a loading error.

---

## 29. Candidate Portal — Complete Feature Set (Updated)

The candidate portal has been significantly expanded beyond the original resume upload workflow. It is now a **multi-feature career platform** accessible via a persistent sidebar navigation.

### Sidebar Navigation (Authenticated Users)

All authenticated candidates see a dark glassmorphism sidebar on the left with the following navigation items:

| Icon | Label | URL | Description |
| :--- | :--- | :--- | :--- |
| 💼 | **Job Board** | `/candidate/jobs/` | Browse and apply to live job postings created by recruiters |
| 📝 | **Resume Builder** | `/candidate/resume-builder/` | AI-assisted structured resume editor with live A4 preview |
| 🐙 | **GitHub** | `/candidate/github-analyzer/` | Analyze any public GitHub profile for skills, activity, and AI feedback |
| 📬 | **Inbox** | `/candidate/inbox/` | Unified inbox for system notifications and recruiter messages |
| 👤 | **Profile** | `/candidate/profile/` | View and edit candidate profile with education, experience, and social links |
| 🚪 | **Logout** | `/candidate/logout/` | Securely ends the candidate session |

The sidebar brand logo (`⚡ AI Resume / ANALYZER`) uses a vibrant green-to-blue gradient icon box with elevated shadow, giving a premium feel.

---

## 30. Smart Resume Builder — Full Architecture

The Smart Resume Builder (`/candidate/resume-builder/`) is a **full in-browser career document editor** with AI enhancement capabilities. It is designed for creating ATS-optimized, industry-standard resumes.

### 30.1 Layout

The page uses a **two-panel responsive grid layout** (`grid-template-columns: 1fr 1.2fr`):

- **Left panel (Editor):** All structured data input forms and AI bullet enhancement
- **Right panel (Live Preview):** A white A4-sized classic paper resume that updates in real-time as the candidate fills out fields

### 30.2 Section Tabs

The editor is split into 5 tabs, each capturing a distinct resume section:

| Tab | Data Captured |
| :--- | :--- |
| 👤 **Info** | Full name, email, phone, LinkedIn, GitHub/portfolio, professional summary |
| 🎓 **Education** | Degree/certification, institution name, year range, GPA |
| 💼 **Experience** | Job title, company, location, date range, and nested bullet points per role |
| 🚀 **Projects** | Project title, link/GitHub URL, tech stack/timeline, and nested bullet points |
| 🛠 **Skills** | Individual skill line items with AI enhancement option |

### 30.3 JavaScript State Architecture

The builder uses a hierarchical JSON state object (`state`) that mirrors a complete resume structure:

```javascript
const state = {
  summary: { name, email, phone, linkedin, github, summary },
  education: [{ id, degree, institution, gpa, year }],
  experience: [{ id, title, company, location, dates,
    bullets: [{ id, text, enhanced: [], tip }]
  }],
  projects: [{ id, title, link, timeline,
    bullets: [{ id, text, enhanced: [], tip }]
  }],
  skills: [{ id, text }]
};
```

All state mutations (`addBlock`, `removeBlock`, `updateBlock`, `addInternalBullet`, `removeBullet`, `updateBullet`) trigger `renderEditor()` and `renderPreview()` simultaneously for live updates.

### 30.4 AI Bullet Enhancement (`✨ Enhance`)

Every bullet point inside Experience, Projects, and Skills tabs has an **`✨ Enhance`** button. On click:

1. Makes a `POST` to `/candidate/resume-builder/enhance/` with `{ bullet, role }`
2. The backend view `ai_enhance_bullet()` calls `api/services/ai_service.py` which forwards the prompt to **OpenAI GPT-4o-mini**
3. The API returns 3 polished, STAR-format, metric-driven bullet alternatives
4. These alternatives appear as clickable green "Use This" cards below the input
5. Clicking a suggestion replaces the original text and clears the alternatives

### 30.5 Live Resume Preview (Classic Paper)

The right panel renders a white `#ffffff` classic formatted resume using **`Times New Roman`** (traditional recruiter-friendly font) inside a light-gray "desk" background. As the candidate types, the preview updates in real-time with proper professional formatting:

- **Header:** Name (bold, uppercase, centred), Contact line (email | phone | LinkedIn | GitHub)
- **Sections:** All resume sections appear with a horizontal rule `h2` separator styled to match traditional resume conventions
- **Each Experience entry:** Renders as `Job Title, Company` (bold, left) with `Dates` (right), followed by `Location` (italic), then a bullet list

### 30.6 ATS Score Indicator

A compact circular ring indicator in the top-right of the preview panel shows an **ATS Readiness Score** (0–100). The score animates and changes color:

- 🔴 Red: 0–39 (Incomplete)
- 🟡 Yellow: 40–69 (Developing)
- 🟢 Green: 70–100 (ATS Ready)

Score is computed based on: presence of contact details, professional summary, education, and total bullet count.

### 30.7 PDF Export

A red **`📥 PDF`** button in the preview toolbar triggers `window.print()`. A dedicated `@media print` ruleset in the CSS:

1. Hides the entire dark UI (sidebar, toolbar, editor panel)
2. Resets all layout constraints
3. Renders only the `classic-paper` div, exactly as shown in the preview

This produces a pixel-perfect, clean PDF with no artifacts or dark backgrounds.

---

## 31. GitHub Analyzer — Full Feature Documentation

The GitHub Analyzer (`/candidate/github-analyzer/`) fetches and analyzes any public GitHub profile using the **GitHub REST API** (no API key required for public data; 60 requests/hour rate limit applies).

### 31.1 Input Parameters

| Field | Description |
| :--- | :--- |
| **GitHub Username** | The target public profile to analyze |
| **Compare Against Role** | Optional — selects a job role from the platform's `JOB_ROLE_SKILLS` database to run a skill-match comparison |

### 31.2 Backend Service (`api/services/github_service.py`)

The `fetch_github_profile(username)` function:

1. Calls `https://api.github.com/users/{username}` to get profile data (name, bio, location, company, followers, public repos count)
2. Calls `https://api.github.com/users/{username}/repos?sort=stars&per_page=30` to fetch up to 30 repos, aggregating total stars, forks, and language distribution
3. Computes an **Activity Score** (0–100) based on: recency of pushes, stars, forks, and repo count
4. Extracts a list of **Skills** from detected repository languages and topic tags (e.g., `python`, `machine-learning`, `docker`)
5. Returns a structured dictionary ready for JSON serialization

### 31.3 AI Scoring Algorithm (`views.py` — `fetch_github_data`)

After the GitHub service returns profile data, the view runs a **Dynamic Scoring Algorithm** to compute an `ai_feedback` object:

```text
overall_score = activity_score × 0.40         (base)
             + stars_bonus  (15–25 pts)        (community impact)
             + repos_bonus  (10–15 pts)        (portfolio volume)
             + followers_bonus (10 pts)        (peer recognition)
             + role_match_bonus (0–30 pts)     (if role selected)
             = min(100, total)
```

**Score breakpoints:**

- `≥ 80` → Outstanding Profile 🟢
- `≥ 50` → Solid Presence 🟡
- `< 50` → Needs Development 🔴

### 31.4 Actionable AI Feedback Cards

Based on the computed score and profile data, the system generates up to 3 colored feedback cards:

| Card Type | Condition | Example Message |
| :--- | :--- | :--- |
| ✅ **Success** (green) | `score ≥ 80` | "Outstanding GitHub presence! Your profile is highly attractive to engineering managers." |
| 💡 **Warning** (yellow) | `score 50–79` or missing role skills | "To align better as a Data Scientist, consider pinning projects built with: tensorflow, pandas, scikit-learn." |
| ⚠️ **Danger** (red) | `score < 50` or empty bio | "Your GitHub bio is empty or too short. Add a professional summary of your technical focus." |

### 31.5 Animated Score Counter

When results render, the `ai-overall-score` element performs a smooth count-up animation from `0` to the final score via a `setInterval` timer, providing a polished data visualization experience.

### 31.6 Role Skill Match Analysis

If a role is selected, the system computes:

- **Matched Skills** (green chips): Skills detected in GitHub repos that are required for the role
- **Missing Skills** (red chips): Role-required skills not found in any repository
- **Role Match %** displayed as a progress bar

### 31.7 Top Repositories Display

The top 6 repositories (by stars) are shown as rich cards with:

- Repository name (linked to GitHub)
- Star ⭐ and Fork 🍴 counts
- Description excerpt
- Topic tags (blue chips)
- Primary language indicator

---

## 32. Job Board — Candidate Side

The Job Board (`/candidate/jobs/`) lets candidates browse all active job postings created by recruiters and apply directly from the platform.

### 32.1 Listing View (`jobs_list.html`)

- Shows all `JobPosting` objects with `is_active=True`
- Each listing card shows: job title, company, location, salary range, and required skills as badges
- A clear **"Apply Now"** button navigates to the application form

### 32.2 Application Flow (`job_apply.html`)

1. Candidate selects or uploads a resume to attach
2. Submits the application form
3. Backend `apply_to_job()` view in `candidate/views.py`:
   - Creates a `JobApplication` record linking the candidate's `CandidateAnalysis` to the `JobPosting`
   - Immediately computes and persists the `ml_selection_probability` via `ml_pipeline.predict_selection_probability()`
   - Sends a `Notification` to the recruiter of the new application
   - Redirects the candidate to a success confirmation page

This ensures that every application immediately has a valid ML score attached, enabling correct ranking in the recruiter's ATS dashboard.

---

## 33. Candidate Profile Page

The Profile page (`/candidate/profile/`) allows candidates to view and edit their full professional profile.

### 33.1 View Mode

Displays:

- Profile avatar (initial-based avatar with gradient background)
- Display name, email, phone
- Bio / professional summary
- Education details (degree, institution, year)
- Work experience entries
- Social links (LinkedIn, GitHub, Portfolio)
- List of extracted/imported skills as chips

### 33.2 Edit Mode

Toggled via an **"Edit Profile"** button. All fields become editable inline. On save:

- `POST` to `/candidate/profile/` with updated form data
- Updates the `CandidateProfile` model fields
- Displays a success notification

### 33.3 Theme: Dark Glassmorphism

The profile page mirrors the recruiter portal aesthetic:

- Glass panels with `backdrop-filter: blur(20px)` and `rgba` backgrounds
- Gradient avatar circle
- Subtle border glow on hover
- Animated section transitions

---

## 34. Unified Inbox — Candidates

The Inbox (`/candidate/inbox/`) consolidates all candidate communications in one place.

### 34.1 Data Sources

| Source | Model | Icon |
| :--- | :--- | :--- |
| System Notifications | `Notification` | 🔔 |
| Recruiter Messages | `RecruiterMessage` (where `recipient=user`) | 📩 |

### 34.2 Features

- **Unified Timeline:** Both notification types appear in one chronological feed sorted by `created_at DESC`
- **Type Badges:** Color-coded labels distinguish system vs. recruiter messages
- **Read/Unread State:** Unread items appear with a highlighted border; unread count badge shown in the sidebar nav link
- **Mark All Read:** One-click button via `POST /candidate/inbox/mark-all-read/` marks all items as read and clears the unread badge

---

## 35. Updated Project File Structure (Complete)

```text
antigravity cv/
│
├── manage.py                         # Django entry point
├── requirements.txt                  # Python dependencies
├── db.sqlite3                        # SQLite database (auto-created)
│
├── recruitment/                      # Django project settings
│   ├── settings.py
│   ├── urls.py                       # Root URL dispatcher
│   ├── wsgi.py / asgi.py
│   └── celery.py
│
├── candidate/                        # Candidate app
│   ├── models.py                     # CandidateAnalysis, UserProfile, JobRole, Notification
│   ├── views.py                      # All candidate view functions (upload, dashboard, resume builder,
│   │                                 # GitHub analyzer, job board, inbox, profile, auth)
│   ├── engine.py                     # Main AI pipeline orchestrator
│   ├── urls.py                       # Candidate URL patterns
│   ├── forms.py                      # Upload, signup, profile forms
│   ├── data.py                       # JOB_ROLE_SKILLS, TECHNICAL_SKILLS, SOFT_SKILLS databases
│   ├── pdf_report.py                 # reportlab PDF generator for resume reports
│   ├── tasks.py                      # Celery async tasks
│   ├── serializers.py                # DRF serializers for candidate API
│   ├── api_urls.py                   # REST API URL patterns
│   ├── api_views.py                  # REST API views
│   └── templates/candidate/
│       ├── base.html                 # Sidebar layout for authenticated / minimal for public
│       ├── upload.html               # Resume upload page
│       ├── dashboard.html            # Analysis results dashboard
│       ├── report.html               # Full printable report
│       ├── login.html                # Candidate login
│       ├── signup.html               # Candidate registration
│       ├── profile.html              # Candidate profile (view/edit)
│       ├── jobs_list.html            # Job board listing
│       ├── job_apply.html            # Job application form
│       ├── inbox.html                # Unified inbox
│       ├── messages.html             # Recruiter message detail
│       ├── notifications.html        # Notification list
│       ├── resume_builder.html       # Pro Resume Builder (live A4 preview, AI enhance)
│       └── github_analyzer.html     # GitHub Profile Analyzer with AI scoring
│
├── recruiter/                        # Recruiter ATS app
│   ├── models.py                     # JobPosting, JobApplication, Interview, RecruiterMessage, MLModelVersion
│   ├── views.py                      # ATS dashboard, job CRUD, interview, messages, compare, analytics
│   ├── ml_pipeline.py                # XGBoost training + prediction + heuristic fallback
│   ├── urls.py                       # Recruiter URL patterns
│   ├── forms.py                      # Job creation / edit forms
│   ├── tasks.py                      # Background ML tasks
│   ├── api_urls.py / api_views.py    # Recruiter REST API endpoints
│   └── templates/recruiter/
│       ├── base.html                 # Recruiter sidebar layout
│       ├── ats_dashboard.html        # Main recruiter overview
│       ├── job_detail.html           # Ranked candidate list per job
│       ├── job_create.html           # Create/edit job posting form
│       ├── interview_calendar.html   # All interviews timeline view
│       ├── interview_schedule.html   # Schedule new interview form
│       ├── interview_detail.html     # Single interview detail (AI scores, candidate info)
│       ├── compare.html              # Side-by-side candidate comparison
│       ├── messages_hub.html         # Recruiter sent messages inbox
│       ├── message_detail.html       # Single message detail
│       ├── send_message.html         # Compose new message form
│       ├── ml_metrics.html           # ML model version tracking and metrics
│       ├── ceo_analytics.html        # Platform-wide analytics dashboard
│       ├── profile.html              # Recruiter profile
│       ├── login.html                # Recruiter login
│       └── signup.html               # Recruiter registration
│
├── ai_core/                          # Standalone AI/ML module
│   ├── engine.py                     # Facade — single public interface for all AI operations
│   ├── nlp_extraction.py             # 3-layer skill extractor (keyword → abbreviation → semantic)
│   ├── matching.py                   # Hybrid matcher (TF-IDF + BM25 + Sentence-BERT)
│   ├── scoring.py                    # Weighted composite scorer + bias removal
│   ├── resume_classifier.py          # Random Forest resume domain classifier (25 categories)
│   └── clustering.py                 # K-Means candidate skill clustering
│
├── api/                              # REST API app + external services
│   ├── views.py                      # General REST endpoints (bulk upload, public report)
│   ├── models.py                     # CentralizedResume model
│   ├── urls.py                       # API URL routing
│   ├── consumers.py                  # WebSocket consumer (Django Channels)
│   ├── routing.py                    # WebSocket URL routing
│   ├── ml_views.py                   # ML metrics API views
│   └── services/
│       ├── ai_service.py             # Google Gemini qualitative feedback + bullet enhancement
│       ├── github_service.py         # GitHub REST API profile fetching and skill extraction
│       ├── ocr_service.py            # Tesseract OCR for image resumes
│       ├── adzuna_service.py         # Adzuna job listings + salary API
│       ├── bulk_analysis_service.py  # Batch resume processing for recruiters
│       ├── bulk_upload_service.py    # Bulk file upload handler
│       ├── trends_service.py         # Google Trends skill demand data
│       └── public_link_service.py    # Shareable public resume report links
│
└── ml_models/                        # ML model files (disk storage)
    ├── kaggle_trainer.py             # Offline training script (RF + LR) on Kaggle dataset
    ├── rf_resume_classifier.joblib   # Trained Random Forest model file
    ├── rf_tfidf_vectorizer.joblib    # TF-IDF vectorizer for RF input features
    ├── logistic_regression.joblib    # Alternate LR classifier
    ├── lr_scaler.joblib              # StandardScaler for LR features
    ├── xgb_kaggle_*.joblib           # Multiple versioned XGBoost model files
    └── fine_tuned_bert/              # Fine-tuned Sentence-BERT model directory
```

---

## 36. GitHub Service API (`api/services/github_service.py`)

This service wraps the public GitHub REST API v3 with no authentication requirement.

### Functions

#### `fetch_github_profile(username: str) -> dict`

**Steps:**

1. `GET https://api.github.com/users/{username}` — Fetch base profile data
2. `GET https://api.github.com/users/{username}/repos?sort=stars&per_page=30` — Fetch top repos by stars
3. Aggregate language bytes across repos → compute percentage distribution
4. Extract `topics` tags from each repo and merge with detected languages as `extracted_skills`
5. Compute Activity Score:

```python
activity_score = min(100, int(
    (repo_count * 2)
  + (total_stars * 0.5)
  + (followers * 0.3)
  + fresh_commit_bonus   # 15 pts if last_pushed within 30 days
))
```

**Returns:**

```json
{
  "username": "johndoe",
  "name": "John Doe",
  "bio": "Python developer building cool things",
  "avatar_url": "https://avatars.githubusercontent.com/...",
  "profile_url": "https://github.com/johndoe",
  "location": "New York, US",
  "company": "Acme Corp",
  "blog": "https://johndoe.dev",
  "public_repos": 42,
  "followers": 128,
  "total_stars": 387,
  "activity_score": 76,
  "languages": [{"name": "Python", "percent": 68}, {"name": "JavaScript", "percent": 22}],
  "extracted_skills": ["python", "django", "machine-learning", "docker"],
  "top_repos": [{
    "name": "awesome-project",
    "url": "https://github.com/johndoe/awesome-project",
    "description": "A very awesome project",
    "stars": 110,
    "forks": 34,
    "language": "Python",
    "topics": ["machine-learning", "nlp"]
  }]
}
```

---

## 37. AI Bullet Enhancement API

### Endpoint

`POST /candidate/resume-builder/enhance/`

### Request Body

```json
{
  "bullet": "Worked on machine learning project for image recognition",
  "role": "AI Engineer"
}
```

### Backend Logic (`ai_service.py`)

The view calls `ai_service.enhance_resume_bullet(bullet, role)` which:

1. Builds a structured prompt:

   ```text
   You are a professional resume writer. Rewrite the following bullet point into 3 powerful,
   achievement-focused, metric-driven STAR-format alternatives for a {role} resume.
   Return ONLY valid JSON: {"enhanced": ["...", "...", "..."], "tips": "..."}
   Original: {bullet}
   ```

2. Calls `genai.GenerativeModel.generate_content(...)` via Google Gemini API
3. Parses the JSON response and returns it

### Response Body

```json
{
  "enhanced": [
    "Designed and deployed a CNN-based image recognition pipeline using TensorFlow, achieving 94.3% validation accuracy on a dataset of 50,000 images.",
    "Engineered a real-time image classification API in Python (FastAPI + PyTorch) serving 1,200 requests/minute with <50ms latency.",
    "Led development of a transfer learning model (ResNet-50) reducing training time by 40% while maintaining 91% F1 score across 12 object categories."
  ],
  "tips": "Quantify your impact wherever possible. Mention the specific framework/model architecture and the business outcome it achieved."
}
```

---

## 38. Key URL Reference

### Candidate Portal URLs

| URL | View Function | Description |
| :--- | :--- | :--- |
| `/candidate/upload/` | `upload_resume` | Resume upload + AI analysis trigger |
| `/candidate/<id>/dashboard/` | `dashboard` | Analysis results dashboard |
| `/candidate/<id>/report/` | `report` | Full detailed report |
| `/candidate/<id>/report/pdf/` | `download_pdf` | Download PDF version |
| `/candidate/share/<token>/` | `share_report` | Public shareable report link |
| `/candidate/login/` | `home_login` | Candidate login |
| `/candidate/signup/` | `user_signup` | Candidate registration |
| `/candidate/logout/` | `user_logout` | Logout |
| `/candidate/profile/` | `user_profile` | Profile view/edit |
| `/candidate/jobs/` | `job_listings` | Browse job board |
| `/candidate/jobs/<id>/apply/` | `apply_to_job` | Apply to a specific job |
| `/candidate/inbox/` | `inbox` | Unified inbox |
| `/candidate/inbox/mark-all-read/` | `mark_all_read` | Mark all notifications read |
| `/candidate/resume-builder/` | `resume_builder` | Smart Resume Builder |
| `/candidate/resume-builder/enhance/` | `ai_enhance_bullet` | AI bullet enhancement endpoint |
| `/candidate/github-analyzer/` | `github_analyzer` | GitHub Profile Analyzer |
| `/candidate/github-analyzer/fetch/` | `fetch_github_data` | GitHub data fetch + AI scoring endpoint |

### Recruiter Portal URLs

| URL | View Function | Description |
| :--- | :--- | :--- |
| `/recruiter/dashboard/` | `recruiter_dashboard` | Main ATS overview |
| `/recruiter/job/create/` | `job_create` | Create new job posting |
| `/recruiter/job/<pk>/` | `job_detail` | Ranked applicants for a job |
| `/recruiter/job/<pk>/toggle/` | `toggle_job_active` | Toggle job active/inactive status |
| `/recruiter/profile/` | `recruiter_profile` | Recruiter profile page |
| `/recruiter/interviews/` | `interview_calendar` | All interviews timeline |
| `/recruiter/interview/<pk>/` | `interview_detail` | Single interview detail |
| `/recruiter/interview/schedule/<app_pk>/` | `schedule_interview` | Schedule new interview for an application |
| `/recruiter/interview/<pk>/edit/` | `interview_edit` | Edit interview details |
| `/recruiter/interview/<pk>/cancel/` | `interview_cancel` | Cancel an interview |
| `/recruiter/interview/<pk>/complete/` | `interview_complete` | Mark interview as completed |
| `/recruiter/compare/` | `compare_candidates` | Side-by-side candidate comparison |
| `/recruiter/messages/` | `messages_hub` | Recruiter sent messages |
| `/recruiter/messages/<pk>/` | `message_detail` | Single message thread |
| `/recruiter/message/<app_pk>/` | `send_message` | Compose new message for an application |
| `/recruiter/messages/<pk>/edit/` | `message_edit` | Edit a sent message |
| `/recruiter/messages/<pk>/delete/` | `message_delete` | Delete a message |
| `/recruiter/ml-models/` | `ml_model_metrics` | ML version tracking |
| `/recruiter/ml-models/retrain/` | `retrain_model` | Retrain XGBoost model |
| `/recruiter/ml-models/download/` | `download_model_weights` | Download active model weights |
| `/recruiter/application/<app_pk>/status/` | `change_application_status` | Update application status |
| `/recruiter/ceo-analytics/` | `ceo_analytics` | Platform-wide analytics |

---

## 39. Dual AI Scoring System

A key design decision is the clear separation of two distinct scoring mechanisms, both visible in the recruiter's ATS dashboard:

### AI Match — Technical Score

- **Source:** `CandidateAnalysis.overall_score` computed by `ai_core/scoring.py`
- **Algorithm:** Weighted composite formula (Skill Match 50% + Experience 20% + Education 10% + Semantic Similarity 20%)
- **Range:** 0–100
- **Label:** Excellent / Good / Average / Low
- **Meaning:** Measures raw technical alignment between the resume and the job role requirements
- **Shown as:** "AI Match" badge (primary metric, displayed first)

### ML Match — Hire Probability

- **Source:** `JobApplication.ml_selection_probability` predicted by `recruiter/ml_pipeline.py`
- **Algorithm:** XGBoost binary classifier trained on historical `JobApplication` records where `status == 'hired'`
- **Range:** 0.0–1.0 (displayed as percentage)
- **Fallback:** If fewer than 10 historical records exist, a heuristic formula computes an estimated probability from the existing scores
- **Meaning:** Predicts the likelihood this candidate will ultimately be hired, based on patterns from past decisions
- **Shown as:** "ML Match" badge (secondary metric, displayed after AI Match)

This distinction is explicitly labelled throughout the UI — in the Job Detail table, Compare page, Interview Detail, and Message Detail views.

---

## 40. Recent Session Improvements (March 2026)

This section documents the latest round of improvements made to the platform:

### 40.1 Candidate Base Template Refactor (`candidate/base.html`)

**Problem:** The `TemplateSyntaxError` `'block' tag with name 'content' appears more than once` caused all candidate pages to crash.

**Solution:** Rewrote `base.html` so that `{% block content %}` appears exactly once. The `{% if user.is_authenticated %}` conditional now only wraps HTML layout elements (sidebar vs. minimal navbar), not the block tag itself.

**Added:** A proper authenticated sidebar layout matching the recruiter portal's visual language (persistent left nav, top header bar showing logged-in username).

### 40.2 Sidebar Brand Logo Upgrade

The `⚡ AI ResumeAnalyzer` sidebar brand was redesigned to a premium two-element layout:

- **Icon box:** 40×40px rounded square with `linear-gradient(135deg, #10b981, #3b82f6)` fill and a green-glow box shadow
- **Text stack:** "AI Resume" (bold, white, 1.15rem) above "ANALYZER" (muted, uppercase, letter-spaced) — creating a clear visual hierarchy

### 40.3 Smart Resume Builder Architectural Upgrade

The Resume Builder was upgraded from a flat bullet-point generator to a **fully structured hierarchical CV editor**:

- **Before:** Flat list of generic bullet points, single text preview box
- **After:** Nested state with Education, Experience, and Project "blocks" each containing their own bullet lists; live A4 rendered preview; structured fields for role titles, dates, GPA, links
- **Added:** Browser-native PDF export via `window.print()` with a Print CSS ruleset that isolates only the classic resume paper
- **Added:** Animated ATS score ring with color state transitions

### 40.4 GitHub Analyzer AI Scoring

Added a complete AI feedback module to the GitHub Analyzer backend and frontend:

- **Backend:** `fetch_github_data` view now computes `ai_feedback` containing an `overall_score`, `highlights` (positive achievements), and `actionable` (typed feedback cards: success/warning/danger)
- **Frontend:** New "🧠 AI Feedback & Scoring" panel appears after analysis with animated score counter, strength bullets, and color-coded feedback cards

### 40.5 UI Consistency

All recruiter and candidate score displays were standardized:

1. **AI Match (Technical Score)** always appears first
2. **ML Match (Hire Probability)** always appears second
3. This order is enforced in: Job Detail table, Compare page, Interview Detail, and Message Detail templates

---

*This document is a complete technical reference for the RecruiterPro AI-Powered Resume Analyzer & Recruitment Platform.*

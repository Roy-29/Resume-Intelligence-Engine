"""
AI Core: Resume Category Classifier
Uses a trained Random Forest model to predict resume domain/category.
Falls back to simple rule-based classification if no trained model exists.
"""
import os
import re
import joblib
import numpy as np
from django.conf import settings


# Category labels from the Kaggle dataset
CATEGORY_LABELS = {
    0: 'Data Science', 1: 'HR', 2: 'Advocate', 3: 'Arts',
    4: 'Web Designing', 5: 'Mechanical Engineer', 6: 'Sales',
    7: 'Health and fitness', 8: 'Civil Engineer', 9: 'Java Developer',
    10: 'Business Analyst', 11: 'SAP Developer', 12: 'Automation Testing',
    13: 'Electrical Engineering', 14: 'Operations Manager',
    15: 'Python Developer', 16: 'DevOps Engineer', 17: 'Network Security Engineer',
    18: 'PMO', 19: 'Database', 20: 'Hadoop', 21: 'ETL Developer',
    22: 'DotNet Developer', 23: 'Blockchain', 24: 'Testing',
}

# Broader domain mapping for display
DOMAIN_MAP = {
    'Data Science': 'Data & AI',
    'Python Developer': 'Software Engineering',
    'Java Developer': 'Software Engineering',
    'Web Designing': 'Software Engineering',
    'DotNet Developer': 'Software Engineering',
    'DevOps Engineer': 'Infrastructure',
    'Hadoop': 'Data & AI',
    'ETL Developer': 'Data & AI',
    'Database': 'Data & AI',
    'Blockchain': 'Software Engineering',
    'Automation Testing': 'Quality Assurance',
    'Testing': 'Quality Assurance',
    'Network Security Engineer': 'Infrastructure',
    'Business Analyst': 'Business',
    'Operations Manager': 'Business',
    'PMO': 'Business',
    'HR': 'Business',
    'Sales': 'Business',
    'Mechanical Engineer': 'Engineering',
    'Civil Engineer': 'Engineering',
    'Electrical Engineering': 'Engineering',
    'Health and fitness': 'Healthcare',
    'Advocate': 'Legal',
    'Arts': 'Creative',
    'SAP Developer': 'Enterprise Software',
}


def _load_rf_model():
    """Load the trained RF model and TF-IDF vectorizer."""
    models_dir = os.path.join(settings.BASE_DIR, 'ml_models')
    rf_path = os.path.join(models_dir, 'rf_resume_classifier.joblib')
    tfidf_path = os.path.join(models_dir, 'rf_tfidf_vectorizer.joblib')

    if os.path.exists(rf_path) and os.path.exists(tfidf_path):
        return joblib.load(rf_path), joblib.load(tfidf_path)
    return None, None


def classify_resume_ml(resume_text: str) -> dict:
    """
    Classify a resume using the trained Random Forest model.
    Returns: { 'category': str, 'domain': str, 'confidence': float, 'top_3': list }
    Falls back to rule-based if no model is available.
    """
    rf, tfidf = _load_rf_model()

    if rf is None or tfidf is None:
        # Fallback to rule-based
        return _fallback_classify(resume_text)

    # Clean text
    text_clean = re.sub(r'http\S+', '', resume_text)
    text_clean = re.sub(r'[^\x00-\x7f]', ' ', text_clean)
    text_clean = re.sub(r'\s+', ' ', text_clean).strip()

    # TF-IDF features
    X_tfidf = tfidf.transform([text_clean])

    # Numerical features (same as training)
    text_lower = text_clean.lower()
    tech_terms = [
        'python', 'java', 'javascript', 'react', 'node', 'sql', 'aws',
        'docker', 'kubernetes', 'machine learning', 'deep learning',
        'tensorflow', 'pytorch', 'html', 'css', 'git', 'linux',
        'mongodb', 'postgresql', 'rest api', 'flask', 'django',
    ]
    power_keywords = [
        'achieved', 'improved', 'developed', 'designed', 'implemented',
        'managed', 'led', 'optimized', 'built', 'delivered',
    ]
    edu_tiers = {'phd': 95, 'master': 80, 'mba': 80, 'bachelor': 60, 'diploma': 40}

    skill_count = sum(1 for t in tech_terms if t in text_lower)
    keyword_score = min(sum(1 for w in power_keywords if w in text_lower) * 8, 100)

    exp_match = re.findall(r'(\d{1,2})\+?\s*(?:years?|yrs?)', text_lower)
    experience = float(max(int(y) for y in exp_match)) if exp_match else 0.0

    edu_score = max((s for kw, s in edu_tiers.items() if kw in text_lower), default=0)

    from scipy.sparse import hstack, csr_matrix
    X_num = csr_matrix([[skill_count, keyword_score, experience, edu_score]])
    X = hstack([X_tfidf, X_num])

    # Predict
    prediction = rf.predict(X)[0]
    probabilities = rf.predict_proba(X)[0]

    category = CATEGORY_LABELS.get(prediction, 'Unknown')
    domain = DOMAIN_MAP.get(category, 'General')
    confidence = float(max(probabilities) * 100)

    # Top 3 predictions
    top_indices = np.argsort(probabilities)[::-1][:3]
    top_3 = [
        {
            'category': CATEGORY_LABELS.get(idx, 'Unknown'),
            'domain': DOMAIN_MAP.get(CATEGORY_LABELS.get(idx, ''), 'General'),
            'confidence': float(probabilities[idx] * 100),
        }
        for idx in top_indices
    ]

    return {
        'category': category,
        'domain': domain,
        'confidence': confidence,
        'top_3': top_3,
    }


def _fallback_classify(text: str) -> dict:
    """Simple rule-based fallback classification."""
    text_lower = text.lower()
    from candidate.data import TECHNICAL_SKILLS, SOFT_SKILLS

    tech_count = sum(1 for s in TECHNICAL_SKILLS if s in text_lower)
    soft_count = sum(1 for s in SOFT_SKILLS if s in text_lower)

    if 'machine learning' in text_lower or 'data science' in text_lower:
        cat = 'Data Science'
    elif 'web' in text_lower or 'frontend' in text_lower or 'react' in text_lower:
        cat = 'Web Designing'
    elif 'devops' in text_lower or 'docker' in text_lower or 'kubernetes' in text_lower:
        cat = 'DevOps Engineer'
    elif tech_count > soft_count:
        cat = 'Python Developer'
    else:
        cat = 'Business Analyst'

    return {
        'category': cat,
        'domain': DOMAIN_MAP.get(cat, 'General'),
        'confidence': 0.0,  # no confidence when using fallback
        'top_3': [{'category': cat, 'domain': DOMAIN_MAP.get(cat, 'General'), 'confidence': 0.0}],
    }

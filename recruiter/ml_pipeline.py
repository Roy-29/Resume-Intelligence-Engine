"""
Recruiter App: ML Training Pipeline
Trains an XGBoost Classifier on historical data to predict candidate success.
"""
import os
import uuid
import joblib
import pandas as pd
import numpy as np
from xgboost import XGBClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, confusion_matrix
from django.conf import settings
from .models import MLModelVersion

def extract_features(applications):
    """
    Convert Django querysets to pandas DataFrame features.
    Features: skill_score, experience_score, semantic_sim (job_match_percentage), education_score
    Target: 1 if status == 'hired' else 0
    """
    data = []
    for app in applications:
        analysis = app.candidate_analysis
        data.append({
            'skill_score': analysis.skill_score,
            'exp_score': analysis.experience_score,
            'semantic_sim': analysis.job_match_percentage, # Re-using this as proxy for now
            'edu_score': analysis.education_score,
            'target': 1 if app.status == 'hired' else 0
        })
    return pd.DataFrame(data)

def train_selection_model(applications_queryset):
    """
    Trains XGBoost model on historical data.
    Saves the model as .joblib and logs metrics to DB.
    """
    df = extract_features(applications_queryset)
    
    if len(df) < 10:
        return {"error": "Need at least 10 historical applications to train the model."}
    
    # We need both classes to train
    if len(df['target'].unique()) < 2:
        return {"error": "Need both hired and non-hired examples to train the model."}

    X = df[['skill_score', 'exp_score', 'semantic_sim', 'edu_score']]
    y = df['target']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train XGBoost
    model = XGBClassifier(n_estimators=100, max_depth=3, learning_rate=0.1, use_label_encoder=False, eval_metric='logloss')
    model.fit(X_train, y_train)

    # Evaluate
    preds = model.predict(X_test)
    probs = model.predict_proba(X_test)[:, 1]

    acc = accuracy_score(y_test, preds)
    try:
        roc = roc_auc_score(y_test, probs)
    except ValueError:
        roc = 0.5 # Default if only one class in test set
        
    cm = confusion_matrix(y_test, preds).tolist()

    # Save to disk
    version_id = f"xgb_{uuid.uuid4().hex[:8]}"
    models_dir = os.path.join(settings.BASE_DIR, 'ml_models')
    os.makedirs(models_dir, exist_ok=True)
    file_path = os.path.join(models_dir, f"{version_id}.joblib")
    
    joblib.dump(model, file_path)

    # Deactivate old models
    MLModelVersion.objects.update(is_active=False)

    # Log to DB
    ml_version = MLModelVersion.objects.create(
        version_id=version_id,
        is_active=True,
        accuracy=acc * 100,
        roc_auc=roc,
        confusion_matrix_json={'matrix': cm},
        file_path=file_path
    )

    return {
        "success": True,
        "version": version_id,
        "accuracy": acc * 100,
        "roc_auc": roc,
    }

def predict_selection_probability(skill_score, exp_score, semantic_sim, edu_score):
    """Loads current active model and predicts a single instance."""
    active_model = MLModelVersion.objects.filter(is_active=True).first()
    if not active_model or not os.path.exists(active_model.file_path):
        # Fallback to a weighted heuristic score if no XGBoost model is trained yet
        # Skills (40%), Experience (30%), Job Semantic Sim (20%), Education (10%)
        fallback_prob = (skill_score * 0.4) + (exp_score * 0.3) + (semantic_sim * 0.2) + (edu_score * 0.1)
        return float(min(100.0, fallback_prob))
    
    model = joblib.load(active_model.file_path)
    X = pd.DataFrame([{
        'skill_score': skill_score,
        'exp_score': exp_score,
        'semantic_sim': semantic_sim,
        'edu_score': edu_score
    }])
    
    try:
        prob = model.predict_proba(X)[0][1]
        # Mix the raw XGBoost probability with a bit of the semantic score heuristic 
        # to ensure it never totally flatlines to 0% purely on ML confidence
        heuristic = (skill_score * 0.3) + (exp_score * 0.2) + (semantic_sim * 0.2)
        mixed_prob = (prob * 100 * 0.7) + (heuristic * 0.3)
        return float(max(15.0, min(100.0, mixed_prob)))
    except ValueError:
        # If the loaded model was trained on different features (legacy), use fallback
        fallback_prob = (skill_score * 0.4) + (exp_score * 0.3) + (semantic_sim * 0.2) + (edu_score * 0.1)
        return float(max(15.0, min(100.0, fallback_prob)))

"""
Model Loader
=============
Loads the best trained model for prediction.
"""
import os
import joblib
import logging

logger = logging.getLogger(__name__)

TRAINED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trained')


_CACHED_BUNDLE = None
_NO_MODEL_FOUND = False


def clear_model_cache():
    """Clear cached model bundle in memory (call after re-training models)."""
    global _CACHED_BUNDLE, _NO_MODEL_FOUND
    _CACHED_BUNDLE = None
    _NO_MODEL_FOUND = False


def load_best_model(force_reload: bool = False):
    """
    Load the best model with in-memory caching.
    Returns: (model, vectorizer, label_encoder, model_name) or raises error.
    """
    global _CACHED_BUNDLE, _NO_MODEL_FOUND
    if _CACHED_BUNDLE is not None and not force_reload:
        return _CACHED_BUNDLE
    if _NO_MODEL_FOUND and not force_reload:
        raise FileNotFoundError("No best model found. Train models first.")

    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'recruitment.settings')
    
    from recruiter.models import ModelTrainingReport
    
    best = ModelTrainingReport.objects.filter(is_best=True).first()
    if not best:
        _NO_MODEL_FOUND = True
        raise FileNotFoundError("No best model found. Train models first.")

    model = joblib.load(best.model_file_path)
    
    vec_path = os.path.join(TRAINED_DIR, 'tfidf_vectorizer.joblib')
    vectorizer = joblib.load(vec_path)

    le_path = os.path.join(TRAINED_DIR, 'label_encoder.joblib')
    label_encoder = joblib.load(le_path) if os.path.exists(le_path) else None

    _CACHED_BUNDLE = (model, vectorizer, label_encoder, best.model_name)
    return _CACHED_BUNDLE


def predict_resume(resume_text: str):
    """
    Predict the category/score for a single resume using the best model.
    
    Returns:
        dict with predicted_category, predicted_score, model_used
    """
    model, vectorizer, label_encoder, model_name = load_best_model()

    X = vectorizer.transform([resume_text])
    
    pred = model.predict(X)[0]
    
    # Get prediction confidence
    score = 0.0
    if hasattr(model, 'predict_proba'):
        proba = model.predict_proba(X)[0]
        score = float(max(proba)) * 100
    elif hasattr(model, 'decision_function'):
        dec = model.decision_function(X)[0]
        if hasattr(dec, '__len__'):
            score = float(max(dec))
        else:
            score = float(dec)
        # Normalize to 0-100 range
        score = min(max((score + 2) / 4 * 100, 0), 100)
    
    # Decode label
    category = label_encoder.inverse_transform([pred])[0] if label_encoder else str(pred)

    # Fit category
    if score >= 80:
        fit = "Excellent Fit"
    elif score >= 60:
        fit = "Good Fit"
    else:
        fit = "Low Fit"

    return {
        'predicted_category': category,
        'predicted_score': round(score, 1),
        'fit_category': fit,
        'model_used': model_name,
    }

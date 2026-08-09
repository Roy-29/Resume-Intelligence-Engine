"""
Feature Engineering
===================
TF-IDF vectorization for the ML training pipeline.
"""
import os
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
import logging

logger = logging.getLogger(__name__)

TRAINED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'trained')
os.makedirs(TRAINED_DIR, exist_ok=True)

VECTORIZER_PATH = os.path.join(TRAINED_DIR, 'tfidf_vectorizer.joblib')


def build_tfidf_features(texts, max_features=1000, fit=True):
    """
    Build TF-IDF feature matrix from a list of resume texts.
    
    If fit=True, fits a new vectorizer and saves it.
    If fit=False, loads the saved vectorizer and transforms.
    
    Returns: (sparse_matrix, vectorizer)
    """
    if fit:
        vectorizer = TfidfVectorizer(
            max_features=max_features,
            stop_words='english',
            ngram_range=(1, 2),
            sublinear_tf=True,
            min_df=2,
            max_df=0.95,
        )
        X = vectorizer.fit_transform(texts)
        joblib.dump(vectorizer, VECTORIZER_PATH)
        logger.info(f"TF-IDF vectorizer fitted with {X.shape[1]} features, saved to {VECTORIZER_PATH}")
    else:
        if not os.path.exists(VECTORIZER_PATH):
            raise FileNotFoundError("No saved TF-IDF vectorizer found. Train models first.")
        vectorizer = joblib.load(VECTORIZER_PATH)
        X = vectorizer.transform(texts)
        logger.info(f"TF-IDF transformed {X.shape[0]} samples using saved vectorizer")

    return X, vectorizer

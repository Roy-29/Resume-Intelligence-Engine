"""
AI Core: Matching Engine
Implements Strategy Pattern for dynamic algorithm switching.
"""
import numpy as np
from abc import ABC, abstractmethod
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rank_bm25 import BM25Okapi
from sentence_transformers import SentenceTransformer

import os

# Load model lazily to save startup time
_semantic_model = None

def get_semantic_model():
    global _semantic_model
    if _semantic_model is None:
        model_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ml_models', 'fine_tuned_bert')
        if os.path.exists(model_path):
            _semantic_model = SentenceTransformer(model_path)
        else:
            # all-MiniLM-L6-v2 is an excellent balance of speed and semantic capability
            _semantic_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _semantic_model


class BaseMatcher(ABC):
    @abstractmethod
    def match(self, resume_text: str, job_text: str) -> float:
        pass


class TFIDFMatcher(BaseMatcher):
    def match(self, resume_text: str, job_text: str) -> float:
        vectorizer = TfidfVectorizer(stop_words='english')
        try:
            tfidf_matrix = vectorizer.fit_transform([resume_text, job_text])
            score = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
        except ValueError:
            score = 0
        return float(score * 100)


class BM25Matcher(BaseMatcher):
    def match(self, resume_text: str, job_text: str) -> float:
        # Tokenize very simply
        corpus = [resume_text.lower().split()]
        bm25 = BM25Okapi(corpus)
        query = job_text.lower().split()
        scores = bm25.get_scores(query)
        # Normalize roughly to 0-100 range for consistency
        raw_score = scores[0] if len(scores) > 0 else 0
        # BM25 is unbounded, we cap it heuristically here
        normalized = min(raw_score * 2, 100.0) 
        return float(normalized)


class SemanticMatcher(BaseMatcher):
    def match(self, resume_text: str, job_text: str) -> float:
        model = get_semantic_model()
        # Truncate to avoid exceeding model sequence length
        emb_resume = model.encode(resume_text[:2000], convert_to_tensor=True)
        emb_job = model.encode(job_text[:2000], convert_to_tensor=True)
        
        from sentence_transformers import util
        score = util.cos_sim(emb_resume, emb_job).item()
        return float(max(0, score) * 100)


class HybridMatcher(BaseMatcher):
    """Combines TF-IDF, BM25, and Semantic Match for the most robust score."""
    def match(self, resume_text: str, job_text: str) -> float:
        tfidf_score = TFIDFMatcher().match(resume_text, job_text)
        bm25_score = BM25Matcher().match(resume_text, job_text)
        semantic_score = SemanticMatcher().match(resume_text, job_text)
        
        # Weighted hybrid
        # 40% Semantic, 40% TF-IDF, 20% BM25
        final = (semantic_score * 0.40) + (tfidf_score * 0.40) + (bm25_score * 0.20)
        return float(final)

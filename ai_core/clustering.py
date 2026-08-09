"""
AI Core: Clustering
Provides Candidate group clustering based on skill vectors.
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
import numpy as np

def cluster_candidates(candidate_skills_list: list[list[str]], num_clusters: int = 4) -> list[int]:
    """
    Groups candidates into `num_clusters` domains based on their extracted skills.
    `candidate_skills_list` should be a list where each element is a list of skills for one candidate.
    Returns a list of cluster IDs corresponding to the input candidates.
    """
    if not candidate_skills_list or len(candidate_skills_list) < num_clusters:
        # Not enough data to cluster meaningfully, put everyone in cluster 0
        return [0] * len(candidate_skills_list)
        
    # Convert list of skills into space-separated pseudo-documents
    documents = [" ".join(skills) for skills in candidate_skills_list]
    
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(documents)
    
    kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
    kmeans.fit(X)
    
    return kmeans.labels_.tolist()

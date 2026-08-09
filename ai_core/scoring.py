"""
AI Core: Scoring Engine
Weighted Composite Scoring and Bias Removal mapping.
"""
import re

def remove_bias(text: str) -> str:
    """
    Remove common gendered pronouns and subjective bias terms.
    Provides a more blind-scoring approach.
    """
    bias_terms = [
        r'\bhe\b', r'\bhim\b', r'\bhis\b',
        r'\bshe\b', r'\bher\b', r'\bhers\b',
        r'\bmale\b', r'\bfemale\b',
        r'\bguy\b', r'\bgirl\b', r'\bman\b', r'\bwoman\b'
    ]
    cleaned = text
    for term in bias_terms:
        cleaned = re.sub(term, '[REDACTED]', cleaned, flags=re.IGNORECASE)
    return cleaned


def calculate_advanced_score(skill_match_pct: float, experience_score: float, education_score: float, semantic_sim: float) -> dict:
    """
    Final Score = (Skill Match × 50%) + (Experience Match × 20%) + (Education Match × 10%) + (Semantic Similarity × 20%)
    """
    final_score = (skill_match_pct * 0.50) + (experience_score * 0.20) + (education_score * 0.10) + (semantic_sim * 0.20)
    
    # Cap at 100
    final_score = min(max(final_score, 0), 100.0)
    
    if final_score >= 80:
        fit = 'Excellent Fit'
    elif final_score >= 60:
        fit = 'Good Fit'
    elif final_score >= 40:
        fit = 'Moderate Fit'
    else:
        fit = 'Low Fit'
        
    return {
        'final_score': final_score,
        'fit_category': fit,
        'breakdown': {
            'skills': skill_match_pct * 0.50,
            'experience': experience_score * 0.20,
            'education': education_score * 0.10,
            'semantic': semantic_sim * 0.20
        }
    }

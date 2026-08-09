"""
AI Core: Facade Interface
"""
from .nlp_extraction import SkillExtractor
from .matching import HybridMatcher, TFIDFMatcher, BM25Matcher, SemanticMatcher
from .scoring import remove_bias, calculate_advanced_score

# Instantiate singletons
extractor = SkillExtractor()
hybrid_matcher = HybridMatcher()

def extract_skills_advanced(text: str) -> dict:
    return extractor.extract(text)

def match_resume_hybrid(resume_text: str, job_text: str) -> float:
    return hybrid_matcher.match(resume_text, job_text)

def scrub_bias(text: str) -> str:
    return remove_bias(text)

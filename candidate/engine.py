"""
Resume Analysis Engine
======================
Text extraction, NER, skill detection, scoring, job matching, suggestions.

Hardened with defensive checks:
- MAX_PAGES limit to prevent DoS from large PDFs
- File size guard (10 MB)
- OCR fallback for scanned/image-only PDFs
- Resume validation heuristic (flags non-resume documents)
- Bias term scrubbing before scoring
- Negative-context skill stripping
- Dynamic year for 'present' in experience calculation
"""
import os
import re
import math
import logging
from datetime import datetime
from collections import Counter

import pdfplumber
from docx import Document as DocxDocument

from .data import (
    ALL_SKILLS, TECHNICAL_SKILLS, SOFT_SKILLS,
    JOB_ROLE_SKILLS, MARKET_DATA,
    EDUCATION_KEYWORDS, GENERAL_SUGGESTIONS, SKILL_GAP_SUGGESTIONS,
)

logger = logging.getLogger(__name__)

# ── Safety Constants ─────────────────────────────────────
MAX_PAGES = 20          # Prevent DoS from 500-page books
MAX_FILE_SIZE_MB = 10   # Reject files larger than 10 MB
MIN_PDF_TEXT_CHARS = 50 # Below this, attempt OCR fallback

# ── Optional: try loading spaCy ──────────────────────────────
try:
    import spacy
    nlp = spacy.load('en_core_web_sm')
except Exception:
    nlp = None

# ── Optional: scikit-learn for TF-IDF ────────────────────────
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity as sk_cosine
    HAS_SKLEARN = True
except ImportError:
    HAS_SKLEARN = False


# ═══════════════════════════════════════════════
#  1. TEXT EXTRACTION
# ═══════════════════════════════════════════════
def extract_text(file_path: str) -> str:
    """Extract raw text from PDF or DOCX with OCR fallback."""
    path_lower = file_path.lower()
    if path_lower.endswith('.pdf'):
        text = _extract_pdf(file_path)
        # Fix 3: OCR fallback — if pdfplumber got almost nothing, try OCR
        if len(text.strip()) < MIN_PDF_TEXT_CHARS:
            logger.info(f"PDF text extraction returned <{MIN_PDF_TEXT_CHARS} chars, attempting OCR fallback.")
            ocr_text = _ocr_fallback(file_path)
            if ocr_text and len(ocr_text.strip()) > len(text.strip()):
                text = ocr_text
        return text
    elif path_lower.endswith('.docx'):
        return _extract_docx(file_path)
    return ''


def _extract_pdf(path: str) -> str:
    """Extract text from PDF with a MAX_PAGES safety limit."""
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages):
            if i >= MAX_PAGES:
                logger.warning(f"PDF has {len(pdf.pages)} pages; stopped at {MAX_PAGES} to prevent overload.")
                break
            t = page.extract_text()
            if t:
                text_parts.append(t)
    return '\n'.join(text_parts)


def _ocr_fallback(file_path: str) -> str:
    """Attempt OCR extraction for scanned/image-only PDFs."""
    try:
        from api.services.ocr_service import OCRService
        # For PDFs, try converting first page to image then OCR
        # pytesseract can handle image files directly
        from pdf2image import convert_from_path
        images = convert_from_path(file_path, first_page=1, last_page=min(MAX_PAGES, 5))
        all_text = []
        for img in images:
            text = OCRService.extract_text_from_image(img)
            if text:
                all_text.append(text)
        return '\n'.join(all_text)
    except ImportError:
        logger.warning("pdf2image or Tesseract not available. OCR fallback skipped.")
        return ''
    except Exception as e:
        logger.warning(f"OCR fallback failed: {e}")
        return ''


def _extract_docx(path: str) -> str:
    doc = DocxDocument(path)
    return '\n'.join(p.text for p in doc.paragraphs if p.text.strip())


# ═══════════════════════════════════════════════
#  2. ENTITY EXTRACTION (NER + regex)
# ═══════════════════════════════════════════════
def extract_entities(text: str) -> dict:
    """Return name, email, phone extracted from resume text."""
    entities = {
        'name': '',
        'email': '',
        'phone': '',
    }

    # Email
    email_match = re.search(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', text)
    if email_match:
        entities['email'] = email_match.group()

    # Phone
    phone_match = re.search(
        r'(?:\+?\d{1,3}[\s\-]?)?(?:\(?\d{2,5}\)?[\s\-]?)?\d{3,5}[\s\-]?\d{3,5}', text
    )
    if phone_match:
        raw = phone_match.group().strip()
        digits = re.sub(r'\D', '', raw)
        if 7 <= len(digits) <= 15:
            entities['phone'] = raw

    # Name via spaCy NER
    if nlp:
        doc = nlp(text[:3000])  # first ~3000 chars
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                entities['name'] = ent.text.strip()
                break

    # Fallback: first non-empty line as name
    if not entities['name']:
        for line in text.split('\n'):
            line = line.strip()
            if line and not re.search(r'[@\d]', line) and len(line) < 60:
                entities['name'] = line
                break

    return entities


# ═══════════════════════════════════════════════
#  3. SKILL EXTRACTION
# ═══════════════════════════════════════════════
def extract_skills(text: str) -> dict:
    """Return dict with 'technical', 'soft', and 'all' skill lists."""
    text_lower = text.lower()
    found_tech = []
    found_soft = []

    for skill in TECHNICAL_SKILLS:
        pattern = r'(?<![a-zA-Z])' + re.escape(skill) + r'(?![a-zA-Z])'
        if re.search(pattern, text_lower):
            found_tech.append(skill.title())

    for skill in SOFT_SKILLS:
        pattern = r'(?<![a-zA-Z])' + re.escape(skill) + r'(?![a-zA-Z])'
        if re.search(pattern, text_lower):
            found_soft.append(skill.title())

    return {
        'technical': sorted(set(found_tech)),
        'soft': sorted(set(found_soft)),
        'all': sorted(set(found_tech + found_soft)),
    }


# ═══════════════════════════════════════════════
#  4. EXPERIENCE CALCULATION
# ═══════════════════════════════════════════════
_YEAR_RANGE = re.compile(
    r'((?:19|20)\d{2})\s*[\-–—to]+\s*((?:19|20)\d{2}|present|current|now|ongoing)',
    re.IGNORECASE,
)

_YEARS_EXP = re.compile(
    r'(\d{1,2})\+?\s*(?:years?|yrs?)\s*(?:of\s+)?(?:experience|exp)?',
    re.IGNORECASE,
)


def calculate_experience(text: str) -> float:
    """Estimate total years of experience from resume text."""
    current_year = datetime.now().year  # Fix 7: dynamic year instead of hardcoded 2025

    # Method 1: explicit "X years experience"
    explicit = _YEARS_EXP.findall(text)
    if explicit:
        return float(max(int(y) for y in explicit))

    # Method 2: date ranges
    total = 0.0
    for start_str, end_str in _YEAR_RANGE.findall(text):
        try:
            start = int(start_str)
            if end_str.lower() in ('present', 'current', 'now', 'ongoing'):
                end = current_year
            else:
                end = int(end_str)
            diff = end - start
            if 0 < diff <= 50:
                total += diff
        except ValueError:
            pass
    return total


# ═══════════════════════════════════════════════
#  5. EDUCATION DETECTION
# ═══════════════════════════════════════════════
def detect_education(text: str) -> tuple:
    """Return (education_level_label, score_weight)."""
    text_lower = text.lower()
    best = ('Not Detected', 0)
    for keyword, (label, weight) in EDUCATION_KEYWORDS.items():
        if keyword in text_lower and weight > best[1]:
            best = (label, weight)
    return best


# ═══════════════════════════════════════════════
#  6. RESUME CLASSIFICATION
# ═══════════════════════════════════════════════
def classify_resume(skills: list, experience: float) -> str:
    """Classify as Technical / Management / Fresher."""
    tech_count = sum(1 for s in skills if s.lower() in TECHNICAL_SKILLS)
    soft_count = sum(1 for s in skills if s.lower() in SOFT_SKILLS)

    if experience < 1 and len(skills) < 5:
        return 'fresher'
    if soft_count > tech_count and any(
        kw in [s.lower() for s in skills]
        for kw in ('leadership', 'project management', 'strategic planning')
    ):
        return 'management'
    return 'technical'


# ═══════════════════════════════════════════════
#  7. SCORING ENGINE
# ═══════════════════════════════════════════════
def score_resume(text: str, skills: dict, experience: float,
                 education_weight: float, job_role_title: str = '') -> dict:
    """
    Calculate weighted resume quality score (0-100).
    Skill Strength 40% | Experience 20% | Keyword 15% | Education 10% | Completeness 15%
    """
    skill_score = _skill_strength_score(skills)
    exp_score = _experience_score(experience)
    keyword_score = _keyword_score(text)
    edu_score = min(education_weight, 100)
    comp_score = _completeness_score(text, skills, experience)

    overall = (
        skill_score * 0.40 +
        exp_score * 0.20 +
        keyword_score * 0.15 +
        edu_score * 0.10 +
        comp_score * 0.15
    )

    return {
        'overall': round(overall, 1),
        'skill': round(skill_score, 1),
        'experience': round(exp_score, 1),
        'keyword': round(keyword_score, 1),
        'education': round(edu_score, 1),
        'completeness': round(comp_score, 1),
    }


def _skill_strength_score(skills: dict) -> float:
    total = len(skills.get('all', []))
    tech = len(skills.get('technical', []))
    if total == 0:
        return 10
    base = min(total * 5, 60)
    diversity = min(tech * 3, 30)
    return min(base + diversity + 10, 100)


def _experience_score(years: float) -> float:
    if years <= 0:
        return 15
    if years < 1:
        return 30
    if years < 3:
        return 50
    if years < 5:
        return 70
    if years < 10:
        return 85
    return 95


def _keyword_score(text: str) -> float:
    """Score based on presence of industry power-keywords."""
    power_words = [
        'achieved', 'improved', 'developed', 'designed', 'implemented',
        'managed', 'led', 'optimized', 'built', 'delivered',
        'increased', 'reduced', 'automated', 'launched', 'created',
        'collaborated', 'analyzed', 'mentored', 'architected', 'scaled',
    ]
    text_lower = text.lower()
    found = sum(1 for w in power_words if w in text_lower)
    return min(found * 8, 100)


def _completeness_score(text: str, skills: dict, experience: float) -> float:
    """Score based on resume section completeness."""
    score = 0
    text_lower = text.lower()

    checks = [
        (any(s in text_lower for s in ['experience', 'work history', 'employment']), 15),
        (any(s in text_lower for s in ['education', 'academic', 'university', 'degree']), 15),
        (any(s in text_lower for s in ['skills', 'technical skills', 'competencies']), 15),
        (any(s in text_lower for s in ['project', 'projects']), 10),
        (bool(re.search(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', text)), 10),
        (any(s in text_lower for s in ['linkedin', 'github', 'portfolio', 'website']), 10),
        (any(s in text_lower for s in ['summary', 'objective', 'profile', 'about']), 10),
        (any(s in text_lower for s in ['certification', 'certified', 'certificate']), 5),
        (len(skills.get('all', [])) >= 5, 5),
        (experience > 0, 5),
    ]
    for condition, points in checks:
        if condition:
            score += points
    return min(score, 100)


# ═══════════════════════════════════════════════
#  8. JOB MATCHING (TF-IDF + Cosine Similarity)
# ═══════════════════════════════════════════════
def match_job(resume_text: str, candidate_skills: list, job_role_title: str) -> dict:
    """Compare resume against a job role; return match %, matched, missing skills."""
    role_data = JOB_ROLE_SKILLS.get(job_role_title, {})
    if not role_data:
        return {'match_pct': 0, 'matched': [], 'missing': [], 'description': ''}

    required = [s.lower() for s in role_data.get('required', [])]
    nice = [s.lower() for s in role_data.get('nice_to_have', [])]
    all_role_skills = required + nice

    cand_lower = {s.lower() for s in candidate_skills}

    matched = [s.title() for s in all_role_skills if s in cand_lower]
    missing = [s.title() for s in required if s not in cand_lower]

    # Skill-based match
    if required:
        req_match = sum(1 for s in required if s in cand_lower) / len(required)
    else:
        req_match = 0

    nice_match = 0
    if nice:
        nice_match = sum(1 for s in nice if s in cand_lower) / len(nice)

    skill_pct = req_match * 0.75 + nice_match * 0.25

    # TF-IDF text similarity (if available)
    text_sim = 0
    if HAS_SKLEARN:
        role_text = role_data.get('description', '') + ' ' + ' '.join(all_role_skills)
        try:
            vec = TfidfVectorizer(stop_words='english')
            tfidf = vec.fit_transform([resume_text, role_text])
            text_sim = sk_cosine(tfidf[0:1], tfidf[1:2])[0][0]
        except Exception:
            pass

    combined = skill_pct * 0.7 + text_sim * 0.3
    match_pct = round(min(combined * 100, 100), 1)

    return {
        'match_pct': match_pct,
        'matched': matched,
        'missing': missing,
        'description': role_data.get('description', ''),
    }


# ═══════════════════════════════════════════════
#  9. SKILL GAP SUGGESTIONS
# ═══════════════════════════════════════════════
def generate_suggestions(candidate_skills: list, missing_skills: list,
                         experience: float, completeness: float) -> list:
    """Generate AI improvement suggestions."""
    suggestions = []

    # Specific gap-based suggestions
    for skill in missing_skills[:6]:
        key = skill.lower()
        if key in SKILL_GAP_SUGGESTIONS:
            suggestions.append(SKILL_GAP_SUGGESTIONS[key])
        else:
            suggestions.append(f"Consider adding {skill} to your skill set for this role.")

    # Experience-based
    if experience < 1:
        suggestions.append(
            "Gain practical experience through internships, freelance projects, or open-source contributions."
        )
    elif experience < 3:
        suggestions.append(
            "Highlight specific project outcomes and measurable results to strengthen your mid-level candidacy."
        )

    # Completeness-based
    if completeness < 60:
        suggestions.append(
            "Your resume is missing key sections. Add a summary, projects, and certifications."
        )

    # General tips
    if len(candidate_skills) < 5:
        suggestions.append(GENERAL_SUGGESTIONS[0])
        suggestions.append(GENERAL_SUGGESTIONS[1])
    else:
        suggestions.append(GENERAL_SUGGESTIONS[3])

    suggestions.append(GENERAL_SUGGESTIONS[2])  # GitHub/portfolio link

    return suggestions[:10]


# ═══════════════════════════════════════════════
# 10. CAREER PATH SUGGESTIONS
# ═══════════════════════════════════════════════
def suggest_career_paths(skills: list, experience: float, category: str) -> list:
    """Suggest career paths based on current skills."""
    cand_lower = {s.lower() for s in skills}
    scored = []

    for role, data in JOB_ROLE_SKILLS.items():
        required = set(s.lower() for s in data['required'])
        overlap = len(cand_lower & required)
        if overlap > 0:
            pct = overlap / len(required) * 100
            scored.append({'role': role, 'fit': round(pct, 1), 'category': data['category']})

    scored.sort(key=lambda x: x['fit'], reverse=True)
    return scored[:5]


# ═══════════════════════════════════════════════
# 11. MARKET INSIGHTS
# ═══════════════════════════════════════════════
def get_market_insights(job_role_title: str) -> dict:
    """Return market data for a job role."""
    return MARKET_DATA.get(job_role_title, {
        'avg_salary': 'Data not available',
        'demand_growth': 'N/A',
        'top_skills': [],
        'hiring_trend': [0] * 12,
        'months': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
    })


# ═══════════════════════════════════════════════
# 12. FULL ANALYSIS PIPELINE
# ═══════════════════════════════════════════════
# ═══════════════════════════════════════════════
# 12a. RESUME VALIDATION
# ═══════════════════════════════════════════════
def _is_likely_resume(text: str) -> tuple:
    """
    Heuristic check: does this text look like a resume?
    Returns (is_resume: bool, confidence: str, signals_found: int).
    Requires at least 2 of 5 common resume signals.
    """
    text_lower = text.lower()
    signals = 0

    # Signal 1: Contains an email address
    if re.search(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}', text):
        signals += 1

    # Signal 2: Contains a phone number
    if re.search(r'(?:\+?\d{1,3}[\s\-]?)?\(?\d{2,5}\)?[\s\-]?\d{3,5}[\s\-]?\d{3,5}', text):
        signals += 1

    # Signal 3: Contains education keywords
    edu_words = ['bachelor', 'master', 'phd', 'university', 'college', 'degree',
                 'b.tech', 'm.tech', 'bsc', 'msc', 'diploma', 'b.e.', 'mba']
    if any(w in text_lower for w in edu_words):
        signals += 1

    # Signal 4: Contains experience/work section headers
    work_words = ['experience', 'work history', 'employment', 'professional experience',
                  'work experience', 'career', 'internship']
    if any(w in text_lower for w in work_words):
        signals += 1

    # Signal 5: Contains skills section headers
    skill_words = ['skills', 'technical skills', 'competencies', 'proficiencies',
                   'technologies', 'tools', 'expertise']
    if any(w in text_lower for w in skill_words):
        signals += 1

    is_resume = signals >= 2
    if signals >= 4:
        confidence = 'high'
    elif signals >= 2:
        confidence = 'medium'
    else:
        confidence = 'low'

    return is_resume, confidence, signals


# ═══════════════════════════════════════════════
# 12b. NEGATIVE CONTEXT STRIPPING
# ═══════════════════════════════════════════════
_NEGATION_PATTERNS = [
    r"(?:no|not|don'?t|lack|without|zero)\s+(?:experience|knowledge|expertise|familiarity|proficiency)\s+(?:in|with|of)\s+",
    r"(?:not\s+familiar|unfamiliar|not\s+proficient|no\s+hands[\-\s]on)\s+(?:in|with)\s+",
    r"(?:haven'?t|have\s+not)\s+(?:used|worked|learned|studied)\s+",
]

def _strip_negated_skills(text: str, skills_list: list) -> list:
    """
    Remove skills that appear in a negated context.
    E.g., 'I do not have experience in Python' → remove 'Python'.
    """
    text_lower = text.lower()
    negated_skills = set()

    for pattern in _NEGATION_PATTERNS:
        for match in re.finditer(pattern, text_lower):
            # Grab the next ~60 chars after the negation phrase
            after = text_lower[match.end():match.end() + 60]
            for skill in skills_list:
                if skill.lower() in after:
                    negated_skills.add(skill)

    if negated_skills:
        logger.info(f"Stripped negated skills: {negated_skills}")

    return [s for s in skills_list if s not in negated_skills]


# ═══════════════════════════════════════════════
# 13. FULL ANALYSIS PIPELINE
# ═══════════════════════════════════════════════
def analyse_resume(file_path: str, job_role_title: str = '') -> dict:
    """Run the complete analysis pipeline and return all results."""

    # Fix 2: File size guard
    try:
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            return {'error': f'File is too large ({file_size_mb:.1f} MB). Maximum allowed is {MAX_FILE_SIZE_MB} MB.'}
    except OSError:
        pass

    # 1. Extract text
    raw_text = extract_text(file_path)
    if not raw_text.strip():
        return {'error': 'Could not extract text from the uploaded file.'}

    # Fix 5: Bias scrubbing — remove gendered terms before any scoring
    try:
        from ai_core.scoring import remove_bias
        cleaned_text = remove_bias(raw_text)
    except ImportError:
        cleaned_text = raw_text

    # Fix 4: Resume validation
    is_resume, resume_confidence, resume_signals = _is_likely_resume(raw_text)
    warning = None
    if not is_resume:
        warning = (
            'This document may not be a valid resume. '
            f'Only {resume_signals}/5 resume signals were detected. '
            'Results may be unreliable.'
        )
        logger.warning(f"Document failed resume validation: {resume_signals}/5 signals.")

    # 2. Entities (use raw text to preserve original names/emails)
    entities = extract_entities(raw_text)

    # 3. Skills (use cleaned text for bias-free extraction)
    skills = extract_skills(cleaned_text)

    # Fix 6: Strip negated skills
    skills['technical'] = _strip_negated_skills(raw_text, skills['technical'])
    skills['soft'] = _strip_negated_skills(raw_text, skills['soft'])
    skills['all'] = sorted(set(skills['technical'] + skills['soft']))

    # 4. Experience
    experience = calculate_experience(cleaned_text)

    # 5. Education
    edu_label, edu_weight = detect_education(cleaned_text)

    # 6. Classification
    category = classify_resume(skills['all'], experience)

    # 7. Scores
    scores = score_resume(cleaned_text, skills, experience, edu_weight, job_role_title)

    # 8. Job matching
    job_match = {}
    if job_role_title:
        job_match = match_job(cleaned_text, skills['all'], job_role_title)

    # 9. Suggestions
    missing = job_match.get('missing', [])
    suggestions = generate_suggestions(
        skills['all'], missing, experience, scores['completeness']
    )

    # 10. Career paths
    career_paths = suggest_career_paths(skills['all'], experience, category)

    # 11. Market insights
    market = get_market_insights(job_role_title) if job_role_title else {}

    result = {
        'text': raw_text,
        'entities': entities,
        'skills': skills,
        'experience_years': experience,
        'education_level': edu_label,
        'education_weight': edu_weight,
        'category': category,
        'scores': scores,
        'job_match': job_match,
        'suggestions': suggestions,
        'career_paths': career_paths,
        'market': market,
    }

    if warning:
        result['warning'] = warning

    return result

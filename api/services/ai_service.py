import os
import json
import random
from dotenv import load_dotenv

load_dotenv()
import time
import logging
import re
import requests

logger = logging.getLogger(__name__)

# Providers & Configuration
AI_PROVIDER = os.environ.get('AI_PROVIDER', 'huggingface').lower()
HF_API_KEY = os.environ.get('HUGGINGFACE_API_KEY', 'dummy-key')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'dummy-key')

# Retry Configuration
MAX_RETRIES = 3
BASE_DELAY = 1  # seconds (exponential backoff: 1s, 2s, 4s)

# Hugging Face Router & Models (Free Serverless Inference API)
HF_ROUTER_URL = "https://router.huggingface.co/v1/chat/completions"
HF_MODELS = [
    "Qwen/Qwen2.5-72B-Instruct",
    "meta-llama/Llama-3.2-3B-Instruct",
    "mistralai/Mistral-7B-Instruct-v0.3"
]

# Initialize Gemini Client if valid API key is present
genai_client = None
if GEMINI_API_KEY and GEMINI_API_KEY != 'dummy-key':
    try:
        from google import genai
        genai_client = genai.Client(api_key=GEMINI_API_KEY)
    except Exception as e:
        logger.warning(f"Could not initialize Gemini client: {e}")


def _extract_json_from_text(text: str) -> str:
    """Helper to extract clean JSON string if response contains markdown code fences."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _call_huggingface_with_retry(prompt: str) -> str:
    """Call Hugging Face Free Serverless Inference API (OpenAI-compatible chat endpoint)."""
    if not HF_API_KEY or HF_API_KEY == 'dummy-key':
        raise ValueError("Hugging Face API key is not configured. Set HUGGINGFACE_API_KEY in .env")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {HF_API_KEY}"
    }

    last_exception = None
    for model_name in HF_MODELS:
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a precise technical resume writer and ATS specialist. Output ONLY valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 1000,
            "temperature": 0.3
        }

        for attempt in range(MAX_RETRIES):
            try:
                res = requests.post(HF_ROUTER_URL, headers=headers, json=payload, timeout=25)
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    return _extract_json_from_text(content)
                elif res.status_code in (429, 503, 500, 504):
                    delay = BASE_DELAY * (2 ** attempt)
                    logger.warning(f"HF API {res.status_code} ({model_name}, attempt {attempt + 1}/{MAX_RETRIES}): Retrying in {delay}s...")
                    time.sleep(delay)
                else:
                    logger.warning(f"HF API HTTP {res.status_code} for model {model_name}")
                    break
            except Exception as e:
                last_exception = e
                delay = BASE_DELAY * (2 ** attempt)
                logger.warning(f"HF API Error ({model_name}, attempt {attempt + 1}/{MAX_RETRIES}): {e}. Retrying in {delay}s...")
                time.sleep(delay)

    raise Exception(f"All Hugging Face models failed. Last error: {last_exception}")


def _call_gemini_with_retry(prompt: str) -> str:
    """Call Gemini API with retry logic and model fallback."""
    if not genai_client:
        raise ValueError("Gemini API key is not configured. Set GEMINI_API_KEY in .env")
    from google.genai import types
    last_exception = None

    # Try ultra-fast gemini-2.5-flash first, fallback to gemini-1.5-flash
    models_to_try = ["gemini-2.5-flash", "gemini-1.5-flash"]
    for model_name in models_to_try:
        for attempt in range(MAX_RETRIES):
            try:
                response = genai_client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                    )
                )
                return _extract_json_from_text(response.text)
            except Exception as e:
                last_exception = e
                if '429' in str(e) or '503' in str(e) or '500' in str(e):
                    delay = BASE_DELAY * (2 ** attempt)
                    time.sleep(delay)
                else:
                    break  # Try next model if non-transient error

    if last_exception:
        raise last_exception
    raise Exception("Unknown error during Gemini API call")


def _generate_ai_response(prompt: str) -> str:
    """Routes request to primary provider with fallback support."""
    # If Gemini is configured, prefer it for 10x lower latency (1s vs 15s)
    if genai_client and AI_PROVIDER != 'huggingface':
        try:
            return _call_gemini_with_retry(prompt)
        except Exception as e:
            logger.warning(f"Gemini provider failed: {e}. Trying Hugging Face fallback...")
            return _call_huggingface_with_retry(prompt)
    else:
        try:
            return _call_huggingface_with_retry(prompt)
        except Exception as e:
            logger.warning(f"Hugging Face provider failed: {e}. Trying Gemini fallback...")
            if genai_client:
                return _call_gemini_with_retry(prompt)
            raise


ACTION_VERBS = [
    "Developed", "Engineered", "Implemented", "Architected", "Optimized",
    "Designed", "Built", "Delivered", "Automated", "Led", "Collaborated",
    "Reduced", "Increased", "Improved", "Launched", "Deployed", "Managed",
]


def enhance_resume_bullet(bullet_text: str, job_role: str) -> dict:
    """
    Takes a rough resume bullet point and returns 3 polished, ATS-friendly versions.
    Uses Hugging Face Free API with retry and fallback logic.
    """
    prompt = (
        f"You are an expert technical resume writer. Target Job Role: {job_role}\n"
        f"Original bullet: \"{bullet_text}\"\n\n"
        "Rewrite this rough bullet into 3 powerful, quantified, ATS-optimized alternatives. "
        "Each bullet must start with a strong action verb and include specific metrics or outcomes.\n\n"
        "Return ONLY a valid JSON object with this exact structure:\n"
        "{\n"
        "  \"enhanced\": [\n"
        "    \"<enhanced bullet 1>\",\n"
        "    \"<enhanced bullet 2>\",\n"
        "    \"<enhanced bullet 3>\"\n"
        "  ],\n"
        "  \"tips\": \"<one short tip on making this bullet stronger>\"\n"
        "}"
    )

    try:
        response_text = _generate_ai_response(prompt)
        return json.loads(response_text)

    except Exception as e:
        logger.warning(f"AI Service Fallback engaged: {e}")
        # --- Local Rule-Based Fallback (no API key needed) ---
        verb1, verb2, verb3 = random.sample(ACTION_VERBS, 3)
        metric = "[Insert Specific Metric/Outcome here]"

        clean = bullet_text.strip().rstrip(".")
        clean = clean[0].upper() + clean[1:] if clean else "Contributed to core system"

        return {
            "enhanced": [
                f"{verb1} {clean}, resulting in {metric}.",
                f"{verb2} and optimized {clean.lower()} to improve overall performance.",
                f"{verb3} {clean.lower()} as part of a cross-functional team.",
            ],
            "tips": "Add specific numbers (%, time saved, team size) to make your bullet stand out to ATS systems.",
        }


def generate_resume_feedback(resume_text, target_role):
    """
    Provides overall qualitative feedback and skill gap analysis.
    Uses Hugging Face Free API with retry and fallback logic.
    """
    prompt = (
        "You are an expert technical recruiter and resume reviewer.\n"
        f"Target Role: {target_role}\n\n"
        f"Resume Text:\n{resume_text}\n\n"
        "Analyze the candidate's resume and provide strictly valid JSON output.\n\n"
        "Return a JSON object with this exact structure:\n"
        "{\n"
        "  \"overall_feedback\": \"<short professional summary of the resume>\",\n"
        "  \"missing_skills\": [\"<skill 1>\", \"<skill 2>\"],\n"
        "  \"improvement_suggestions\": [\"<actionable advice 1>\", \"<actionable advice 2>\"],\n"
        "  \"optimization_score\": <integer from 0 to 100>\n"
        "}"
    )

    try:
        response_text = _generate_ai_response(prompt)
        return json.loads(response_text)
        
    except Exception as e:
        logger.warning(f"AI Service Fallback engaged: {e}")
        # Fallback for dev mode without API Keys
        return {
            "overall_feedback": "Unable to generate detailed AI feedback at this time. Please ensure the resume highlights relevant skills for the role.",
            "missing_skills": ["Review the job description for specific required skills."],
            "improvement_suggestions": [
                "Quantify your impacts with metrics (e.g. increased performance by X%)",
                "Ensure all required technical skills are explicitly listed."
            ],
            "optimization_score": 0
        }

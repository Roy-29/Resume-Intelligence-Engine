import os
import requests
from django.core.cache import cache

ADZUNA_APP_ID = os.environ.get('ADZUNA_APP_ID', 'DUMMY_ID')
ADZUNA_APP_KEY = os.environ.get('ADZUNA_APP_KEY', 'DUMMY_KEY')

# Country code, example sets to gb (UK) or us
COUNTRY = 'gb'
BASE_URL = f"https://api.adzuna.com/v1/api/jobs/{COUNTRY}"

def fetch_jobs(city, skill, page=1):
    cache_key = f"adzuna_jobs_{city}_{skill}_{page}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return cached_data
        
    url = f"{BASE_URL}/search/{page}"
    params = {
        'app_id': ADZUNA_APP_ID,
        'app_key': ADZUNA_APP_KEY,
        'what': skill,
        'where': city,
        'results_per_page': 10
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        parsed_results = {
            "city": city,
            "total_results": data.get('count', 0),
            "jobs": []
        }
        
        for item in data.get('results', []):
            parsed_results["jobs"].append({
                "title": item.get('title'),
                "company": item.get('company', {}).get('display_name'),
                "location": item.get('location', {}).get('display_name'),
                "salary_min": item.get('salary_min'),
                "salary_max": item.get('salary_max'),
                "redirect_url": item.get('redirect_url'),
                "description_snippet": item.get('description')
            })
            
        # Cache for 1 hour
        cache.set(cache_key, parsed_results, 3600)
        return parsed_results
        
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

def fetch_salary_insights(role, city):
    cache_key = f"adzuna_salary_{role}_{city}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return cached_data
        
    url = f"{BASE_URL}/historystats"
    params = {
        'app_id': ADZUNA_APP_ID,
        'app_key': ADZUNA_APP_KEY,
        'what': role,
        'where': city,
        'months': 1
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        month_data = data.get('month', {})
        if not month_data:
            return {"error": "No salary data found."}
            
        # Adzuna historystats returns average salary per month in a dictionary
        latest_month = sorted(month_data.keys())[-1]
        avg_salary = month_data[latest_month]
        
        result = {
            "role": role,
            "city": city,
            "average_salary": avg_salary,
            "salary_min": int(avg_salary * 0.8), # Approximation as API only gives average
            "salary_max": int(avg_salary * 1.2),
        }
        
        cache.set(cache_key, result, 86400) # Cache for 24h
        return result
        
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

from pytrends.request import TrendReq
from django.core.cache import cache
import pandas as pd

def fetch_skill_trend(skill, months=12):
    """
    Fetches the 12-month Google Trends data for a specific skill.
    """
    cache_key = f"pytrends_skill_{skill}_{months}"
    cached_data = cache.get(cache_key)
    
    if cached_data:
        return cached_data
        
    try:
        # Initialize pytrends
        pytrend = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
        
        # Build payload for the past 12 months
        timeframe = f'today {months}-m'
        pytrend.build_payload(kw_list=[skill], timeframe=timeframe)
        
        # Fetch interest over time
        df = pytrend.interest_over_time()
        
        if df.empty:
            return {"error": "No trend data found for this skill."}
            
        # Format for frontend chart compatibility
        trend_data = []
        for date, row in df.iterrows():
            trend_data.append({
                "date": date.strftime('%Y-%m'),
                "score": int(row[skill])
            })
            
        result = {
            "skill": skill,
            "trend_data": trend_data
        }
        
        # Cache for 24 hours (trends don't change fast)
        cache.set(cache_key, result, 86400)
        return result
        
    except Exception as e:
        return {"error": str(e)}

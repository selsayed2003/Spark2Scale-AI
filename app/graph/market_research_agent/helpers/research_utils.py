import json
import http.client
import os
import pandas as pd
from app.core.config import settings, gemini_client
from app.graph.market_research_agent import prompts
from app.graph.market_research_agent.logger_config import get_logger

logger = get_logger("ResearchUtils")

SERPER_API_KEY = settings.SERPER_API_KEY

def generate_smart_queries(business_idea):
    logger.info(f"   🧠 Brainstorming search terms for: '{business_idea}'...")
    try:
        prompt = prompts.generate_smart_queries_prompt(business_idea)
        response = gemini_client.models.generate_content(model=settings.GEMINI_MODEL_NAME, contents=prompt)
        return json.loads(response.text.replace("```json", "").replace("```", "").strip())
    except Exception as e:
        logger.warning(f"Smart query generation failed: {e}")
        return [f"{business_idea} alternatives", f"top {business_idea} apps list", f"{business_idea} competitors"]

def extract_competitors_strict(search_data, business_idea):
    """
    STRICT MODE: Extracts only Company Names. Filters out Blog Titles.
    """
    print(f"   🧪 Extracting Real App Names from {len(search_data)} results...")
    
    raw_text = ""
    for item in search_data:
        raw_text += f"- Title: {item.get('title')}\n  Snippet: {item.get('snippet')}\n\n"

    prompt = prompts.extract_competitors_prompt(business_idea, raw_text)
    
    try:
        response = gemini_client.models.generate_content(model=settings.GEMINI_MODEL_NAME, contents=prompt)
        return json.loads(response.text.replace("```json", "").replace("```", "").strip())
    except Exception as e:
        print(f"   ⚠️ Extraction Failed: {e}")
        return []

def execute_serper_search(queries):
    """
    Performs Serper Google Searches for a list of queries.
    """
    all_raw_results = []
    print(f"   🔎 executing {len(queries)} search queries...")
    
    for q in queries:
        conn = http.client.HTTPSConnection("google.serper.dev")
        payload = json.dumps({ "q": q, "num": 5 })
        headers = { 'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json' }
        try:
            conn.request("POST", "/search", payload, headers)
            res = conn.getresponse()
            data = json.loads(res.read().decode("utf-8"))
            if "organic" in data:
                all_raw_results.extend(data["organic"])
        except: pass
    
    return all_raw_results

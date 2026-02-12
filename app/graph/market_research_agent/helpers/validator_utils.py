import json
import http.client
import os
import re
from app.core.config import settings, gemini_client
from app.graph.market_research_agent import prompts
from app.graph.market_research_agent.logger_config import get_logger

logger = get_logger("ValidatorUtils")

SERPER_API_KEY = settings.SERPER_API_KEY

def extract_json_from_text(text):
    """
    Extracts the first valid JSON block from a string, handling markdown code blocks.
    """
    try:
        # 1. Try to find content within ```json ... ``` blocks
        match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        
        # 2. Try to find content within curly braces { ... }
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
            
        # 3. Fallback: try raw text if it looks like JSON
        return json.loads(text)
    except Exception as e:
        logger.warning(f"JSON Extraction Failed: {e}")
        return None

def search_forums(query):
    try:
        conn = http.client.HTTPSConnection("google.serper.dev")
        payload = json.dumps({ "q": query, "num": 10 })
        headers = { 'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json' }
        conn.request("POST", "/search", payload, headers)
        return json.loads(conn.getresponse().read().decode("utf-8"))
    except Exception as e:
        logger.warning(f"Forum search error: {e}")
        return {}

def generate_validation_queries(idea, problem_statement):
    try:
        prompt = prompts.generate_validation_queries_prompt(idea, problem_statement)
        res = gemini_client.GenerativeModel(settings.GEMINI_MODEL_NAME).generate_content(prompt)
        return extract_json_from_text(res.text)
    except Exception as e: 
        logger.warning(f"Validation query generation error: {e}")
        return None

def analyze_pain_points(idea, problem_statement, raw_results):
    judge_prompt = prompts.analyze_pain_points_prompt(idea, problem_statement, raw_results)
    
    try:
        res = gemini_client.GenerativeModel(settings.GEMINI_MODEL_NAME).generate_content(judge_prompt)
        return extract_json_from_text(res.text)
    except Exception as e:
        logger.error(f"⚠️ Error: {e}")
        return None

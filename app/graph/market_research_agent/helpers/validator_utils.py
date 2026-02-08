import json
import http.client
import os
from app.core.config import settings, gemini_client
from app.graph.market_research_agent import prompts
from app.graph.market_research_agent.logger_config import get_logger

logger = get_logger("ValidatorUtils")

SERPER_API_KEY = settings.SERPER_API_KEY

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
        res = gemini_client.models.generate_content(model=settings.GEMINI_MODEL_NAME, contents=prompt)
        return json.loads(res.text.replace("```json","").replace("```","").strip())
    except Exception as e: 
        logger.warning(f"Validation query generation error: {e}")
        return {"problem_queries": [f"{problem_statement} reddit"], "solution_queries": [f"{idea} reviews"]}

def analyze_pain_points(idea, problem_statement, raw_results):
    judge_prompt = prompts.analyze_pain_points_prompt(idea, problem_statement, raw_results)
    
    try:
        res = gemini_client.models.generate_content(model=settings.GEMINI_MODEL_NAME, contents=judge_prompt)
        return json.loads(res.text.replace("```json","").replace("```","").strip())
    except Exception as e:
        logger.error(f"⚠️ Error: {e}")
        return {}

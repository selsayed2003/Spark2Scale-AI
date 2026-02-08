import json
import http.client
import os
from app.core.config import settings, gemini_client

SERPER_API_KEY = settings.SERPER_API_KEY

def search_forums(query):
    try:
        conn = http.client.HTTPSConnection("google.serper.dev")
        payload = json.dumps({ "q": query, "num": 10 })
        headers = { 'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json' }
        conn.request("POST", "/search", payload, headers)
        return json.loads(conn.getresponse().read().decode("utf-8"))
    except: return {}

def generate_validation_queries(idea, problem_statement):
    try:
        prompt = f"Idea: {idea} | Problem: {problem_statement}. Return JSON: {{ 'problem_queries': ['q1'], 'solution_queries': ['q2'] }}"
        res = gemini_client.models.generate_content(model=settings.GEMINI_MODEL_NAME, contents=prompt)
        return json.loads(res.text.replace("```json","").replace("```","").strip())
    except: 
        return {"problem_queries": [f"{problem_statement} reddit"], "solution_queries": [f"{idea} reviews"]}

def analyze_pain_points(idea, problem_statement, raw_results):
    judge_prompt = f"""
    HYPOTHESIS: '{idea}' solves '{problem_statement}'.
    EVIDENCE: {raw_results[:20]}
    
    TASK:
    1. Assign a PAIN SCORE (0-100). How intense is the user's frustration?
       - 0-20: Mild inconvenience.
       - 80-100: Urgent, emotional, expensive problem.
    2. Verdict & Reasoning.
    
    OUTPUT JSON: 
    {{ 
        "verdict": "VALIDATED/WEAK/INVALID", 
        "pain_score": 0,
        "pain_score_reasoning": "Why you gave this score",
        "solution_fit_score": "High/Medium/Low",
        "reasoning": "..." 
    }}
    """
    try:
        res = gemini_client.models.generate_content(model=settings.GEMINI_MODEL_NAME, contents=judge_prompt)
        return json.loads(res.text.replace("```json","").replace("```","").strip())
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return {}

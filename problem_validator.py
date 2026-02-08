import http.client
import json
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
SERPER_API_KEY, GEMINI_API_KEY = os.getenv("SERPER_API_KEY"), os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

def search_forums(query):
    try:
        conn = http.client.HTTPSConnection("google.serper.dev")
        payload = json.dumps({ "q": query, "num": 10 })
        headers = { 'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json' }
        conn.request("POST", "/search", payload, headers)
        return json.loads(conn.getresponse().read().decode("utf-8"))
    except: return {}

def validate_problem(idea, problem_statement):
    print(f"\n😤 [Tool 6] Validating Problem & Quantifying Pain...")
    
    # 1. Get Queries
    try:
        prompt = f"Idea: {idea} | Problem: {problem_statement}. Return JSON: {{ 'problem_queries': ['q1'], 'solution_queries': ['q2'] }}"
        res = client.models.generate_content(model='gemini-2.5-flash-lite', contents=prompt)
        queries = json.loads(res.text.replace("```json","").replace("```","").strip())
    except: queries = {"problem_queries": [f"{problem_statement} reddit"], "solution_queries": [f"{idea} reviews"]}

    # 2. Search
    raw_results = []
    for q in queries.get("problem_queries", []):
        res = search_forums(f"site:reddit.com {q}")
        if "organic" in res:
            for item in res["organic"]: raw_results.append(f"[PROBLEM] {item.get('title','')} - {item.get('snippet','')}")
            
    for q in queries.get("solution_queries", []):
        res = search_forums(f"site:reddit.com {q}")
        if "organic" in res:
            for item in res["organic"]: raw_results.append(f"[SOLUTION] {item.get('title','')} - {item.get('snippet','')}")

    if not raw_results: return None

    # 3. AI SCORING (The New Numerical Data)
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
        res = client.models.generate_content(model='gemini-2.5-flash-lite', contents=judge_prompt)
        analysis = json.loads(res.text.replace("```json","").replace("```","").strip())
        
        os.makedirs("data_output", exist_ok=True)
        with open(f"data_output/{idea.replace(' ', '_')}_validation.json", "w") as f: json.dump(analysis, f, indent=4)
        
        print(f"⚖️  VERDICT: {analysis.get('verdict')} | 🩸 PAIN SCORE: {analysis.get('pain_score')}/100")
        return f"data_output/{idea.replace(' ', '_')}_validation.json"
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return None
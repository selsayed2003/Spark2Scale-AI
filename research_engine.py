import http.client
import json
import pandas as pd
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
CLIENT = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_smart_queries(business_idea):
    print(f"   🧠 Brainstorming search terms for: '{business_idea}'...")
    try:
        prompt = f"""
        Business Idea: "{business_idea}"
        Generate 4 Google Search Queries to find SPECIFIC COMPETITOR APP NAMES.
        Focus on: "alternatives to", "vs", "pricing", "features".
        RETURN JSON list of strings.
        """
        response = CLIENT.models.generate_content(model='gemini-2.5-flash-lite', contents=prompt)
        return json.loads(response.text.replace("```json", "").replace("```", "").strip())
    except:
        return [f"{business_idea} alternatives", f"top {business_idea} apps list", f"{business_idea} competitors"]

def extract_competitors_strict(search_data, business_idea):
    """
    STRICT MODE: Extracts only Company Names. Filters out Blog Titles.
    """
    print(f"   🧪 Extracting Real App Names from {len(search_data)} results...")
    
    raw_text = ""
    for item in search_data:
        raw_text += f"- Title: {item.get('title')}\n  Snippet: {item.get('snippet')}\n\n"

    prompt = f"""
    You are a Data Cleaner.
    Topic: "{business_idea}"
    Search Results:
    {raw_text}
    
    TASK: List the top 5 DIRECT COMPETITORS (Company/App Names Only).
    
    CRITICAL RULES:
    1. DO NOT return article titles (e.g. "Top 10 Apps"). Extract the APP NAME inside (e.g. "Tinder").
    2. DO NOT return generic terms (e.g. "AI Dating").
    3. EXTRACT 3 KEY FEATURES for each.
    
    RETURN JSON List:
    [
        {{ "Name": "App Name", "Features": "Feature A, Feature B" }},
        {{ "Name": "App Name", "Features": "Feature C, Feature D" }}
    ]
    """
    
    try:
        response = CLIENT.models.generate_content(model='gemini-2.5-flash-lite', contents=prompt)
        return json.loads(response.text.replace("```json", "").replace("```", "").strip())
    except Exception as e:
        print(f"   ⚠️ Extraction Failed: {e}")
        return []

def find_competitors(business_idea: str):
    print(f"\n🕵️ [Tool 3] Deep Market Research (Strict Mode) for: '{business_idea}'...")
    
    queries = generate_smart_queries(business_idea)
    all_raw_results = []
    
    for q in queries:
        print(f"   🔎 Searching: '{q}'...")
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

    if not all_raw_results: return None
        
    # AI Extraction
    competitors = extract_competitors_strict(all_raw_results, business_idea)
    
    if competitors:
        os.makedirs("data_output", exist_ok=True)
        filename = f"data_output/{business_idea.replace(' ', '_')}_competitors.csv"
        
        df = pd.DataFrame(competitors)
        # Fix for missing feature columns
        if "Features" not in df.columns: df["Features"] = "Standard Features"
        
        df.to_csv(filename, index=False)
        print(f"✅ Success: Extracted {len(df)} VALID competitors.")
        return filename
    
    return None
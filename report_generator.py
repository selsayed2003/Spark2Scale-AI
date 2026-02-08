import pandas as pd
import os
from google import genai
from dotenv import load_dotenv

load_dotenv()
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def generate_report(file_path: str, query: str, trend_file=None, finance_file=None):
    print(f"\n📝 [Tool 5] Synthesizing Data & Calculating Opportunity Score...")
    
    # 1. Load Validation Data
    pain_score = 0
    val_data = ""
    if os.path.exists(file_path):
        with open(file_path, 'r') as f: 
            val_data = f.read()
            import json
            try: 
                d = json.loads(val_data)
                pain_score = d.get('pain_score', 50)
            except: pass

    # 2. Load Trend Data
    growth_pct = 0
    trend_summary = "No trend data."
    if trend_file and os.path.exists(trend_file):
        try:
            stats = pd.read_csv("data_output/market_stats.csv")
            growth_row = stats[stats['metric'] == 'growth_pct']
            if not growth_row.empty:
                growth_pct = float(growth_row.iloc[0]['value'])
                trend_summary = f"12-Month Growth: {growth_pct:.1f}%"
        except: pass

    # 3. Load Financial Data (NEW)
    finance_summary = "No financial projections available."
    if finance_file and os.path.exists(finance_file):
        try:
            df_fin = pd.read_csv(finance_file)
            finance_summary = df_fin.to_string(index=False)
        except: pass

    # 4. Calculate Opportunity Score
    growth_score = max(0, min(100, growth_pct + 50))
    opp_score = (pain_score * 0.6) + (growth_score * 0.4)
    grade = "C"
    if opp_score > 80: grade = "A (Gold Mine)"
    elif opp_score > 60: grade = "B (Solid)"
    
    prompt = f"""
    You are a Venture Capital Analyst.
    TOPIC: {query}
    
    --- EXECUTIVE DASHBOARD ---
    PAIN SCORE: {pain_score}/100
    GROWTH RATE: {growth_pct:.1f}%
    OPPORTUNITY GRADE: {grade} ({opp_score:.1f})
    
    --- FINANCIAL PROJECTIONS (Estimates) ---
    {finance_summary}
    *See attached charts for breakdown.*
    
    --- QUALITATIVE EVIDENCE ---
    {val_data}
    
    TASK: Write a comprehensive Investment Memo.
    1. Executive Summary with the Dashboard.
    2. Market Validation (Pain & Trends).
    3. Financial Feasibility Analysis (Discuss costs, revenue potential, and break-even timeline based on the projections above).
    4. Final Verdict & Key Risks.
    """
    
    try:
        res = client.models.generate_content(model='gemini-2.5-flash-lite', contents=prompt)
        with open("data_output/FINAL_MARKET_REPORT.md", "w", encoding="utf-8") as f: f.write(res.text)
        print(f"✅ Final Report Saved.")
    except Exception as e: print(f"⚠️ Report Error: {e}")
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import json
import os
import http.client
from google import genai
from dotenv import load_dotenv

load_dotenv()
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def detect_currency(idea):
    """
    Asks AI to identify the target country and currency code.
    """
    print(f"   🌍 Detecting location and currency for: '{idea}'...")
    try:
        prompt = f"""
        Analyze this business idea: "{idea}"
        
        TASK: Identify the likely Target Country and its Currency.
        Return JSON: {{ "country": "CountryName", "currency_code": "XXX", "currency_symbol": "$" }}
        
        Examples:
        - "Cat Cafe in Cairo" -> {{ "country": "Egypt", "currency_code": "EGP", "currency_symbol": "EGP" }}
        - "Bakery in Paris" -> {{ "country": "France", "currency_code": "EUR", "currency_symbol": "€" }}
        - "Online SaaS" -> {{ "country": "Global", "currency_code": "USD", "currency_symbol": "$" }}
        """
        res = client.models.generate_content(model='gemini-2.5-flash-lite', contents=prompt)
        return json.loads(res.text.replace("```json","").replace("```","").strip())
    except:
        return {"country": "Global", "currency_code": "USD", "currency_symbol": "$"}

def search_cost_data(query):
    """
    Searches Google for specific cost data.
    """
    print(f"   🔎 Searching market for: '{query}'...")
    try:
        conn = http.client.HTTPSConnection("google.serper.dev")
        payload = json.dumps({ "q": query, "num": 5 })
        headers = { 'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json' }
        conn.request("POST", "/search", payload, headers)
        res = conn.getresponse()
        data = json.loads(res.read().decode("utf-8"))
        
        evidence = ""
        if "organic" in data:
            for item in data["organic"]:
                evidence += f"- {item.get('title')}: {item.get('snippet')} (Source: {item.get('link')})\n"
        return evidence
    except Exception as e:
        print(f"   ⚠️ Search failed: {e}")
        return ""

def get_real_world_estimates(idea):
    """
    1. Detects Currency.
    2. Searches for BROAD cost categories.
    3. Extracts Numbers.
    """
    # Step 1: Detect Location & Currency
    loc_data = detect_currency(idea)
    curr_code = loc_data.get("currency_code", "USD")
    country = loc_data.get("country", "Global")
    
    # Step 2: Generate BROAD Search Queries
    print(f"   🤖 Identifying cost drivers in {country} ({curr_code})...")
    plan_prompt = f"""
    Business: "{idea}"
    Location: {country}
    Currency: {curr_code}
    
    TASK: List 4 SIMPLE, BROAD search queries to find real costs.
    RULES:
    - Do NOT be too specific (Don't say "Cat Cafe Rent").
    - USE BROAD CATEGORIES (e.g. say "Commercial shop rent price {country} per meter").
    - Focus on: Rent, Staff Salaries, Raw Materials (e.g. Coffee/Cat Food), Equipment.
    
    RETURN JSON list of strings.
    """
    try:
        res = client.models.generate_content(model='gemini-2.5-flash-lite', contents=plan_prompt)
        queries = json.loads(res.text.replace("```json","").replace("```","").strip())
    except:
        queries = [f"commercial rent prices {country}", f"average salary {country}", f"coffee bean price {country}"]

    # Step 3: Search
    market_data = ""
    for q in queries:
        market_data += search_cost_data(q) + "\n"
        
    # Step 4: Extract Financials
    print(f"   🧮 Extracting {curr_code} financial model from search results...")
    extract_prompt = f"""
    You are a Conservative CFO.
    BUSINESS: {idea}
    MARKET DATA: {market_data}
    
    TASK: Build a Financial Estimate.
    
    CRITICAL RULES FOR REALISM:
    1. MARKETING IS EXPENSIVE: Allocate at least 20-30% of revenue to Marketing/CAC.
    2. SERVERS ARE EXPENSIVE: If it's an AI app, 'Utilities/Server' costs should be high.
    3. PROFIT MARGIN: A realistic Net Profit is 15-30%, NOT 90%. Adjust expenses up if needed.
    
    RETURN JSON (No Markdown):
    {{
        "currency": "{curr_code}",
        "startup_costs": {{
            "development": 0, "legal": 0, "marketing_launch": 0, "reserves": 0
        }},
        "monthly_fixed_costs": {{
            "server_infrastructure": 0, "marketing_spend": 0, "staff": 0, "misc": 0
        }},
        "revenue_assumptions": {{
            "avg_ticket_price": 0, "daily_customers": 0
        }},
        "sources_used": ["List source names"]
    }}
    """
    
    try:
        res = client.models.generate_content(model='gemini-2.5-flash-lite', contents=extract_prompt)
        return json.loads(res.text.replace("```json","").replace("```","").strip())
    except Exception as e:
        print(f"⚠️ Extraction Error: {e}")
        return {
            "currency": curr_code,
            "startup_costs": {"renovation_decor": 50000},
            "monthly_fixed_costs": {"rent": 10000},
            "revenue_assumptions": {"avg_ticket_price": 100, "daily_customers": 30},
            "sources_used": ["Fallback Estimation"]
        }

def generate_financial_visuals(estimates):
    print("   📊 Generating Localized Financial Charts...")
    os.makedirs("data_output", exist_ok=True)
    
    curr = estimates.get("currency", "USD")
    startup = estimates["startup_costs"]
    monthly = estimates["monthly_fixed_costs"]
    rev = estimates["revenue_assumptions"]
    
    total_startup = sum(startup.values())
    total_monthly = sum(monthly.values())
    
    # Revenue Math
    avg_ticket = rev.get("avg_ticket_price", 0)
    customers = rev.get("daily_customers", 0)
    monthly_rev = customers * avg_ticket * 30
    monthly_profit = monthly_rev - total_monthly
    
    # --- CHART 1: Startup Breakdown ---
    plt.figure(figsize=(8, 8))
    plt.pie(startup.values(), labels=startup.keys(), autopct='%1.1f%%', colors=plt.cm.Pastel1.colors)
    plt.title(f"Startup Costs in {curr}\nTotal: {total_startup:,.0f} {curr}")
    plt.savefig("data_output/finance_startup_pie.png")
    plt.close()
    
    # --- CHART 2: Break-Even ---
    months = np.arange(0, 25)
    cash_flow = -total_startup + (months * monthly_profit)
    break_even_month = total_startup / monthly_profit if monthly_profit > 0 else 99
    
    plt.figure(figsize=(10, 6))
    plt.plot(months, cash_flow, label=f'Net Cash ({curr})', color='green', linewidth=2)
    plt.axhline(0, color='black', linestyle='--')
    plt.title(f"Break-Even Analysis (Profit: {monthly_profit:,.0f} {curr}/mo)")
    plt.xlabel("Months")
    plt.ylabel(f"Cash Position ({curr})")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.savefig("data_output/finance_breakeven_line.png")
    plt.close()
    
    # Save CSV
    summary = {
        "Metric": ["Currency", "Total Startup", "Monthly Expenses", "Monthly Revenue", "Net Profit", "Break-Even Month"],
        "Value": [curr, total_startup, total_monthly, monthly_rev, monthly_profit, break_even_month]
    }
    pd.DataFrame(summary).to_csv("data_output/finance_summary.csv", index=False)
    
    with open("data_output/finance_sources.txt", "w") as f:
        f.write("SOURCES USED:\n")
        for s in estimates.get("sources_used", []): f.write(f"- {s}\n")
            
    print(f"✅ Success: Financials built in {curr}.")
    return "data_output/finance_summary.csv"

def run_finance_model(idea):
    print(f"\n💰 [Tool 8] Starting Localized Financial Model...")
    estimates = get_real_world_estimates(idea)
    return generate_financial_visuals(estimates)

if __name__ == "__main__":
    run_finance_model("Cat Cafe in Cairo")
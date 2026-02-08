import json
import aiohttp
import asyncio
import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from app.core.config import settings, gemini_client

SERPER_API_KEY = settings.SERPER_API_KEY

def detect_currency(idea):
    print(f"   🌍 Detecting location and currency for: '{idea}'...")
    try:
        prompt = f"""
        Analyze this business idea: "{idea}"
        RETURN JSON: {{ "country": "CountryName", "currency_code": "XXX", "currency_symbol": "$" }}
        """
        res = gemini_client.models.generate_content(model=settings.GEMINI_MODEL_NAME, contents=prompt)
        return json.loads(res.text.replace("```json","").replace("```","").strip())
    except:
        return {"country": "Global", "currency_code": "USD", "currency_symbol": "$"}

def search_cost_data(query):
    print(f"   🔎 Searching market for: '{query}'...")
    try:
        conn = http.client.HTTPSConnection("google.serper.dev")
        payload = json.dumps({ "q": query, "num": 5 })
        headers = { 'X-API-KEY': SERPER_API_KEY, 'Content-Type': 'application/json' }
        conn.request("POST", "/search", payload, headers)
        data = json.loads(conn.getresponse().read().decode("utf-8"))
        
        evidence = ""
        if "organic" in data:
            for item in data["organic"]:
                evidence += f"- {item.get('title')}: {item.get('snippet')} (Source: {item.get('link')})\n"
        return evidence
    except Exception as e:
        print(f"   ⚠️ Search failed: {e}")
        return ""

def get_real_world_estimates(idea):
    loc_data = detect_currency(idea)
    curr_code = loc_data.get("currency_code", "USD")
    country = loc_data.get("country", "Global")
    
    print(f"   🤖 Identifying cost drivers in {country} ({curr_code})...")
    plan_prompt = f"""
    Business: "{idea}"
    Location: {country}
    Currency: {curr_code}
    TASK: List 4 SIMPLE, BROAD search queries to find real costs.
    RETURN JSON list of strings.
    """
    try:
        res = gemini_client.models.generate_content(model=settings.GEMINI_MODEL_NAME, contents=plan_prompt)
        queries = json.loads(res.text.replace("```json","").replace("```","").strip())
    except:
        queries = [f"commercial rent prices {country}", f"average salary {country}", f"coffee bean price {country}"]

    market_data = ""
    for q in queries:
        market_data += search_cost_data(q) + "\n"
        
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
        res = gemini_client.models.generate_content(model=settings.GEMINI_MODEL_NAME, contents=extract_prompt)
        return json.loads(res.text.replace("```json","").replace("```","").strip())
    except Exception as e:
        print(f"⚠️ Extraction Error: {e}")
        # FIXED: Tech Startup Fallback Defaults
        return {
            "currency": curr_code,
            "startup_costs": {"development": 20000, "marketing_launch": 10000, "legal": 5000, "reserves": 5000},
            "monthly_fixed_costs": {"server_infrastructure": 500, "marketing_spend": 2000, "gross_margin_buffer": 1000},
            "revenue_assumptions": {"avg_ticket_price": 15, "daily_customers": 100},
            "sources_used": ["Fallback Estimation (Tech Startup)"]
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
    
    avg_ticket = rev.get("avg_ticket_price", 0)
    customers = rev.get("daily_customers", 0)
    monthly_rev = customers * avg_ticket * 30
    monthly_profit = monthly_rev - total_monthly
    
    plt.figure(figsize=(8, 8))
    plt.pie(startup.values(), labels=startup.keys(), autopct='%1.1f%%', colors=plt.cm.Pastel1.colors)
    plt.title(f"Startup Costs in {curr}\nTotal: {total_startup:,.0f} {curr}")
    plt.savefig("data_output/finance_startup_pie.png")
    plt.close()
    
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

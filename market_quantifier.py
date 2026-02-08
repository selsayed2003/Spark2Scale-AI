import pandas as pd
import matplotlib.pyplot as plt
from pytrends.request import TrendReq
import requests
import os
import datetime
from google import genai
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_API_KEY)

def get_wiki_topic(user_query):
    try:
        prompt = f"""
        Query: "{user_query}"
        Task: Return the EXACT Wikipedia Article Title.
        - "Cat Cafe in Cairo" -> "Cat_café"
        RETURN ONLY STRING.
        """
        response = client.models.generate_content(model='gemini-2.5-flash-lite', contents=prompt)
        return response.text.strip().replace(" ", "_").replace('"', "")
    except: return "Business"

def fetch_wikipedia_data(topic):
    print(f"   📖 Switching to Wikipedia Data for: '{topic}'...")
    end = datetime.datetime.now()
    start = end - datetime.timedelta(days=365)
    url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/{topic}/daily/{start.strftime('%Y%m%d')}/{end.strftime('%Y%m%d')}"
    headers = {'User-Agent': 'MarketResearchAgent/1.0'}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code != 200: return None, None
        data = response.json()
        if 'items' not in data: return None, None
        
        dates = [datetime.datetime.strptime(item['timestamp'], "%Y%m%d00") for item in data['items']]
        views = [item['views'] for item in data['items']]
        return pd.DataFrame({'interest': views}, index=dates), f"Wikipedia Views: {topic}"
    except: return None, None

def fetch_trend_data(keywords, geo_code='EG'):
    print(f"\n📊 [Tool 7] Quantifying Market Demand...")
    data, source_name = None, "Google Trends"
    
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        pytrends.build_payload(keywords, cat=0, timeframe='today 12-m', geo=geo_code)
        data = pytrends.interest_over_time()
        if data.empty: raise Exception("Empty")
        if 'isPartial' in data.columns: del data['isPartial']
        print("   ✅ Acquired Google Trends Data.")
    except:
        wiki_topic = get_wiki_topic(keywords[0])
        data, source_name = fetch_wikipedia_data(wiki_topic)

    if data is not None and not data.empty:
        col = data.columns[0]
        
        # --- NEW: SMARTER MATH (Moving Averages) ---
        # Instead of Day 1 vs Day 365, we compare Month 1 Avg vs Last Month Avg
        # This handles spikes (like your chart had) much better.
        start_avg = data[col].head(30).mean()
        end_avg = data[col].tail(30).mean()
        
        # Avoid division by zero
        if start_avg == 0: start_avg = 1 
        
        growth_pct = ((end_avg - start_avg) / start_avg) * 100
        
        # Save Metadata for the Report Generator
        stats = pd.DataFrame({
            'metric': ['growth_pct', 'start_avg', 'end_avg', 'source'],
            'value': [growth_pct, start_avg, end_avg, source_name]
        })
        os.makedirs("data_output", exist_ok=True)
        stats.to_csv("data_output/market_stats.csv", index=False)

        # Plot
        plt.figure(figsize=(10, 6))
        plt.plot(data.index, data[col], label=f"{source_name} (Growth: {growth_pct:.1f}%)", color='#2ca02c') # Green line
        
        # Add Trendline
        z =  pd.Series(range(len(data)))
        p =  pd.Series(data[col].values)
        m, b =  (p.cov(z) / z.var()), p.mean() - (p.cov(z) / z.var()) * z.mean() # Simple Linear Regression
        plt.plot(data.index, m*z + b, color='red', linestyle='--', alpha=0.5, label="Trendline")

        plt.title(f"Market Demand: 12-Month Trend ({source_name})")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.savefig(f"data_output/market_demand_chart.png")
        data.to_csv(f"data_output/market_trends.csv")
        plt.close()
        
        print(f"✅ Success: Growth calculated at {growth_pct:.1f}%")
        return "data_output/market_trends.csv", "data_output/market_demand_chart.png"
        
    return None, None
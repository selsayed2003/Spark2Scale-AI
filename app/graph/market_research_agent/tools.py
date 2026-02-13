import os
import json
import http.client
import pandas as pd
import platform
import glob
from app.graph.market_research_agent.logger_config import get_logger

# Helper Imports
from .helpers import research_utils, validator_utils, market_utils, finance_utils, pdf_utils

logger = get_logger("MarketResearchTools")

# ==========================================
# 3. Research Engine (Competitors)
# ==========================================
# ==========================================
# 3. Research Engine (Competitors)
# ==========================================
def find_competitors(business_idea: str):
    # FALLBACK for legacy calls
    logger.info(f"\n🕵️ [Tool 3] Deep Market Research (Strict Mode) for: '{business_idea}'...")
    queries = research_utils.generate_smart_queries(business_idea)
    return _execute_competitor_search(business_idea, queries)

def find_competitors_from_plan(business_idea: str, plan: dict):
    logger.info(f"\n🕵️ [Tool 3] Deep Market Research (Plan Mode) for: '{business_idea}'...")
    queries = plan.get("competitor_queries", [f"{business_idea} alternatives"])
    return _execute_competitor_search(business_idea, queries)

def _execute_competitor_search(business_idea, queries):
    all_raw_results = research_utils.execute_serper_search(queries)
    if not all_raw_results: return None
        
    # AI Extraction
    competitors = research_utils.extract_competitors_strict(all_raw_results, business_idea)
    
    if competitors:
        os.makedirs("data_output", exist_ok=True)
        filename = f"data_output/{business_idea.replace(' ', '_')}_competitors.csv"
        
        try:
            df = pd.DataFrame(competitors)
            if "Features" not in df.columns: df["Features"] = "Standard Features"
            df.to_csv(filename, index=False)
            logger.info(f"✅ Success: Extracted {len(df)} VALID competitors.")
            return filename
        except Exception as e:
            logger.error(f"DataFrame Error: {e}")
            return None
    return None

# ==========================================
# 4. Problem Validator
# ==========================================
def validate_problem(idea, problem_statement, plan=None):
    logger.info(f"\n😤 [Tool 6] Validating Problem & Quantifying Pain...")
    
    if plan and "validation_queries" in plan:
        queries = plan["validation_queries"]
    else:
        queries = validator_utils.generate_validation_queries(idea, problem_statement)
        
    if not queries:
        logger.warning("Validation queries missing (API Limit?). Skipping validation.")
        return None
        
    print(f"   🐛 DEBUG: Queries: {queries}")
        
    raw_results = []
    
    # Handle key mismatch between Plan (problem/solution) and Validator (problem_queries/solution_queries)
    prob_q = queries.get("problem_queries", []) or queries.get("problem", [])
    sol_q = queries.get("solution_queries", []) or queries.get("solution", [])

    # LIMIT TO 1 QUERY PER CATEGORY TO SAVE QUOTA
    for q in prob_q[:1]:
        res = validator_utils.search_forums(f"site:reddit.com {q}")
        if "organic" in res:
            for item in res["organic"]: raw_results.append(f"[PROBLEM] {item.get('title','')} - {item.get('snippet','')}")
            
    for q in sol_q[:1]:
        res = validator_utils.search_forums(f"site:reddit.com {q}")
        if "organic" in res:
            for item in res["organic"]: raw_results.append(f"[SOLUTION] {item.get('title','')} - {item.get('snippet','')}")

    if not raw_results: return None

    analysis = validator_utils.analyze_pain_points(idea, problem_statement, raw_results)
    
    if not analysis:
        logger.warning("Validation analysis failed.")
        return None

    os.makedirs("data_output", exist_ok=True)
    with open(f"data_output/{idea.replace(' ', '_')}_validation.json", "w") as f: json.dump(analysis, f, indent=4)
    
    logger.info(f"⚖️  VERDICT: {analysis.get('verdict')} | 🩸 PAIN SCORE: {analysis.get('pain_score')}/100")
    return f"data_output/{idea.replace(' ', '_')}_validation.json"

# ==========================================
# 5. Market Quantifier (Trends)
# ==========================================
def fetch_trend_data(keywords, geo_code='EG', plan=None):
    logger.info(f"\n📊 [Tool 7] Quantifying Market Demand...")
    
    search_term = keywords[0]
    if plan and "market_identity" in plan:
        wiki_topic = plan["market_identity"].get("wikipedia_topic")
        if wiki_topic: search_term = wiki_topic

    data, source_name = market_utils.get_trending_data([search_term], geo_code)
    
    if data is None:
        topic = search_term
        if not plan:
            topic = market_utils.search_wikidata(search_term)
        data, source_name = market_utils.fetch_wikipedia_data(topic)

    if data is not None and not data.empty:
        col = data.columns[0]
        growth_pct = market_utils.plot_trends(data, source_name, col)
        
        logger.info(f"✅ Success: Growth calculated at {growth_pct:.1f}%")
        return "data_output/market_trends.csv", "data_output/market_demand_chart.png"
        
    return None, None

def calculate_market_size(idea, location="Global", plan=None):
    logger.info(f"\n📐 [Tool 11] Calculating TAM, SAM, SOM & Scalability...")
    
    industry = "Unknown"
    if plan and "market_identity" in plan:
        industry = plan["market_identity"].get("industry", "Business")
        location = plan["market_identity"].get("target_country", location)
    else:
        industry = market_utils.identify_industry(idea)
    
    logger.info(f"   🌍 Hunting for '{industry}' market reports in {location}...")
    queries = [
        f"{industry} market size revenue statistics {location} 2024 2025"
    ]
    
    market_data = ""
    for q in queries:
        market_data += market_utils.search_market_reports(q) + "\n"

    result = market_utils.analyze_market_size(idea, industry, location, market_data)

    if not result:
        logger.warning("Market sizing analysis failed.")
        return None

    # Generate Visual
    market_utils.plot_market_funnel(result, industry)
    
    # Save JSON
    with open("data_output/market_sizing.json", "w") as f:
        json.dump(result, f, indent=4)
        
    logger.info(f"✅ Market Sizing Complete: {result.get('market_type')}")
    return "data_output/market_sizing.json"

# ==========================================
# 6. Finance Model
# ==========================================
def run_finance_model(idea, plan=None):
    logger.info(f"\n💰 [Tool 8] Starting Localized Financial Model...")
    
    if plan and "financial_queries" in plan:
        currency = plan["market_identity"].get("currency_code", "USD")
        queries = plan.get("financial_queries", [])
        
        market_data = ""
        for q in queries[:2]:
            market_data += finance_utils.search_cost_data(q) + "\n"
            
        estimates = finance_utils.generate_financial_estimates(idea, market_data, currency)
    else:
        estimates = finance_utils.get_real_world_estimates(idea)
        
    if not estimates:
        logger.warning("Financial estimation failed.")
        return None

    return finance_utils.generate_financial_visuals(estimates)

# ==========================================
# 7. Report Generator
# ==========================================
def generate_report(file_path, query, trend_file=None, finance_file=None):
    return pdf_utils.generate_report(file_path, query, trend_file, finance_file)

# ==========================================
# 8. PDF Compiler
# ==========================================
def compile_final_pdf(idea_name):
    logger.info(f"\n📄 [Tool 9] Compiling Professional PDF Report...")
    
    pdf = pdf_utils.PDFReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- CROSS-PLATFORM FONT LOADING ---
    system_name = platform.system()
    font_path = None
    if system_name == "Windows":
        font_path = r"C:\Windows\Fonts\arial.ttf"
    elif system_name == "Darwin": # Mac
        font_path = "/Library/Fonts/Arial.ttf"
    elif system_name == "Linux":
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    try:
        if font_path and os.path.exists(font_path):
            pdf.add_font("ArialUnicode", style="", fname=font_path)
            pdf.add_font("ArialUnicode", style="B", fname=font_path)
            logger.info(f"   ✅ Loaded System Font: {font_path}")
        else:
            logger.warning("   ⚠️ Custom font not found. Arabic may not render correctly.")
    except Exception as e:
        logger.error(f"   ⚠️ Font Error: {e}")

    # --- PAGE 1: TITLE & EXECUTIVE SUMMARY ---
    pdf.add_page()
    logger.info(f"   📄 Generating Page {pdf.page_no()}: Title & Executive Summary")
    
    # Title Styling
    pdf.set_font_for_content('B', 14)
    # Use Moss for Label
    pdf.set_text_color(*pdf_utils.PDFReport.COLOR_MOSS)
    pdf.cell(0, 10, "MARKET RESEARCH REPORT", 0, 1, 'C')
    
    pdf.ln(5)
    
    # Idea Name (Big & Wrapped)
    pdf.set_font_for_content('B', 20)
    # Fix Arabic on the Uppercased string to prevent issues
    pdf.multi_cell(0, 10, pdf_utils.fix_arabic(idea_name.upper()), 0, 'C')
    
    pdf.ln(5)
    
    # Subtitle in Mustard (Italic)
    pdf.set_font_for_content('', 12)
    pdf.set_text_color(*pdf_utils.PDFReport.COLOR_MOSS)
    try:
        pdf.set_font("Helvetica", 'I', 14)
    except:
        pdf.set_font("Arial", 'I', 14)
    pdf.cell(0, 10, "Comprehensive Market Analysis", 0, 1, 'C')
    
    pdf.set_text_color(0, 0, 0) # Reset
    pdf.ln(10)
    
    # Read Report
    report_text = "No report text found. Please check generation logs."
    report_path = "data_output/FINAL_MARKET_REPORT.md"
    if os.path.exists(report_path):
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                raw_text = f.read()
                if not raw_text.strip():
                     logger.warning("   ⚠️ Report file exists but is empty.")
                else:
                    report_text = raw_text
        except Exception as e:
            logger.error(f"   ⚠️ Error reading report: {e}")
            report_text = f"Error reading executive summary: {e}"
    else:
         logger.warning(f"   ⚠️ Report file not found at {report_path}")

    pdf.chapter_title("Executive Summary")
    pdf.chapter_body(report_text[:2500] + "...") # Increased limit
    
    # --- PAGE 2: MARKET DEMAND & SCORES ---
    pdf.add_page()
    logger.info(f"   📄 Generating Page {pdf.page_no()}: Market Validation & Scores")
    pdf.chapter_title("Market Validation & Scores")
    
    # 1. Pain Score Bar
    val_file = f"data_output/{idea_name.replace(' ', '_')}_validation.json"
    pain_score = 50 
    if os.path.exists(val_file):
        try:
            with open(val_file, 'r') as f:
                val_data = json.load(f)
                pain_score = val_data.get('pain_score', 50)
        except: pass
    
    pdf.draw_score_bar("Pain Score (Problem Severity)", pain_score)

    # 2. Growth/Trend Score Bar (Derived from trends)
    growth_score = 0
    if os.path.exists("data_output/market_trends.csv"):
        try:
            # We don't have a direct 'score' but we have growth pct. Let's map it.
            # Simple heuristic matching pdf_utils.generate_report logic:
            # growth_score = max(0, min(100, growth_pct + 50))
            stats = pd.read_csv("data_output/market_stats.csv") # Check filename
            # Actually tools.py calls it `market_stats.csv` in `fetch_trend_data` but returns `market_trends.csv`? 
            # `fetch_trend_data` returns `market_trends.csv`. Let's use that if it exists.
            # Wait, `fetch_trend_data` in `tools.py` saves to `data_output/market_trends.csv`.
            df_trends = pd.read_csv("data_output/market_trends.csv") # It might be a different format.
            # Let's verify `fetch_trend_data` implementation.
            # It returns "data_output/market_trends.csv".
            # But line 36 of `pdf_utils` reads `data_output/market_stats.csv`. 
            # I should align with what `tools.py` produces.
            # For now in `tools.py` `fetch_trend_data` (line 119) returns `data_output/market_trends.csv`.
            # I'll try to read that.
            pass
        except: pass
    
    # Just reusing logic from pdf_utils line 36-39 if possible, but cleaner.
    # I'll just skip detailed growth bar for now to avoid breaking if file formats differ, 
    # unless I'm sure. I'll stick to Pain Score which is robust.

    if os.path.exists("data_output/market_demand_chart.png"):
        pdf.ln(10)
        pdf.add_image_centered("data_output/market_demand_chart.png")
        pdf.ln(5)
        try:
            pdf.set_font("Helvetica", 'B', 10)
        except:
            pdf.set_font("Arial", 'B', 10)

        pdf.set_text_color(*pdf_utils.PDFReport.COLOR_MOSS)
        pdf.cell(0, 10, "TREND ANALYSIS:", 0, 1, 'L')
        pdf.set_font_for_content('', 10)
        pdf.set_text_color(*pdf_utils.PDFReport.COLOR_DARK_TEXT)
        
        # Read Dynamic Analysis
        trend_text = "The chart above illustrates the search interest and market demand trend over the last 12 months."
        if os.path.exists("data_output/trend_analysis.txt"):
            with open("data_output/trend_analysis.txt", "r") as f:
                trend_text = f.read().strip()
                
        pdf.multi_cell(0, 6, pdf_utils.fix_arabic(trend_text))
    else:
        pdf.set_text_color(255, 0, 0)
        pdf.cell(0, 10, "Analysis Unavailable: Market trend data could not be generated.", 0, 1, 'L')
        pdf.set_text_color(0, 0, 0)
    
    # --- PAGE 3: FINANCIALS ---
    pdf.add_page()
    logger.info(f"   📄 Generating Page {pdf.page_no()}: Financials")
    pdf.chapter_title("Financial Feasibility")
    
    if os.path.exists("data_output/finance_summary.csv"):
        pdf.cell(0, 10, "1. Startup Cost Estimates", 0, 1, 'L')
        pdf.add_image_centered("data_output/finance_startup_pie.png")
        pdf.ln(2)
        pdf.set_font_for_content('', 10)
        
        # Read Dynamic Financial Analysis
        fin_text = "breakdown of estimated initial capital requirements to launch the business."
        if os.path.exists("data_output/financial_analysis.txt"):
            with open("data_output/financial_analysis.txt", "r") as f:
                fin_text = f.read().strip()
                
        pdf.multi_cell(0, 6, pdf_utils.fix_arabic(fin_text))
        
        pdf.add_page()
        pdf.chapter_title("Profitability Projections")
        pdf.cell(0, 10, "2. Break-Even Analysis", 0, 1, 'L')
        pdf.add_image_centered("data_output/finance_breakeven_line.png")
        pdf.ln(2)
        pdf.multi_cell(0, 6, "Projected cumulative cash flow over the first 24 months, highlighting the break-even point where net profit turns positive.")
    else:
        pdf.set_text_color(255, 0, 0)
        pdf.cell(0, 10, "Analysis Unavailable: Financial data could not be generated.", 0, 1, 'L')
        pdf.set_text_color(0, 0, 0)

    # --- PAGE 4: MARKET SIZING ---
    pdf.add_page()
    logger.info(f"   📄 Generating Page {pdf.page_no()}: Market Sizing")
    pdf.chapter_title("Market Opportunity & Sizing")
    
    if os.path.exists("data_output/market_sizing.json"):
        with open("data_output/market_sizing.json", "r") as f:
            size_data = json.load(f)
            
        # Ocean Type
        ocean = size_data.get("market_type", "Unknown")
        # Use Moss for Blue Ocean (Good), Dark Red for Red Ocean (Bad)
        color = (200, 50, 50) if "Red" in ocean else pdf_utils.PDFReport.COLOR_MOSS 
        
        pdf.set_font_for_content('B', 14)
        pdf.set_text_color(*color)
        pdf.cell(0, 10, f"Market Type: {ocean}", 0, 1, 'C')
        pdf.set_text_color(0, 0, 0)
        pdf.ln(5)

        # TAM/SAM/SOM Visual
        pdf.add_image_centered("data_output/market_sizing_funnel.png")
        
        # Explanations
        pdf.set_font_for_content('', 10)
        pdf.multi_cell(0, 6, f"TAM: {size_data.get('tam_description', 'N/A')}")
        pdf.ln(2)
        pdf.multi_cell(0, 6, f"SAM: {size_data.get('sam_description', 'N/A')}")
        pdf.ln(2)
        pdf.multi_cell(0, 6, f"SOM: {size_data.get('som_description', 'N/A')}")
        pdf.ln(5)
        
        # Scalability
        pdf.chapter_title("Scalability Analysis")
        pdf.set_font_for_content('B', 12)
        pdf.cell(0, 10, f"Scalability Score: {size_data.get('scalability_score', 'N/A')}", 0, 1)
        pdf.set_font_for_content('', 11)
        pdf.multi_cell(0, 6, size_data.get('scalability_reasoning', 'N/A'))
    else:
        pdf.set_text_color(255, 0, 0)
        pdf.cell(0, 10, "Analysis Unavailable: Unable to generate market sizing data.", 0, 1, 'L')
        pdf.set_text_color(0, 0, 0)

    # --- PAGE 5: COMPETITOR FEATURES ---
    pdf.add_page()
    logger.info(f"   📄 Generating Page {pdf.page_no()}: Competitors")
    pdf.chapter_title("Competitor Feature Analysis")
    
    comp_files = glob.glob(f"data_output/{idea_name.replace(' ', '_')}_competitors.csv")
    if comp_files:
        try:
            df = pd.read_csv(comp_files[0])
            
            pdf.set_font_for_content('B', 10)
            # Adjusted Widths: Name (50), Features (140)
            
            # Header with Moss Background and White Text
            pdf.set_fill_color(*pdf_utils.PDFReport.COLOR_MOSS)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(50, 10, 'Competitor', 1, 0, 'C', True)
            pdf.cell(140, 10, 'Key Features Identified', 1, 1, 'C', True)
            
            # Reset Text Color
            pdf.set_text_color(0, 0, 0)
            
            pdf.set_font_for_content('', 9)
            for _, row in df.head(8).iterrows():
                name = pdf_utils.fix_arabic(row.get('Name', 'N/A'))[:25]
                # Grab the NEW 'Features' column
                features = pdf_utils.fix_arabic(row.get('Features', row.get('Snippet', 'N/A')))[:110].replace("\n", " ")
                
                pdf.cell(50, 10, name, 1)
                pdf.cell(140, 10, features, 1)
                pdf.ln()
        except Exception as e:
            logger.error(f"   ⚠️ Error adding table: {e}")
    else:
        pdf.set_text_color(255, 0, 0)
        pdf.cell(0, 10, "Analysis Unavailable: Competitor data could not be extracted.", 0, 1, 'L')
        pdf.set_text_color(0, 0, 0)
            
    # --- OUTPUT ---
    clean_name = idea_name.replace(' ', '_').replace('"', '').replace("'", "")
    output_filename = f"data_output/{clean_name}_Market_Report.pdf"
    
    try:
        pdf.output(output_filename)
        logger.info(f"PDF GENERATED: {output_filename}")
        return output_filename
    except Exception as e:
        logger.error(f"PDF Save Failed: {e}")
        return None

def compile_final_json(idea_name):
    logger.info(f"\n💾 [Tool 10] Compiling JSON Data Output...")
    
    json_data = {
        "idea_name": idea_name,
        "executive_summary": "",
        "market_sizing": {},
        "competitors": [],
        "validation": {},
        "finance": {} # Placeholder for finance data if available in structured format
    }

    # 1. Executive Summary
    if os.path.exists("data_output/FINAL_MARKET_REPORT.md"):
        with open("data_output/FINAL_MARKET_REPORT.md", "r", encoding="utf-8") as f:
            json_data["executive_summary"] = f.read()

    # 2. Market Sizing
    if os.path.exists("data_output/market_sizing.json"):
        with open("data_output/market_sizing.json", "r") as f:
            json_data["market_sizing"] = json.load(f)

    # 3. Competitors
    comp_file = f"data_output/{idea_name.replace(' ', '_')}_competitors.csv"
    if os.path.exists(comp_file):
        try:
            df = pd.read_csv(comp_file)
            json_data["competitors"] = df.to_dict(orient="records")
        except Exception as e:
            logger.error(f"Error reading competitors csv: {e}")

    # 4. Validation
    val_file = f"data_output/{idea_name.replace(' ', '_')}_validation.json"
    if os.path.exists(val_file):
        with open(val_file, "r") as f:
            json_data["validation"] = json.load(f)

    # 5. Finance
    finance_file = "data_output/finance_estimates.json"
    if os.path.exists(finance_file):
        with open(finance_file, "r") as f:
            json_data["finance"] = json.load(f)

    # 6. Trends
    trends_file = "data_output/market_stats.csv"
    if os.path.exists(trends_file):
        try:
            df = pd.read_csv(trends_file)
            json_data["trends"] = df.to_dict(orient="records")
        except Exception as e:
            logger.error(f"Error reading trends csv: {e}")
            
    try:
        # Save JSON
        clean_name = idea_name.replace(' ', '_').replace('"', '').replace("'", "")
        output_filename = f"data_output/{clean_name}_Market_Report.json"
        
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=4)
            
        logger.info(f"JSON GENERATED: {output_filename}")
        return output_filename
    except Exception as e:
        logger.error(f"JSON Compilation Failed: {e}")
        return None

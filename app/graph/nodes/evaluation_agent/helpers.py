import json
import os
import base64
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_community.tools import DuckDuckGoSearchRun
from datetime import datetime


def load_schema(filename="schema.json"):
    """
    Loads a JSON schema file from the same directory as this script.
    Returns the dict or None if file is missing/invalid.
    """
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        
        file_path = os.path.join(base_dir, filename)
        
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
            
    except FileNotFoundError:
        print(f"Warning: Could not find '{filename}' at {file_path}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error: '{filename}' contains invalid JSON. \nDetails: {e}")
        return None
    
def extract_team_data(data):
    """
    Extracts fields for the Founder Market Fit Agent:
    - Founder Profiles (Experience, Role, Ownership)
    - Execution History (Shipments, Start Date)
    - Problem Context (To cross-reference skills vs. the actual problem)
    """
    root = data.get("startup_evaluation", {})
    team_section = root.get("founder_and_team", {})
    problem_section = root.get("problem_definition", {})

    return {
        # --- 1. THE FOUNDERS (Who are they?) ---
        "founders": [
            {
                "name": f.get("name"),
                "role": f.get("role"),
                "equity": f.get("ownership_percentage"),
                "prior_experience": f.get("prior_experience"),
                "years_experience": f.get("years_direct_experience"),
                "fit_statement": f.get("founder_market_fit_statement")
            }
            for f in team_section.get("founders", [])
        ],

        # --- 2. EXECUTION (Can they build?) ---
        "execution_history": {
            "start_date": team_section.get("execution", {}).get("full_time_start_date"),
            "shipments": team_section.get("execution", {}).get("key_shipments", [])
        },

        # --- 3. PROBLEM CONTEXT (Do their skills match this problem?) ---
        # The agent needs to know the problem to judge if the founder is an "Insider"
        "problem_context": {
            "statement": problem_section.get("problem_statement"),
            "current_solution": problem_section.get("current_solution"),
            "gap": problem_section.get("gap_analysis")
        }
    }
def extract_problem_data(data):
    """
    Extracts only the fields necessary for the Problem Evaluation Agent:
    - Clarity & Urgency (Problem Statement, Impact, Frequency)
    - Market Maturity (Current Solutions, Gap, Evidence)
    - Audience Scope (Customer Profile, Beachhead)
    - Founder Alignment (Why them?)
    """
    # Navigate to the main sections safely
    root = data.get("startup_evaluation", {})
    problem_def = root.get("problem_definition", {})
    market_scope = root.get("market_and_scope", {})
    founder_section = root.get("founder_and_team", {})

    return {
        # --- 1. CORE PROBLEM (Clarity & Urgency) ---
        "problem_core": {
            "statement": problem_def.get("problem_statement"),
            "impact": problem_def.get("impact_metrics"), # Includes cost_type & description
            "frequency": problem_def.get("frequency")
        },

        # --- 2. MARKET MATURITY (Why Now?) ---
        "market_maturity": {
            "current_solutions": problem_def.get("current_solution"),
            "gap_analysis": problem_def.get("gap_analysis"),
            "customer_evidence": problem_def.get("evidence", {}).get("customer_quotes", [])
        },

        # --- 3. AUDIENCE (Targeted vs. Broad) ---
        "audience": {
            "profile": problem_def.get("customer_profile"), # Role, Industry, etc.
            "beachhead": market_scope.get("beachhead_market")
        },

        # --- 4. FOUNDER ALIGNMENT (The "Insider" Signal) ---
        # We extract just the fit statement list to save context window
        "founder_alignment_statements": [
            f.get("founder_market_fit_statement", "Not specified") 
            for f in founder_section.get("founders", [])
        ]
    }
def extract_product_data(data):
    return {
        # --- 1. COMPANY SNAPSHOT (ALL FIELDS) ---
        # "Context: Stage, Speed (Founded Date), and Resources (Amount Raised)"
        "snapshot": {
            "company_name": data.get("company_snapshot", {}).get("company_name"),
            "website": data.get("company_snapshot", {}).get("website"),
            "hq_location": data.get("company_snapshot", {}).get("hq_location"),
            "date_founded": data.get("company_snapshot", {}).get("date_founded"),
            "current_stage": data.get("company_snapshot", {}).get("current_stage"),
            "amount_raised": data.get("company_snapshot", {}).get("amount_raised"),
            "current_round": data.get("company_snapshot", {}).get("current_round")
        },

        # --- 2. PRODUCT & SOLUTION (ALL FIELDS) ---
        # "The Core: Status, Visuals, Moat, Stickiness"
        "product": {
            "status": data.get("product_and_solution", {}).get("product_status"),
            "visuals": data.get("product_and_solution", {}).get("visuals"),
            "stickiness": data.get("product_and_solution", {}).get("stickiness"),
            "differentiation": data.get("product_and_solution", {}).get("differentiation"),
            "moat": data.get("product_and_solution", {}).get("moat")
        },

        # --- 3. CRITICAL DEPENDENCIES (Keep these for Scoring Logic) ---
        
        # From Problem (Needed for "10x Better" check)
        "baseline_solution": data.get("problem_definition", {}).get("current_state"),
        "problem_gap": data.get("problem_definition", {}).get("gap"),

        # From Team (Needed for "How quickly can it be built?" check)
        "shipping_history": data.get("founder_and_team", {}).get("team_execution"),

        # From Market & Strategy (Needed for "Roadmap" & "Red/Blue Ocean" check)
        "expansion_roadmap": data.get("market_and_scope", {}).get("expansion"),
        "category_strategy": data.get("vision_and_strategy", {}).get("categorization"),
        "future_vision": data.get("vision_and_strategy", {}).get("future_view")
    }


def extract_market_data(data):
    """
    Transforms raw startup JSON into the simplified structure needed for Market Analysis.
    """
  
    
    # Safely get sections
    snapshot = data.get("company_snapshot", {})
    market = data.get("market_and_scope", {})
    problem = data.get("problem_definition", {})
    business = data.get("business_model", {})
    vision = data.get("vision_and_strategy", {})
    gtm = data.get("gtm_strategy", {})

    return {
        "entry_point": {
            "beachhead_definition": market.get("beachhead_market", "Unknown Market"),
            "target_customer": problem.get("customer_profile", {}),
            "som_size_claim": market.get("market_size_estimate", "Not specified"),
            "location": snapshot.get("hq_location", "Global")
        },
        "scalability": {
            "expansion_plan": market.get("expansion_strategy"),
            "long_term_vision": market.get("long_term_vision"),
            "future_category": vision.get("category_definition")
        },
        "economics": {
            "price": business.get("average_price_per_customer"),
            "pricing_model": business.get("pricing_model"),
            "frequency": problem.get("frequency")
        },
        "risks": {
            "current_competitors": problem.get("current_solution"),
            "stated_risk": vision.get("primary_risk"),
            "acquisition_channel": gtm.get("primary_acquisition_channel")
        }
    }


from datetime import datetime

def extract_traction_data(data):
    """
    Extracts traction metrics tailored strictly to the company's stage (Pre-Seed vs. Seed).
    Includes flattened fields to prevent LLM 'Missing Data' hallucinations.
    """
    root = data.get("startup_evaluation", {})
    snapshot = root.get("company_snapshot", {})
    problem = root.get("problem_definition", {})
    evidence = problem.get("evidence", {})
    
    # 1. Determine Stage
    stage_raw = snapshot.get("current_stage", "Pre-Seed").lower()
    
    # 2. Base Context (Needed for both)
    base_context = {
        "stage": snapshot.get("current_stage"),
        "founded_date": snapshot.get("date_founded"),
        "current_date": datetime.now().strftime("%Y-%m-%d"), # <--- Added for "Time vs Progress" math
        "execution_velocity": root.get("founder_and_team", {}).get("execution", {}).get("key_shipments", [])
    }
    
    # 3. Source Sections
    traction = root.get("traction_metrics", {})
    gtm = root.get("gtm_strategy", {})
    biz = root.get("business_model", {})

    # Helper: Determine B2B vs B2C Focus (Critical for "Ghost Pilot" check)
    industry = problem.get("customer_profile", {}).get("industry", "").lower()
    role = problem.get("customer_profile", {}).get("role", "").lower()
    is_b2b = "business" in industry or "b2b" in industry or "enterprise" in role
    focus_type = "B2B" if is_b2b else "B2C"

    # ==========================================
    # PATH A: PRE-SEED TRACTION (Validation Focus)
    # ==========================================
    if "pre" in stage_raw:
        return {
            "analysis_type": "Pre-Seed Validation",
            "context": base_context,
            "validation_signals": {
                # --- CORE METRICS ---
                "users_total": traction.get("user_count", 0),
                "users_active": traction.get("active_users_monthly", 0),
                "partnerships_lois": traction.get("partnerships_and_lois", []), 
                "early_revenue": traction.get("early_revenue", "0"),
                
                # --- FLATTENED LOGIC FIELDS (Added these) ---
                "interviews_conducted": evidence.get("interviews_conducted", 0), # <--- Was missing
                "waitlist_status": "Implied from user count" if traction.get("user_count", 0) > 0 else "None",
                "focus": focus_type, # <--- Needed for "Ghost Pilot" check
                "sales_cycle": gtm.get("average_sales_cycle", "Unknown") # <--- Needed for logic check
            },
            "defensibility": root.get("product_and_solution", {}).get("defensibility_moat", "None")
        }

    # ==========================================
    # PATH B: SEED TRACTION (Growth Focus)
    # ==========================================
    else:
        return {
            "analysis_type": "Seed Growth",
            "context": base_context,
            "growth_metrics": {
                "mrr": traction.get("early_revenue"), 
                "growth_rate_mom": traction.get("revenue_growth_rate", "Not specified"),
                "retention_metrics": traction.get("retention_metrics", "Not specified"),
                "paid_users": traction.get("paying_customer_count", 0),
                "unit_economics": {
                    "acv": biz.get("average_price_per_customer"),
                    "cac_hint": "Infer from marketing spend if available"
                }
            },
            "sales_machine": {
                "closer": gtm.get("deal_closer"),
                "channel": gtm.get("primary_acquisition_channel"),
                "sales_cycle": gtm.get("average_sales_cycle"),
                "sales_motion": gtm.get("sales_motion"), # <--- Added for Unit Econ check
                "conversion_friction": "Low" if gtm.get("sales_motion") == "Self-serve" else "High"
            }
        }
def extract_gtm_pre_seed(data):
    """
    Extracts GTM data for Pre-Seed.
    NOW UPDATED: Includes 'unit_economics' block so the Calculator works.
    """
    gtm = data.get("gtm_strategy", {})
    problem = data.get("problem_definition", {})
    biz = data.get("business_model", {})       # <--- Added extraction
    traction = data.get("traction_metrics", {}) # <--- Added extraction
    
    return {
        "analysis_type": "Pre-Seed GTM (Validation)",
        "context": {
            "company_name": data.get("company_snapshot", {}).get("company_name"),
            "founded_date": data.get("company_snapshot", {}).get("date_founded"), # Needed for 'months_alive'
            "stage": "Pre-Seed"
        },
        # THE HYPOTHESIS
        "target_audience": {
            "icp_description": problem.get("customer_profile", {}), 
            "buyer_persona": gtm.get("buyer_persona"),
            "user_persona": gtm.get("user_persona")
        },
        # THE HUSTLE
        "early_distribution": {
            "primary_channel": gtm.get("primary_acquisition_channel"),
            "sales_motion": gtm.get("sales_motion"),
            "early_revenue": traction.get("early_revenue", "0")
        },
        # ECONOMICS (For consistency)
        "pricing_hypothesis": {
            "price_point": biz.get("average_price_per_customer"),
            "model": biz.get("pricing_model")
        },
        # --- NEW BLOCK: REQUIRED FOR CALCULATOR ---
        "unit_economics": {
            "burn_rate": biz.get("monthly_burn", 0),
            "total_users": traction.get("user_count", 0),
            "paid_users": 0, # Usually 0 at Pre-Seed
            "revenue": traction.get("early_revenue", 0),
            "price_point": biz.get("average_price_per_customer", 0)
        }
    }

def extract_gtm_seed(data):
    """
    Extracts GTM data for Seed. 
    INCLUDES: Strategy (Who/How) AND Metrics (CAC/LTV).
    """
    gtm = data.get("gtm_strategy", {})
    biz = data.get("business_model", {})
    traction = data.get("traction_metrics", {})
    problem = data.get("problem_definition", {}) # Added back!
    
    return {
        "analysis_type": "Seed GTM (Scalability & Economics)",
        "context": {
            "company_name": data.get("company_snapshot", {}).get("company_name"),
            "stage": "Seed"
        },
        
        # --- PART 1: STRATEGY (The Foundation - Same as Pre-Seed) ---
        "strategy": {
            "icp_description": problem.get("customer_profile", {}),
            "personas": {
                "buyer": gtm.get("buyer_persona"),
                "user": gtm.get("user_persona")
            },
             "pricing_model": biz.get("pricing_model") # Needed to check fit
        },

        # --- PART 2: THE ENGINE (The Motion) ---
        "sales_machine": {
            "primary_channel": gtm.get("primary_acquisition_channel"),
            "closer": gtm.get("deal_closer"), # Critical: Is founder still doing it?
            "sales_cycle": gtm.get("average_sales_cycle"),
            "sales_motion": gtm.get("sales_motion")
        },

        # --- PART 3: THE MATH (The Metrics - New for Seed) ---
        "unit_economics": {
            "burn_rate": biz.get("monthly_burn"),
            "total_users": traction.get("user_count"),
            "paid_users": traction.get("paying_customer_count"),
            "revenue": traction.get("early_revenue"),
            "price_point": biz.get("average_price_per_customer"),
            "growth_rate": traction.get("revenue_growth_rate"),
            "retention": traction.get("retention_metrics")
        }
    }

def extract_business_pre_seed(data):
    """
    Extracts Business Model data for Pre-Seed.
    Focus: Pricing Hypothesis, Margins, and Cash Runway.
    Includes Sector Context for AI Judgment.
    """
    biz = data.get("business_model", {})
    traction = data.get("traction_metrics", {})
    funds = data.get("fundraising_and_use_of_funds", {})
    
    # --- NEW: Extract Sector Context ---
    problem = data.get("problem_definition", {})
    customer_profile = problem.get("customer_profile", {})
    industry = customer_profile.get("industry", "Unknown Sector")
    role = customer_profile.get("role", "Unknown Buyer")
    sector_info = f"{industry} (Targeting: {role})"

    return {
        "analysis_type": "Pre-Seed Economics (Hypothesis)",
        "sector_context": sector_info, # <--- ADDED THIS for the LLM Judge
        "context": {
            "stage": "Pre-Seed",
            "company_name": data.get("company_snapshot", {}).get("company_name")
        },
        
        # 1. THE LOGIC (How we make money)
        "monetization_structure": {
            "pricing_model": biz.get("pricing_model"),         # SaaS vs Transaction
            "price_point": biz.get("average_price_per_customer"), # The $50
            "gross_margin": biz.get("gross_margin")    # The % profit (33 vs 50)
        },

        # 2. THE VALIDATION (Early Signals)
        "early_signals": {
            "revenue": traction.get("early_revenue", "0"),
            "pilots": traction.get("partnerships_and_lois", [])
        },

        # 3. THE SURVIVAL (Cash Flow)
        "cash_health": {
            "burn_rate": biz.get("monthly_burn"),
            "runway_months": biz.get("runway_months"),
            "capital_ask": funds.get("current_round_target"),
            "spend_plan": funds.get("use_of_funds_over_next_18_months")
        }
    }

def extract_business_seed(data):
    """
    Extracts Business Model data for Seed.
    Key Feature: Auto-calculates MRR if missing.
    Includes Sector Context for AI Judgment.
    """
    biz = data.get("business_model", {})
    traction = data.get("traction_metrics", {})
    funds = data.get("fundraising_and_use_of_funds", {})
    gtm = data.get("gtm_strategy", {}) 
    
    # --- NEW: Extract Sector Context ---
    problem = data.get("problem_definition", {})
    customer_profile = problem.get("customer_profile", {})
    industry = customer_profile.get("industry", "Unknown Sector")
    role = customer_profile.get("role", "Unknown Buyer")
    sector_info = f"{industry} (Targeting: {role})"
    
    # 1. SMART MRR CALCULATION
    # Try to get raw MRR first
    raw_mrr = traction.get("monthly_recurring_revenue")
    
    # If raw MRR is missing/zero, calculate it: (Paying Users * Price)
    if not raw_mrr or raw_mrr == "0":
        try:
            users = float(traction.get("number_of_paying_customers") or 0)
            price = float(biz.get("average_price_per_customer") or 0)
            calculated_mrr = users * price
            mrr_value = calculated_mrr
        except:
            mrr_value = 0
    else:
        mrr_value = raw_mrr

    return {
        "analysis_type": "Seed Economics (Unit Metrics)",
        "sector_context": sector_info, # <--- ADDED THIS for the LLM Judge
        "context": {
            "stage": "Seed",
            "company_name": data.get("company_snapshot", {}).get("company_name")
        },
        
        # --- PART 1: THE FOUNDATION ---
        "monetization_structure": {
            "pricing_model": biz.get("pricing_model"),
            "price_point": biz.get("average_price_per_customer"),
            "gross_margin": biz.get("gross_margin")
        },
        "cash_health": {
            "burn_rate": biz.get("monthly_burn"),
            "runway_months": biz.get("runway_months"),
            "capital_ask": funds.get("current_round_target"),
            "spend_plan": funds.get("use_of_funds_over_next_18_months")
        },

        # --- PART 2: THE ENGINE (With Calculated MRR) ---
        "revenue_momentum": {
            "mrr": mrr_value,                                   # <--- NOW ROBUST
            "is_mrr_calculated": (not raw_mrr or raw_mrr=="0"), # Flag for the AI to know
            "growth_rate": traction.get("revenue_growth_rate", "0%"),
            "paying_customers": traction.get("number_of_paying_customers")
        },

        # --- PART 3: THE LEAKY BUCKET ---
        "retention_health": {
            "churn_metric": traction.get("retention_metrics"), 
            "sales_motion": gtm.get("sales_motion") 
        }
    }


def extract_vision_data(data):
    """
    Extracts the 'Narrative Arc' of the startup.
    Focus: Vision, Category Definition, and Long-Term Ambition.
    """
    
    market = data.get("market_and_scope", {})
    product = data.get("product_and_solution", {})
    strategy = data.get("vision_and_strategy", {})
    problem = data.get("problem_definition", {})

    return {
        "analysis_type": "Vision & Narrative Check",
        "context": {
            "stage": data.get("company_snapshot", {}).get("current_stage", "Pre-Seed"),
            "company_name": data.get("company_snapshot", {}).get("company_name")
        },
        
        # 1. THE AMBITION (Where are we going?)
        "north_star": {
            "5_year_vision": strategy.get("five_year_vision"),
            "long_term_market": market.get("long_term_market_vision"),
            "expansion_plan": market.get("expansion_strategy")
        },

        # 2. THE CATEGORY (What are we?)
        "category_play": {
            "definition": strategy.get("category_definition"),
            "differentiation": product.get("differentiation"),
            "moat": product.get("defensibility_moat")
        },

        # 3. THE GROUNDING (Are we obsessed with the customer?)
        "customer_obsession": {
            "problem_statement": problem.get("problem_statement"),
            "customer_quotes": problem.get("evidence", {}).get("customer_quotes", [])
        },

        # 4. THE SELF-AWARENESS (Do we know what kills us?)
        "risk_awareness": {
            "primary_risk": strategy.get("primary_risk")
        }
    }


def extract_operations_data(data):
    """
    Extracts data for Operational Readiness & Fundability.
    Focus: Cap Table, Burn, Runway, and Use of Funds.
    """
    snapshot = data.get("company_snapshot", {})
    founders = data.get("founder_and_team", {}).get("founders", [])
    economics = data.get("business_model", {})
    fundraising = data.get("fundraising_and_use_of_funds", {}) # You might need to add this section to your form parser if not there

    # Calculate Total Founder Ownership
    total_founder_equity = sum([f.get("ownership_percentage", 0) for f in founders])
    raw_industry = data.get("problem_definition", {}).get("customer_profile", {}).get("industry", "Technology")
    sector = raw_industry.split("/")[0].strip() if "/" in raw_industry else raw_industry
    return {
        "analysis_type": "Operational Readiness Check",
        "context": {
            "stage": snapshot.get("current_stage", "Pre-Seed"),
            "location": snapshot.get("hq_location", "Global"), # Add Location
            "sector": sector,
            "round_target": snapshot.get("current_round", {}).get("target_amount"),
            "target_close": snapshot.get("current_round", {}).get("target_close_date")
        },
        "cap_table": {
            "total_founder_equity": total_founder_equity,
            "founder_count": len(founders),
            "existing_investors": fundraising.get("existing_investors", "None")
        },
        "financial_health": {
            "monthly_burn": economics.get("monthly_burn"),
            "runway_months": economics.get("runway_months"),
            "gross_margin": economics.get("gross_margin")
        },
        "the_plan": {
            "use_of_funds": fundraising.get("use_of_funds", []), # List of priorities
            "milestones": fundraising.get("key_milestones", "")
        }
    }
def capture_screenshot(url: str):
    """
    Visits a URL using Selenium and returns the screenshot as a Base64 string.
    """
    print(f"📸 Visiting {url} for visual check...")
    
    if not url:
        return {"error": "No URL provided."}

    screenshot_path = "screenshot.png"
    
    try:
        chrome_options = Options()
        chrome_options.add_argument("--headless") 
        chrome_options.add_argument("--window-size=1280,720")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        driver.set_page_load_timeout(15)
        
        try:
            driver.get(url)
            time.sleep(3) # Wait for React/Vue
            driver.save_screenshot(screenshot_path)
            driver.quit()
            
            # Convert to Base64 for LangChain
            with open(screenshot_path, "rb") as image_file:
                image_data = base64.b64encode(image_file.read()).decode("utf-8")
            
            # Cleanup
            if os.path.exists(screenshot_path):
                os.remove(screenshot_path)
                
            return {"image_b64": image_data, "status": "Success"}

        except Exception as e:
            driver.quit()
            return {"error": f"Timeout/Access Error: {str(e)}"}
            
    except Exception as e:
        return {"error": f"Driver Error: {str(e)}"}
    
def generate_queries(vision_data: dict) -> tuple[str, list]:
    """
    Helper to generate the same queries for both engines.
    Returns: (Topic, List of Queries)
    """
    current_year = datetime.now().year
    forecast_year = current_year + 5
    
    category = vision_data.get("category_play", {}).get("definition", "")
    problem = vision_data.get("customer_obsession", {}).get("problem_statement", "")
    
    # Fallback topic
    search_topic = category if len(category) > 3 else "startup market trends"
    
    queries = [
        f"future of {search_topic} market {forecast_year} forecast",
        f"VC investment trends in {search_topic} {current_year}",
        f"is {search_topic} market growing or shrinking {current_year}?",
        f"risks and regulation for {search_topic} startups {current_year}"
    ]
    return search_topic, queries


def get_market_signals_serper(vision_data: dict) -> str:
    """
    Runs search using Google Serper API via standard HTTP requests.
    Requires: os.environ["SERPER_API_KEY"]
    """
    print("🌐 Running Market Search (Serper/Google)...")
    
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        raise ValueError("Missing SERPER_API_KEY")

    # Generate queries (assuming generate_queries function exists in your scope)
    topic, queries = generate_queries(vision_data)
    
    raw_results = []
    url = "https://google.serper.dev/search"
    headers = {
        'X-API-KEY': api_key,
        'Content-Type': 'application/json'
    }
    
    try:
        for q in queries:
            payload = json.dumps({"q": q})
            
            # Direct HTTP Request
            response = requests.post(url, headers=headers, data=payload)
            
            if response.status_code == 200:
                data = response.json()
                
                # Take top 2 organic results
                organic = data.get('organic', [])[:2] 
                
                for r in organic:
                    entry = (
                        f"--- SOURCE (Serper): {q} ---\n"
                        f"Title: {r.get('title', 'No Title')}\n"
                        f"Snippet: {r.get('snippet', 'No Snippet')}\n"
                        f"Link: {r.get('link', 'No Link')}\n"
                    )
                    raw_results.append(entry)
            else:
                print(f"   ⚠️ Serper Request Error {response.status_code}: {response.text}")
                
        return "\n".join(raw_results) if raw_results else "No Serper results found."

    except Exception as e:
        print(f"   ❌ Serper Error: {e}")
        return f"Error running Serper: {str(e)}"
    
def get_market_signals_duckduckgo(vision_data: dict) -> str:
    """Runs search using DuckDuckGo."""
    print("   -> Running DuckDuckGo Search...")
    _, queries = generate_queries(vision_data)
    raw_results = []

    try:
        ddg = DuckDuckGoSearchRun()
        for q in queries:
            result_text = ddg.run(q)
            raw_results.append(f"SOURCE (DuckDuckGo): {result_text[:300]}...") 
            
        return "\n".join(raw_results) if raw_results else "No DuckDuckGo results."
    except Exception as e:
        return f"DuckDuckGo Error: {str(e)}"
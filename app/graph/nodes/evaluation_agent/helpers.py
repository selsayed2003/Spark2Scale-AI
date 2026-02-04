import json
import os
import base64
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

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
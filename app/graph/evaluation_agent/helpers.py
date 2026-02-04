import json
import base64
import asyncio
from playwright.async_api import async_playwright
from app.core.logger import get_logger

# --- INITIALIZE LOGGER ---
logger = get_logger(__name__)


def load_schema(schema_name: str) -> str:
    """
    Loads a JSON schema from the schema.json file.
    """
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(current_dir, "schema.json")
    
    with open(schema_path, "r") as f:
        schemas = json.load(f)
        
    return json.dumps(schemas.get(schema_name, {}), indent=2)

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

def check_missing_fields(data, parent_path=""):
    '''Recursively checks for empty values in a nested JSON object to identify incomplete data.
    
    Params:
        data - The dictionary or list to be scanned for missing values.
        parent_path - A string tracking the nested key hierarchy for error reporting (defaults to empty string).
        
    Returns:
        list - A list of strings, each detailing the path of a missing or empty field.
    '''
    missing_errors = []

    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{parent_path}.{key}" if parent_path else key

            if value is None or value == "" or value == [] or value == {}:
                missing_errors.append(f"Missing Value: Field '{current_path}' is empty.")
            else:
                missing_errors.extend(check_missing_fields(value, current_path))

    elif isinstance(data, list):
        for index, item in enumerate(data):
            item_path = f"{parent_path}[{index}]"
            missing_errors.extend(check_missing_fields(item, item_path))

    return missing_errors

async def capture_screenshot(url: str):
    """
    Visits a URL using Playwright (Async) and returns the screenshot as a Base64 string.
    """
    logger.info(f"📸 Visiting {url} for visual check (Async)...")
    
    if not url:
        return {"error": "No URL provided."}

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            # Create a context with a known viewport and user agent to mimic a real user
            context = await browser.new_context(
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            page = await context.new_page()
            
            try:
                # Wait up to 15 seconds for load
                await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                
                # Small delay to ensure any JS rendering stabilizes
                await asyncio.sleep(3)
                
                screenshot_bytes = await page.screenshot(type='png')
                image_data = base64.b64encode(screenshot_bytes).decode("utf-8")
                
                return {"image_b64": image_data, "status": "Success"}
                
            except Exception as e:
                return {"error": f"Timeout/Access Error: {str(e)}"}
            finally:
                await browser.close()
            
    except Exception as e:
        return {"error": f"Playwright Driver Error: {str(e)}"}
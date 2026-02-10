import json
import os
import time
import asyncio
import aiohttp
from datetime import datetime
from dotenv import load_dotenv
import builtwith
from urllib.parse import urlparse

# LangChain & AI Imports
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
from google.api_core.exceptions import ResourceExhausted

# Resilience
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Relative Imports
from .prompts import (
    BUSINESS_MODEL_JUDGE_PROMPT,
    CONTRADICTION_MARKET_PROMPT_TEMPLATE,
    CONTRADICTION_OPERATIONS_PROMPT_TEMPLATE,
    CONTRADICTION_PRE_SEED_BIZ_MODEL_PROMPT,
    CONTRADICTION_PRODUCT_PROMPT_TEMPLATE,
    CONTRADICTION_SEED_BIZ_MODEL_PROMPT,
    CONTRADICTION_TEAM_PROMPT_TEMPLATE,
    CONTRADICTION_VISION_PROMPT_TEMPLATE,
    ECONOMIC_JUDGEMENT_PROMPT,
    OPERATIONS_SCORING_AGENT_PROMPT,
    RISK_BIZ_MODEL_PRE_SEED_PROMPT,
    RISK_BIZ_MODEL_SEED_PROMPT,
    VALUATION_RISK_MARKET_PROMPT_TEMPLATE,
    VALUATION_RISK_OPS_PRE_SEED_PROMPT,
    VALUATION_RISK_OPS_SEED_PROMPT, 
    VALUATION_RISK_PROBLEM_PROMPT_TEMPLATE,
    VALUATION_RISK_PRODUCT_PROMPT_TEMPLATE, 
    VALUATION_RISK_TEAM_PROMPT_TEMPLATE, 
    TEAM_SCORING_AGENT_PROMPT, 
    CONTRADICTION_PROBLEM_PROMPT_TEMPLATE, 
    PROBLEM_SCORING_AGENT_PROMPT,
    VISION_SCORING_AGENT_PROMPT,
    VISUAL_VERIFICATION_PROMPT,
    PRODUCT_SCORING_AGENT_PROMPT,
    MARKET_SCORING_AGENT_PROMPT,
    CONTRADICTION_PRE_SEED_TRACTION_AGENT_PROMPT,
    CONTRADICTION_SEED_TRACTION_AGENT_PROMPT,
    VALUATION_RISK_TRACTION_PRE_SEED_PROMPT,
    VALUATION_RISK_TRACTION_SEED_PROMPT,
    TRACTION_SCORING_PRE_SEED_PROMPT,
    TRACTION_SCORING_SEED_PROMPT,
    CONTRADICTION_PRE_SEED_GTM_AGENT_PROMPT,
    CONTRADICTION_SEED_GTM_AGENT_PROMPT,
    VALUATION_RISK_GTM_PRE_SEED_PROMPT,
    VALUATION_RISK_GTM_SEED_PROMPT,
    SCORING_GTM_PRE_SEED_PROMPT,
    SCORING_GTM_SEED_PROMPT,
    SCORING_BIZ_PRE_SEED_PROMPT,
    SCORING_BIZ_SEED_PROMPT,
    CATEGORY_FUTURE_PROMPT,
    MARKET_LOCAL_DEPENDENCY_PROMPT,
    VALUATION_RISK_VISION_PRE_SEED_PROMPT,
    VALUATION_RISK_VISION_SEED_PROMPT
)
from .helpers import (
    extract_business_pre_seed, extract_business_seed,
    extract_gtm_pre_seed, extract_gtm_seed,
    extract_operations_data, extract_problem_data, 
    extract_team_data, extract_traction_data, 
    extract_product_data, extract_market_data, 
    extract_vision_data, # Added
    capture_screenshot, check_missing_fields,
    get_market_signals_serper, get_market_signals_duckduckgo # Added
)
from app.core.llm import get_llm
from app.core.logger import get_logger
from app.core.limiter import concurrency_limiter
# Load Environment Variables
load_dotenv()

# --- INITIALIZE LOGGER ---
logger = get_logger(__name__)

# --- CONFIGURATION ---
RETRY_CONFIG = {
    "wait": wait_exponential(multiplier=2, min=10, max=120),
    "stop": stop_after_attempt(20),
    "retry": retry_if_exception_type((ResourceExhausted, ChatGoogleGenerativeAIError))
}

# --- TOOLS & AGENTS ---

@retry(**RETRY_CONFIG)
async def contradiction_check(data: dict, agent_prompt: str) -> str:
    async with concurrency_limiter:
        logger.info("🤖 Contradiction Check...")
        llm = get_llm(temperature=0)
        chain = PromptTemplate.from_template(agent_prompt) | llm | StrOutputParser()
        return await chain.ainvoke({
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "json_data": json.dumps(data, indent=2) 
        })

@retry(**RETRY_CONFIG)
async def team_risk_check(data: dict, agent_prompt: str) -> str:
    async with concurrency_limiter:
        logger.info("📉 Team Risk Check...")
        llm = get_llm(temperature=0)
        chain = PromptTemplate.from_template(agent_prompt) | llm | StrOutputParser()
        return await chain.ainvoke({"json_data": json.dumps(data, indent=2)})

@retry(**RETRY_CONFIG)
async def loaded_risk_check_with_search(problem_data: dict, search_results: dict, agent_prompt: str) -> str:
    async with concurrency_limiter:
        logger.info("🛡️ Problem Risk Check...")
        llm = get_llm(temperature=0)
        chain = PromptTemplate.from_template(agent_prompt) | llm | StrOutputParser()
        return await chain.ainvoke({
            "internal_json": json.dumps(problem_data, indent=2),
            "external_search_json": json.dumps(search_results, indent=2)
        })

@retry(**RETRY_CONFIG)
async def team_scoring_agent(data_package: dict) -> dict:
    async with concurrency_limiter:
        logger.info("🏆 Team Scoring...")
        llm = get_llm(temperature=0)
        chain = PromptTemplate.from_template(TEAM_SCORING_AGENT_PROMPT) | llm | JsonOutputParser()
        return await chain.ainvoke({
            "user_json_data": json.dumps(data_package.get("user_data", {}), indent=2),
            "risk_agent_output": str(data_package.get("risk_report")),
            "contradiction_agent_output": str(data_package.get("contradiction_report")),
            "missing_info_output": str(data_package.get("missing_report"))
        })
@retry(**RETRY_CONFIG)
async def verify_problem_claims(problem_statement: str, target_audience: str) -> dict:
    logger.info("🔎 Verifying Problem Claims...")
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key: return {"error": "Missing SERPER_API_KEY."}

    # 1. Generate Queries (Needs LLM -> Needs Limiter)
    async with concurrency_limiter:
        llm = get_llm(temperature=0)
        query_gen_prompt = f"""
        Search Expert. Convert to 3 Google queries.
        Audience: {target_audience}
        Problem: {problem_statement}
        Output JSON ONLY: {{"pain_query": "...", "symptom_query": "...", "solution_query": "..."}}
        """
        try:
            resp = await llm.ainvoke(query_gen_prompt)
            clean_json = resp.content.replace("```json", "").replace("```", "").strip()
            queries = json.loads(clean_json)
        except:
            queries = {"pain_query": f"{problem_statement} reddit", "symptom_query": f"{target_audience} struggle", "solution_query": f"solution {problem_statement}"}

    # 2. Execute Search (No LLM -> No Limiter needed, just async IO)
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
    results_report = {"generated_queries": queries, "pain_validation_search": [], "competitor_search": []}

    async def run_single_search(session, q):
        try:
            async with session.post(url, headers=headers, json={"q": q, "num": 4}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [{"title": r.get("title"), "link": r.get("link"), "snippet": r.get("snippet")} for r in data.get("organic", [])]
        except: return []
        return []

    async with aiohttp.ClientSession() as session:
        pain, symptom, sol = await asyncio.gather(
            run_single_search(session, queries.get("pain_query")),
            run_single_search(session, queries.get("symptom_query")),
            run_single_search(session, queries.get("solution_query"))
        )
        results_report["pain_validation_search"] = pain + symptom
        results_report["competitor_search"] = sol

    return results_report

@retry(**RETRY_CONFIG)
async def problem_scoring_agent(data_package: dict) -> dict:
    async with concurrency_limiter:
        logger.info("🏆 Problem Scoring...")
        llm = get_llm(temperature=0)
        chain = PromptTemplate.from_template(PROBLEM_SCORING_AGENT_PROMPT) | llm | JsonOutputParser()
        return await chain.ainvoke({
            "problem_json": json.dumps(data_package.get("problem_definition", {}), indent=2),
            "missing_report": str(data_package.get("missing_report")),
            "search_json": json.dumps(data_package.get("search_report", {}), indent=2),
            "risk_report": str(data_package.get("risk_report")),
            "contradiction_report": str(data_package.get("contradiction_report"))
        })

@retry(**RETRY_CONFIG)
async def tech_stack_detective(url: str):
    logger.info(f"🛠️ Tech Stack Detective: {url}")
    if not url: return {"verdict": "No URL"}
    
    # Simple logic, no LLM, no limiter needed
    try:
        tech_data = await asyncio.to_thread(builtwith.parse, url)
        detected = [item for sublist in tech_data.values() for item in sublist]
        return {"technologies_found": detected, "status": "Success"}
    except Exception as e:
        return {"error": str(e)}

@retry(**RETRY_CONFIG)
async def analyze_visuals_with_langchain(company_name, website_url, prompt_template):
    if not website_url: return "No URL."
    
    capture = await capture_screenshot(website_url)
    if "error" in capture: return f"Visual Error: {capture['error']}"

    async with concurrency_limiter:
        logger.info("👁️ Vision Analysis...")
        llm = get_llm(temperature=0)
        msg = HumanMessage(content=[
            {"type": "text", "text": prompt_template.format(company_name=company_name, website_url=website_url)},
            {"type": "image_url", "image_url": f"data:image/png;base64,{capture['image_b64']}"}
        ])
        resp = await llm.ainvoke([msg])
        return resp.content

@retry(**RETRY_CONFIG)
async def product_scoring_agent(data_package: dict) -> dict:
    async with concurrency_limiter:
        logger.info("🏆 Product Scoring...")
        llm = get_llm(temperature=0)
        chain = PromptTemplate.from_template(PRODUCT_SCORING_AGENT_PROMPT) | llm | JsonOutputParser()
        return await chain.ainvoke({
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "internal_data": json.dumps(data_package.get("internal_data", {}), indent=2),
            "contradiction_report": str(data_package.get("contradiction_report")),
            "risk_report": str(data_package.get("risk_report")),
            "tech_stack_report": str(data_package.get("tech_stack_report")),
            "visual_analysis_report": str(data_package.get("visual_analysis_report"))
        })
@retry(**RETRY_CONFIG)
async def regulation_trend_radar_tool(category: str, location: str):
    logger.info(f"📡 Radar Scan: '{category}' in '{location}'...")
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': os.environ.get("SERPER_API_KEY"), 'Content-Type': 'application/json'}
    results_data = {}
    current_year = datetime.now().year

    async with aiohttp.ClientSession() as session:
        # Check 1: Regulations
        try:
            reg_q = f"{category} regulatory risks compliance laws {location}"
            async with session.post(url, headers=headers, json={"q": reg_q}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    hits = data.get("organic", [])[:3]
                    results_data["regulatory_evidence"] = "\n".join([f"- {r['snippet']}" for r in hits])
        except Exception as e:
            results_data["regulatory_evidence"] = f"Failed: {str(e)}"

        # Check 2: Trends
        try:
            trend_q = f"{category} market growth outlook {current_year} {location}"
            async with session.post(url, headers=headers, json={"q": trend_q}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    hits = data.get("organic", [])[:3]
                    results_data["trend_evidence"] = "\n".join([f"- {r['snippet']}" for r in hits])
        except Exception as e:
            results_data["trend_evidence"] = f"Failed: {str(e)}"

    return {"tool": "Regulation_Radar", "findings": results_data}

@retry(**RETRY_CONFIG)
async def tam_sam_verifier_tool(beachhead: str, location: str, claimed_size: str):
    logger.info(f"📊 TAM Check: '{beachhead}' in '{location}'...")
    if not os.environ.get("SERPER_API_KEY"):
        return {"tool": "TAM_Verifier", "status": "Simulated", "evidence": "Simulated: Market data not available."}

    search_query = f"total number of {beachhead} in {location} statistics {datetime.now().year}"
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': os.environ.get("SERPER_API_KEY"), 'Content-Type': 'application/json'}

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, headers=headers, json={"q": search_query}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    snippets = [f"- {i.get('title')}: {i.get('snippet')}" for i in data.get("organic", [])[:3]]
                    return {
                        "tool": "TAM_Verifier",
                        "founder_claim": claimed_size,
                        "search_evidence": "\n".join(snippets),
                        "status": "Success"
                    }
        except Exception as e:
            return {"error": str(e)}
    return {"error": "Search Failed"}

async def local_dependency_detective(tech_stack: str, acquisition_channel: str, product_desc: str):
    """Analyzes platform risk. Uses Limiter because it calls LLM."""
    async with concurrency_limiter:
        logger.info("🕵️ Dependency Detective...")
        
        # Fallback logic handled by 'provider="ollama"' inside get_llm wrapper 
        # But for stability in this script, we default to Gemini with retries
        llm = get_llm(temperature=0, provider="gemini")
        
        prompt_text = f"""
        Analyze platform risks for Product: {product_desc}, Tech: {tech_stack}, Channel: {acquisition_channel}.
        Respond ONLY JSON: {{ "risk_level": "High/Medium/Low", "red_flags": ["..."], "search_query_needed": "..." }}
        """
        
        try:
            chain = StrOutputParser()
            resp_text = await llm.ainvoke(prompt_text)
            clean_json = resp_text.replace("```json", "").replace("```", "").strip()
            analysis = json.loads(clean_json)
            return {"tool": "Dependency_Detective", "risk_level": analysis.get("risk_level"), "analysis": str(analysis)}
        except Exception as e:
            return {"tool": "Dependency_Detective", "error": str(e)}

@retry(**RETRY_CONFIG)
async def market_risk_agent(market_inputs, tam_result, radar_result, dep_result):
    async with concurrency_limiter:
        logger.info("📉 Market Risk...")
        llm = get_llm(temperature=0)
        chain = PromptTemplate.from_template(VALUATION_RISK_MARKET_PROMPT_TEMPLATE) | llm | StrOutputParser()
        return await chain.ainvoke({
            "internal_json": json.dumps(market_inputs, indent=2),
            "tam_report": json.dumps(tam_result, indent=2),
            "radar_report": json.dumps(radar_result, indent=2),
            "dependency_report": json.dumps(dep_result, indent=2)
        })

@retry(**RETRY_CONFIG)
async def market_scoring_agent(data_package: dict) -> dict:
    async with concurrency_limiter:
        logger.info("⚖️ Market Scoring...")
        llm = get_llm(temperature=0)
        chain = PromptTemplate.from_template(MARKET_SCORING_AGENT_PROMPT) | llm | JsonOutputParser()
        
        result_dict = await chain.ainvoke({
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "internal_data": json.dumps(data_package.get("internal_data", {}), indent=2),
            "contradiction_report": str(data_package.get("contradiction_report", "None")),
            "tam_report": str(data_package.get("tam_report", "None")),
            "radar_report": str(data_package.get("radar_report", "None")),
            "dependency_report": str(data_package.get("dependency_report", "None"))
        })
        
        # Enrich
        score_val = str(result_dict.get('score', "0")).split("/")[0]
        score_num = int(score_val) if score_val.isdigit() else 0
        rubric_map = {0: "Undefined", 1: "Narrow", 2: "Medium", 3: "Large", 4: "Expanding", 5: "Blue Ocean"}
        result_dict["rubric_rating"] = rubric_map.get(score_num, "Unknown")
        result_dict["score_numeric"] = score_num
        return result_dict
# =========================================================
# TRACTION AGENT TOOLS
# =========================================================

@retry(**RETRY_CONFIG)
async def traction_risk_agent(traction_data: dict, risk_prompt_template: str) -> str:
    async with concurrency_limiter:
        llm = get_llm(temperature=0)
        chain = PromptTemplate.from_template(risk_prompt_template) | llm | StrOutputParser()
        return await chain.ainvoke({"traction_json": json.dumps(traction_data, indent=2)})

@retry(**RETRY_CONFIG)
async def traction_scoring_agent(data_package: dict) -> dict:
    async with concurrency_limiter:
        logger.info("🚀 Traction Scoring...")
        llm = get_llm(temperature=0)
        traction_data = data_package.get("traction_data", {})
        stage_raw = traction_data.get("context", {}).get("stage", "Pre-Seed").lower()
        template = TRACTION_SCORING_PRE_SEED_PROMPT if "pre" in stage_raw else TRACTION_SCORING_SEED_PROMPT
        chain = PromptTemplate.from_template(template) | llm | JsonOutputParser()
        
        result_dict = await chain.ainvoke({
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "internal_data": json.dumps(traction_data, indent=2),
            "contradiction_report": str(data_package.get("contradiction_report", "None")),
            "risk_report": str(data_package.get("risk_report", "None"))
        })
        
        score_val = str(result_dict.get('score', "0")).split("/")[0]
        result_dict["score_numeric"] = int(score_val) if score_val.isdigit() else 0
        return result_dict

# =========================================================
# GTM & BUSINESS TOOLS
# =========================================================

@retry(**RETRY_CONFIG)
async def gtm_risk_agent(gtm_data: dict, risk_prompt_template: str) -> str:
    async with concurrency_limiter:
        llm = get_llm(temperature=0)
        chain = PromptTemplate.from_template(risk_prompt_template) | llm | StrOutputParser()
        return await chain.ainvoke({"gtm_json": json.dumps(gtm_data, indent=2)})

@retry(**RETRY_CONFIG)
async def gtm_scoring_agent(gtm_data: dict, economics_report: dict, contradiction_report: str, risk_report: str) -> dict:
    async with concurrency_limiter:
        logger.info("🚀 GTM Scoring...")
        llm = get_llm(temperature=0)
        stage_raw = gtm_data.get("context", {}).get("stage", "Pre-Seed").lower()
        template = SCORING_GTM_PRE_SEED_PROMPT if "pre" in stage_raw else SCORING_GTM_SEED_PROMPT
        chain = PromptTemplate.from_template(template) | llm | JsonOutputParser()
        
        result_dict = await chain.ainvoke({
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "gtm_data": json.dumps(gtm_data, indent=2),
            "economics_report": json.dumps(economics_report, indent=2),
            "contradiction_report": str(contradiction_report),
            "risk_report": str(risk_report)
        })
        score_val = str(result_dict.get('score', "0")).split("/")[0]
        result_dict["score_numeric"] = int(score_val) if score_val.isdigit() else 0
        return result_dict
def calculate_economics_with_judgment(gtm_data: dict) -> dict:
    """
    Calculates Unit Economics using WallStreetPrep & HBS formulas, 
    then uses an LLM to render a verdict based on sector benchmarks.
    NOTE: This function mixes Python Math (Calculations) with AI (Judgment).
    """
    
    logger.info("🧮 Calculating Unit Economics & Business Logic...")

    # =========================================================
    # 1. EXTRACT & CALCULATE RAW METRICS (The Math)
    # =========================================================
    
    # A. Setup Variables
    econ = gtm_data.get("unit_economics", {}) or gtm_data.get("economics_inputs", {})
    context = gtm_data.get("context", {})
    strategy = gtm_data.get("strategy", {})
    
    # Safe Float Conversion
    def safe_float(val):
        try: return float(val)
        except: return 0.0

    burn = safe_float(econ.get("burn_rate"))
    total_users = safe_float(econ.get("total_users"))
    paid_users = safe_float(econ.get("paid_users"))
    revenue = safe_float(econ.get("revenue") or econ.get("early_revenue"))
    price = safe_float(econ.get("price_point"))
    
    # B. Calculate "New Users" (Flow Metric)
    founded_str = context.get("founded_date")
    try:
        f_date = datetime.strptime(founded_str, "%Y-%m-%d") if founded_str else datetime.now()
        months_alive = max((datetime.now() - f_date).days / 30, 1)
    except:
        months_alive = 6
    
    avg_new_users_mo = total_users / months_alive

    # C. Calculate Metrics (Based on Standard Formulas)
    metrics = {
        "monthly_burn": f"${int(burn)}",
        "price_point": f"${int(price)}",
        "revenue": f"${int(revenue)}"
    }

    # --- CAC (Source: WallStreetPrep - Σ S&M / New Customers) ---
    # Proxy: We assume 30% of Burn is S&M if not specified
    est_s_m_spend = burn * 0.30
    if avg_new_users_mo > 0:
        metrics["implied_cac"] = round(est_s_m_spend / avg_new_users_mo, 2)
    else:
        metrics["implied_cac"] = "N/A (0 Users)"

    # --- Freemium Conversion (Source: Medium/Lincoln Murphy) ---
    if total_users > 0:
        metrics["conversion_rate"] = round((paid_users / total_users) * 100, 2)
    else:
        metrics["conversion_rate"] = 0

    # --- Payback Period (Proxy for LTV/CAC Rule of 3) ---
    if isinstance(metrics["implied_cac"], (int, float)) and price > 0:
        metrics["payback_months"] = round(metrics["implied_cac"] / price, 1)
    else:
        metrics["payback_months"] = "Unknown"

    # =========================================================
    # 2. THE LLM JUDGE (The Verdict)
    # =========================================================

    # Setup LLM using your Factory
    llm = get_llm(temperature=0)

    # Use the global prompt constant
    chain = PromptTemplate.from_template(ECONOMIC_JUDGEMENT_PROMPT) | llm | StrOutputParser()

    try:
        # Extract meaningful context description
        sector_info = strategy.get("icp_description", "Unknown Tech Startup")
        
        # We use invoke (Sync) here because this function is CPU-bound logic mostly 
        # and doesn't block heavily like a network call. 
        # If preferred, you can make this function async and use ainvoke.
        judgement_json = chain.invoke({
            "sector_info": sector_info,
            "stage": context.get("stage", "Pre-Seed"),
            "model": strategy.get("pricing_model", "Unknown"),
            "cac": metrics["implied_cac"],
            "price": price,
            "payback": metrics["payback_months"],
            "conversion": metrics["conversion_rate"],
            "burn": metrics["monthly_burn"],
            "revenue": metrics["revenue"],
            "paid_users": int(paid_users),
            "users": int(total_users)
        })
        
        # Merge the LLM's judgment into the report
        try:
            parsed_judgement = json.loads(judgement_json.replace("```json", "").replace("```", "").strip())
            metrics["ai_analysis"] = parsed_judgement
        except:
             metrics["ai_analysis"] = {"error": "Could not parse AI judgment", "raw": judgement_json}

    except Exception as e:
        logger.error(f"Economic Calculation Error: {e}")
        metrics["ai_analysis"] = {"error": str(e)}

    return metrics
async def evaluate_business_model_with_context(business_data: dict) -> dict:
    """
    Calculates Profitability & Solvency, then uses an LLM to benchmark 
    against the specific sector (SaaS vs Hardware vs E-commerce).
    """
    async with concurrency_limiter:
        logger.info("💰 Analyzing Business Model & Economics...")

        # =========================================================
        # 1. THE CALCULATOR (Hard Math)
        # =========================================================
        structure = business_data.get("monetization_structure", {})
        cash = business_data.get("cash_health", {})
        momentum = business_data.get("revenue_momentum", {}) 
        context = business_data.get("context", {})

        # Safe conversion helpers
        def safe_float(val):
            try: return float(val)
            except: return 0.0

        # Defaults
        price = safe_float(structure.get("price_point"))
        margin_percent = safe_float(structure.get("gross_margin"))
        burn = safe_float(cash.get("burn_rate"))
        runway_stated = safe_float(cash.get("runway_months"))
        
        # Calculate Implied Cost (Cost of Goods Sold)
        cost_to_serve = price * (1 - (margin_percent / 100)) if price > 0 else 0

        # Format Growth
        growth_raw = momentum.get("growth_rate", "0")
        
        # =========================================================
        # 2. THE LLM JUDGE (Sector Context)
        # =========================================================
        
        # Setup LLM
        llm = get_llm(temperature=0)

        # Setup Chain
        chain = PromptTemplate.from_template(BUSINESS_MODEL_JUDGE_PROMPT) | llm | JsonOutputParser()
        
        try:
            # We need to pull "Sector" from the raw inputs if possible, 
            # or use the "pricing_model" as a proxy.
            sector_context = business_data.get("sector_context", "Tech Startup")

            # Use invoke (sync) as this is CPU/logic bound
            ai_verdict = chain.invoke({
                "company_name": context.get("company_name", "Startup"),
                "stage": context.get("stage", "Pre-Seed"),
                "sector_info": sector_context,
                "pricing_model": structure.get("pricing_model", "Unknown"),
                "price": price,
                "margin": margin_percent,
                "burn": int(burn),
                "runway": runway_stated,
                "growth": growth_raw,
                "cost_to_serve": round(cost_to_serve, 2)
            })
            
            # Merge Math + AI Verdict
            report = {
                "metrics": {
                    "monthly_burn": f"${int(burn)}",
                    "runway_months": runway_stated,
                    "gross_margin": f"{margin_percent}%",
                    "implied_cost": f"${round(cost_to_serve, 2)}",
                    "growth_rate": growth_raw
                },
                "ai_analysis": ai_verdict
            }
            return report

        except Exception as e:
            logger.error(f"Business Model Analysis Failed: {e}")
            return {
                "error": "Business Model Analysis Failed", 
                "details": str(e)
            }
@retry(**RETRY_CONFIG)
async def business_risk_agent(business_data: dict, risk_prompt_template: str) -> str:
    async with concurrency_limiter:
        llm = get_llm(temperature=0)
        chain = PromptTemplate.from_template(risk_prompt_template) | llm | StrOutputParser()
        return await chain.ainvoke({"business_data": json.dumps(business_data, indent=2)})

@retry(**RETRY_CONFIG)
async def business_scoring_agent(data_package: dict) -> dict:
    async with concurrency_limiter:
        logger.info("🚀 Business Scoring...")
        llm = get_llm(temperature=0)
        business_data = data_package.get("business_data", {})
        stage_raw = business_data.get("context", {}).get("stage", "Pre-Seed").lower()
        template = SCORING_BIZ_PRE_SEED_PROMPT if "pre" in stage_raw else SCORING_BIZ_SEED_PROMPT
        chain = PromptTemplate.from_template(template) | llm | JsonOutputParser()
        
        result_dict = await chain.ainvoke({
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "business_data": json.dumps(business_data, indent=2),
            "calculator_report": json.dumps(data_package.get("calculator_report", {}), indent=2),
            "contradiction_report": str(data_package.get("contradiction_report", "None")),
            "risk_report": str(data_package.get("risk_report", "None"))
        })
        score_val = str(result_dict.get('score', "0")).split("/")[0]
        result_dict["score_numeric"] = int(score_val) if score_val.isdigit() else 0
        return result_dict

# =========================================================
# VISION & OPS TOOLS
# =========================================================

@retry(**RETRY_CONFIG)
async def analyze_category_future(vision_data: dict) -> dict:
    """Async wrapper for the search helpers"""
    logger.info("🌐 Vision Market Analysis...")
    
    # 1. Try Serper First (Fast & Parallel)
    market_text = await get_market_signals_serper(vision_data)
    
    # 2. Conditional Fallback: Only run DDG if Serper failed or returned nothing
    if "No Serper results found" in market_text or "API Key found" in market_text:
        logger.warning("⚠️ Serper returned no data. Engaging DuckDuckGo Fallback...")
        ddg_text = get_market_signals_duckduckgo(vision_data)
        combined_signals = f"=== DUCKDUCKGO (FALLBACK) ===\n{ddg_text}"
    else:
        combined_signals = f"=== SERPER ===\n{market_text}"
    
    llm = get_llm(temperature=0)
    prompt = PromptTemplate.from_template(CATEGORY_FUTURE_PROMPT)
    chain = prompt | llm | JsonOutputParser()
    
    moat = f"{vision_data.get('category_play', {}).get('moat')} (Diff: {vision_data.get('category_play', {}).get('differentiation')})"
    
    return await chain.ainvoke({
        "category": vision_data.get("category_play", {}).get("definition", "Unknown"),
        "problem": vision_data.get("customer_obsession", {}).get("problem_statement", "Unknown"),
        "moat": moat,
        "market_signals": combined_signals
    })

@retry(**RETRY_CONFIG)
async def vision_risk_agent(vision_data: dict, market_analysis: dict, template: str) -> str:
    async with concurrency_limiter:
        llm = get_llm(temperature=0.1)
        chain = PromptTemplate.from_template(template) | llm | StrOutputParser()
        return await chain.ainvoke({
            "vision_data": json.dumps(vision_data, indent=2),
            "market_analysis": json.dumps(market_analysis, indent=2)
        })

@retry(**RETRY_CONFIG)
async def vision_scoring_agent(data_package: dict) -> dict:
    async with concurrency_limiter:
        logger.info("⚖️ Vision Scoring...")
        llm = get_llm(temperature=0)
        chain = PromptTemplate.from_template(VISION_SCORING_AGENT_PROMPT) | llm | JsonOutputParser()
        
        result_dict = await chain.ainvoke({
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "vision_data": json.dumps(data_package.get("vision_data", {}), indent=2),
            "market_analysis": json.dumps(data_package.get("market_analysis", {}), indent=2),
            "contradiction_report": str(data_package.get("contradiction_report", "None")),
            "risk_report": str(data_package.get("risk_report", "None"))
        })
        score_val = str(result_dict.get('score', "0")).split("/")[0]
        result_dict["score_numeric"] = int(score_val) if score_val.isdigit() else 0
        return result_dict

@retry(**RETRY_CONFIG)
async def get_funding_benchmarks(location: str, stage: str, sector: str) -> str:
    logger.info(f"💰 Searching Benchmarks for {stage} {sector} in {location}...")
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': os.environ.get("SERPER_API_KEY"), 'Content-Type': 'application/json'}
    current_year = datetime.now().year
    
    queries = [
        f"average {stage} {sector} startup round size {location} {current_year}",
        f"average {stage} {sector} startup valuation {location} {current_year}"
    ]
    results = []
    
    async with aiohttp.ClientSession() as session:
        for q in queries:
            try:
                async with session.post(url, headers=headers, json={"q": q}) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        for r in data.get('organic', [])[:2]:
                            results.append(f"SOURCE: {r.get('title')} - {r.get('snippet')}")
            except Exception: pass
            
    return "\n".join(results) if results else "No specific benchmarks found."

@retry(**RETRY_CONFIG)
async def operations_risk_agent(operations_data: dict, benchmarks: str, template: str) -> str:
    async with concurrency_limiter:
        llm = get_llm(temperature=0)
        chain = PromptTemplate.from_template(template) | llm | StrOutputParser()
        return await chain.ainvoke({
            "operations_data": json.dumps(operations_data, indent=2),
            "benchmarks": benchmarks
        })

@retry(**RETRY_CONFIG)
async def operations_scoring_agent(data_package: dict) -> dict:
    async with concurrency_limiter:
        logger.info("⚖️ Operations Scoring...")
        llm = get_llm(temperature=0)
        chain = PromptTemplate.from_template(OPERATIONS_SCORING_AGENT_PROMPT) | llm | JsonOutputParser()
        
        result_dict = await chain.ainvoke({
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "operations_data": json.dumps(data_package.get("operations_data", {}), indent=2),
            "benchmarks": str(data_package.get("benchmarks", "None")),
            "contradiction_report": str(data_package.get("contradiction_report", "None")),
            "risk_report": str(data_package.get("risk_report", "None"))
        })
        score_val = str(result_dict.get('score', "0")).split("/")[0]
        result_dict["score_numeric"] = int(score_val) if score_val.isdigit() else 0
        return result_dict
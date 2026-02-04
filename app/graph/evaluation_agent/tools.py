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
    CONTRADICTION_PRODUCT_PROMPT_TEMPLATE,
    CONTRADICTION_TEAM_PROMPT_TEMPLATE, 
    VALUATION_RISK_PROBLEM_PROMPT_TEMPLATE,
    VALUATION_RISK_PRODUCT_PROMPT_TEMPLATE, 
    VALUATION_RISK_TEAM_PROMPT_TEMPLATE, 
    TEAM_SCORING_AGENT_PROMPT, 
    CONTRADICTION_PROBLEM_PROMPT_TEMPLATE, 
    PROBLEM_SCORING_AGENT_PROMPT,
    VISUAL_VERIFICATION_PROMPT,
    PRODUCT_SCORING_AGENT_PROMPT
)
from .helpers import extract_problem_data, extract_team_data, extract_product_data, capture_screenshot, check_missing_fields
from app.core.llm import get_llm
from app.core.logger import get_logger
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
    logger.info("🤖 Running Contradiction Check...")
    llm = get_llm(temperature=0)
    prompt = PromptTemplate.from_template(agent_prompt)
    
    try:
        chain = prompt | llm | StrOutputParser()
        result = await chain.ainvoke({
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "json_data": json.dumps(data, indent=2) 
        })
        return result
    except Exception as e:
        logger.error(f"Error performing Contradiction Check: {str(e)}")
        return f"Error performing Contradiction Check: {str(e)}"

@retry(**RETRY_CONFIG)
async def team_risk_check(data: dict, agent_prompt: str) -> str:
    logger.info("📉 Running Team Risk Check...")
    llm = get_llm(temperature=0)
    prompt = PromptTemplate.from_template(agent_prompt)

    try:
        chain = prompt | llm | StrOutputParser()
        result = await chain.ainvoke({
            "json_data": json.dumps(data, indent=2)
        })
        return result
    except Exception as e:
        logger.error(f"Error performing Risk Check: {str(e)}")
        return f"Error performing Risk Check: {str(e)}"
    
@retry(**RETRY_CONFIG)
async def loaded_risk_check_with_search(problem_data: dict, search_results: dict, agent_prompt: str) -> str:
    logger.info("🛡️ Running Loaded Risk Check...")
    llm = get_llm(temperature=0)
    prompt = PromptTemplate.from_template(agent_prompt)

    try:
        chain = prompt | llm | StrOutputParser()
        result = await chain.ainvoke({
            "internal_json": json.dumps(problem_data, indent=2),
            "external_search_json": json.dumps(search_results, indent=2)
        })
        return result
    except Exception as e:
        logger.error(f"Loaded Risk Check Error: {str(e)}")
        return f"## Problem Risks\n* **System Error**: {str(e)}"

@retry(**RETRY_CONFIG)
async def verify_problem_claims(problem_statement: str, target_audience: str) -> dict:
    logger.info("🔎 Verifying Problem Claims...")
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        logger.error("Missing SERPER_API_KEY")
        return {"error": "Missing SERPER_API_KEY."}

    # 1. Generate Queries
    llm = get_llm(temperature=0)
    query_gen_prompt = f"""
    You are a Search Expert. Convert this startup problem into 3 specific Google search queries.
    Target Audience: {target_audience}
    Problem: {problem_statement}
    Output JSON ONLY: {{"pain_query": "...", "symptom_query": "...", "solution_query": "..."}}
    """
    try:
        query_response = await llm.ainvoke(query_gen_prompt)
        clean_json = query_response.content.replace("```json", "").replace("```", "").strip()
        queries = json.loads(clean_json)
    except:
        queries = {
            "pain_query": f"{problem_statement} reddit",
            "symptom_query": f"{target_audience} struggle forum",
            "solution_query": f"solution for {problem_statement}"
        }

    # 2. Execute Search (Async HTTP)
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
        # Run all 3 searches in parallel
        pain, symptom, sol = await asyncio.gather(
            run_single_search(session, queries.get("pain_query")),
            run_single_search(session, queries.get("symptom_query")),
            run_single_search(session, queries.get("solution_query"))
        )
        results_report["pain_validation_search"] = pain + symptom
        results_report["competitor_search"] = sol

    return results_report

@retry(**RETRY_CONFIG)
async def tech_stack_detective(url: str):
    logger.info(f"🛠️ Analyzing tech stack of {url}...")
    if not url: return {"verdict": "No URL"}
    
    # Domain Check (Sync is fine here, it's instant)
    domain = urlparse(url).netloc.lower()
    known_subdomains = {
        "canva.site": "Canva", "wixsite.com": "Wix", "bubbleapps.io": "Bubble",
        "framer.website": "Framer", "myshopify.com": "Shopify", "wordpress.com": "WordPress",
        "webflow.io": "Webflow", "softr.app": "Softr"
    }
    for sub, platform in known_subdomains.items():
        if sub in domain:
            return {"verdict": f"No-Code ({platform})", "is_no_code": True, "technologies_found": [platform]}

    # Deep Scan (Wrap blocking call in thread)
    try:
        tech_data = await asyncio.to_thread(builtwith.parse, url)
        # (Simplified logic for brevity - keeping your detection logic)
        detected_tech = [item for sublist in tech_data.values() for item in sublist]
        return {"technologies_found": detected_tech, "verdict": "Custom / Standard Stack", "is_no_code": False}
    except Exception as e:
        logger.error(f"Tech stack detection failed: {str(e)}")
        return {"error": str(e), "status": "Failed"}

@retry(**RETRY_CONFIG)
async def analyze_visuals_with_langchain(company_name, website_url, prompt_template):
    if not website_url: return "## Visual Risks\n* **Website Offline**: No URL provided."
    
    # Async Screenshot
    capture_result = await capture_screenshot(website_url)
    if "error" in capture_result:
        logger.warning(f"Visual Analysis Skipped: {capture_result['error']}")
        return f"## Visual Risks\n* **Website Offline**: {capture_result['error']}"

    image_b64 = capture_result["image_b64"]
    llm_vision = get_llm(temperature=0)
    
    formatted_prompt = prompt_template.format(company_name=company_name, website_url=website_url)
    message = HumanMessage(content=[
        {"type": "text", "text": formatted_prompt},
        {"type": "image_url", "image_url": f"data:image/png;base64,{image_b64}"}
    ])

    try:
        response = await llm_vision.ainvoke([message])
        return response.content
    except Exception as e:
        logger.error(f"Visual Analysis Error: {str(e)}")
        return f"## Visual Analysis Error: {str(e)}"
    
@retry(**RETRY_CONFIG)
async def team_scoring_agent(data_package: dict) -> dict:
    llm = get_llm(temperature=0)
    prompt = PromptTemplate.from_template(TEAM_SCORING_AGENT_PROMPT)
    chain = prompt | llm | JsonOutputParser()
    return await chain.ainvoke({
        "user_json_data": json.dumps(data_package.get("user_data", {}), indent=2),
        "risk_agent_output": str(data_package.get("risk_report", "None")),
        "contradiction_agent_output": str(data_package.get("contradiction_report", "None")),
        "missing_info_output": str(data_package.get("missing_report", "None"))
    })

@retry(**RETRY_CONFIG)
async def problem_scoring_agent(data_package: dict) -> dict:
    llm = get_llm(temperature=0)
    prompt = PromptTemplate.from_template(PROBLEM_SCORING_AGENT_PROMPT)
    chain = prompt | llm | JsonOutputParser()
    
    result = await chain.ainvoke({
        "problem_json": json.dumps(data_package.get("problem_definition", {}), indent=2),
        "missing_report": str(data_package.get("missing_report", "None")),
        "search_json": json.dumps(data_package.get("search_report", {}), indent=2),
        "risk_report": str(data_package.get("risk_report", "None")),
        "contradiction_report": str(data_package.get("contradiction_report", "None"))
    })
    
   
    return result

@retry(**RETRY_CONFIG)
async def product_scoring_agent(data_package: dict) -> dict:
    llm = get_llm(temperature=0)
    prompt = PromptTemplate.from_template(PRODUCT_SCORING_AGENT_PROMPT)
    chain = prompt | llm | JsonOutputParser()
    
    result = await chain.ainvoke({
        "current_date": datetime.now().strftime("%Y-%m-%d"),
        "internal_data": json.dumps(data_package.get("internal_data", {}), indent=2),
        "contradiction_report": str(data_package.get("contradiction_report", "None")),
        "risk_report": str(data_package.get("risk_report", "None")),
        "tech_stack_report": str(data_package.get("tech_stack_report", "None")),
        "visual_analysis_report": str(data_package.get("visual_analysis_report", "None"))
    })
    return result
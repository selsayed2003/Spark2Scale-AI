import json
<<<<<<< HEAD:app/graph/nodes/evaluation_agent/schema.py
from pydantic import BaseModel, Field
from typing import List

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

class Plan(BaseModel):
    steps: List[str] = Field(..., description="Short ordered steps for solving the task.")
    key_risks: List[str] = Field(..., description="Major risks/unknowns that should be addressed.")
    desired_output_structure: List[str] = Field(..., description="Headings to include in final answer.")
=======
import os
import time
import asyncio
import aiohttp
from datetime import datetime
from dotenv import load_dotenv
import builtwith
from urllib.parse import urlparse

# LangChain & AI Imports
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

# Load Environment Variables
load_dotenv()

# --- CONFIGURATION ---
RETRY_CONFIG = {
    "wait": wait_exponential(multiplier=2, min=10, max=120),
    "stop": stop_after_attempt(20),
    "retry": retry_if_exception_type((ResourceExhausted, ChatGoogleGenerativeAIError))
}

# --- TOOLS & AGENTS ---

@retry(**RETRY_CONFIG)
async def contradiction_check(data: dict, agent_prompt: str) -> str:
    '''Uses Google Gemini Flash to detect logical contradictions within the provided startup data.
    '''
    print("🤖 Running Contradiction Check...")
    llm_flash = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0, 
        google_api_key=os.environ.get("GEMINI_API_KEY") 
    )

    prompt = PromptTemplate.from_template(agent_prompt)
    
    try:
        chain = prompt | llm_flash | StrOutputParser()
        result = await chain.ainvoke({
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "json_data": json.dumps(data, indent=2) 
        })
        print("   -> Contradiction Check Done.")
        return result
    except Exception as e:
        print(f"   -> Contradiction Check Failed: {e}")
        return f"Error performing Contradiction Check: {str(e)}"

@retry(**RETRY_CONFIG)
async def team_risk_check(data: dict, agent_prompt: str) -> str:
    '''Identifies specific investment risks by analyzing the startup data through an AI agent.
    '''
    print("📉 Running Team Risk Check...")
    llm_flash = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0, 
        google_api_key=os.environ.get("GEMINI_API_KEY")
    )

    prompt = PromptTemplate.from_template(agent_prompt)

    try:
        chain = prompt | llm_flash | StrOutputParser()
        result = await chain.ainvoke({
            "json_data": json.dumps(data, indent=2)
        })
        print("   -> Team Risk Check Done.")
        return result
    except Exception as e:
        print(f"   -> Team Risk Check Failed: {e}")
        return f"Error performing Risk Check: {str(e)}"
    
@retry(**RETRY_CONFIG)
async def loaded_risk_check_with_search(problem_data: dict, search_results: dict, agent_prompt: str) -> str:
    '''Analyzes problem statement risks by cross-referencing internal claims with external search results.
    '''
    print("🛡️  Running Loaded Risk Check...")
    llm_flash = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=os.environ.get("GEMINI_API_KEY")
    )

    prompt = PromptTemplate.from_template(agent_prompt)

    try:
        chain = prompt | llm_flash | StrOutputParser()
        result = await chain.ainvoke({
            "internal_json": json.dumps(problem_data, indent=2),
            "external_search_json": json.dumps(search_results, indent=2)
        })
        print("   -> Loaded Risk Check Done.")
        return result
    except Exception as e:
        print(f"   -> Loaded Risk Check Failed: {e}")
        return f"## Problem Risks\n* **System Error**: Could not perform risk check.\n  * *Evidence:* {str(e)}"


@retry(**RETRY_CONFIG)
async def verify_problem_claims(problem_statement: str, target_audience: str) -> dict:
    '''Performs a targeted web search using Serper API to verify the validity of a startup's problem claim.
    '''
    print("🔎 Verifying Problem Claims...")
    api_key = os.environ.get("SERPER_API_KEY")
    google_api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        return {"error": "Missing SERPER_API_KEY."}

    # STEP 1: GENERATE QUERIES
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=google_api_key)
    
    query_gen_prompt = f"""
    You are a Search Expert. Convert this startup problem into 3 specific Google search queries.
    
    Target Audience: {target_audience}
    Problem: {problem_statement}
    
    Output JSON ONLY:
    {{
        "pain_query": "Find forum discussions (Reddit/Quora) using specific keywords from the problem.",
        "symptom_query": "Find discussions describing the FEELING of the problem using SIMPLE, NON-TECHNICAL words.",
        "solution_query": "Find existing competitors or software solutions."
    }}
    """
    
    try:
        query_response = await llm.ainvoke(query_gen_prompt)
        clean_json = query_response.content.replace("```json", "").replace("```", "").strip()
        queries = json.loads(clean_json)
        
        pain_q = queries.get("pain_query", f"{problem_statement} reddit")
        symptom_q = queries.get("symptom_query", f"{target_audience} struggle reddit")
        sol_q = queries.get("solution_query", f"solution for {problem_statement}")
    except Exception:
        pain_q = f"{target_audience} {problem_statement} reddit"
        symptom_q = f"{target_audience} struggle help forum"
        sol_q = f"best solution for {problem_statement}"

    # STEP 2: EXECUTE SEARCH
    url = "https://google.serper.dev/search"
    headers = {'X-API-KEY': api_key, 'Content-Type': 'application/json'}
    
    results_report = {
        "generated_queries": { 
            "technical_pain": pain_q, 
            "human_symptom": symptom_q, 
            "competitor": sol_q 
        }, 
        "pain_validation_search": [], 
        "competitor_search": []
    }

    async def run_search(session, query):
        try:
            async with session.post(url, headers=headers, json={"q": query, "num": 4}) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [
                        {"title": r.get("title"), "link": r.get("link"), "snippet": r.get("snippet")}
                        for r in data.get("organic", [])
                    ]
        except: 
            return []
        return []

    async with aiohttp.ClientSession() as session:
        # Run searches in parallel
        pain_res, symptom_res, sol_res = await asyncio.gather(
            run_search(session, pain_q),
            run_search(session, symptom_q),
            run_search(session, sol_q)
        )
        
        results_report["pain_validation_search"].extend(pain_res)
        results_report["pain_validation_search"].extend(symptom_res)
        results_report["competitor_search"] = sol_res
    
    print("   -> Problem Claims Verified.")
    return results_report

@retry(**RETRY_CONFIG)
async def tech_stack_detective(url: str):
    """
    Identifies if a site is No-Code (Canva, Bubble, Webflow) or Custom Code.
    Now includes a 'Domain Check' to catch subdomains like 'my.canva.site'.
    """
    print(f"🛠️ Analyzing tech stack of {url}...")
    
    # --- 1. SMART DOMAIN CHECK (Fastest Method) ---
    domain = urlparse(url).netloc.lower()
    
    known_subdomains = {
        "canva.site": "Canva",
        "wixsite.com": "Wix",
        "bubbleapps.io": "Bubble",
        "framer.website": "Framer",
        "myshopify.com": "Shopify",
        "wordpress.com": "WordPress",
        "webflow.io": "Webflow",
        "softr.app": "Softr",
        "glideapp.io": "Glide",
        "carrd.co": "Carrd"
    }
    
    for sub, platform in known_subdomains.items():
        if sub in domain:
            return {
                "technologies_found": [platform, "Subdomain Identified"],
                "is_no_code": True,
                "verdict": f"No-Code ({platform})",
                "status": "Success",
                "evidence": f"URL contains '{sub}'"
            }

    # --- 2. DEEP TECH SCAN (If domain check passed) ---
    try:
        # builtwith is blocking, but it's fast enough or we could wrap it in to_thread if needed.
        # For strict async compliance with minimal blocking, we can use asyncio.to_thread
        tech_data = await asyncio.to_thread(builtwith.parse, url)
        
        detected_tech = []
        is_no_code = False
        no_code_platform = None
        
        # Flatten the dictionary
        for category, items in tech_data.items():
            for item in items:
                detected_tech.append(item)
                
        # Expanded No-Code List
        no_code_signals = [
            "Bubble", "Webflow", "Wix", "Squarespace", 
            "WordPress", "Framer", "Shopify", "Weebly", "Carrd",
            "Canva", "Tilda", "Kajabi", "Teachable", "Thinkific", 
            "Ghost", "Substack", "Gumroad", "Notion"
        ]
        
        for tech in detected_tech:
            for signal in no_code_signals:
                if signal.lower() in tech.lower():
                    is_no_code = True
                    no_code_platform = signal
                    break
            if is_no_code:
                break

        # 3. Formulate Verdict
        if is_no_code:
            verdict = f"Likely No-Code ({no_code_platform})"
        else:
            verdict = "Custom / Standard Stack"
        
        return {
            "technologies_found": detected_tech,
            "is_no_code": is_no_code,
            "verdict": verdict,
            "status": "Success",
            "evidence": "Tech Stack Fingerprint"
        }
        
    except Exception as e:
        return {
            "error": f"Tech detection failed: {str(e)}", 
            "status": "Failed"
        }

@retry(**RETRY_CONFIG)
async def analyze_visuals_with_langchain(company_name, website_url, prompt_template):
    """
    Captures a screenshot and sends it + the text prompt to Gemini Vision.
    """
    
    if not website_url:
        return "## Visual Risks\n* **Website Offline**: No URL provided."
    
    # Await the async capture
    capture_result = await capture_screenshot(website_url)
    
    if "error" in capture_result:
        return f"## Visual Risks\n* **Website Offline**: {capture_result['error']}"

    image_b64 = capture_result["image_b64"]

    # 2. Prepare the Model
    llm_vision = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        temperature=0,
        google_api_key=os.environ.get("GEMINI_API_KEY")
    )

    # 3. Format the Text Prompt (Inject variables)
    formatted_prompt_text = prompt_template.format(
        company_name=company_name,
        website_url=website_url
    )

    from langchain_core.messages import HumanMessage
    # 4. Construct the Multimodal Message
    message = HumanMessage(
        content=[
            {"type": "text", "text": formatted_prompt_text},
            {"type": "image_url", "image_url": f"data:image/png;base64,{image_b64}"}
        ]
    )

    # 5. Invoke (Async)
    try:
        response = await llm_vision.ainvoke([message])
        return response.content
    except Exception as e:
        return f"## Visual Analysis Error\n* **AI Processing Failed**: {str(e)}"
    
@retry(**RETRY_CONFIG)
async def team_scoring_agent(data_package: dict) -> dict:
    '''Synthesizes risk reports, contradiction checks, and missing info to assign a final team investment score.
    '''
    llm_flash = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0, 
        google_api_key=os.environ.get("GEMINI_API_KEY")
    )

    prompt = PromptTemplate.from_template(TEAM_SCORING_AGENT_PROMPT)

    try:
        chain = prompt | llm_flash | JsonOutputParser()
        
        result_dict = await chain.ainvoke({
            "user_json_data": json.dumps(data_package.get("user_data", {}), indent=2),
            "risk_agent_output": str(data_package.get("risk_report", "None")),
            "contradiction_agent_output": str(data_package.get("contradiction_report", "None")),
            "missing_info_output": str(data_package.get("missing_report", "None"))
        })
        return result_dict
    except Exception as e:
        return {"result": f"System Error: {str(e)}"}

@retry(**RETRY_CONFIG)
async def problem_scoring_agent(data_package: dict) -> str:
    '''Synthesizes various problem-related reports to assign a final qualitative and quantitative score.
    '''
    llm_flash = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0, 
        google_api_key=os.environ.get("GEMINI_API_KEY")
    )

    prompt = PromptTemplate.from_template(PROBLEM_SCORING_AGENT_PROMPT)
    chain = prompt | llm_flash | JsonOutputParser()
    
    result_dict = await chain.ainvoke({
        "problem_json": json.dumps(data_package.get("problem_definition", {}), indent=2),
        "missing_report": str(data_package.get("missing_report", "None")),
        "search_json": json.dumps(data_package.get("search_report", {}), indent=2),
        "risk_report": str(data_package.get("risk_report", "None")),
        "contradiction_report": str(data_package.get("contradiction_report", "None"))
    })

    evidence_formatted = "\n".join([f"- {e}" for e in result_dict.get('evidence_used', [])])
    
    final_text = (
        f"{result_dict.get('title', 'Problem Evaluation')}\n"
        f"Score: {result_dict.get('score', 'N/A')} - {result_dict.get('rubric_definition', '')}\n"
        f"Confidence: {result_dict.get('confidence_level', 'Unknown')}\n\n"
        f"Explanation:\n{result_dict.get('explanation', 'No explanation.')}\n\n"
        f"Key Evidence:\n{evidence_formatted}"
    )
    return final_text

@retry(**RETRY_CONFIG)
async def product_scoring_agent(data_package: dict) -> str:
    '''Synthesizes product reports to assign a final score (No extra tools required).'''
    
    # 1. Setup LLM
    llm_flash = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=os.environ.get("GEMINI_API_KEY")
    )

    # 2. Define Prompt
    prompt = PromptTemplate(
        template=PRODUCT_SCORING_AGENT_PROMPT,
        input_variables=[
            "current_date",
            "internal_data", 
            "contradiction_report", 
            "risk_report", 
            "tech_stack_report", 
            "visual_analysis_report"
        ]
    )
    today_str = datetime.now().strftime("%Y-%m-%d")

    # 3. Execution Chain
    chain = prompt | llm_flash | JsonOutputParser()
    
    try:
        # 4. Invoke (Removed ocean_meter_report)
        result_dict = await chain.ainvoke({
            "current_date": today_str,
            "internal_data": json.dumps(data_package.get("internal_data", {}), indent=2),
            "contradiction_report": str(data_package.get("contradiction_report", "None")),
            "risk_report": str(data_package.get("risk_report", "None")), # LLM reads this to decide Ocean Type
            "tech_stack_report": str(data_package.get("tech_stack_report", "None")),
            "visual_analysis_report": str(data_package.get("visual_analysis_report", "None"))
        })

        # 5. Format Output
        red_flags_list = result_dict.get('red_flags', [])
        formatted_flags = "\n".join([f"🚩 {flag}" for flag in red_flags_list]) if red_flags_list else "✅ No critical flags."

        score = result_dict.get('score', 0)
        rubric_map = {
            0: "No Product / Vaporware",
            1: "Me-too Solution",
            2: "Incremental Improvement",
            3: "Clear Value (Pre-Seed Bar)",
            4: "Non-Obvious / 10x (Seed Bar)",
            5: "Breakthrough / Defensible Moat"
        }
        
        final_text = (
            f"🎯 **Product & Solution Evaluation**\n"
            f"**Score:** {score}/5 - {rubric_map.get(score, '')}\n"
            f"**Confidence:** {result_dict.get('confidence_level', 'Unknown')}\n\n"
            
            f"**🌊 Ocean Analysis (AI Derived):**\n"
            f"{result_dict.get('ocean_analysis', 'Not analyzed.')}\n\n"
            
            f"**📝 Justification:**\n"
            f"{result_dict.get('justification', 'No justification provided.')}\n\n"
            
            f"**⚠️ Red Flags:**\n"
            f"{formatted_flags}"
        )
        return final_text

    except Exception as e:
        return f"❌ Scoring Failed: {str(e)}"
>>>>>>> origin/Salma:app/graph/evaluation_agent/schema.py

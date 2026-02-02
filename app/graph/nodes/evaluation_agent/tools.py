import json
import os
import time
import requests
from datetime import datetime
from dotenv import load_dotenv

# LangChain & AI Imports
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import ChatGoogleGenerativeAIError
from google.api_core.exceptions import ResourceExhausted

# Resilience
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Local Imports (Assumed to exist based on your code)
from prompts import (
    CONTRADICTION_TEAM_PROMPT_TEMPLATE, 
    VALUATION_RISK_PROBLEM_PROMPT_TEMPLATE, 
    VALUATION_RISK_TEAM_PROMPT_TEMPLATE, 
    TEAM_SCORING_AGENT_PROMPT, 
    CONTRADICTION_PROBLEM_PROMPT_TEMPLATE, 
    PROBLEM_SCORING_AGENT_PROMPT
)
from helpers import load_schema

# Load Environment Variables
load_dotenv()

# --- CONFIGURATION ---
RETRY_CONFIG = {
    "wait": wait_exponential(multiplier=2, min=10, max=120),
    "stop": stop_after_attempt(20),
    "retry": retry_if_exception_type((ResourceExhausted, ChatGoogleGenerativeAIError))
}

# --- TOOLS & AGENTS ---

def check_missing_fields(data, parent_path=""):
    '''Recursively checks for empty values in a nested JSON object.'''
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

@retry(**RETRY_CONFIG)
def contradiction_check(data: dict, agent_prompt: str) -> str:
    '''Uses Google Gemini Flash to detect logical contradictions in startup data.'''
    llm_flash = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0, 
        google_api_key=os.environ.get("GEMINI_API_KEY") 
    )

    prompt = PromptTemplate.from_template(agent_prompt)
    
    try:
        chain = prompt | llm_flash | StrOutputParser()
        result = chain.invoke({
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "json_data": json.dumps(data, indent=2) 
        })
        return result
    except Exception as e:
        return f"Error performing Contradiction Check: {str(e)}"

@retry(**RETRY_CONFIG)
def risk_check(data: dict, agent_prompt: str) -> str:
    '''Identifies specific investment risks.'''
    llm_flash = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0, 
        google_api_key=os.environ.get("GEMINI_API_KEY")
    )

    prompt = PromptTemplate.from_template(agent_prompt)

    try:
        chain = prompt | llm_flash | StrOutputParser()
        result = chain.invoke({
            "json_data": json.dumps(data, indent=2)
        })
        return result
    except Exception as e:
        return f"Error performing Risk Check: {str(e)}"

@retry(**RETRY_CONFIG)
def verify_problem_claims(problem_statement: str, target_audience: str) -> dict:
    """Performs a targeted web search to verify if a startup's problem is real."""
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
        query_response = llm.invoke(query_gen_prompt)
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

    def run_search(query):
        try:
            resp = requests.post(url, headers=headers, data=json.dumps({"q": query, "num": 4}))
            if resp.status_code == 200:
                return [
                    {"title": r.get("title"), "link": r.get("link"), "snippet": r.get("snippet")}
                    for r in resp.json().get("organic", [])
                ]
        except: 
            return []
        return []

    results_report["pain_validation_search"].extend(run_search(pain_q))
    results_report["pain_validation_search"].extend(run_search(symptom_q))
    results_report["competitor_search"] = run_search(sol_q)

    return results_report

@retry(**RETRY_CONFIG)
def problem_risk_check(problem_data: dict, search_results: dict) -> str:
    """Analyzes problem statement risks cross-referencing search results."""
    llm_flash = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=os.environ.get("GEMINI_API_KEY")
    )

    prompt = PromptTemplate.from_template(VALUATION_RISK_PROBLEM_PROMPT_TEMPLATE)

    try:
        chain = prompt | llm_flash | StrOutputParser()
        result = chain.invoke({
            "internal_json": json.dumps(problem_data, indent=2),
            "external_search_json": json.dumps(search_results, indent=2)
        })
        return result
    except Exception as e:
        return f"## Problem Risks\n* **System Error**: Could not perform risk check.\n  * *Evidence:* {str(e)}"

@retry(**RETRY_CONFIG)
def team_scoring_agent(data_package: dict) -> dict:
    """Synthesizes Team reports to assign a final investment score."""
    llm_flash = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0, 
        google_api_key=os.environ.get("GEMINI_API_KEY")
    )

    prompt = PromptTemplate.from_template(TEAM_SCORING_AGENT_PROMPT)

    try:
        chain = prompt | llm_flash | JsonOutputParser()
        
        result_dict = chain.invoke({
            "user_json_data": json.dumps(data_package.get("user_data", {}), indent=2),
            "risk_agent_output": str(data_package.get("risk_report", "None")),
            "contradiction_agent_output": str(data_package.get("contradiction_report", "None")),
            "missing_info_output": str(data_package.get("missing_report", "None"))
        })
        return result_dict
    except Exception as e:
        return {"result": f"System Error: {str(e)}"}

@retry(**RETRY_CONFIG)
def problem_scoring_agent(data_package: dict) -> str:
    """Synthesizes Problem reports to assign a final score."""
    llm_flash = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0, 
        google_api_key=os.environ.get("GEMINI_API_KEY")
    )

    prompt = PromptTemplate.from_template(PROBLEM_SCORING_AGENT_PROMPT)
    chain = prompt | llm_flash | JsonOutputParser()
    
    result_dict = chain.invoke({
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


# --- MAIN EXECUTION PIPELINE ---
if __name__ == "__main__":
    
    # 1. Load Data
    print("📂 Loading data from schema.json...")
    input_data = load_schema("schema.json")
    
    if not input_data:
        print("❌ Error: Could not load schema.json. Using dummy data.")
        input_data = {"startup_evaluation": {}}
    
    start_time = time.time()
    
    # Check Missing Fields (Global)
    missing_fields_result = check_missing_fields(input_data)

    # =========================================================
    # PHASE 1: TEAM EVALUATION
    # =========================================================
    print("\n" + "="*50)
    print("👥 PHASE 1: TEAM EVALUATION AGENT")
    print("="*50)

    # A. Contradiction Check
    print("\n🤖 Running Team Contradiction Check...")
    try:
        team_contradiction_result = contradiction_check(input_data, agent_prompt=CONTRADICTION_TEAM_PROMPT_TEMPLATE)
        print("   -> Done.")
    except Exception as e:
        print(f"❌ Execution Error (Contradiction): {e}")
        team_contradiction_result = "Error."

    # B. Risk Check
    print("\n📉 Running Team Risk Check...")
    try:
        team_risk_result = risk_check(input_data, agent_prompt=VALUATION_RISK_TEAM_PROMPT_TEMPLATE)
        print("   -> Done.")
    except Exception as e:
        print(f"❌ Execution Error (Risk): {e}")
        team_risk_result = "Error."
    
    # C. Scoring Agent
    print("\n🏆 Running Team Scoring Agent...")
    try:
        team_package = {
            "user_data": input_data,
            "risk_report": team_risk_result,
            "contradiction_report": team_contradiction_result,
            "missing_report": missing_fields_result
        }
        final_team_score = team_scoring_agent(team_package)
        print(json.dumps(final_team_score, indent=2))
    except Exception as e:
        print(f"❌ Execution Error (Team Scoring): {e}")

    # =========================================================
    # PHASE 2: PROBLEM EVALUATION
    # =========================================================
    print("\n" + "="*50)
    print("🧩 PHASE 2: PROBLEM EVALUATION AGENT")
    print("="*50)

    problem_def = input_data.get("startup_evaluation", {}).get("problem_definition", {})
    
    # A. Search Validation
    print("\n🔎 Searching for Evidence (Problem Validation)...")
    if problem_def:
        search_output = verify_problem_claims(
            problem_statement=problem_def.get("problem_statement", ""),
            target_audience=problem_def.get("customer_profile", {}).get("role", "")
        )
        print("   -> Search Complete.")
    else:
        print("⚠️ No problem definition found.")
        search_output = {}

    # B. Risk Check (Problem Specific)
    print("\n📉 Analyzing Problem Risks...")
    try:
        problem_risk_report = problem_risk_check(
            problem_data=problem_def,
            search_results=search_output
        )
        print("   -> Done.")
    except Exception as e:
        problem_risk_report = f"Error: {e}"

    # C. Contradiction Check (Problem Specific)
    print("\n🤖 Running Problem Contradiction Check...")
    try:
        problem_contradiction_result = contradiction_check(input_data, agent_prompt=CONTRADICTION_PROBLEM_PROMPT_TEMPLATE)
        print("   -> Done.")
    except Exception as e:
        print(f"❌ Execution Error (Contradiction): {e}")
        problem_contradiction_result = "Contradiction Check Failed."
    
    # D. Scoring Agent
    print("\n🏆 Running Problem Scoring Agent...")
    try:
        problem_data_package = {
            "problem_definition": problem_def,
            "missing_report": missing_fields_result,
            "search_report": search_output,
            "risk_report": problem_risk_report,
            "contradiction_report": problem_contradiction_result
        }
        final_problem_score = problem_scoring_agent(problem_data_package)
        print(final_problem_score)
    except Exception as e:
        print(f"❌ Execution Error (Problem Scoring): {e}")

    # =========================================================
    # FINISH
    # =========================================================
    end_time = time.time()
    execution_time = end_time - start_time
    print("\n" + "="*50)
    print(f"✅ Pipeline finished in {execution_time:.2f} seconds")
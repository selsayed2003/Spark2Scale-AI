import spacy
from langchain_core.tools import tool
from langchain_google_community import GoogleSearchAPIWrapper
from spacy.cli import download
import json
import os
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from prompts import CONTRADICTION_TEAM_PROMPT_TEMPLATE, VALUATION_RISK_PROBLEM_PROMPT_TEMPLATE, VALUATION_RISK_TEAM_PROMPT_TEMPLATE, SCORING_AGENT_PROMPT
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
load_dotenv()
from helpers import load_schema
import requests

# try:
#     nlp = spacy.load("en_core_web_sm")
# except OSError:                             
#     download("en_core_web_sm")
#     nlp = spacy.load("en_core_web_sm")

# @tool
# def calculate_information_density(text: str):
#     """
#     Calculates the 'Information Density' of a text.
#     A low score indicates ambiguity/fluff. A high score indicates concrete facts.
#     """
#     doc = nlp(text)
    
#     # 1. Identify "Hard Facts" (Entities)

#     fact_types = {"ORG", "GPE", "DATE", "MONEY", "CARDINAL", "PERCENT", "PRODUCT"}
    
#     entities = [ent.text for ent in doc.ents if ent.label_ in fact_types]
    
#     # 2. Identify "Weak Phrases" 

#     weak_phrases = {
#         "aim to", "hope", "believe", "visionary", "disruptive", "passionate",
#         "approximately", "roughly", "trying", "unique", "cutting-edge"
#     }
#     found_weakness = [token.text for token in doc if token.text.lower() in weak_phrases]
    
#     # 3. Calculate Density Score
#     word_count = len(doc)
#     if word_count == 0:
#         return {"score": 0, "status": "Empty Text"}
        
#     # Density = (Facts / Total Words)
#     # Typical "Good" Pitch > 0.10 (1 fact per 10 words)
#     density_score = len(entities) / word_count
    
#     return {
#         "density_score": round(density_score, 3), # Higher is better
#         "is_ambiguous": density_score < 0.08,     # Threshold for "Fluff"
#         "fact_count": len(entities),
#         "word_count": word_count,
#         "extracted_facts": entities[:5],          # Return top 5 facts for LLM context
#         "flagged_weak_phrases": list(set(found_weakness))
#     }

# @tool
# def verify_founder_claims(query: str):
#     """
#     Searches Google to verify founder claims. 
#     Use specific queries like 'Name Company Role'.
#     """
#     search = GoogleSearchAPIWrapper(k=3) # Top 3 results
#     try:
#         results = search.run(query)
#         if not results or "No good Google Search Result" in results:
#             return "No verification found online."
#         return results
#     except Exception as e:
#         return f"Search Error: {e}"
    

# @tool
def check_missing_fields(data, parent_path=""):
    '''Recursively checks for empty values in a nested JSON object.

    This function traverses the input dictionary or list to identify fields 
    that are None, empty strings (""), empty lists ([]), or empty dictionaries ({}).

    Params:
        data - The parsed JSON object (dict or list) to validate.
        parent_path - The dot-notation path to the current field during recursion. Defaults to "".

    Returns:
        list[str] - A list of error strings identifying the specific path of missing data.

    Raises:
        RecursionError: raises if the JSON structure is too deep (exceeds recursion limit).
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


# @tool
def contradiction_check(data: dict) -> str:
    '''Uses Google Gemini Flash to detect logical contradictions in startup data.

    This function first validates the input against 'schema.json'.
    If valid, it identifies logical impossibilities (Timeline, Financial, Consistency).

    Params:
        data - The full, flattened JSON object representing the startup profile.

    Returns:
        str - A formatted list of contradictions (bullet points) or "No contradictions found."

    Raises:
        ValidationError: raises if the input data does not match schema.json.
        GoogleAPIError: raises if the Gemini API key is missing.
    '''
    
    # 1. SETUP MODEL
    llm_flash = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0, 
        google_api_key=os.environ.get("GEMINI_API_KEY") 
    )

    # 2. CREATE PROMPT OBJECT
    prompt = PromptTemplate.from_template(CONTRADICTION_TEAM_PROMPT_TEMPLATE)
    
    # 3. EXECUTE CHAIN
    try:
        chain = prompt | llm_flash | StrOutputParser()
        
        result = chain.invoke({
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "json_data": json.dumps(data, indent=2) 
        })
        return result

    except Exception as e:
        return f"Error performing Contradiction Check: {str(e)}"

#@tool
def risk_check(data: dict, agent_prompt: str) -> str:
    '''Identifies specific investment risks using Berkus and YC methodologies.

    This function uses an LLM to critique the startup's founder profile, 
    cap table, execution speed, and market insight to find reasons an investor might say "No".

    Params:
        data - The full, flattened JSON object representing the startup profile.

    Returns:
        str - A formatted list of risks (bullet points) generated by the LLM.

    Raises:
        GoogleAPIError: raises if the API key is invalid.
    '''
    
    # 1. SETUP MODEL
    llm_flash = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0, 
        google_api_key=os.environ.get("GEMINI_API_KEY")
    )

    prompt = PromptTemplate.from_template(agent_prompt)

    # 3. EXECUTE CHAIN
    try:
        chain = prompt | llm_flash | StrOutputParser()
        
        result = chain.invoke({
            "json_data": json.dumps(data, indent=2)
        })
        return result

    except Exception as e:
        return f"Error performing Risk Check: {str(e)}"
    

# @tool
def problem_risk_check(problem_data: dict, search_results: dict) -> str:
    """
    Analyzes the startup's problem statement for critical risks (Market Education, Timing, Clarity).
    Crucially, it cross-references the founder's claims with real-world Web Search results 
    to validate if the pain is real or imaginary.

    Params:
        problem_data (dict): Section 3 of the schema (Problem Definition).
        search_results (dict): Output from the 'verify_problem_claims' tool.

    Returns:
        str: A bulleted list of verified risks with evidence.
    """

    # 1. SETUP MODEL
    llm_flash = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0,
        google_api_key=os.environ.get("GEMINI_API_KEY")
    )

    

    prompt = PromptTemplate.from_template(VALUATION_RISK_PROBLEM_PROMPT_TEMPLATE)

    # 3. EXECUTE CHAIN
    try:
        chain = prompt | llm_flash | StrOutputParser()

        # Format inputs as strings
        internal_str = json.dumps(problem_data, indent=2)
        external_str = json.dumps(search_results, indent=2)

        result = chain.invoke({
            "internal_json": internal_str,
            "external_search_json": external_str
        })
        return result

    except Exception as e:
        return f"## Problem Risks\n* **System Error**: Could not perform risk check.\n  * *Evidence:* {str(e)}"
# @tool
def final_scoring_agent(data_package: dict) -> dict:
    """
    Synthesizes reports from Risk, Contradiction, and Missing Info agents
    to assign a final investment score.

    Params:
        data_package (dict): A dictionary containing:
            - 'user_data': The raw startup JSON.
            - 'risk_report': String output from risk_check.
            - 'contradiction_report': String output from contradiction_check.
            - 'missing_report': List or String from check_missing_fields.

    Returns:
        dict: A JSON object containing:
            - 'title': "Founder Market Fit Evaluation"
            - 'score': "X.X / 5.0"
            - 'explanation': Synthesized reasoning including contradictions/missing info.
            - 'risks': List of key risks identified.
    """
    
    # 1. SETUP MODEL
    llm_flash = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0, 
        google_api_key=os.environ.get("GEMINI_API_KEY")
    )


    prompt = PromptTemplate.from_template(SCORING_AGENT_PROMPT)

    # 3. EXECUTE CHAIN
    try:
        chain = prompt | llm_flash | JsonOutputParser()
        
        # Safe extraction of inputs
        user_data_str = json.dumps(data_package.get("user_data", {}), indent=2)
        risk_out = str(data_package.get("risk_report", "None"))
        contra_out = str(data_package.get("contradiction_report", "None"))
        missing_out = str(data_package.get("missing_report", "None"))

        result_dict = chain.invoke({
            "user_json_data": user_data_str,
            "risk_agent_output": risk_out,
            "contradiction_agent_output": contra_out,
            "missing_info_output": missing_out
        })

        
        
        return result_dict

    except Exception as e:
        return {
           
            "result": f"System Error: {str(e)}",
          
        }


# @tool

def verify_problem_claims(problem_statement: str, target_audience: str) -> dict:
    """
    Performs a targeted web search to verify if a startup's problem is real.
    
    UPDATED LOGIC:
    Generates 3 types of queries to ensure we find "Symptom" discussions, 
    even if the founder uses complex technical jargon.
    """
    
    api_key = os.environ.get("SERPER_API_KEY")
    google_api_key = os.environ.get("GEMINI_API_KEY")
    
    if not api_key:
        return {"error": "Missing SERPER_API_KEY."}

    # --- STEP 1: GENERATE 3 OPTIMIZED QUERIES ---
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=google_api_key)
    
    query_gen_prompt = f"""
    You are a Search Expert. Convert this startup problem into 3 specific Google search queries.
    
    Target Audience: {target_audience}
    Problem: {problem_statement}
    
    Output JSON ONLY:
    {{
        "pain_query": "Find forum discussions (Reddit/Quora) using specific keywords from the problem.",
        "symptom_query": "Find discussions describing the FEELING of the problem using SIMPLE, NON-TECHNICAL words. (e.g. if problem is 'Alpha Wave Optimization', search for 'Brain fog afternoon crash').",
        "solution_query": "Find existing competitors or software solutions."
    }}
    """
    
    try:
        # Generate the queries
        query_response = llm.invoke(query_gen_prompt)
        
        # Parse the JSON output
        clean_json = query_response.content.replace("```json", "").replace("```", "").strip()
        queries = json.loads(clean_json)
        
        pain_q = queries.get("pain_query", f"{problem_statement} reddit")
        symptom_q = queries.get("symptom_query", f"{target_audience} struggle reddit")
        sol_q = queries.get("solution_query", f"solution for {problem_statement}")
        
    except Exception as e:
        # Fallback if LLM fails
        pain_q = f"{target_audience} {problem_statement} reddit"
        symptom_q = f"{target_audience} struggle help forum"
        sol_q = f"best solution for {problem_statement}"

    # --- STEP 2: EXECUTE SERPER SEARCH ---
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

    # Helper function to run search
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

    # Search 1: Technical Pain (Original)
    results_report["pain_validation_search"].extend(run_search(pain_q))
    
    # Search 2: Human Symptom (NEW - This fixes the "Uneducated" Risk)
    # We append these results to 'pain_validation_search' so the Risk Agent sees them.
    results_report["pain_validation_search"].extend(run_search(symptom_q))

    # Search 3: Competitors
    results_report["competitor_search"] = run_search(sol_q)

    return results_report


# --- TEST BLOCK ---
if __name__ == "__main__":
    
    # 1. Load Data
    print("Loading data from schema.json...")
    input_data = load_schema("schema.json")
    
    if not input_data:
        print("❌ Error: Could not load schema.json. Using dummy data.")
        input_data = {"startup_evaluation": {}} # Dummy fallback

    # # ---------------------------------------------------------
    # # TEST 1: Contradiction Check (Returns Markdown String)
    # # ---------------------------------------------------------
    # print("\n" + "="*40)
    # print("🤖 RUNNING CONTRADICTION CHECK")
    # print("="*40)
    
    # try:
    #     # Note: If running locally without LangGraph, we call the function directly
    #     contradiction_result = contradiction_check(input_data)
    #     print(contradiction_result)

    # except Exception as e:
    #     print(f"❌ Execution Error (Contradiction): {e}")

    # # ---------------------------------------------------------
    # # TEST 2: Risk Check (Returns Markdown String)
    # # ---------------------------------------------------------
    # print("\n" + "="*40)
    # print("📉 RUNNING RISK CHECK")
    # print("="*40)

    # try:
    #     risk_result = risk_check(input_data, agent_prompt=VALUATION_RISK_TEAM_PROMPT_TEMPLATE)
    #     print(risk_result)

    # except Exception as e:
    #     print(f"❌ Execution Error (Risk): {e}")
    
    # # ---------------------------------------------------------
    # # TEST 3: Scoring Agent
    # # ---------------------------------------------------------
    # print("\n" + "="*40)
    # print("🏆 RUNNING FINAL SCORING AGENT")
    # print("="*40)

    # # Mock Data Package (Simulating what the previous nodes produced)
    # test_package = {
    #     "user_data": input_data,
    #     "risk_report": "## Risks\n* **Solo Founder Risk**: Tarek owns 100% equity.\n* **Tech Risk**: No CTO.",
    #     "contradiction_report": "No contradictions found.",
    #     "missing_report": ["Missing Value: 'linkedin_url' is empty."]
    # }

    # try:
    #     final_score = final_scoring_agent(test_package)
    #     print(json.dumps(final_score, indent=2)) 
        
    # except Exception as e:
    #     print(f"❌ Execution Error: {e}")
    # Extracting arguments from your loaded JSON data
    problem_def = input_data["startup_evaluation"]["problem_definition"]

    # 2. RUN SEARCH (The Reality Check)
    print("🔎 Searching for evidence...")
    search_output = verify_problem_claims(
        problem_statement=problem_def["problem_statement"],
        target_audience=problem_def["customer_profile"]["role"]
    )
    print(json.dumps(search_output, indent=2))

    # 3. RUN RISK CHECK (The Analysis)
    print("📉 Analyzing Risks...")
    risk_report = problem_risk_check(
        problem_data=problem_def,
        search_results=search_output
    )

    print(risk_report)
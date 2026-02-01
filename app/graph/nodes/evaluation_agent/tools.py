import spacy
from langchain_core.tools import tool
from langchain_google_community import GoogleSearchAPIWrapper
from spacy.cli import download
import json
import os
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from prompts import CONTRADICTION_PROMPT_TEMPLATE, VALUATION_RISK_PROMPT_TEMPLATE, SCORING_AGENT_PROMPT
from langchain_core.prompts import PromptTemplate
from dotenv import load_dotenv
load_dotenv()
from helpers import load_schema

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
    prompt = PromptTemplate.from_template(CONTRADICTION_PROMPT_TEMPLATE)
    
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
def risk_check(data: dict) -> str:
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

    prompt = PromptTemplate.from_template(VALUATION_RISK_PROMPT_TEMPLATE)

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
        
        user_data_str = json.dumps(data_package.get("user_data", {}), indent=2)
        risk_out = str(data_package.get("risk_report", "None"))
        contra_out = str(data_package.get("contradiction_report", "None"))
        missing_out = str(data_package.get("missing_report", "None"))

        result = chain.invoke({
            "user_json_data": user_data_str,
            "risk_agent_output": risk_out,
            "contradiction_agent_output": contra_out,
            "missing_info_output": missing_out
        })
        return result

    except Exception as e:
        return {
           
            "result": f"System Error: {str(e)}",
          
        }

# --- TEST BLOCK ---
if __name__ == "__main__":
    
    # 1. Load Data
    print("Loading data from schema.json...")
    input_data = load_schema("schema.json")
    
    if not input_data:
        print("❌ Error: Could not load schema.json. Using dummy data.")
        input_data = {"startup_evaluation": {}} # Dummy fallback

    # ---------------------------------------------------------
    # TEST 1: Contradiction Check (Returns Markdown String)
    # ---------------------------------------------------------
    print("\n" + "="*40)
    print("🤖 RUNNING CONTRADICTION CHECK")
    print("="*40)
    
    try:
        # Note: If running locally without LangGraph, we call the function directly
        contradiction_result = contradiction_check(input_data)
        print(contradiction_result)

    except Exception as e:
        print(f"❌ Execution Error (Contradiction): {e}")

    # ---------------------------------------------------------
    # TEST 2: Risk Check (Returns Markdown String)
    # ---------------------------------------------------------
    print("\n" + "="*40)
    print("📉 RUNNING RISK CHECK")
    print("="*40)

    try:
        risk_result = risk_check(input_data)
        print(risk_result)

    except Exception as e:
        print(f"❌ Execution Error (Risk): {e}")
    
    # ---------------------------------------------------------
    # TEST 3: Scoring Agent
    # ---------------------------------------------------------
    print("\n" + "="*40)
    print("🏆 RUNNING FINAL SCORING AGENT")
    print("="*40)

    # Mock Data Package (Simulating what the previous nodes produced)
    test_package = {
        "user_data": input_data,
        "risk_report": "## Risks\n* **Solo Founder Risk**: Tarek owns 100% equity.\n* **Tech Risk**: No CTO.",
        "contradiction_report": "No contradictions found.",
        "missing_report": ["Missing Value: 'linkedin_url' is empty."]
    }

    try:
        final_score = final_scoring_agent(test_package)
        print(json.dumps(final_score, indent=2)) 
        
    except Exception as e:
        print(f"❌ Execution Error: {e}")
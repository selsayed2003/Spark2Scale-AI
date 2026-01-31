import spacy
from langchain_core.tools import tool
from langchain_google_community import GoogleSearchAPIWrapper
from spacy.cli import download
import json
import os
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import JsonOutputParser
from prompts import CONTRADICTION_PROMPT_TEMPLATE
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
    """Recursively checks for empty values in a nested JSON object.

    This function traverses the input dictionary or list to identify fields 
    that are None, empty strings (""), empty lists ([]), or empty dictionaries ({}).

    Args:
        data (dict | list): The parsed JSON object to validate. This typically 
            represents the startup evaluation schema (e.g., founder profiles, metrics).
        parent_path (str, optional): The dot-notation path to the current 
            field during recursion (used internally). Defaults to "".

    Returns:
        list[str]: A list of error messages. Each message specifies the 
            dot-notation path of the field that is missing a value.
            Returns an empty list if no missing fields are found.
            
    Example:
        >>> check_missing_fields({"name": "", "age": 30})
        ["Missing Value: Field 'name' is empty."]
    """
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
def contradiction_check(data: dict) -> dict:
    """
    Uses Google Gemini Flash to detect logical contradictions. 
    Input should be the full flattened JSON of the startup profile.
    """
    
    # 1. SETUP MODEL
    # Using gemini-1.5-flash for speed/cost.
    llm_flash = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0, 
        google_api_key=os.environ.get("GEMINI_API_KEY")
    )

    # 2. CREATE PROMPT OBJECT
    # Uses the template imported from prompts.py
    prompt = PromptTemplate.from_template(CONTRADICTION_PROMPT_TEMPLATE)
    
    # 3. EXECUTE CHAIN
    try:
        chain = prompt | llm_flash | JsonOutputParser()
        
        # Convert dict to string so the LLM can read the structure
        # We pass exactly the variables the prompt expects: {current_date} and {json_data}
        result = chain.invoke({
            "current_date": datetime.now().strftime("%Y-%m-%d"),
            "json_data": json.dumps(data, indent=2) 
        })
        return result

    except Exception as e:
        return {
            "error": f"Contradiction Check Failed: {e}",
            "contradiction_found": False
        }


# --- TEST BLOCK ---
if __name__ == "__main__":
    
   
    
    print("Loading data from schema.json...")
    input_data = load_schema("schema.json")
    
    if not input_data:
        print("❌ Error: Could not load schema.json. Using dummy data.")
        input_data = {"startup_evaluation": {}} # Dummy fallback

    # 2. Run the check
    print("\nRunning Contradiction Check...")
    try:
        # Call directly for local testing
        result = contradiction_check(input_data)
        
        # 3. Print Results
        if "error" in result:
            print(f"❌ CRITICAL ERROR: {result['error']}")

        elif result.get("contradiction_found"):
            print(f"⚠️ Contradictions Found (Severity: {result.get('severity_score')})")
            checks = result.get("checks", {})
            for check_name, details in checks.items():
                if details["status"] == "FAIL":
                    print(f"   ❌ {check_name}: {details['reason']}")
                else:
                    print(f"   ✅ {check_name}: PASS")
        else:
            print("✅ No Logic Contradictions Found.")

    except Exception as e:
        print(f"❌ Execution Error: {e}")
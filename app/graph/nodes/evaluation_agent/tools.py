import spacy
from langchain_core.tools import tool
from langchain_google_community import GoogleSearchAPIWrapper
from spacy.cli import download

try:
    nlp = spacy.load("en_core_web_sm")
except OSError:                             
    download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

@tool
def calculate_information_density(text: str) -> dict:
    """
    Calculates the 'Information Density' of a text.
    A low score indicates ambiguity/fluff. A high score indicates concrete facts.
    """
    doc = nlp(text)
    
    # 1. Identify "Hard Facts" (Entities)

    fact_types = {"ORG", "GPE", "DATE", "MONEY", "CARDINAL", "PERCENT", "PRODUCT"}
    
    entities = [ent.text for ent in doc.ents if ent.label_ in fact_types]
    
    # 2. Identify "Weak Phrases" 
  
    weak_phrases = {
        "aim to", "hope", "believe", "visionary", "disruptive", "passionate",
        "approximately", "roughly", "trying", "unique", "cutting-edge"
    }
    found_weakness = [token.text for token in doc if token.text.lower() in weak_phrases]
    
    # 3. Calculate Density Score
    word_count = len(doc)
    if word_count == 0:
        return {"score": 0, "status": "Empty Text"}
        
    # Density = (Facts / Total Words)
    # Typical "Good" Pitch > 0.10 (1 fact per 10 words)
    density_score = len(entities) / word_count
    
    return {
        "density_score": round(density_score, 3), # Higher is better
        "is_ambiguous": density_score < 0.08,     # Threshold for "Fluff"
        "fact_count": len(entities),
        "word_count": word_count,
        "extracted_facts": entities[:5],          # Return top 5 facts for LLM context
        "flagged_weak_phrases": list(set(found_weakness))
    }

@tool
def verify_founder_claims(query: str) -> str:
    """
    Searches Google to verify founder claims. 
    Use specific queries like 'Name Company Role'.
    """
    search = GoogleSearchAPIWrapper(k=3) # Top 3 results
    try:
        results = search.run(query)
        if not results or "No good Google Search Result" in results:
            return "No verification found online."
        return results
    except Exception as e:
        return f"Search Error: {e}"
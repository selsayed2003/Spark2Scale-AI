import json
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from app.core.llm import get_llm

# --- THE WRITER PROMPT ---
REPORT_WRITER_PROMPT = """
You are a Senior Venture Capital Partner writing an investment memo for a founder. 
Your goal is to be **constructive, professional, and empathetic**, but brutally honest about the data.

### INPUT DATA (Strict Grounding):
{json_data}

### INSTRUCTIONS:
1. **Analyze the Data:** Look at the scores (0-5) and red flags in the JSON.
2. **Executive Summary:** Write a high-level paragraph summarizing the startup's status. 
   - Highlight the biggest strength (e.g., "Problem" score 3/5).
   - Gently but clearly state the deal-breakers (e.g., "Team" score 0/5, "Traction" 0/5).
   - Use phrases like "Our analysis indicates..." or "The data suggests..."
3. **Agent Deep Dives:** For each section (Team, Market, etc.), write a **1-2 sentence "Insight"**.
   - Do NOT just list the flags (we have a list for that).
   - Synthesize *why* the score is low/high.
   - Example: Instead of "Start date is in future," write "The timeline data suggests the project is in a conceptual phase, as execution metrics cannot be verified against a future start date."
4. **Action Plan:** Create 3 specific, prioritized next steps based on the red flags.

### OUTPUT FORMAT (JSON ONLY):
{{
    "executive_summary": "...",
    "agent_insights": {{
        "team": "...",
        "problem": "...",
        "market": "...",
        "traction": "...",
        "business": "...",
        "gtm": "...",
        "vision": "...",
        "operations": "...",
        "product": "..."
    }},
    "action_plan": [
        "Step 1: ...",
        "Step 2: ...",
        "Step 3: ..."
    ]
}}
"""

async def write_professional_report(raw_data: dict) -> dict:
    """
    Uses an LLM to synthesize the raw agent outputs into a cohesive narrative.
    """
    try:
        # 1. Setup LLM
        llm = get_llm(temperature=0.2) 
        
        # 2. Prepare Data (Minify to save tokens)
        minified_data = {}
        for key, val in raw_data.items():
            if isinstance(val, dict) and "score" in val:
                minified_data[key] = {
                    "score": val.get("score"),
                    "flags": val.get("red_flags", [])[:3], 
                    "raw_explanation": val.get("explanation")
                }

        # 3. Run the Writer Chain
        prompt = PromptTemplate(template=REPORT_WRITER_PROMPT, input_variables=["json_data"])
        chain = prompt | llm | JsonOutputParser()
        
        narrative = await chain.ainvoke({"json_data": json.dumps(minified_data, indent=2)})
        
        return narrative

    except Exception as e:
        print(f"Report Writing Failed: {e}")
        # Fallback if LLM fails
        return {
            "executive_summary": "Automated analysis based on provided data points.",
            "agent_insights": {},
            "action_plan": ["Review critical red flags.", "Validate business model.", "Update timeline data."]
        }
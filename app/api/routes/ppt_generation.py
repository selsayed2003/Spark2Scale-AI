import os
import time
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from app.graph.ppt_generation_agent import app_graph
from app.graph.ppt_generation_agent.state import PPTGenerationState
from app.graph.ppt_generation_agent.tools.ppt_tools import generate_pptx_file
from app.graph.ppt_generation_agent.tools.input_loader import load_input_directory
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

# Constants
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
INPUT_DIR = os.path.join(PROJECT_ROOT, "app/graph/ppt_generation_agent/input")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "app/graph/ppt_generation_agent/output")

class PPTInput(BaseModel):
    research_data: str
    logo_path: Optional[str] = None
    color_palette: Optional[List[str]] = None
    use_default_colors: bool = True

async def run_ppt_generation(state: PPTGenerationState, output_path: str):
    """Helper to run the graph and save the file."""
    try:
        # Run the graph
        final_state = await app_graph.ainvoke(state)
        
        final_draft = final_state.get("draft")
        if not final_draft:
            raise HTTPException(status_code=500, detail="Draft generation failed.")

        if not os.path.exists(os.path.dirname(output_path)):
            os.makedirs(os.path.dirname(output_path))
        
        # Use the Presenton engine to generate the PPTX
        await generate_pptx_file(final_draft, output_path)
        
        return {
            "status": "success",
            "ppt_path": output_path,
            "title": final_draft.title,
            "iterations": final_state.get("iteration", 0)
        }
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg and "RESOURCE_EXHAUSTED" in error_msg:
            logger.warning(f"Gemini Quota Exhausted: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Gemini API quota exceeded. Please wait 1-2 minutes and try again."
            )
        logger.error(f"Error in PPT generation: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@router.post("/generate")
async def generate_ppt(input_data: PPTInput):
    """Trigger the PPT Generation workflow with provided data."""
    timestamp = int(time.time())
    output_filename = os.path.join(OUTPUT_DIR, f"presentation_{timestamp}.pptx")
    
    initial_state: PPTGenerationState = {
        "research_data": input_data.research_data,
        "logo_path": input_data.logo_path,
        "color_palette": input_data.color_palette,
        "use_default_colors": input_data.use_default_colors,
        "draft": None,
        "critique": None,
        "iteration": 0,
        "ppt_path": None
    }
    return await run_ppt_generation(initial_state, output_filename)

@router.post("/generate-test")
async def generate_test_ppt():
    """Trigger test case: Logo + combined input from JSON or CSV (startup info + market research)."""
    logo_path = os.path.join(INPUT_DIR, "Logo.jpg")
    loaded = load_input_directory(INPUT_DIR)
    research_data = loaded.research_data.strip() or "Startup Pitch Deck (no input files)"
    timestamp = int(time.time())
    output_filename = os.path.join(OUTPUT_DIR, f"api_test_assil_{timestamp}.pptx")
    initial_state: PPTGenerationState = {
        "research_data": research_data,
        "logo_path": logo_path if os.path.exists(logo_path) else None,
        "color_palette": None,
        "use_default_colors": False,
        "draft": None,
        "critique": None,
        "iteration": 0,
        "ppt_path": None,
    }
    return await run_ppt_generation(initial_state, output_filename)

@router.post("/generate-from-local")
async def generate_from_local():
    """Scan the input folder for JSON or CSV files and generate a presentation."""
    return await generate_deck_from_local_files()

async def generate_deck_from_local_files(output_dir: str = OUTPUT_DIR) -> dict:
    """
    Scans the input folder for JSON or CSV files, constructs the state, 
    and runs the PPT generation workflow. 
    Can be called by API or CLI.
    """
    loaded = load_input_directory(INPUT_DIR)
    if not loaded.research_data and not loaded.flat_data:
        raise HTTPException(
            status_code=400,
            detail="No JSON or CSV files found in the input directory.",
        )
    
    research_data = loaded.research_data.strip() or _flat_data_to_research_text(loaded.flat_data)
    logo_path = os.path.join(INPUT_DIR, "Logo.jpg")
    timestamp = int(time.time())
    output_filename = os.path.join(output_dir, f"premium_pitch_deck_{timestamp}.pptx")
    
    initial_state: PPTGenerationState = {
        "research_data": research_data,
        "logo_path": logo_path if os.path.exists(logo_path) else None,
        "color_palette": None,
        "use_default_colors": not os.path.exists(logo_path),
        "draft": None,
        "critique": None,
        "iteration": 0,
        "ppt_path": None,
    }
    
    return await run_ppt_generation(initial_state, output_filename)


def _flat_data_to_research_text(flat_data: dict) -> str:
    """Turn flat_data into a string for the LLM when only flat_data is available."""
    if not flat_data:
        return "Startup pitch deck data."
    return "\n".join(f"{k}: {v}" for k, v in flat_data.items() if v)

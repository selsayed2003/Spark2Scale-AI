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
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "app/graph/ppt_generation_agent/output")


class PPTInput(BaseModel):
    """
    Main API contract: caller provides fully prepared research_data
    (already merged from the two JSON files on their side), plus optional
    logo and color palette.
    """

    research_data: str
    logo_path: Optional[str] = None
    color_palette: Optional[List[str]] = None
    use_default_colors: bool = True


async def run_ppt_generation(state: PPTGenerationState, output_path: str):
    """Run the graph and save the PPTX file."""
    try:
        # 1) Run the LLM graph to get a PPTDraft
        final_state = await app_graph.ainvoke(state)
        final_draft = final_state.get("draft")
        if not final_draft:
            raise HTTPException(status_code=500, detail="Draft generation failed.")

        # 2) Ensure target directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 3) Render PPTX with Presenton engine
        await generate_pptx_file(final_draft, output_path)

        return {
            "status": "success",
            "ppt_path": output_path,
            "title": final_draft.title,
            "iterations": final_state.get("iteration", 0),
        }
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg and "RESOURCE_EXHAUSTED" in error_msg:
            logger.warning(f"Gemini Quota Exhausted: {error_msg}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Gemini API quota exceeded. Please wait 1-2 minutes and try again.",
            )
        logger.error(f"Error in PPT generation: {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)


async def generate_deck_from_local_files(output_dir: str):
    """
    Load input from local directory and run PPT generation.
    Used by generate_pitch_deck.py script.
    """
    # Load input data from the standard input directory
    input_dir = os.path.join(PROJECT_ROOT, "app/graph/ppt_generation_agent/input")
    loaded_input = load_input_directory(input_dir)
    
    if not loaded_input or not loaded_input.research_data:
        raise ValueError("No valid input data found in input directory")
    
    # Scan for logo file in input directory
    logo_path = None
    if os.path.isdir(input_dir):
        for filename in os.listdir(input_dir):
            lower_name = filename.lower()
            if lower_name.startswith("logo") and lower_name.endswith((".png", ".jpg", ".jpeg")):
                logo_path = os.path.join(input_dir, filename)
                logger.info(f"Found logo file: {logo_path}")
                break
    
    timestamp = int(time.time())
    output_filename = os.path.join(output_dir, f"presentation_{timestamp}.pptx")
    
    # Create initial state from loaded input (LoadedInput is a dataclass, not a dict)
    initial_state: PPTGenerationState = {
        "research_data": loaded_input.research_data,
        "logo_path": logo_path,
        "color_palette": None,  # TODO: Support color palette from input
        "use_default_colors": not bool(logo_path),  # Use logo colors if logo is provided
        "draft": None,
        "critique": None,
        "iteration": 0,
        "ppt_path": None,
    }
    
    return await run_ppt_generation(initial_state, output_filename)


@router.post("/generate")
async def generate_ppt(input_data: PPTInput):
    """
    Single, main endpoint.

    Assumption (per project design):
    - The client has already loaded and merged the **two JSON input files**
      and passes them as `research_data` (string).
    - There are no CSV inputs.
    - Input files are guaranteed to exist and be valid on the client side.
    """
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
        "ppt_path": None,
    }
    return await run_ppt_generation(initial_state, output_filename)

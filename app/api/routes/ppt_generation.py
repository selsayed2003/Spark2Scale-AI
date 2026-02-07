import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.graph.ppt_generation_agent import app_graph
from app.graph.ppt_generation_agent.state import PPTGenerationState
from app.graph.ppt_generation_agent.utils import generate_pptx_file
from app.core.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()

class PPTInput(BaseModel):
    research_data: str

@router.post("/generate")
async def generate_ppt(input_data: PPTInput):
    """
    Trigger the PPT Generation workflow.
    """
    try:
        initial_state: PPTGenerationState = {
            "research_data": input_data.research_data,
            "draft": None,
            "critique": None,
            "iteration": 0,
            "ppt_path": None
        }
        
        # Run the graph
        final_state = await app_graph.ainvoke(initial_state)
        
        # Determine output directory
        output_dir = os.path.join(
            os.path.dirname(__file__),
            "../../../graph/ppt_generation_agent"
        )
        


        final_draft = final_state.get("draft")
        if final_draft:
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            output_filename = os.path.join(output_dir, "presentation.pptx")
            
            # Use the Presenton engine to generate the PPTX
            await generate_pptx_file(final_draft, output_filename)
            
            final_state["ppt_path"] = output_filename
            return {
                "status": "success",
                "ppt_path": output_filename,
                "title": final_draft.title,
                "iterations": final_state["iteration"]
            }
        else:
            return {"status": "failed", "message": "Draft generation failed."}
            
    except Exception as e:
        logger.error(f"Error in PPT generation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

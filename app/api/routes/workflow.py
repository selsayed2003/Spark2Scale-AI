from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from app.graph.workflow import app_graph
from app.graph.state import AgentState

router = APIRouter()

class WorkflowInput(BaseModel):
    idea: str

class WorkflowResponse(BaseModel):
    status: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

@router.post("/invoke", response_model=WorkflowResponse)
async def invoke_workflow(input_data: WorkflowInput):
    """
    Trigger the LangGraph workflow with an idea.
    Returns the workflow result including recommendation file paths.
    """
    try:
        initial_state: AgentState = {"input_idea": input_data.idea}
        result = app_graph.invoke(initial_state)
        
        # Extract file paths if available
        response_data = {
            "recommendation": result.get("recommendation"),
            "evaluation": result.get("evaluation"),
            "market_research": result.get("market_research"),
            "ppt_path": result.get("ppt_path")
        }
        
        # Add file paths if available
        if result.get("recommendation_files"):
            response_data["output_files"] = result["recommendation_files"]
            
        return WorkflowResponse(
            status="success",
            message="Workflow completed successfully",
            data=response_data
        )
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"Error in invoke_workflow: {error_trace}")
        
        return WorkflowResponse(
            status="error",
            error=str(e)
        )

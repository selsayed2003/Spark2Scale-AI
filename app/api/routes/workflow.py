from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.graph.workflow import app_graph
from app.graph.state import AgentState

router = APIRouter()

class WorkflowInput(BaseModel):
    idea: str

@router.post("/invoke")
async def invoke_workflow(input_data: WorkflowInput):
    """
    Trigger the LangGraph workflow with an idea.
    """
    try:
        initial_state: AgentState = {"input_idea": input_data.idea}
        result = app_graph.invoke(initial_state)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

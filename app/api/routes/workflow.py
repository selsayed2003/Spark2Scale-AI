from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.graph.market_research_agent.workflow import market_research_app
from app.graph.evaluation_agent.workflow import evaluation_app
from app.graph.recommendation_agent.workflow import recommendation_app
from app.graph.ppt_generation_agent.workflow import ppt_generation_app

router = APIRouter()

class WorkflowInput(BaseModel):
    idea: str
    problem: str = "General Problem" # Default if not provided

@router.post("/market_research/invoke")
async def invoke_market_research(input_data: WorkflowInput):
    try:
        initial_state = {"input_idea": input_data.idea, "input_problem": input_data.problem}
        result = market_research_app.invoke(initial_state)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluation/invoke")
async def invoke_evaluation(input_data: WorkflowInput): # Input might need adjustment based on agent needs
    try:
        # Evaluation needs 'market_research' input usually, but for now just mapping idea
        initial_state = {"market_research": f"Research for {input_data.idea}"} 
        result = evaluation_app.invoke(initial_state)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/recommendation/invoke")
async def invoke_recommendation(input_data: WorkflowInput):
    try:
        initial_state = {"evaluation": f"Evaluation for {input_data.idea}"}
        result = recommendation_app.invoke(initial_state)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/ppt_generation/invoke")
async def invoke_ppt_generation(input_data: WorkflowInput):
    try:
        initial_state = {"recommendation": f"Recommendation for {input_data.idea}"}
        result = ppt_generation_app.invoke(initial_state)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from app.graph.evaluation_agent import evaluation_graph
from pydantic import BaseModel

router = APIRouter()

class EvalInput(BaseModel):
    startup_evaluation: Dict[str, Any]

@router.post("/evaluate")
async def evaluate_idea(input_data: EvalInput):
    try:
        # Run the Graph
        state = await evaluation_graph.ainvoke({"user_data": input_data.model_dump()})
        
        # FILTER: Only return the Clean Reports
        # This removes 'search_results', 'tech_stack', etc. from the final response
        return {
            "team_report": state.get("team_report"),
            "problem_report": state.get("problem_report"),
            "product_report": state.get("product_report")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
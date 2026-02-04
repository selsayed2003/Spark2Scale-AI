from fastapi import APIRouter
from app.graph.evaluation_agent import app_graph
from pydantic import BaseModel

router = APIRouter()

class EvalInput(BaseModel):
    idea: str

@router.post("/evaluate")
async def evaluate_idea(input_data: EvalInput):
    result = await app_graph.ainvoke({"input_idea": input_data.idea})
    return result

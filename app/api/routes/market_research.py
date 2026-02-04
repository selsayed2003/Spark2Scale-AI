from fastapi import APIRouter
from app.graph.market_research_agent import app_graph
from pydantic import BaseModel

router = APIRouter()

class ResearchInput(BaseModel):
    idea: str

@router.post("/research")
async def research_idea(input_data: ResearchInput):
    result = await app_graph.ainvoke({"input_idea": input_data.idea})
    return result

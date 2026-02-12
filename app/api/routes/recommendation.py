# from fastapi import APIRouter
# from app.graph.recommendation_agent import app_graph
# from pydantic import BaseModel

# router = APIRouter()

# class RecInput(BaseModel):
#     idea: str

# @router.post("/recommend")
# async def recommend_idea(input_data: RecInput):
#     result = await app_graph.ainvoke({"input_idea": input_data.idea})
#     return result

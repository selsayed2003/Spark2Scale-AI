from typing import Literal
from langgraph.graph import StateGraph, END
from .state import PPTGenerationState
from .node import generator_node, recommender_node, refiner_node
from app.core.config import config
from app.core.logger import get_logger

logger = get_logger(__name__)

def should_refine(state: PPTGenerationState) -> Literal["refiner", "end"]:
    iteration = state["iteration"]
    max_iterations = config.MAX_ITERATIONS
    critique = state.get("critique")
    
    if iteration >= max_iterations:
        logger.info(f"--- MAX ITERATIONS REACHED ({iteration}/{max_iterations}) ---")
        return "end"
    
    if critique and critique.score >= 90:
        logger.info(f"--- SCORE THRESHOLD MET ({critique.score}/100) ---")
        return "end"
    
    logger.info(f"--- REFINING (Score: {critique.score if critique else 0}, Iteration: {iteration}) ---")
    return "refiner"

workflow = StateGraph(PPTGenerationState)

workflow.add_node("generator", generator_node)
workflow.add_node("recommender", recommender_node)
workflow.add_node("refiner", refiner_node)

workflow.set_entry_point("generator")

workflow.add_edge("generator", "recommender")

workflow.add_conditional_edges(
    "recommender",
    should_refine,
    {
        "refiner": "refiner",
        "end": END
    }
)

workflow.add_edge("refiner", "recommender")

app_graph = workflow.compile()
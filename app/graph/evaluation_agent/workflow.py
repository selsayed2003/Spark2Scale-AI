import time
import os
from langgraph.graph import StateGraph, END, START
from .state import AgentState

# --- IMPORT ALL NODES (Existing + New) ---
from .node import (
    planner_node,
    team_node,
    problem_node,
    # New Agents
    market_node,
    traction_node,
    gtm_node,
    business_node,
    vision_node,
    operations_node,
    # Product Fan-Out Nodes (Optimized)
    product_tools_node,
    product_contradiction_node,
    product_risk_node,
    product_final_scoring_node
)

from app.core.logger import get_logger

logger = get_logger(__name__)

def create_evaluation_graph():
    # 1. Initialize Graph
    workflow = StateGraph(AgentState)

    # =========================================================
    # 2. ADD NODES
    # =========================================================
    
    # --- Shared Start ---
    workflow.add_node("planner_node", planner_node)

    # --- Core Parallel Agents ---
    workflow.add_node("team_node", team_node)
    workflow.add_node("problem_node", problem_node)
    workflow.add_node("market_node", market_node)
    workflow.add_node("traction_node", traction_node)
    workflow.add_node("gtm_node", gtm_node)
    workflow.add_node("business_node", business_node)
    workflow.add_node("vision_node", vision_node)
    workflow.add_node("operations_node", operations_node)

    # --- Product Agent (Fan-Out Architecture) ---
    # These 3 run in parallel to speed up the slow Product analysis
    workflow.add_node("product_tools_node", product_tools_node)
    workflow.add_node("product_contradiction_node", product_contradiction_node)
    workflow.add_node("product_risk_node", product_risk_node)
    
    # This node waits for the 3 above to finish
    workflow.add_node("product_final_scoring_node", product_final_scoring_node)

    # =========================================================
    # 3. DEFINE EDGES (The Flow)
    # =========================================================

    # START -> Planner
    workflow.add_edge(START, "planner_node")

    # Planner -> FAN OUT to EVERYTHING (Parallel Execution)
    # LangGraph runs all nodes connected to the same source in parallel
    workflow.add_edge("planner_node", "team_node")
    workflow.add_edge("planner_node", "problem_node")
    workflow.add_edge("planner_node", "market_node")
    workflow.add_edge("planner_node", "traction_node")
    workflow.add_edge("planner_node", "gtm_node")
    workflow.add_edge("planner_node", "business_node")
    workflow.add_edge("planner_node", "vision_node")
    workflow.add_edge("planner_node", "operations_node")
    
    # Fan out to Product Parts
    workflow.add_edge("planner_node", "product_tools_node")
    workflow.add_edge("planner_node", "product_contradiction_node")
    workflow.add_edge("planner_node", "product_risk_node")

    # --- Convergence Points ---
    
    # Product parts converge to Final Scoring
    workflow.add_edge("product_tools_node", "product_final_scoring_node")
    workflow.add_edge("product_contradiction_node", "product_final_scoring_node")
    workflow.add_edge("product_risk_node", "product_final_scoring_node")

    # --- End Points ---
    workflow.add_edge("team_node", END)
    workflow.add_edge("problem_node", END)
    workflow.add_edge("market_node", END)
    workflow.add_edge("traction_node", END)
    workflow.add_edge("gtm_node", END)
    workflow.add_edge("business_node", END)
    workflow.add_edge("vision_node", END)
    workflow.add_edge("operations_node", END)
    workflow.add_edge("product_final_scoring_node", END)

    return workflow.compile()

# Compile the app
app = create_evaluation_graph()

async def run_pipeline(user_data):
    """
    Helper to run the graph with timing and logging.
    """
    start_time = time.time()
    initial_state = {"user_data": user_data}
    
    logger.info("🚀 Starting 9-Agent Parallel Evaluation Pipeline...")
    try:
        # Ainvoke handles the async parallel execution automatically
        result = await app.ainvoke(initial_state)
    except Exception as e:
        logger.error(f"🔥 Graph Execution Error: {e}", exc_info=True)
        raise e
        
    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"✅ Pipeline Finished in {duration:.2f} seconds.")
    
    return result

def save_graph_image(file_path="graph_visualization.png"):
    """
    Generates a Mermaid PNG of the complex graph structure.
    """
    try:
        png_data = app.get_graph().draw_mermaid_png()
        with open(file_path, "wb") as f:
            f.write(png_data)
        logger.info(f"🖼️ Graph visualization saved to {file_path}")
    except Exception as e:
        logger.error(f"⚠️ Could not save graph image: {e}")
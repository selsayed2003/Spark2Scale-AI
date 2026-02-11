import time
from langgraph.graph import StateGraph, END, START
from .state import AgentState

# --- IMPORT ALL NODES ---
from .node import (
    planner_node,
    team_node,
    problem_node,
    market_node,
    traction_node,
    gtm_node,
    business_node,
    vision_node,
    operations_node,
    # Product Nodes (We will chain these too!)
    product_tools_node,
    product_contradiction_node,
    product_risk_node,
    product_final_scoring_node,
    final_node
)

from app.core.logger import get_logger

logger = get_logger(__name__)

def create_evaluation_graph():
    # 1. Initialize Graph
    workflow = StateGraph(AgentState)

    # =========================================================
    # 2. ADD NODES
    # =========================================================
    
    workflow.add_node("planner_node", planner_node)
    
    # Core Agents
    workflow.add_node("team_node", team_node)
    workflow.add_node("problem_node", problem_node)
    workflow.add_node("vision_node", vision_node)
    workflow.add_node("market_node", market_node)
    
    # Product Chain (Broken down sequentially)
    workflow.add_node("product_tools_node", product_tools_node)
    workflow.add_node("product_contradiction_node", product_contradiction_node)
    workflow.add_node("product_risk_node", product_risk_node)
    workflow.add_node("product_final_scoring_node", product_final_scoring_node)

    # Rest of Agents
    workflow.add_node("traction_node", traction_node)
    workflow.add_node("gtm_node", gtm_node)
    workflow.add_node("business_node", business_node)
    workflow.add_node("operations_node", operations_node)
    workflow.add_node("final_node", final_node)

    # =========================================================
    # 3. DEFINE EDGES (The Sequential Chain)
    # =========================================================

    # 1. Start -> Plan
    workflow.add_edge(START, "planner_node")
    
    # 2. Plan -> Team
    workflow.add_edge("planner_node", "team_node")
    
    # 3. Team -> Problem
    workflow.add_edge("team_node", "problem_node")
    
    # 4. Problem -> Vision
    workflow.add_edge("problem_node", "vision_node")

    # 5. Vision -> Market
    workflow.add_edge("vision_node", "market_node")

    # 6. Market -> Product Chain (Tools -> Contradiction -> Risk -> Score)
    workflow.add_edge("market_node", "product_tools_node")
    workflow.add_edge("product_tools_node", "product_contradiction_node")
    workflow.add_edge("product_contradiction_node", "product_risk_node")
    workflow.add_edge("product_risk_node", "product_final_scoring_node")

    # 7. Product Score -> Traction
    workflow.add_edge("product_final_scoring_node", "traction_node")

    # 8. Traction -> GTM
    workflow.add_edge("traction_node", "gtm_node")

    # 9. GTM -> Business
    workflow.add_edge("gtm_node", "business_node")

    # 10. Business -> Operations
    workflow.add_edge("business_node", "operations_node")

    # 11. Operations -> END
    workflow.add_edge("operations_node", "final_node")
    workflow.add_edge("final_node", END)

    return workflow.compile()

# Compile the app
app = create_evaluation_graph()
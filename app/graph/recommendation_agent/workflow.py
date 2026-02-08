from langgraph.graph import StateGraph, END
from app.graph.recommendation_agent.state import RecommendationState
from app.graph.recommendation_agent.node import recommendation_node

def create_recommendation_graph():
    workflow = StateGraph(RecommendationState)

    # Add nodes
    workflow.add_node("recommendation_node", recommendation_node)

    # Define edges
    workflow.set_entry_point("recommendation_node")
    workflow.add_edge("recommendation_node", END)

    return workflow.compile()

recommendation_app = create_recommendation_graph()

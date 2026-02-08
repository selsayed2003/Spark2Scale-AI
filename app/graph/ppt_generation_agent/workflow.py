from langgraph.graph import StateGraph, END
from app.graph.ppt_generation_agent.state import PPTGenerationState
from app.graph.ppt_generation_agent.node import ppt_generation_node

def create_ppt_generation_graph():
    workflow = StateGraph(PPTGenerationState)

    # Add nodes
    workflow.add_node("ppt_generation_node", ppt_generation_node)

    # Define edges
    workflow.set_entry_point("ppt_generation_node")
    workflow.add_edge("ppt_generation_node", END)

    return workflow.compile()

ppt_generation_app = create_ppt_generation_graph()

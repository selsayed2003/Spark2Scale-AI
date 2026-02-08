from langgraph.graph import StateGraph, END
from app.graph.evaluation_agent.state import EvaluationState
from app.graph.evaluation_agent.node import evaluation_node

def create_evaluation_graph():
    workflow = StateGraph(EvaluationState)

    # Add nodes
    workflow.add_node("evaluation_node", evaluation_node)

    # Define edges
    workflow.set_entry_point("evaluation_node")
    workflow.add_edge("evaluation_node", END)

    return workflow.compile()

evaluation_app = create_evaluation_graph()

from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.graph.nodes.evaluation_agent import evaluation_node
from app.graph.nodes.recommendation_agent import recommendation_node
from app.graph.nodes.market_research_agent import market_research_node
from app.graph.nodes.ppt_generation_agent import ppt_generation_node

def create_graph():
    workflow = StateGraph(AgentState)

    # Add nodes
    # Add nodes
    workflow.add_node("evaluation_step", evaluation_node)
    workflow.add_node("recommendation_step", recommendation_node)
    workflow.add_node("market_research_step", market_research_node)
    workflow.add_node("ppt_generation_step", ppt_generation_node)

    # Define edges - for now, we'll do a sequential flow
    # Idea -> Market Research -> Evaluation -> Recommendation -> PPT
    
    workflow.set_entry_point("market_research_step")
    
    workflow.add_edge("market_research_step", "evaluation_step")
    workflow.add_edge("evaluation_step", "recommendation_step")
    workflow.add_edge("recommendation_step", "ppt_generation_step")
    workflow.add_edge("ppt_generation_step", END)

    return workflow.compile()

app_graph = create_graph()

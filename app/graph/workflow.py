from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.graph.nodes.evaluation_agent import evaluation_node
from app.graph.nodes.recommendation_agent import recommendation_node
from app.graph.nodes.market_research_agent import market_research_node
from app.graph.nodes.ppt_generation_agent import ppt_generation_node

def create_graph():
    workflow = StateGraph(AgentState)

    # Add nodes (using different names from state keys to avoid conflicts)
    workflow.add_node("evaluate", evaluation_node)
    workflow.add_node("recommend", recommendation_node)
    workflow.add_node("research", market_research_node)
    workflow.add_node("generate_ppt", ppt_generation_node)

    # Define edges - for now, we'll do a sequential flow
    # Idea -> Market Research -> Evaluation -> Recommendation -> PPT
    
    workflow.set_entry_point("research")
    
    workflow.add_edge("research", "evaluate")
    workflow.add_edge("evaluate", "recommend")
    workflow.add_edge("recommend", "generate_ppt")
    workflow.add_edge("generate_ppt", END)

    return workflow.compile()

app_graph = create_graph()

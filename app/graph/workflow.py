from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.graph.evaluation_agent.workflow import evaluation_app
from app.graph.recommendation_agent.workflow import recommendation_app
from app.graph.market_research_agent.workflow import market_research_app
from app.graph.ppt_generation_agent.workflow import ppt_generation_app

def create_graph():
    workflow = StateGraph(AgentState)

    # Add nodes
    # Add nodes
    workflow.add_node("evaluation_step", evaluation_app)
    workflow.add_node("recommendation_step", recommendation_app)
    workflow.add_node("market_research_step", market_research_app)
    workflow.add_node("ppt_generation_step", ppt_generation_app)

    # Define edges - for now, we'll do a sequential flow
    # Idea -> Market Research -> Evaluation -> Recommendation -> PPT
    
    workflow.set_entry_point("market_research_step")
    
    workflow.add_edge("market_research_step", "evaluation_step")
    workflow.add_edge("evaluation_step", "recommendation_step")
    workflow.add_edge("recommendation_step", "ppt_generation_step")
    workflow.add_edge("ppt_generation_step", END)

    return workflow.compile()

app_graph = create_graph()

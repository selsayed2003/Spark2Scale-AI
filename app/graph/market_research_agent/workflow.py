from langgraph.graph import StateGraph, END
from app.graph.market_research_agent.state import MarketResearchState
from app.graph.market_research_agent.nodes import (
    plan_node,
    competitors_node,
    validation_node,
    trends_node,
    finance_node,
    market_sizing_node,
    report_node,
    pdf_node
)

def create_market_research_graph():
    workflow = StateGraph(MarketResearchState)

    # Add nodes
    workflow.add_node("plan", plan_node)
    workflow.add_node("competitors", competitors_node)
    workflow.add_node("validation", validation_node)
    workflow.add_node("trends", trends_node)
    workflow.add_node("finance", finance_node)
    workflow.add_node("market_sizing", market_sizing_node)
    workflow.add_node("report", report_node)
    workflow.add_node("pdf", pdf_node)

    # Define edges (Sequential Chain)
    workflow.set_entry_point("plan")
    workflow.add_edge("plan", "competitors")
    workflow.add_edge("competitors", "validation")
    workflow.add_edge("validation", "trends")
    workflow.add_edge("trends", "finance")
    workflow.add_edge("finance", "market_sizing")
    workflow.add_edge("market_sizing", "report")
    workflow.add_edge("report", "pdf")
    workflow.add_edge("pdf", END)

    return workflow.compile()

market_research_app = create_market_research_graph()

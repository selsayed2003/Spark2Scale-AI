from langgraph.graph import StateGraph, END
from .state import MarketResearchState
from .node import market_research_node

workflow = StateGraph(MarketResearchState)
workflow.add_node("market_research", market_research_node)
workflow.set_entry_point("market_research")
workflow.add_edge("market_research", END)

app_graph = workflow.compile()

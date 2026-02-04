from langgraph.graph import StateGraph, END
from .state import RecommendationState
from .node import recommendation_node

workflow = StateGraph(RecommendationState)
workflow.add_node("recommendation", recommendation_node)
workflow.set_entry_point("recommendation")
workflow.add_edge("recommendation", END)

app_graph = workflow.compile()

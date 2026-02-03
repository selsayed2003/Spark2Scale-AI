from langgraph.graph import StateGraph, END
from .state import EvaluationState
from .node import evaluation_node

workflow = StateGraph(EvaluationState)
workflow.add_node("evaluation", evaluation_node)
workflow.set_entry_point("evaluation")
workflow.add_edge("evaluation", END)

app_graph = workflow.compile()

from app.graph.state import AgentState

def evaluation_node(state: AgentState):
    """
    Evaluates the input project/idea.
    """
    # TODO: Implement evaluation logic using LLM
    print("Executing Evaluation Agent")
    # Mock result
    result = "Standard Evaluation: Feasible"
    return {"evaluation": result}

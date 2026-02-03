from .state import EvaluationState

def evaluation_node(state: EvaluationState):
    """
    Evaluates the input project/idea.
    """
    # TODO: Implement evaluation logic using LLM
    print("Executing Evaluation Agent")
    # Mock result
    result = "Standard Evaluation: Feasible"
    return {"evaluation": result}

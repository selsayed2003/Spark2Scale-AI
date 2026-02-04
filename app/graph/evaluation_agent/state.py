<<<<<<< HEAD:app/graph/nodes/evaluation_agent/state.py
from typing import TypedDict, Annotated, Dict, Any, List, Union
import operator

def replace_reducer(a, b):
    return b

class AgentState(TypedDict):
    # --- INPUT ---
    user_data: Dict[str, Any]
    
    # --- OUTPUTS ---
    plan: Annotated[dict, replace_reducer] # Validation Plan
    
    # Team Branch Output
    team_report: Annotated[Dict[str, Any], operator.ior]
    
    # Problem Branch Output
    problem_report: Annotated[str, replace_reducer]
    search_results: Annotated[Dict[str, Any], operator.ior]
    risk_report: Annotated[str, replace_reducer] # For problem risk
    contradiction_report: Annotated[str, replace_reducer] # For problem contradiction
    
    # Product Branch Output
    tech_stack: Annotated[Dict[str, Any], operator.ior]
    visual_analysis: Annotated[str, replace_reducer]
    product_contradiction: Annotated[str, replace_reducer] # Distinct key for product
    product_report: Annotated[str, replace_reducer]
    
    # General / Shared
    missing_report: Annotated[List[str], operator.add]
=======
from typing import TypedDict, Optional

class EvaluationState(TypedDict):
    input_idea: str
    evaluation: Optional[str]
>>>>>>> origin/Salma:app/graph/evaluation_agent/state.py

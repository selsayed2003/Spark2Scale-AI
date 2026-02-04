from typing import TypedDict, Annotated, Dict, Any, List, Union
import operator

def replace_reducer(a, b):
    return b

class AgentState(TypedDict):
    # --- INPUT ---
    user_data: Dict[str, Any]
    
    # --- OUTPUTS ---
    # Team Branch
    team_report: Annotated[Dict[str, Any], operator.ior]
    
    # Problem Branch
    problem_report: Annotated[Dict[str, Any], replace_reducer]
    search_results: Annotated[Dict[str, Any], operator.ior]
    problem_risk_report: Annotated[str, replace_reducer]
    problem_contradiction: Annotated[str, replace_reducer]
    
    # Product Branch (Fan-Out Outputs)
    tech_stack: Annotated[Dict[str, Any], operator.ior]
    visual_analysis: Annotated[str, replace_reducer]
    product_contradiction: Annotated[str, replace_reducer]
    product_risk_report: Annotated[str, replace_reducer]
    product_report: Annotated[Dict[str, Any], replace_reducer]
    
    # Shared
    missing_report: Annotated[List[str], operator.add]
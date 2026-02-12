from typing import TypedDict, Optional, Dict, Any, List

class RecommendationState(TypedDict):
    """
    Intermediate state fields for the recommendation agent.
    """
    insights: Optional[Dict[str, Any]]
    matched_patterns: Optional[List[Dict[str, Any]]]
    refined_statements: Optional[Dict[str, Any]]

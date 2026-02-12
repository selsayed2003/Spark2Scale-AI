from typing import TypedDict, Optional, Dict, Any, List

from app.graph.nodes.recommendation_agent.state import RecommendationState

class AgentState(TypedDict, RecommendationState):
    input_idea: str
    evaluation: Optional[str]
    recommendation: Optional[str]
    recommendation_files: Optional[Dict[str, Any]]  # Tracks output file paths
    market_research: Optional[str]
    ppt_path: Optional[str]

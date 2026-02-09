from typing import TypedDict, Optional, Dict, Any

class AgentState(TypedDict):
    input_idea: str
    evaluation: Optional[str]
    recommendation: Optional[str]
    recommendation_files: Optional[Dict[str, Any]]  # Tracks output file paths
    market_research: Optional[str]
    ppt_path: Optional[str]

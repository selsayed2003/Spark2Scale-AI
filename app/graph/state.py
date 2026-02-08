from typing import TypedDict, Optional

class AgentState(TypedDict):
    input_idea: str
    input_problem: str
    evaluation: Optional[str]
    recommendation: Optional[str]
    market_research: Optional[str]
    ppt_path: Optional[str]

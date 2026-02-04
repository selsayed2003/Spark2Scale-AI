from typing import TypedDict, Optional

class RecommendationState(TypedDict):
    input_idea: str
    recommendation: Optional[str]

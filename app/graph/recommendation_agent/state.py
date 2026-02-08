from typing import TypedDict, Optional

class RecommendationState(TypedDict):
    evaluation: str
    recommendation: Optional[str]

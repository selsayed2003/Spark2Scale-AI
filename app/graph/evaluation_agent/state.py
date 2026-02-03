from typing import TypedDict, Optional

class EvaluationState(TypedDict):
    input_idea: str
    evaluation: Optional[str]

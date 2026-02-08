from typing import TypedDict, Optional

class PPTGenerationState(TypedDict):
    recommendation: str
    ppt_path: Optional[str]

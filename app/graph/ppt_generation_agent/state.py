from typing import Optional, TypedDict
from .schema import PPTDraft, Critique

# --- Agent State ---

class PPTGenerationState(TypedDict):
    """
    Represents the state of the PPT generation graph.
    """
    research_data: str
    draft: Optional[PPTDraft]
    critique: Optional[Critique]
    iteration: int
    ppt_path: Optional[str]

import json
from pydantic import BaseModel, Field
from typing import List, Dict, Any

# --- EXISTING ---
class Plan(BaseModel):
    steps: List[str] = Field(..., description="Short ordered steps for solving the task.")
    key_risks: List[str] = Field(..., description="Major risks/unknowns that should be addressed.")
    desired_output_structure: List[str] = Field(..., description="Headings to include in final answer.")

# --- OPTIONAL: Input Validation ---
class EvaluationInput(BaseModel):
    startup_evaluation: Dict[str, Any] = Field(..., description="The full JSON object containing startup data")
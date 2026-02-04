import json
from pydantic import BaseModel, Field
from typing import List

def load_schema(schema_name: str) -> str:
    """
    Loads a JSON schema from the schema.json file.
    """
    import os
    current_dir = os.path.dirname(os.path.abspath(__file__))
    schema_path = os.path.join(current_dir, "schema.json")
    
    with open(schema_path, "r") as f:
        schemas = json.load(f)
        
    return json.dumps(schemas.get(schema_name, {}), indent=2)

class Plan(BaseModel):
    steps: List[str] = Field(..., description="Short ordered steps for solving the task.")
    key_risks: List[str] = Field(..., description="Major risks/unknowns that should be addressed.")
    desired_output_structure: List[str] = Field(..., description="Headings to include in final answer.")

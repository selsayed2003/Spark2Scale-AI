from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class SectionScore(BaseModel):
    score: int
    description: str

class StartupScores(BaseModel):
    team: SectionScore
    problem: SectionScore
    product: SectionScore
    market: SectionScore
    traction: SectionScore
    gtm: SectionScore
    economics: SectionScore
    vision: SectionScore
    ops: SectionScore

class StartupData(BaseModel):
    stage: str
    company_context: str
    scores: StartupScores
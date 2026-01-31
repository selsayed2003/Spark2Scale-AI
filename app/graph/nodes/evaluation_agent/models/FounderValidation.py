from typing import TypedDict, List, Optional

class FounderValidationState(TypedDict):
    # Inputs
    founder_profile: dict
    startup_stage: str # "Pre-Seed" or "Seed"

    # Worker Outputs
    fact_check_results: Optional[str]
    ambiguity_score: Optional[float]
    identified_risks: List[str]
    
    # Final Outputs
    final_score: int
    confidence: str # "High", "Medium", "Low"
    reasoning: str
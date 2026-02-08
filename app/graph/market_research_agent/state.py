from typing import TypedDict, Optional

class MarketResearchState(TypedDict):
    input_idea: str
    input_problem: str
    
    # Intermediate Data Files
    competitors_file: Optional[str]
    validation_file: Optional[str]
    trends_file: Optional[str]
    finance_file: Optional[str]
    market_limit_file: Optional[str]
    
    # Final Outputs
    report_text: Optional[str]
    pdf_path: Optional[str]
    market_research: Optional[str] # Final message

from app.graph.market_research_agent.state import MarketResearchState
from .tools import (
    find_competitors,
    validate_problem,
    fetch_trend_data,
    run_finance_model,
    generate_report,
    compile_final_pdf,
    calculate_market_size
)
import os
from app.graph.market_research_agent.logger_config import get_logger

logger = get_logger("MarketResearchNodes")

def competitors_node(state: MarketResearchState):
    logger.info("\n👉 Step 1: Researching Competitors...")
    idea = state.get("input_idea")
    file_path = find_competitors(idea)
    return {"competitors_file": file_path}

def validation_node(state: MarketResearchState):
    logger.info("\n👉 Step 2: Validating Pain Points...")
    idea = state.get("input_idea")
    problem = state.get("input_problem")
    file_path = validate_problem(idea, problem)
    return {"validation_file": file_path}

def trends_node(state: MarketResearchState):
    logger.info("\n👉 Step 3: Analyzing Market Trends...")
    idea = state.get("input_idea")
    trend_keyword = idea.split(" in ")[0]
    trend_csv, _ = fetch_trend_data([trend_keyword], geo_code='EG')
    return {"trends_file": trend_csv}

def finance_node(state: MarketResearchState):
    logger.info("\n👉 Step 5: Building Financial Model...")
    idea = state.get("input_idea")
    finance_csv = run_finance_model(idea)
    return {"finance_file": finance_csv}

def market_sizing_node(state: MarketResearchState):
    logger.info("\n👉 Step 6: Calculating TAM/SAM/SOM...")
    idea = state.get("input_idea")
    # localization could be passed in state if needed, defaulting to Egypt for now based on previous code
    file_path = calculate_market_size(idea, location="Egypt")
    return {"market_limit_file": file_path}

def report_node(state: MarketResearchState):
    logger.info("\n👉 Step 7: Writing Strategy Report...")
    idea = state.get("input_idea")
    val_file = state.get("validation_file")
    trend_file = state.get("trends_file")
    finance_file = state.get("finance_file")
    
    if val_file: 
        logger.info(f"Generating report using validation file: {val_file}")
        generate_report(val_file, idea, trend_file=trend_file, finance_file=finance_file)
        
    return {"report_text": "Report Generated"}

def pdf_node(state: MarketResearchState):
    logger.info("\n👉 Step 8: Compiling Final PDF Deck...")
    idea = state.get("input_idea")
    pdf_file = compile_final_pdf(idea)
    result = f"Research complete. PDF Report available at: {pdf_file}"
    return {"pdf_path": pdf_file, "market_research": result}

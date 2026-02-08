from app.graph.state import AgentState
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

def market_research_node(state: AgentState):
    """
    Conducts market research using the consolidated tools.
    """
    idea = state.get("input_idea")
    problem = state.get("input_problem")
    
    print(f"\n🤖 [Market Research Agent] Analyzing: '{idea}'...")
    print(f"   🎯 Problem: '{problem}'")
    
    os.makedirs("data_output", exist_ok=True)
    
    # 1. Competitors
    print("\n👉 Step 1: Researching Competitors...")
    find_competitors(idea)
    
    # 2. Validation
    print("\n👉 Step 2: Validating Pain Points...")
    val_file = validate_problem(idea, problem)
    
    # 3. Trends
    print("\n👉 Step 3: analyzing Market Trends...")
    trend_keyword = idea.split(" in ")[0]
    trend_csv, _ = fetch_trend_data([trend_keyword], geo_code='EG')

    # 5. Finance
    print("\n👉 Step 5: Building Financial Model...")
    finance_csv = run_finance_model(idea)
    
    # 6. Market Sizing
    print("\n👉 Step 6: Calculating TAM/SAM/SOM...")
    calculate_market_size(idea, location="Egypt")

    # 7. Text Report
    print("\n👉 Step 7: Writing Strategy Report...")
    if val_file: 
        generate_report(val_file, idea, trend_file=trend_csv, finance_file=finance_csv)

    # 8. PDF Compiler
    print("\n👉 Step 8: Compiling Final PDF Deck...")
    pdf_file = compile_final_pdf(idea)
    
    result = f"Research complete. PDF Report available at: {pdf_file}"
    return {"market_research": result}

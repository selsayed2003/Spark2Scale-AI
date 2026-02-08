import sys
import os

# Import all tools
from research_engine import find_competitors        # Tool 3
from problem_validator import validate_problem      # Tool 6
from market_quantifier import fetch_trend_data      # Tool 7
from finance_model import run_finance_model         # Tool 8
from report_generator import generate_report        # Tool 5
from pdf_compiler import compile_final_pdf          # Tool 9 (NEW)

def run_agent(idea, problem_statement):
    print(f"\n🤖 [Market Research Agent] Analyzing: '{idea}'...")
    print(f"   🎯 Problem: '{problem_statement}'")
    
    os.makedirs("data_output", exist_ok=True)
    
    # 1. Competitors
    print("\n👉 Step 1: Researching Competitors...")
    find_competitors(idea)
    
    # 2. Validation
    print("\n👉 Step 2: Validating Pain Points...")
    val_file = validate_problem(idea, problem_statement)
    
    # 3. Trends
    print("\n👉 Step 3: analyzing Market Trends...")
    trend_keyword = idea.split(" in ")[0]
    trend_csv, _ = fetch_trend_data([trend_keyword], geo_code='EG')

    # 4. Finance
    print("\n👉 Step 4: Building Financial Model...")
    finance_csv = run_finance_model(idea)
    
    # 5. Text Report
    print("\n👉 Step 5: Writing Strategy Report...")
    if val_file: 
        generate_report(val_file, idea, trend_file=trend_csv, finance_file=finance_csv)

    # 6. PDF Compiler
    print("\n👉 Step 6: Compiling Final PDF Deck...")
    pdf_file = compile_final_pdf(idea)
    
    print(f"\n✅ DONE! Open this file to see your business plan:\n   📂 {pdf_file}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('Usage: python universal_router.py "Idea" "Problem"')
        sys.exit(1)
    run_agent(sys.argv[1], sys.argv[2])
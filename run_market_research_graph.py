import sys
import os

# Add the project root to python path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.graph.workflow import app_graph
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def run_agent(idea, problem_statement):
    print(f"🚀 Running Market Research Graph for: '{idea}'")
    initial_state = {
        "input_idea": idea,
        "input_problem": problem_statement,
        "evaluation": None,
        "recommendation": None,
        "market_research": None,
        "ppt_path": None
    }
    
    try:
        result = app_graph.invoke(initial_state)
        print("\n✅ Graph execution finished successfully!")
        print("Final State Snippet:")
        print(f"Market Research: {str(result.get('market_research'))[:100]}...")
    except Exception as e:
        print(f"❌ Graph execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print('Usage: python run_market_research_graph.py "Idea" "Problem"')
        # Default for testing if arguments (optional)
        # run_agent("Cat Cafe in Cairo", "People want a place to relax with pets")
        sys.exit(1)
    run_agent(sys.argv[1], sys.argv[2])

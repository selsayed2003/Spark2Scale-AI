from app.graph.workflow import app_graph
import os
import sys

# Mock API keys for testing if they are not set
if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = "sk-mock-key"
if "TAVILY_API_KEY" not in os.environ:
    os.environ["TAVILY_API_KEY"] = "tvly-mock-key"

def test_workflow():
    print("Starting Workflow Test...")
    initial_state = {"input_idea": "AI-powered sustainable farming platform"}
    
    try:
        # Invoke the graph
        result = app_graph.invoke(initial_state)
        
        print("\nWorkflow Execution Successful!")
        print("-" * 30)
        print(f"Input Idea: {result.get('input_idea')}")
        print(f"Market Research: {result.get('market_research')}")
        print(f"Evaluation: {result.get('evaluation')}")
        print(f"Recommendation: {result.get('recommendation')}")
        print(f"PPT Path: {result.get('ppt_path')}")
        print("-" * 30)
        
    except Exception as e:
        print(f"\nWorkflow Failed: {str(e)}")

if __name__ == "__main__":
    # Add current directory to path to ensure imports work
    sys.path.append(os.getcwd())
    test_workflow()

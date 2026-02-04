import time
import os
from langgraph.graph import StateGraph, END, START
from .state import AgentState
from .node import (
    planner_node,
    team_node,
    problem_node,
    product_tools_node,
    product_scoring_node
)

# 1. Initialize Graph
workflow = StateGraph(AgentState)

# 2. Add Nodes
workflow.add_node("planner_node", planner_node)
workflow.add_node("team_node", team_node)
workflow.add_node("problem_node", problem_node)
workflow.add_node("product_tools_node", product_tools_node)
workflow.add_node("product_scoring_node", product_scoring_node)

# 3. Define Edges
# Start -> Planner
workflow.add_edge(START, "planner_node")

# Planner -> Parallel Execution (Team, Problem, Product)
workflow.add_edge("planner_node", "team_node")
workflow.add_edge("planner_node", "problem_node")
workflow.add_edge("planner_node", "product_tools_node")

# Team Branch -> End
workflow.add_edge("team_node", END)

# Problem Branch -> End
workflow.add_edge("problem_node", END)

# Product Branch
workflow.add_edge("product_tools_node", "product_scoring_node")
workflow.add_edge("product_scoring_node", END)

# 4. Compile
app = workflow.compile()

async def run_pipeline(user_data):
    """
    Helper to run the graph with timing.
    """
    start_time = time.time()
    initial_state = {"user_data": user_data}
    
    print("🚀 Starting Logic Graph Execution...")
    try:
        result = await app.ainvoke(initial_state)
    except Exception as e:
        print(f"🔥 Graph Execution Error: {e}")
        raise e
        
    end_time = time.time()
    duration = end_time - start_time
    print(f"✅ Graph Finished in {duration:.2f} seconds.")
    
    # Inject timing info into result if needed, or just return result
    # result["_execution_time"] = duration 
    return result

def save_graph_image(file_path="graph_visualization.png"):
    """
    Generates and saves a mermaid PNG of the graph.
    Requires graphviz/mermaid cli tools or ipython context, 
    but `draw_mermaid_png` returns binary data we can write to file.
    """
    try:
        png_data = app.get_graph().draw_mermaid_png()
        with open(file_path, "wb") as f:
            f.write(png_data)
        print(f"🖼️ Graph visualization saved to {file_path}")
    except Exception as e:
        print(f"⚠️ Could not save graph image: {e}")

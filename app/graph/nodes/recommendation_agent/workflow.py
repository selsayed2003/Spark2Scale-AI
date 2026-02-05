from .schema import StartupData
from .helpers import extract_key_insights
from .tools import detect_patterns
from .node import AgentNodes

def run_recommendation_agent(raw_input, eval_output, api_key):
    # 1. Parse & Validate
    data = StartupData(**eval_output)
    insights = extract_key_insights(raw_input)
    
    # 2. Deterministic Analysis
    matched_patterns = detect_patterns(data.scores)
    
    # 3. AI Nodes
    agent = AgentNodes(api_key)
    replacements = agent.improve_statements(insights)
    final_report = agent.synthesize_report(data, matched_patterns, insights, replacements)
    
    return final_report
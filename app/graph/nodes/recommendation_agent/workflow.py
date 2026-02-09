from .schema import StartupData
from .helpers import extract_key_insights
from .tools import detect_patterns
from .node import AgentNodes
from app.utils.output_manager import OutputManager
import time

def run_recommendation_agent(raw_input, eval_output, api_key, save_output=True, request_id=None):
    """
    Run the recommendation agent workflow
    
    Args:
        raw_input: Raw startup input data
        eval_output: Evaluation output data
        api_key: Gemini API key
        save_output: Whether to save output to files (default: True)
        request_id: Optional request ID for tracking
        
    Returns:
        tuple: (final_report, output_paths) or just final_report if save_output=False
    """
    start_time = time.time()
    
    # 1. Parse & Validate
    data = StartupData(**eval_output)
    insights = extract_key_insights(raw_input)
    
    # 2. Convert Pydantic scores to dict format for pattern detection
    # Pattern detection expects: scores['team']['score'] and scores['team']['description']
    scores_dict = data.scores.model_dump()
    
    # 3. Deterministic Analysis
    matched_patterns = detect_patterns(scores_dict)
    
    # 4. AI Nodes
    agent = AgentNodes(api_key)
    replacements = agent.improve_statements(insights)
    final_report = agent.synthesize_report(data, matched_patterns, insights, replacements)
    
    # 5. Save output if requested
    output_paths = None
    if save_output:
        processing_time = time.time() - start_time
        output_manager = OutputManager()
        output_paths = output_manager.save_recommendation(
            recommendation_text=final_report,
            raw_input=raw_input,
            eval_output=eval_output,
            insights=insights,
            patterns=matched_patterns,
            refined_statements=replacements,  # Add refined statements
            request_id=request_id,
            processing_time=processing_time
        )
        print(f"\n✅ Output saved to: {output_paths['folder']}")
        print(f"   - JSON: {output_paths['files']['json']}")
        print(f"   - Markdown: {output_paths['files']['markdown']}")
    
    return (final_report, output_paths) if save_output else final_report


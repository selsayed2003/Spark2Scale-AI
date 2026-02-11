import asyncio
import os
from app.graph.ppt_generation_agent import app_graph
from app.graph.ppt_generation_agent.state import PPTGenerationState
from app.graph.ppt_generation_agent.utils import generate_pptx_file

async def main():
    print("Starting PPT Generation with Logo Theme...")
    
    # Paths relative to project root
    logo_path = "app/graph/ppt_generation_agent/input/Logo.jpg"
    output_dir = "app/graph/ppt_generation_agent/output"
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    import time
    timestamp = int(time.time())
    output_filename = os.path.join(output_dir, f"logo_themed_v{timestamp}.pptx")
    
    # Load Data from CSVs (just like the original flow)
    input_dir = "app/graph/ppt_generation_agent/input"
    combined_research = []
    
    for filename in ["startup info.csv", "market research.csv"]:
        filepath = os.path.join(input_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                combined_research.append(f"--- Data from {filename} ---\n{f.read()}")
    
    research_data = "\n\n".join(combined_research) if combined_research else "Create a professional pitch deck."
    
    # Initial state with logo path
    initial_state: PPTGenerationState = {
        "research_data": research_data,
        "logo_path": logo_path,
        "color_palette": None,
        "use_default_colors": False, # Set to False to use the logo colors!
        "draft": None,
        "critique": None,
        "iteration": 0,
        "ppt_path": None
    }
    
    try:
        print("Running AI Agents (Generation -> Recommendation -> Refinement)...")
        final_state = await app_graph.ainvoke(initial_state)
        
        final_draft = final_state.get("draft")
        if final_draft:
            print(f"Draft generated: {final_draft.title}")
            print(f"Theme used: {final_draft.theme} (Dynamic colors from logo applied)")
            
            print(f"Saving PPTX to: {output_filename}")
            await generate_pptx_file(final_draft, output_filename)
            
            if os.path.exists(output_filename):
                print(f"\nSUCCESS! Your presentation is ready at: {output_filename}")
            else:
                print("\nError: PPTX file was not created.")
        else:
            print("\nError: Draft generation failed.")
            
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg and "RESOURCE_EXHAUSTED" in error_msg:
            print("\n" + "="*50)
            print("⚠️  GEMINI API QUOTA EXHAUSTED")
            print("="*50)
            print("Your Gemini API free tier limit has been reached.")
            print("Please wait 1-2 minutes for the quota to reset and try again.")
            print("="*50)
        else:
            print(f"\n❌ Error during generation: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())

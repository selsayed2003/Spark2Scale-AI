import asyncio
import os
from app.graph.ppt_generation_agent import app_graph
from app.graph.ppt_generation_agent.state import PPTGenerationState
from app.graph.ppt_generation_agent.utils import generate_pptx_file

import logging

# Configure logging to file
logging.basicConfig(
    filename='reproduction.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    force=True
)

async def main():
    print("Starting PPT Generation Reproduction...")
    logging.info("Starting PPT Generation Reproduction...")
    
    research_data = "Create a pitch deck for an AI-powered bakery."
    
    initial_state: PPTGenerationState = {
        "research_data": research_data,
        "draft": None,
        "critique": None,
        "iteration": 0,
        "ppt_path": None
    }
    
    logging.info("Invoking agent graph...")
    try:
        final_state = await app_graph.ainvoke(initial_state)
        logging.info(f"Agent graph finished. Keys in state: {final_state.keys()}")
        
        final_draft = final_state.get("draft")
        if final_draft:
            logging.info(f"Draft generated: {final_draft.title}")
            print(f"Draft generated: {final_draft.title}")
            
            output_dir = os.path.join(os.getcwd(), "reproduction_output")
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
                
            output_filename = os.path.join(output_dir, "generated_presentation.pptx")
            
            logging.info(f"Generating PPTX file at: {output_filename}")
            await generate_pptx_file(final_draft, output_filename)
            
            if os.path.exists(output_filename):
                logging.info("SUCCESS: PPTX file created successfully.")
                print("SUCCESS: PPTX file created successfully.")
            else:
                logging.error("FAILURE: PPTX file was not found after generation.")
                print("FAILURE: PPTX file was not found after generation.")
                
        else:
            logging.error("FAILURE: Agent failed to generate a draft. State: " + str(final_state))
            print("FAILURE: Agent failed to generate a draft.")
            
    except Exception as e:
        print(f"ERROR: An exception occurred: {e}")
        logging.error(f"ERROR: An exception occurred: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())

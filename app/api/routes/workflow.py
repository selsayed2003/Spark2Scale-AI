from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.graph.market_research_agent.workflow import market_research_app
from app.api.schemas import ResearchRequest, ResearchResponse
from app.graph.market_research_agent.logger_config import get_logger

logger = get_logger("API")

router = APIRouter()

@router.post("/research", response_model=ResearchResponse)
async def run_market_research(request: ResearchRequest):
    logger.info(f"Received API Request for Idea: '{request.idea}'")
    print("DEBUG: VERSION CHECK - LOADED NEW CODE WITH NONE CHECK", flush=True)
    
    initial_state = {
        "input_idea": request.idea,
        "input_problem": request.problem
    }
    
    try:
        print(f"DEBUG: Invoking with {initial_state}", flush=True)
        result = market_research_app.invoke(initial_state)
        print(f"DEBUG: Result type: {type(result)}", flush=True)
        print(f"DEBUG: Result: {result}", flush=True)
        
        if result is None:
            raise ValueError("Workflow invocation returned None")
            
        pdf_path = result.get("pdf_path")
        json_path = result.get("json_path")
        
        # Read the JSON content to return in response
        json_content = {}
        if json_path:
            import json
            import os
            try:
                if os.path.exists(json_path):
                    with open(json_path, "r", encoding="utf-8") as f:
                        json_content = json.load(f)
            except Exception as read_err:
                logger.error(f"Failed to read JSON output: {read_err}")
        
        return ResearchResponse(
            message="Market Research Completed Successfully",
            pdf_path=pdf_path,
            json_path=json_path,
            data=json_content
        )
        
    except Exception as e:
        logger.error(f"API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

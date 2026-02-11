import json
import os
import time
import asyncio
from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from pydantic import BaseModel
from fastapi.responses import FileResponse
from app.utils.pdf_generator import generate_founder_report, generate_investor_report
import zipfile
import uuid
from app.graph.evaluation_agent.helpers import normalize_input_data

# --- Import Logger ---
from app.core.logger import get_logger

# --- Import Individual Nodes ---
from app.graph.evaluation_agent.node import (
    team_node,
    problem_node,
    market_node,
    traction_node,
    gtm_node,
    business_node,
    vision_node,
    operations_node,
    # Product Nodes
    product_final_scoring_node,
    product_tools_node,
    product_contradiction_node,
    product_risk_node
)

# --- Import the Main Graph ---
from app.graph.evaluation_agent import evaluation_graph

router = APIRouter()
logger = get_logger(__name__)

class EvalInput(BaseModel):
    startup_evaluation: Dict[str, Any]


class RawInput(BaseModel):
    data: Any

# --- Helper to Save JSON ---
def save_agent_output(agent_name: str, data: dict):
    directory = "outputs"
    if not os.path.exists(directory):
        os.makedirs(directory)
    
    filepath = os.path.join(directory, f"{agent_name}_output.json")
    
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    logger.info(f"💾 Saved {agent_name} output to {filepath}")

# =========================================================
# 1. INDIVIDUAL AGENT ENDPOINTS
# =========================================================

@router.post("/evaluate/team")
async def run_team_agent(input_data: EvalInput):
    start_time = time.time()
    logger.info("🚀 Starting Team Evaluation...")
    try:
        state = {"user_data": input_data.model_dump()}
        result = await team_node(state)
        
        save_agent_output("team", result)
        
        duration = time.time() - start_time
        logger.info(f"✅ Team Analysis finished in {duration:.2f}s")
        return result
    except Exception as e:
        logger.error(f"❌ Team Analysis Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate/problem")
async def run_problem_agent(input_data: EvalInput):
    start_time = time.time()
    logger.info("🚀 Starting Problem Evaluation...")
    try:
        state = {"user_data": input_data.model_dump()}
        result = await problem_node(state)
        
        save_agent_output("problem", result)
        
        duration = time.time() - start_time
        logger.info(f"✅ Problem Analysis finished in {duration:.2f}s")
        return result
    except Exception as e:
        logger.error(f"❌ Problem Analysis Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate/market")
async def run_market_agent(input_data: EvalInput):
    start_time = time.time()
    logger.info("🚀 Starting Market Evaluation...")
    try:
        state = {"user_data": input_data.model_dump()}
        result = await market_node(state)
        
        save_agent_output("market", result)
        
        duration = time.time() - start_time
        logger.info(f"✅ Market Analysis finished in {duration:.2f}s")
        return result
    except Exception as e:
        logger.error(f"❌ Market Analysis Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate/traction")
async def run_traction_agent(input_data: EvalInput):
    start_time = time.time()
    logger.info("🚀 Starting Traction Evaluation...")
    try:
        state = {"user_data": input_data.model_dump()}
        result = await traction_node(state)
        
        save_agent_output("traction", result)
        
        duration = time.time() - start_time
        logger.info(f"✅ Traction Analysis finished in {duration:.2f}s")
        return result
    except Exception as e:
        logger.error(f"❌ Traction Analysis Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate/gtm")
async def run_gtm_agent(input_data: EvalInput):
    start_time = time.time()
    logger.info("🚀 Starting GTM Evaluation...")
    try:
        state = {"user_data": input_data.model_dump()}
        result = await gtm_node(state)
        
        save_agent_output("gtm", result)
        
        duration = time.time() - start_time
        logger.info(f"✅ GTM Analysis finished in {duration:.2f}s")
        return result
    except Exception as e:
        logger.error(f"❌ GTM Analysis Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate/business")
async def run_business_agent(input_data: EvalInput):
    start_time = time.time()
    logger.info("🚀 Starting Business Model Evaluation...")
    try:
        state = {"user_data": input_data.model_dump()}
        result = await business_node(state)
        
        save_agent_output("business", result)
        
        duration = time.time() - start_time
        logger.info(f"✅ Business Analysis finished in {duration:.2f}s")
        return result
    except Exception as e:
        logger.error(f"❌ Business Analysis Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate/vision")
async def run_vision_agent(input_data: EvalInput):
    start_time = time.time()
    logger.info("🚀 Starting Vision Evaluation...")
    try:
        state = {"user_data": input_data.model_dump()}
        result = await vision_node(state)
        
        save_agent_output("vision", result)
        
        duration = time.time() - start_time
        logger.info(f"✅ Vision Analysis finished in {duration:.2f}s")
        return result
    except Exception as e:
        logger.error(f"❌ Vision Analysis Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/evaluate/operations")
async def run_operations_agent(input_data: EvalInput):
    start_time = time.time()
    logger.info("🚀 Starting Operations Evaluation...")
    try:
        state = {"user_data": input_data.model_dump()}
        result = await operations_node(state)
        
        save_agent_output("operations", result)
        
        duration = time.time() - start_time
        logger.info(f"✅ Operations Analysis finished in {duration:.2f}s")
        return result
    except Exception as e:
        logger.error(f"❌ Operations Analysis Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =========================================================
# SPECIAL CASE: PRODUCT AGENT (Complex Dependency)
# =========================================================

@router.post("/evaluate/product")
async def run_product_agent(input_data: EvalInput):
    start_time = time.time()
    logger.info("🚀 Starting Product Evaluation (Fan-Out)...")
    try:
        state = {"user_data": input_data.model_dump()}
        
        # 1. Run the Fan-Out Nodes manually in parallel
        tools_res, risk_res, contra_res = await asyncio.gather(
            product_tools_node(state),
            product_risk_node(state),
            product_contradiction_node(state)
        )
        
        # 2. Update state
        state.update(tools_res)
        state.update(risk_res)
        state.update(contra_res)
        
        # 3. Run Final Scoring
        final_result = await product_final_scoring_node(state)
        
        save_agent_output("product", final_result)
        
        duration = time.time() - start_time
        logger.info(f"✅ Product Analysis finished in {duration:.2f}s")
        return final_result
        
    except Exception as e:
        logger.error(f"❌ Product Analysis Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =========================================================
# 2. MAIN "RUN ALL" ENDPOINT
# =========================================================

@router.post("/evaluate/all")
async def evaluate_all(raw_payload: RawInput):
    start_time = time.time()
    
    # 1. NORMALIZE (The new first step)
    # Convert input to string if it's a dict to pass to LLM prompt
    raw_str = json.dumps(raw_payload.data) if isinstance(raw_payload.data, dict) else str(raw_payload.data)
    
    normalized_data = await normalize_input_data(raw_str)
    
    # 2. RUN PIPELINE (Pass normalized data)
    logger.info("🚀 Starting FULL Evaluation Pipeline with Normalized Data...")
    try:
        # Run the full LangGraph
        state = await evaluation_graph.ainvoke({"user_data": normalized_data})
        
        # Filter output
        full_report = {
            "team_report": state.get("team_report"),
            "problem_report": state.get("problem_report"),
            "product_report": state.get("product_report"),
            "market_report": state.get("market_report"),
            "traction_report": state.get("traction_report"),
            "gtm_report": state.get("gtm_report"),
            "business_report": state.get("business_report"),
            "vision_report": state.get("vision_report"),
            "operations_report": state.get("operations_report"),
            "final_report": state.get("final_report")
        }
        
        save_agent_output("FULL_REPORT", full_report)
        
        duration = time.time() - start_time
        logger.info(f"✅ FULL Evaluation finished in {duration:.2f}s")
        return full_report
        
    except Exception as e:
        logger.error(f"❌ Full Evaluation Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/generate-report")
async def generate_reports_endpoint(report_data: Dict[str, Any]):
    """
    Generates both Founder and Investor reports and returns them as a ZIP.
    """
    try:
        # Create output dir
        os.makedirs("outputs", exist_ok=True)
        base_id = uuid.uuid4().hex[:6]
        
        # 1. Generate Founder PDF
        f_path = f"outputs/Founder_Report_{base_id}.pdf"
        generate_founder_report(report_data, f_path)
        
        # 2. Generate Investor PDF
        i_path = f"outputs/Investor_Memo_{base_id}.pdf"
        generate_investor_report(report_data, i_path)
        
        # 3. Zip them together
        zip_filename = f"outputs/Evaluation_Package_{base_id}.zip"
        with zipfile.ZipFile(zip_filename, 'w') as zipf:
            zipf.write(f_path, os.path.basename(f_path))
            zipf.write(i_path, os.path.basename(i_path))
            
        return FileResponse(
            path=zip_filename, 
            filename="Spark2Scale_Evaluation_Package.zip", 
            media_type='application/zip'
        )
        
    except Exception as e:
        logger.error(f"❌ PDF Generation Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
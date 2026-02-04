import asyncio
import json
from .state import AgentState
from .tools import (
    contradiction_check, 
    team_risk_check, 
    team_scoring_agent,
    verify_problem_claims, 
    loaded_risk_check_with_search, 
    problem_scoring_agent,
    tech_stack_detective, 
    analyze_visuals_with_langchain, 
    product_scoring_agent
)
from .prompts import (
    PLANNER_PROMPT,
    CONTRADICTION_TEAM_PROMPT_TEMPLATE,
    VALUATION_RISK_TEAM_PROMPT_TEMPLATE,
    CONTRADICTION_PROBLEM_PROMPT_TEMPLATE,
    VALUATION_RISK_PROBLEM_PROMPT_TEMPLATE,
    CONTRADICTION_PRODUCT_PROMPT_TEMPLATE, 
    VALUATION_RISK_PRODUCT_PROMPT_TEMPLATE,
    VISUAL_VERIFICATION_PROMPT
)
from .helpers import (
    extract_team_data, 
    extract_problem_data, 
    extract_product_data, 
    check_missing_fields
)
from .schema import Plan
from langchain_google_genai import ChatGoogleGenerativeAI
import os

async def planner_node(state: AgentState):
    """
    Generates a strategic plan for the evaluation based on initial user data.
    """
    user_data = state.get("user_data", {})
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        temperature=0, 
        google_api_key=os.environ.get("GEMINI_API_KEY")
    )
    
    # Structured output binding
    structured_llm = llm.with_structured_output(Plan)
    
    try:
        plan_obj = await structured_llm.ainvoke(
            PLANNER_PROMPT.format(user_data=json.dumps(user_data, indent=2))
        )
        return {"plan": plan_obj.model_dump()}
    except Exception as e:
        # Fallback empty plan if fails
        return {"plan": {"steps": [], "key_risks": ["Planning Failed"], "desired_output_structure": []}}

async def team_node(state: AgentState):
    """
    Parallel Execution of Team Contradiction & Risk Checks, followed by Scoring.
    """
    user_data = state.get("user_data", {})
    team_data = extract_team_data(user_data)
    missing_report = check_missing_fields(user_data) 

    # Parallel Execution
    contradiction_task = contradiction_check(team_data, CONTRADICTION_TEAM_PROMPT_TEMPLATE)
    risk_task = team_risk_check(team_data, VALUATION_RISK_TEAM_PROMPT_TEMPLATE)
    
    contradiction_res, risk_res = await asyncio.gather(contradiction_task, risk_task)
    
    # Scoring
    package = {
        "user_data": team_data,
        "risk_report": risk_res,
        "contradiction_report": contradiction_res,
        "missing_report": missing_report
    }
    score = await team_scoring_agent(package)
    
    return {"team_report": score}

async def problem_node(state: AgentState):
    """
    Parallel Execution of Search & Contradiction, followed by Risk, then Scoring.
    """
    user_data = state.get("user_data", {})
    problem_data = extract_problem_data(user_data)
    problem_def = user_data.get("startup_evaluation", {}).get("problem_definition", {})
    missing_report = check_missing_fields(user_data)

    # 1. Parallel: Search & Contradiction
    search_task = verify_problem_claims(
        problem_statement=problem_def.get("problem_statement", ""),
        target_audience=problem_def.get("customer_profile", {}).get("role", "")
    )
    contradiction_task = contradiction_check(problem_data, CONTRADICTION_PROBLEM_PROMPT_TEMPLATE)

    search_res, contradiction_res = await asyncio.gather(search_task, contradiction_task)

    # 2. Risk Check (Needs Search Results)
    risk_res = await loaded_risk_check_with_search(
        problem_data=problem_def,
        search_results=search_res,
        agent_prompt=VALUATION_RISK_PROBLEM_PROMPT_TEMPLATE
    )

    # 3. Scoring
    package = {
        "problem_definition": problem_def,
        "missing_report": missing_report,
        "search_report": search_res,
        "risk_report": risk_res,
        "contradiction_report": contradiction_res
    }
    score = await problem_scoring_agent(package)

    return {
        "problem_report": score,
        "search_results": search_res,
        "risk_report": risk_res,
        "contradiction_report": contradiction_res
    }

async def product_tools_node(state: AgentState):
    """
    Parallel: Tech Stack, Visual Analysis, Contradiction Check.
    """
    user_data = state.get("user_data", {})
    product_data = extract_product_data(user_data)
    
    url = user_data.get("startup_evaluation", {}).get("company_snapshot", {}).get("website_url", "")
    company = user_data.get("startup_evaluation", {}).get("company_snapshot", {}).get("company_name", "Startup")

    # Parallel Tasks
    tech_task = tech_stack_detective(url)
    visual_task = analyze_visuals_with_langchain(company, url, VISUAL_VERIFICATION_PROMPT)
    contradiction_task = contradiction_check(product_data, CONTRADICTION_PRODUCT_PROMPT_TEMPLATE)
    
    tech_res, visual_res, contradiction_res = await asyncio.gather(
        tech_task, visual_task, contradiction_task
    )
    
    return {
        "tech_stack": tech_res, 
        "visual_analysis": visual_res,
        "product_contradiction": contradiction_res 
    }

async def product_scoring_node(state: AgentState):
    """
    Product Risk, then Scoring.
    """
    search_res = state.get("search_results")
    if not search_res:
         problem_def = state.get("user_data", {}).get("startup_evaluation", {}).get("problem_definition", {})
         search_res = await verify_problem_claims(
            problem_statement=problem_def.get("problem_statement", ""),
            target_audience=problem_def.get("customer_profile", {}).get("role", "")
         )
    
    competitors = search_res.get("competitor_search", [])
    
    user_data = state.get("user_data", {})
    
    risk_res = await loaded_risk_check_with_search(
        problem_data=extract_product_data(user_data), 
        search_results=competitors,
        agent_prompt=VALUATION_RISK_PRODUCT_PROMPT_TEMPLATE
    )

    package = {
        "internal_data": extract_product_data(user_data),
        "contradiction_report": state.get("product_contradiction", "None"),
        "risk_report": risk_res,
        "tech_stack_report": state.get("tech_stack"),
        "visual_analysis_report": state.get("visual_analysis")
    }
    
    score = await product_scoring_agent(package)
    
    return {"product_report": score}
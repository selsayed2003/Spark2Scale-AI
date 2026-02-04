import os
from langchain_core.messages import SystemMessage, HumanMessage
from app.core.llm import get_llm
from app.core.logger import get_logger
from .state import PPTGenerationState
from .schema import PPTDraft, Critique
from .prompts import GENERATOR_SYSTEM_PROMPT, RECOMMENDER_SYSTEM_PROMPT, REFINER_SYSTEM_PROMPT

logger = get_logger(__name__)
llm = get_llm()

def generator_node(state: PPTGenerationState) -> PPTGenerationState:
    logger.info("--- GENERATING PPT DRAFT ---")
    research_content = state["research_data"]
    
    structured_llm = llm.with_structured_output(PPTDraft)
    
    response = structured_llm.invoke([
        SystemMessage(content=GENERATOR_SYSTEM_PROMPT),
        HumanMessage(content=f"Create a presentation based on this research:\n\n{research_content}")
    ])
    
    return {"draft": response, "iteration": state["iteration"]}

def recommender_node(state: PPTGenerationState) -> PPTGenerationState:
    logger.info("--- RECOMMENDING IMPROVEMENTS ---")
    draft = state["draft"]
    
    structured_llm = llm.with_structured_output(Critique)
    
    response = structured_llm.invoke([
        SystemMessage(content=RECOMMENDER_SYSTEM_PROMPT),
        HumanMessage(content=f"Review this presentation draft:\n\n{draft.model_dump_json()}")
    ])
    
    return {"critique": response, "iteration": state["iteration"]}

def refiner_node(state: PPTGenerationState) -> PPTGenerationState:
    logger.info("--- REFINING PPT DRAFT ---")
    draft = state["draft"]
    critique = state["critique"]
    research_content = state["research_data"]
    
    structured_llm = llm.with_structured_output(PPTDraft)
    
    response = structured_llm.invoke([
        SystemMessage(content=REFINER_SYSTEM_PROMPT),
        HumanMessage(content=f"""
        Refine this draft based on the critique.
        
        Original Research:
        {research_content}
        
        Current Draft:
        {draft.model_dump_json()}
        
        Critique & Recommendations:
        {critique.model_dump_json()}
        """)
    ])
    
    return {"draft": response, "iteration": state["iteration"] + 1}

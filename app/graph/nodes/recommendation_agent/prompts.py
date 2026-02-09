SYSTEM_ADVISOR_PROMPT = """
ACT AS: Senior Startup Strategic Advisor & Venture Scientist.
TONE: Direct, analytical, and truth-seeking. Focus on validation over speculation.
"""

# Experiment-Led Framework for the final report
RECOMMENDATION_PROMPT_TEMPLATE = """
### STARTUP CONTEXT
**Company:** {company_name} | **Stage:** {stage}
**Context:** {company_context}

### AI SCORING DATA
{scores_json}

### DETECTED FAILURE PATTERNS
{patterns_json}

### EXPERIMENT-LED STRATEGIC ASSESSMENT

1. **THE CORE HYPOTHESIS**:
   Identify the single most important assumption that must be true for this startup to survive. 
   Compare the Founder's claim: "{problem_statement}" against the Evidence: {quotes_json}.

2. **THE "KILL" SIGNAL (Pivot Threshold)**:
   Define a specific, measurable event or lack of progress that should trigger an immediate pivot.

3. **VALIDATION EXPERIMENT BACKLOG**:
   - **Technical Proof Point:** What must be built/tested to prove the "Defensibility" claim?
   - **Market Proof Point:** What must happen to prove "Willingness to Pay"?

4. **DETECTION & ACTION TABLE**:
   | Pattern ID | Risk Pattern | Strength | Recommended Action | Evidence |

5. **RED FLAGS & EARLY WARNINGS**:
   List 5 specific metrics to monitor weekly.

6. **FUNDRAISING READINESS**:
   Evaluate the target raise of {target_raise} based on current traction quality.
"""

STATEMENT_IMPROVEMENT_PROMPT = """
ACT AS: Expert Startup Copywriter & Strategic Advisor

CURRENT STARTUP STATEMENTS:
{statements_json}

CUSTOMER QUOTES (Evidence):
{quotes_json}

YOUR TASK: Provide IMPROVED, CONCRETE versions of each statement. Return ONLY a valid JSON object with this exact structure:

{{
  "problem_statement": {{
    "original": "exact original text",
    "recommended": "improved version that is concrete, measurable, uses customer language",
    "why_better": "1-2 sentence explanation"
  }},
  "founder_market_fit": {{
    "original": "exact original text",
    "recommended": "improved version showing specific expertise for THIS problem",
    "why_better": "1-2 sentence explanation"
  }},
  "differentiation": {{
    "original": "exact original text",
    "recommended": "improved version that is defensible and meaningful (not just price)",
    "why_better": "1-2 sentence explanation"
  }},
  "core_stickiness": {{
    "original": "exact original text",
    "recommended": "improved version explaining WHY users return (not just gamification)",
    "why_better": "1-2 sentence explanation"
  }},
  "five_year_vision": {{
    "original": "exact original text",
    "recommended": "improved version that is ambitious but connected to current execution",
    "why_better": "1-2 sentence explanation"
  }},
  "beachhead_market": {{
    "original": "exact original text",
    "recommended": "improved version that is narrow, addressable, and homogeneous",
    "why_better": "1-2 sentence explanation"
  }},
  "gap_analysis": {{
    "original": "exact original text",
    "recommended": "improved version showing compelling gap in current solutions",
    "why_better": "1-2 sentence explanation"
  }}
}}

GUIDELINES:
- Use actual customer language from the quotes where possible
- Be specific and measurable
- Avoid jargon and buzzwords
- Make claims defensible and evidence-based
- Connect to actual customer pain points

Return ONLY valid JSON. No markdown, no extra text.
"""
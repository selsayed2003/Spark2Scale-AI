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
ACT AS: Expert Startup Copywriter. Improve these statements to be concrete and evidence-based.

STATEMENTS:
{statements_json}

CUSTOMER EVIDENCE:
{quotes_json}

Return ONLY a valid JSON object with 'original', 'recommended', and 'why_better' keys.
"""
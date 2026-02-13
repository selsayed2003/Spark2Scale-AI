MARKET_RESEARCH_SYSTEM_PROMPT = """
You are a top-tier market researcher. Analyze the market trends, competitors, and potential opportunities.
"""

def generate_research_plan_prompt(idea, problem):
    return f"""
    ROLE: Lead Market Researcher.
    GOAL: Plan the entire research strategy for "{idea}" (Problem: "{problem}").
    
    TASK: Generate a JSON object containing ALL necessary search parameters.
    
    OUTPUT STRUCTURE (Strict JSON):
    {{
        "competitor_queries": ["query1", "query2 (vs/alternatives)"],
        "validation_queries": {{
            "problem": ["query1 (reddit/forum)"],
            "solution": ["query1 (reviews/feedback)"]
        }},
        "market_identity": {{
            "industry": "Industry Name",
            "wikipedia_topic": "Wikipedia_Title_With_Underscores",
            "target_country": "Detect from idea or default 'Global'",
            "currency_code": "USD/EGP/etc",
            "currency_symbol": "$"
        }},
        "financial_queries": ["salary query", "rent query"]
    }}
    
    RULES:
    1. Competitor Queries: Focus on finding specific app names (e.g., "{idea} alternatives").
    2. Wikipedia Topic: Must be a valid existing article title (e.g. "Online_dating_service").
    3. Country: If idea implies a location (e.g. "in Cairo"), use it. Else Global/US.
    4. Financials: tailored to the detected country.
    """

def generate_smart_queries_prompt(business_idea):
    return f"""
    Business Idea: "{business_idea}"
    Generate 4 Google Search Queries to find SPECIFIC COMPETITOR APP NAMES.
    Focus on: "alternatives to", "vs", "pricing", "features".
    RETURN JSON list of strings.
    """

def extract_competitors_prompt(business_idea, search_data_text):
    return f"""
    You are a Data Cleaner.
    Topic: "{business_idea}"
    Search Results:
    {search_data_text}
    
    TASK: List the top 5 DIRECT COMPETITORS (Company/App Names Only).
    
    CRITICAL RULES:
    1. DO NOT return article titles (e.g. "Top 10 Apps"). Extract the APP NAME inside (e.g. "Tinder").
    2. DO NOT return generic terms (e.g. "AI Dating").
    3. EXTRACT 3 KEY FEATURES for each.
    
    RETURN JSON List:
    [
        {{ "Name": "App Name", "Features": "Feature A, Feature B" }},
        {{ "Name": "App Name", "Features": "Feature C, Feature D" }}
    ]
    """

def generate_validation_queries_prompt(idea, problem_statement):
    return f"Idea: {idea} | Problem: {problem_statement}. Return JSON: {{ 'problem_queries': ['q1'], 'solution_queries': ['q2'] }}"

def analyze_pain_points_prompt(idea, problem_statement, evidence):
    formatted_evidence = evidence
    if isinstance(evidence, list):
        formatted_evidence = "\n".join([str(e) for e in evidence])

    return f"""
    HYPOTHESIS: '{idea}' solves '{problem_statement}'.
    EVIDENCE: 
    {formatted_evidence}
    
    TASK:
    1. Assign a PAIN SCORE (0-100). How intense is the user's frustration?
       - 0-20: Mild inconvenience.
       - 80-100: Urgent, emotional, expensive problem.
    2. Verdict & Reasoning.
    
    OUTPUT JSON: 
    {{ 
        "verdict": "VALIDATED/WEAK/INVALID", 
        "pain_score": 0,
        "pain_score_reasoning": "Why you gave this score",
        "solution_fit_score": "High/Medium/Low",
        "reasoning": "..." 
    }}
    """

def identify_industry_prompt(idea):
    return f"Identify the broader 'Industry' for: '{idea}'. Return ONLY the string (e.g. 'Online Dating Services')."

def wiki_fallback_prompt(query):
    return f"""
    Task: Identify the main Wikipedia Article Title for the industry of: "{query}".
    Examples:
    - "Cat Cafe" -> "Cat_café"
    - "AI Dating App" -> "Online_dating_service"
    - "Solar Panels" -> "Solar_power"
    
    RETURN ONLY THE TITLE STRING (No quotes, use underscores for spaces).
    """

def analyze_market_size_prompt(idea, industry, location, market_data):
    return f"""
    You are a Market Sizing Expert.
    
    IDEA: {idea}
    INDUSTRY: {industry}
    LOCATION: {location}
    SEARCH DATA: 
    {market_data}
    
    TASK: Estimate TAM, SAM, and SOM.
    - TAM (Total Addressable Market): The big number (Global or National revenue).
    - SAM (Serviceable Available Market): The segment relevant to this specific idea/location.
    - SOM (Serviceable Obtainable Market): Realistic capture (e.g. 1-5% of SAM) for a startup.
    
    Also analyze:
    - RED vs BLUE OCEAN: Is it crowded?
    - SCALABILITY: Is it High (Software) or Low (Service)?
    
    RETURN JSON:
    {{
        "tam_value": "$X Billion",
        "tam_description": "Context for TAM...",
        "sam_value": "$X Million",
        "sam_description": "Context for SAM...",
        "som_value": "$X Million",
        "som_description": "Context for SOM...",
        "market_type": "Red Ocean / Blue Ocean",
        "scalability_score": "High/Medium/Low",
        "scalability_reasoning": "Why...",
        "sources": ["Source 1", "Source 2"]
    }}
    """

def detect_currency_prompt(idea):
    return f"""
    Analyze this business idea: "{idea}"
    RETURN JSON: {{ "country": "CountryName", "currency_code": "XXX", "currency_symbol": "$" }}
    """

def financial_plan_prompt(idea, country, currency_code):
    return f"""
    Business: "{idea}"
    Location: {country}
    Currency: {currency_code}
    TASK: Generate 5 SPECIFIC search queries to find real-world numeric cost data.
    Focus on:
    1. Employee salaries (Developer, Marketing) in {country}.
    2. Specific infrastructure costs (e.g. AWS/Azure pricing, Rent in {country}).
    3. Legal/License fees for this specific business type in {country}.
    4. Competitor pricing/Customer acquisition cost benchmarks.
    
    RETURN JSON list of strings. Example: ["Average software engineer salary {country} 2024", "Commercial office rent price {country} per sqm"]
    """

def financial_extraction_prompt(idea, market_data, currency_code):
    return f"""
    You are a Conservative CFO.
    BUSINESS: {idea}
    MARKET DATA: {market_data}
    
    TASK: Build a REALISTIC Financial Estimate based on the MARKET DATA above.
    
    CRITICAL RULES:
    1. USE THE DATA: If the search results say rent is $20/sqm, use that. Do not guess.
    2. REALISM OVER OPTIMISM: 
       - Marketing/CAC should be significant (20-30% of revenue).
       - Staff costs must match local salaries found in search.
    3. REVENUE: Estimate based on similar competitor pricing found.
    4. If data is missing, make a CONSERVATIVE estimate (High Cost, Low Revenue).
    
    RETURN JSON (No Markdown):
    {{
        "currency": "{currency_code}",
        "startup_costs": {{
            "development_app_website": 0,
            "legal_licenses": 0,
            "marketing_launch_campaign": 0,
            "office_equipment_rent": 0,
            "contingency_fund": 0
        }},
        "monthly_fixed_costs": {{
            "server_cloud_infrastructure": 0,
            "marketing_ad_spend": 0,
            "salaries_staff": 0,
            "utilities_tools_misc": 0
        }},
        "revenue_assumptions": {{
            "avg_ticket_price": 0, "daily_customers": 0
        }},
        "sources_used": ["List exact source names/links from market data"]
    }}
    """

def investment_memo_prompt(query, pain_score, growth_pct, grade, opp_score, finance_summary, val_data):
    return f"""
    You are an AI Market Research Engine.
    TOPIC: {query}
    EXECUTIVE DASHBOARD:
    PAIN SCORE: {pain_score}/100
    GROWTH RATE: {growth_pct:.1f}%
    OPPORTUNITY GRADE: {grade} ({opp_score:.1f})
    
    FINANCIAL PROJECTIONS: {finance_summary}
    QUALITATIVE EVIDENCE: {val_data}
    
    Using the data above, write a comprehensive Investment Memo.
    
    CRITICAL INSTRUCTIONS:
    1. **TONE**: strict, professional, OBJECTIVE, THIRD-PERSON. 
       - DO NOT use "I", "me", "my", "we", or "us".
       - Instead, use phrases like "The report evaluates...", "Data indicates...", "Analysis suggests...".
    2. **NAME**: Use the EXACT startup name provided: "{query}". DO NOT invent a new name or rename it.
    3. **Focus**:
       - Executive Summary (Objective overview of potential).
       - Market Opportunity (Trends & Size - cite the growth rate).
       - Competitive Advantage (Based on the grade/score).
       - Financial Viability (Based on the projections/costs).
       - Final Recommendation (Objective verdict based on data).
    """

def trend_analysis_prompt(growth_pct, source, trend_data=""):
    return f"""
    You are a Senior Market Strategist.
    DATA:
    - 12-Month Growth: {growth_pct:.1f}%
    - Source: {source}
    - Recent Trend Data Points: {trend_data}

    TASK: Write a 3-4 sentence detailed analysis of this trend for a report caption.
    - Sentence 1: Analyze the velocity and magnitude of the trend (is it explosive, steady, or declining?).
    - Sentence 2: Explain the underlying drivers (e.g., consumer behavior shifts, technology adoption).
    - Sentence 3: Discuss the strategic implication for a new entrant (e.g., "This creates a window for...", "Suggests high barriers to entry due to saturation").
    - FORMATTING: Use **double asterisks** to bold 2-3 key phrases (e.g., **rapid acceleration**, **market saturation**).

    RETURN ONLY THE PARAGRAPH. No intro/outro.
    """

def financial_analysis_prompt(startup_total, currency, break_even_month, net_profit):
    return f"""
    You are a Senior Financial Consultant.
    DATA:
    - Total Startup Cost: {startup_total:,.0f} {currency}
    - Break-Even Point: Month {break_even_month}
    - Monthly Net Profit (Projected): {net_profit:,.0f} {currency}

    TASK: Write a 3-4 sentence financial health assessment for a report caption.
    - Sentence 1: Evaluate the capital efficiency and barrier to entry based on startup costs.
    - Sentence 2: Assess the risk profile given the break-even timeline (is it fast or slow return?).
    - Sentence 3: Project the long-term sustainability based on the monthly profit margins.
    - FORMATTING: Use **double asterisks** to bold 2-3 key insights (e.g., **capital efficient launch**, **delayed ROI**, **strong margin potential**).

    RETURN ONLY THE PARAGRAPH. No intro/outro.
    """

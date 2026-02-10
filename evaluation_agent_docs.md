# Evaluation Agent - Function Documentation

This document provides a summary of the main functions and their documentation within the Spark2Scale-AI evaluation agent and related API routes.

## app/graph/evaluation_agent/helpers.py

- **load_schema**: Loads a JSON schema from the schema.json file.
- **extract_team_data**: Extracts fields for the Founder Market Fit Agent: Founder Profiles, Execution History, and Problem Context.
- **extract_problem_data**: Extracts fields for the Problem Evaluation Agent: Clarity & Urgency, Market Maturity, Audience Scope, and Founder Alignment.
- **extract_product_data**: Extracts product-related fields (Snapshot, Solution, Moat, Dependencies) for the Product Agent.
- **extract_market_data**: Transforms raw startup JSON into a simplified structure for Market Analysis.
- **extract_traction_data**: Extracts traction metrics tailored to the company's stage (Pre-Seed vs. Seed).
- **extract_gtm_pre_seed / extract_gtm_seed**: Extracts Go-To-Market strategy data for validation or scalability analysis.
- **extract_business_pre_seed / extract_business_seed**: Extracts business model and economic data for profitability and solvency analysis.
- **extract_vision_data**: Extracts vision and narrative data, including long-term strategy and moat.
- **extract_operations_data**: Extracts operational readiness data, including cap table and financial health.
- **check_missing_fields**: Recursively checks for empty values in a nested JSON object to identify incomplete data.
- **capture_screenshot**: Visits a URL using Playwright and returns a screenshot as a Base64 string.
- **generate_queries**: Generates search queries for Vision Analysis based on category definition.
- **get_market_signals_serper**: Runs parallel search using Google Serper API for market signals.
- **get_market_signals_duckduckgo**: Runs search using DuckDuckGo as a synchronous fallback.

## app/graph/evaluation_agent/node.py

- **planner_node**: Generates a strategic plan for the evaluation based on initial user data.
- **team_node**: Executes team contradiction and risk checks, followed by scoring.
- **problem_node**: Executes search, contradiction, risk checks, and final scoring for the problem definition.
- **product_tools_node**: Handles heavy I/O tasks like tech stack detection and visual analysis of the product.
- **product_contradiction_node**: Performs a logic check/contradiction analysis for the product.
- **product_risk_node**: Analyzes market risk and performs competitor checks for the product.
- **product_final_scoring_node / product_scoring_node**: Aggregates all product-related analysis for final scoring.
- **market_node**: Orchestrates market analysis including TAM, regulations, and platform dependency.
- **traction_node**: Analyzes startup traction based on validation signals or growth metrics.
- **gtm_node**: Evaluates the Go-To-Market strategy and unit economics.
- **business_node**: Analyzes the business model, profitability, and solvency.
- **vision_node**: Evaluates the long-term vision, narrative, and category play.
- **operations_node**: Checks operational readiness, fundability, and financial benchmarks.

## app/graph/evaluation_agent/workflow.py

- **create_evaluation_graph**: Initializes and compiles the StateGraph for the 9-agent parallel evaluation pipeline.
- **run_pipeline**: Helper function to run the graph with timing, logging, and error handling.
- **save_graph_image**: Generates a Mermaid PNG visualization of the complex graph structure.

## app/graph/evaluation_agent/tools.py

- **contradiction_check**: Generic AI agent that checks for logical inconsistencies in provided data.
- **team_risk_check**: AI agent specialized in identifying risks related to the founding team.
- **loaded_risk_check_with_search**: Performs risk assessment enriched by external search results.
- **team_scoring_agent**: Scores the founding team based on risk and contradiction reports.
- **verify_problem_claims**: Generates queries and performs searches to verify startup problem claims.
- **problem_scoring_agent**: Scores the problem definition using search data and risk analysis.
- **tech_stack_detective**: Detects the technology stack of a website using the builtwith library.
- **analyze_visuals_with_langchain**: Uses a multimodal LLM to analyze website screenshots for brand/UI quality.
- **product_scoring_agent**: Scores the product based on tech stack, visuals, and risk reports.
- **regulation_trend_radar_tool**: Searches for regulatory risks and market trends in specific sectors and locations.
- **tam_sam_verifier_tool**: Verifies market size claims (TAM/SAM) using search snippets.
- **local_dependency_detective**: Analyzes platform and dependency risks using an LLM.
- **market_scoring_agent**: Scores the market potential and risk profile.
- **traction_scoring_agent**: Provides a numerical score and rubric rating for traction validation.
- **gtm_scoring_agent**: Scores the GTM strategy and economic viability.
- **calculate_economics_with_judgment**: Mixes Python math and AI judgment to evaluate unit economics.
- **evaluate_business_model_with_context**: Calculates profitability/solvency and benchmarks against sector standards.
- **business_scoring_agent**: Scores the business model based on solvency and momentum.
- **analyze_category_future**: Uses multiple search APIs to predict the future outlook of a startup category.
- **vision_scoring_agent**: Scores the vision and narrative strength.
- **get_funding_benchmarks**: Retrieves sector-specific funding data for benchmark analysis.
- **operations_scoring_agent**: Scores operational readiness and fundability.

## app/api/routes/evaluation.py

- **save_agent_output**: Helper function to save agent results as JSON files in the 'outputs' directory.
- **run_team_agent / run_problem_agent / ...**: Individual API endpoints for running specific evaluation nodes.
- **run_product_agent**: Specialized endpoint for the product agent (Fan-Out architecture).
- **evaluate_all**: Main endpoint that runs the full 9-agent parallel pipeline.
- **generate_report_pdf**: Generates a professional PDF report from the evaluation results.

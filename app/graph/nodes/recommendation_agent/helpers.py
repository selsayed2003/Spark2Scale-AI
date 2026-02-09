import json

def calculate_trigger_strength(severity, multipliers):
    base_weight = 0.7
    return round(base_weight * multipliers.get(severity, 1.0), 2)

def extract_key_insights(raw_data):
    ev = raw_data.get("startup_evaluation", {})
    snap = ev.get("company_snapshot", {})
    prob = ev.get("problem_definition", {})
    found = ev.get("founder_and_team", {})
    prod = ev.get("product_and_solution", {})
    trac = ev.get("traction_metrics", {})

    return {
        "company_name": snap.get("company_name", "Unknown"),
        "stage": snap.get("current_stage", "Unknown"),
        "target_raise": snap.get("current_round", {}).get("target_amount", "Unknown"),
        "problem_statement": prob.get("problem_statement", "Unknown"),
        "founder_experience": found.get("founders", [{}])[0].get("prior_experience", "Unknown"),
        "founder_market_fit": found.get("founders", [{}])[0].get("founder_market_fit_statement", "Unknown"),
        "customer_quotes": prob.get("evidence", {}).get("customer_quotes", []),
        "differentiation": prod.get("differentiation", "Unknown"),
        "core_stickiness": prod.get("core_stickiness", "Unknown"),
        "active_users": trac.get("active_users_monthly", 0),
        "early_revenue": trac.get("early_revenue", "USD 0"),
        "five_year_vision": ev.get("vision_and_strategy", {}).get("five_year_vision", "Unknown"),
        "beachhead_market": ev.get("market_and_scope", {}).get("beachhead_market", "Unknown"),
        "gap_analysis": prob.get("gap_analysis", "Unknown")
    }
"""
Load pitch deck input from CSV or JSON. Normalizes to a flat dict for section creation
and a research_data string for the LLM graph.
"""
import csv
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class LoadedInput:
    """Result of loading input directory: flat dict for create_sections_from_data, string for graph."""
    flat_data: Dict[str, Any]
    research_data: str
    source: str  # "csv" | "json"


def read_csv_strict(filepath: str) -> dict:
    """Read CSV into a dictionary using the first row as headers."""
    data = {}
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = content.strip().split("\n")
    if not lines:
        return data
        
    if "," in lines[0]:
        reader = csv.reader(lines)
        rows = list(reader)
        if not rows:
            return data
            
        headers = [h.strip().lower() for h in rows[0]]
        if len(rows) > 1:
            # Assume 2-column key-value if headers are 'key', 'value' or similar, 
            # OR if it just looks like k-v pairs. 
            # But for "strict" reading of a typical CSV, we often expect a single row of values for 1 record,
            # or multiple rows where we might want list of dicts.
            # However, this loader seems to target a single "flat dict" for one startup.
            # Strategy: If 2 columns, treat as Key-Value pairs.
            # If >2 columns, treat row 2 as the values for headers in row 1.
            
            if len(headers) == 2:
                for row in rows: # Treat all rows (including header if it looks like data) as KV? 
                    # Usually better to skip header if it says "field,value".
                    if len(row) >= 2:
                        data[row[0].strip()] = row[1].strip()
            else:
                # Treat as horizontal record (Header Row + Value Row)
                values = rows[1]
                for i, h in enumerate(headers):
                    if i < len(values):
                        data[h] = values[i].strip()
    else:
        data["content"] = content
    return data


def _get(obj: dict, *keys: str, default: str = "") -> str:
    """Navigate nested dict and return string value or default."""
    for key in keys:
        if isinstance(obj, dict) and key in obj:
            obj = obj[key]
        else:
            return default
    if isinstance(obj, (list, dict)):
        return json.dumps(obj) if obj else default
    return str(obj).strip() if obj is not None else default


def _format_founders(founders: List[dict]) -> str:
    if not founders:
        return ""
    parts = []
    for f in founders:
        name = f.get("name", "")
        role = f.get("role", "")
        exp = f.get("years_direct_experience", "")
        fit = f.get("founder_market_fit_statement", "")
        parts.append(f"{name} ({role}, {exp} years): {fit}")
    return " | ".join(parts)


def json_to_flat_dict(merged: dict) -> dict:
    """
    Map merged startup info + market research JSON into the same flat dict shape as CSV.
    Uses keys: company, problem, solution, market_size, business_model, traction, team, ask, validation, competitors, advantages.
    """
    flat: Dict[str, Any] = {}
    # Startup info structure (startup info.json has startup_evaluation; market research has top-level keys)
    startup = merged.get("startup_evaluation") or merged
    cs = startup.get("company_snapshot") or {}
    fd = startup.get("founder_and_team") or {}
    pd = startup.get("problem_definition") or {}
    ps = startup.get("product_and_solution") or {}
    ms = startup.get("market_and_scope") or {}
    tm = startup.get("traction_metrics") or {}
    bm = startup.get("business_model") or {}
    vs = startup.get("vision_and_strategy") or {}

    # Company
    flat["company"] = cs.get("company_name") or merged.get("idea_name") or ""

    # Problem
    problem_parts = [
        _get(pd, "problem_statement"),
        _get(pd, "gap_analysis"),
        _get(pd, "current_solution"),
    ]
    flat["problem"] = " ".join(p for p in problem_parts if p).strip() or "Founders need structured support to validate ideas and reach investors."

    # Solution
    solution_parts = [
        _get(ps, "core_stickiness"),
        _get(ps, "differentiation"),
        _get(ps, "defensibility_moat"),
    ]
    flat["solution"] = " ".join(p for p in solution_parts if p).strip() or "AI-powered evaluation and investor-ready documents."

    # Market size (from market research.json if present)
    mr = merged.get("market_sizing") or {}
    if mr:
        tam = _get(mr, "tam_value") or _get(mr, "tam_description")
        sam = _get(mr, "sam_value") or _get(mr, "sam_description")
        som = _get(mr, "som_value") or _get(mr, "som_description")
        flat["market_size"] = f"TAM: {tam}; SAM: {sam}; SOM: {som}".strip("; ")
    if not flat.get("market_size"):
        flat["market_size"] = f"Beachhead: {ms.get('beachhead_market', '')}; Size: {ms.get('market_size_estimate', '')}; Vision: {ms.get('long_term_vision', '')}".strip("; ")

    # Business model
    bm_parts = [
        f"Pricing: {bm.get('pricing_model', '')}",
        f"Avg price: {bm.get('average_price_per_customer', '')}",
        f"Burn: {bm.get('monthly_burn', '')}",
        f"Runway: {bm.get('runway_months', '')} months",
    ]
    finance = merged.get("finance") or {}
    if finance:
        rev = finance.get("revenue_assumptions") or {}
        bm_parts.append(f"Revenue assumptions: {json.dumps(rev)}")
    flat["business_model"] = "; ".join(p for p in bm_parts if p.split(":", 1)[-1].strip()).strip("; ") or "SaaS / subscription."

    # Traction
    traction_parts = [
        f"Users: {tm.get('user_count', '')}",
        f"Active monthly: {tm.get('active_users_monthly', '')}",
        f"Early revenue: {tm.get('early_revenue', '')}",
    ]
    trends = merged.get("trends") or []
    if trends:
        traction_parts.append("Trends: " + ", ".join(str(t.get("value", t)) for t in trends))
    flat["traction"] = "; ".join(p for p in traction_parts if p.split(":", 1)[-1].strip()).strip("; ") or "Pre-seed stage; early metrics."

    # Team
    founders = fd.get("founders") or []
    flat["team"] = _format_founders(founders) or "Expert founding team."

    # Ask
    current_round = cs.get("current_round") or {}
    ask_parts = [
        f"Target: {current_round.get('target_amount', '')}",
        f"Close: {current_round.get('target_close_date', '')}",
    ]
    use_of_funds = vs.get("use_of_funds") or []
    if use_of_funds:
        ask_parts.append("Use of funds: " + ", ".join(use_of_funds))
    flat["ask"] = "; ".join(ask_parts).strip("; ") or "Raising pre-seed round."

    # Validation (from market research)
    val = merged.get("validation") or {}
    if val:
        flat["validation"] = f"Verdict: {val.get('verdict', '')}; Pain score: {val.get('pain_score', '')}; Solution fit: {val.get('solution_fit_score', '')}. {val.get('reasoning', '')}".strip()
    if not flat.get("validation"):
        flat["validation"] = ""

    # Competitors
    comps = merged.get("competitors") or []
    if comps:
        flat["competitors"] = "; ".join(
            f"{c.get('Name', c)}: {c.get('Features', '')}" for c in comps if isinstance(c, dict)
        ) or json.dumps(comps)
    else:
        flat["competitors"] = flat.get("competitors", "")

    # Advantages
    flat["advantages"] = flat.get("advantages") or _get(ps, "differentiation") or _get(ps, "defensibility_moat") or ""

    return flat


def read_json_file(filepath: str) -> dict:
    """Load a single JSON file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def load_input_directory(input_dir: str) -> LoadedInput:
    """
    Scan input_dir for .csv or .json. Prefer JSON if any .json exists.
    Returns LoadedInput(flat_data, research_data, source).
    """
    if not os.path.isdir(input_dir):
        return LoadedInput(flat_data={}, research_data="", source="")

    all_json: List[str] = []
    all_csv: List[str] = []
    for f in os.listdir(input_dir):
        p = os.path.join(input_dir, f)
        if not os.path.isfile(p):
            continue
        lower = f.lower()
        if lower.endswith(".json"):
            all_json.append(p)
        elif lower.endswith(".csv"):
            all_csv.append(p)

    # Prefer JSON
    if all_json:
        merged: dict = {}
        research_parts: List[str] = []
        for path in sorted(all_json):
            try:
                data = read_json_file(path)
                name = os.path.basename(path)
                research_parts.append(f"--- {name} ---\n{json.dumps(data, indent=2)}")
                # Deep merge: merge data into merged (simple top-level merge for distinct keys)
                if isinstance(data, dict):
                    for k, v in data.items():
                        if k not in merged or merged[k] is None:
                            merged[k] = v
                        elif isinstance(merged[k], dict) and isinstance(v, dict):
                            merged[k] = {**(merged[k] or {}), **(v or {})}
                        else:
                            merged[k] = v
            except Exception:
                continue
        flat_data = json_to_flat_dict(merged)
        research_data = "\n\n".join(research_parts) if research_parts else json.dumps(merged, indent=2)
        return LoadedInput(flat_data=flat_data, research_data=research_data, source="json")

    # CSV fallback
    flat_data = {}
    research_parts = []
    for path in sorted(all_csv):
        flat_data.update(read_csv_strict(path))
        with open(path, "r", encoding="utf-8") as f:
            research_parts.append(f"--- {os.path.basename(path)} ---\n{f.read()}")
    research_data = "\n\n".join(research_parts) if research_parts else ""
    return LoadedInput(flat_data=flat_data, research_data=research_data, source="csv")

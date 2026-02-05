import uvicorn
from app.api.main import app
import os
from dotenv import load_dotenv
from recommendation_agent.workflow import run_recommendation_agent

# 1. Load environment variables from .env file
load_dotenv()

# 2. Retrieve the API Key
MY_API_KEY = os.getenv("GEMINI_API_KEY")

# 3. Use the dictionaries from your notebook here
# (I'm using placeholders; paste your actual dictionaries here)
RAW_INPUT = {
    "startup_evaluation": {
        "meta_data": {
            "form_type": "Pre-Seed & Seed Evaluation",
            "last_updated": "2026-02-02"
        },
        "company_snapshot": {
            "company_name": "BrainGlow",
            "website_url": "https://brainglow-demo.io",
            "hq_location": "San Francisco, USA",
            "date_founded": "2024-06-15",
            "current_stage": "Pre-Seed",
            "amount_raised_to_date": "USD 10,000",
            "current_round": {
                "target_amount": "USD 500,000",
                "target_close_date": "2026-09-01"
            }
        },
        "founder_and_team": {
            "founders": [
                {
                    "name": "Alex Chen",
                    "role": "CEO",
                    "ownership_percentage": 100,
                    "prior_experience": "PhD in Neuroscience; Researcher at university lab.",
                    "years_direct_experience": 4,
                    "founder_market_fit_statement": "I spent 4 years studying EEG patterns and realized that 80% of office workers have suboptimal alpha wave activity during deep work sessions."
                }
            ],
            "execution": {
                "full_time_start_date": "2024-09-01",
                "key_shipments": [
                    {
                        "date": "2024-11-20",
                        "item": "3D printed prototype of headband."
                    },
                    {
                        "date": "2025-01-10",
                        "item": "Launched landing page to collect waitlist emails."
                    }
                ]
            }
        },
        "problem_definition": {
            "customer_profile": {
                "role": "Knowledge Workers / Biohackers",
                "company_size": "Individual",
                "industry": "Consumer Tech / Wellness"
            },
            "problem_statement": "Knowledge workers suffer from invisible 'cognitive drift' because they cannot visualize their real-time brainwave states (Alpha vs. Beta waves) to optimize focus.",
            "current_solution": "Drinking coffee, using Pomodoro timers, or meditation apps like Headspace.",
            "gap_analysis": "Coffee is a stimulant (chemical dependency); Meditation is subjective and doesn't provide real-time biological feedback.",
            "frequency": "Daily (Work sessions).",
            "impact_metrics": {
                "cost_type": "Productivity Loss",
                "description": "Users lose 2 hours a day to 'brain fog' but assume it's normal fatigue."
            },
            "evidence": {
                "interviews_conducted": 30,
                "customer_quotes": [
                    "I usually just drink more coffee when I'm tired; I didn't know 'alpha waves' were a thing.",
                    "Would this actually help me work faster? I guess I'd try it if it wasn't expensive.",
                    "I already use an Apple Watch; I don't know if I want another gadget on my head."
                ]
            }
        },
        "product_and_solution": {
            "product_stage": "Prototype",
            "demo_link": "https://brainglow-demo.io/science",
            "core_stickiness": "Gamified focus scores that unlock badges for maintaining 'Flow State'.",
            "differentiation": "Our headband is 50% cheaper than the Muse headband and focuses on productivity, not just meditation.",
            "defensibility_moat": "Proprietary algorithm that filters out muscle movement noise from the EEG signal."
        },
        "market_and_scope": {
            "beachhead_market": "Biohackers and 'Quantified Self' enthusiasts in Silicon Valley.",
            "market_size_estimate": "50,000 Biohackers globally.",
            "long_term_vision": "A Fitbit for your Brain - worn by every student and worker.",
            "expansion_strategy": "Start with biohackers, then expand to corporate wellness programs."
        },
        "traction_metrics": {
            "stage_context": "Pre-Seed",
            "user_count": 0,
            "active_users_monthly": 0,
            "partnerships_and_lois": [],
            "early_revenue": "USD 0"
        },
        "vision_and_strategy": {
            "five_year_vision": "To make brain health as trackable as heart health.",
            "category_definition": "Neuro-Productivity Hardware.",
            "primary_risk": "Hardware manufacturing costs and consumer adoption friction."
        }
    }
}

EVAL_OUTPUT = {
    "stage": "Pre-Seed",
    "scores": {
        "team": {"score": 3, "description": "Solo founder with strong technical background but no sales experience"},
        "problem": {"score": 2, "description": "Vague customer language and conceptual problem framing"},
        "product": {"score": 2, "description": "Prototype built but many features unused, unknown user behavior"},
        "market": {"score": 2, "description": "Unclear ICP definition, overstated TAM"},
        "traction": {"score": 1, "description": "100 signups but only 5 active weekly users, low retention"},
        "gtm": {"score": 1, "description": "Not selling, trying multiple channels with no clear winner"},
        "economics": {"score": 2, "description": "6 months runway, pricing not tested, low ARPU"},
        "vision": {"score": 5, "description": "Compelling long-term vision, strong narrative"},
        "ops": {"score": 3, "description": "No weekly planning, reactive execution"}
    },
    "company_context": "Neuro-productivity hardware helping knowledge workers optimize focus through EEG tracking."
}

if __name__ == "__main__":
    if not MY_API_KEY:
        print("ERROR: GEMINI_API_KEY not found. Please check your .env file.")
    else:
        print("--- STARTING RECOMMENDATION AGENT ---")
        
        # Execute the workflow
        report = run_recommendation_agent(RAW_INPUT, EVAL_OUTPUT, MY_API_KEY)
        
        print("\n--- FINAL REPORT ---\n")
        print(report)
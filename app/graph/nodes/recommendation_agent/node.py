import json
from google import genai
from .prompts import SYSTEM_ADVISOR_PROMPT, RECOMMENDATION_PROMPT_TEMPLATE, STATEMENT_IMPROVEMENT_PROMPT

class AgentNodes:
    def __init__(self, api_key):
        self.client = genai.Client(api_key=api_key)
        self.model_id = "gemini-3-flash-preview"

    def improve_statements(self, insights):
        statements = {
            "problem": insights['problem_statement'],
            "fmf": insights['founder_market_fit'],
            "diff": insights['differentiation']
        }
        prompt = STATEMENT_IMPROVEMENT_PROMPT.format(
            statements_json=json.dumps(statements),
            quotes_json=json.dumps(insights['customer_quotes'])
        )
        response = self.client.models.generate_content(model=self.model_id, contents=prompt)
        # Handle cleaning of potential markdown
        text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(text)

    def synthesize_report(self, data, patterns, insights, replacements):
        prompt = RECOMMENDATION_PROMPT_TEMPLATE.format(
            company_name=insights['company_name'],
            stage=data.stage,
            company_context=data.company_context,
            scores_json=data.scores.model_dump_json(indent=2),
            patterns_json=json.dumps(patterns, indent=2),
            problem_statement=insights['problem_statement'],
            quotes_json=json.dumps(insights['customer_quotes']),
            target_raise=insights['target_raise'],
            replacements_json=json.dumps(replacements)
        )
        response = self.client.models.generate_content(
            model=self.model_id,
            config={'system_instruction': SYSTEM_ADVISOR_PROMPT},
            contents=prompt
        )
        return response.text
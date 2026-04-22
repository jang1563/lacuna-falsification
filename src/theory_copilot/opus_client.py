import json
from pathlib import Path

import anthropic


class OpusClient:
    def __init__(self, api_key=None, model="claude-opus-4-7", prompts_dir=None):
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)
        self.prompts_dir = Path(prompts_dir) if prompts_dir else Path(__file__).parents[2] / "prompts"

    def _load_prompt(self, filename: str) -> str:
        return (self.prompts_dir / filename).read_text()

    def _call(self, system: str, user_msg: str) -> list:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=32000,
            thinking={"type": "adaptive", "display": "summarized"},
            output_config={"effort": "high"},
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        )
        return response.content

    def propose_laws(self, dataset_card, features, context="") -> dict:
        system = self._load_prompt("law_family_proposal.md")
        user_msg = f"Dataset: {dataset_card}\nFeatures: {features}\nContext: {context}"
        blocks = self._call(system, user_msg)

        raw_thinking = ""
        raw_response = ""
        for b in blocks:
            if b.type == "thinking":
                raw_thinking += b.thinking
            elif b.type == "text":
                raw_response += b.text

        try:
            families = json.loads(raw_response).get("families", [])
        except (json.JSONDecodeError, AttributeError):
            families = []

        return {"families": families, "raw_thinking": raw_thinking, "raw_response": raw_response}

    def judge_candidate(self, equation, metrics) -> dict:
        system = self._load_prompt("skeptic_review.md")
        user_msg = f"Equation: {equation}\nMetrics: {metrics}"
        blocks = self._call(system, user_msg)

        raw_thinking = ""
        raw_response = ""
        for b in blocks:
            if b.type == "thinking":
                raw_thinking += b.thinking
            elif b.type == "text":
                raw_response += b.text

        verdict = "UNCERTAIN"
        reason = ""
        try:
            parsed = json.loads(raw_response)
            verdict = parsed.get("verdict", "UNCERTAIN")
            reason = parsed.get("reason", "")
        except (json.JSONDecodeError, AttributeError):
            pass

        return {"verdict": verdict, "reason": reason, "raw_thinking": raw_thinking}

    def interpret_survivor(self, equation, dataset_context) -> dict:
        system = self._load_prompt("final_explanation.md")
        user_msg = f"Equation: {equation}\nDataset context: {dataset_context}"
        blocks = self._call(system, user_msg)

        raw_response = ""
        for b in blocks:
            if b.type == "text":
                raw_response += b.text

        mechanism = ""
        prediction = ""
        hypothesis = ""
        try:
            parsed = json.loads(raw_response)
            mechanism = parsed.get("mechanism", "")
            prediction = parsed.get("prediction", "")
            hypothesis = parsed.get("hypothesis", "")
        except (json.JSONDecodeError, AttributeError):
            mechanism = raw_response

        return {"mechanism": mechanism, "prediction": prediction, "hypothesis": hypothesis}

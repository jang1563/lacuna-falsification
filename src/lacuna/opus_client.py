from __future__ import annotations

import json
import re
from pathlib import Path

import anthropic

from .cost_ledger import log_usage


_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```\s*$", re.MULTILINE)


def _strip_json_fences(text: str) -> str:
    """Strip ```json fences and surrounding prose from an LLM response."""
    cleaned = _FENCE_RE.sub("", text).strip()
    if not cleaned.startswith(("{", "[")):
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start : end + 1]
    return cleaned


def _safe_json_loads(text: str):
    try:
        return json.loads(_strip_json_fences(text))
    except (json.JSONDecodeError, ValueError):
        return None


class OpusClient:
    def __init__(self, api_key=None, model="claude-opus-4-7", prompts_dir=None):
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key)
        self.prompts_dir = Path(prompts_dir) if prompts_dir else Path(__file__).parents[2] / "prompts"
        self._last_usage = None

    def _load_prompt(self, filename: str) -> str:
        return (self.prompts_dir / filename).read_text()

    def _call(self, system: str, user_msg: str, role: str = "unknown") -> list:
        # Streaming is required: non-streaming .messages.create with
        # max_tokens=32000 + adaptive thinking trips the SDK's 10-minute
        # guard before any network call. The `with ... stream:` pattern
        # keeps the same completion semantics and returns a full Message.
        with self.client.messages.stream(
            model=self.model,
            max_tokens=32000,
            thinking={"type": "adaptive", "display": "summarized"},
            output_config={"effort": "high"},
            system=system,
            messages=[{"role": "user", "content": user_msg}],
        ) as stream:
            final = stream.get_final_message()
        self._last_usage = getattr(final, "usage", None)
        log_usage(self.model, role, self._last_usage)
        return final.content

    def _extract(self, blocks) -> tuple[str, str]:
        thinking_text = ""
        response_text = ""
        for block in blocks:
            if block.type == "thinking":
                thinking_text += block.thinking
            elif block.type == "text":
                response_text += block.text
        return thinking_text, response_text

    def propose_laws(self, dataset_card, features, context="") -> dict:
        system = self._load_prompt("law_family_proposal.md")
        user_msg = (
            f"Dataset card: {dataset_card}\n"
            f"Available features: {features}\n"
            f"Context: {context}\n\n"
            "Output only the JSON described in the system prompt."
        )
        blocks = self._call(system, user_msg, role="scientist")
        raw_thinking, raw_response = self._extract(blocks)

        parsed = _safe_json_loads(raw_response)
        families = parsed.get("families", []) if isinstance(parsed, dict) else []

        return {
            "families": families,
            "raw_thinking": raw_thinking,
            "raw_response": raw_response,
        }

    def judge_candidate(self, equation, metrics) -> dict:
        system = self._load_prompt("skeptic_review.md")
        user_msg = (
            f"Candidate equation: {equation}\n"
            f"Falsification metrics: {json.dumps(metrics, default=str)}\n\n"
            "Output only the JSON described in the system prompt."
        )
        blocks = self._call(system, user_msg, role="skeptic")
        raw_thinking, raw_response = self._extract(blocks)

        parsed = _safe_json_loads(raw_response)
        if not isinstance(parsed, dict):
            parsed = {}

        return {
            "verdict": parsed.get("verdict", "UNCERTAIN"),
            "reason": parsed.get("reason", ""),
            "additional_test": parsed.get("additional_test", ""),
            "raw_thinking": raw_thinking,
            "raw_response": raw_response,
        }

    def interpret_survivor(self, equation, dataset_context) -> dict:
        system = self._load_prompt("final_explanation.md")
        user_msg = (
            f"Surviving equation: {equation}\n"
            f"Dataset context: {dataset_context}\n\n"
            "Output only the JSON described in the system prompt."
        )
        blocks = self._call(system, user_msg, role="interpreter")
        raw_thinking, raw_response = self._extract(blocks)

        parsed = _safe_json_loads(raw_response)
        if isinstance(parsed, dict):
            return {
                "mechanism": parsed.get("mechanism", ""),
                "hypothesis": parsed.get("hypothesis", ""),
                "prediction": parsed.get("prediction", ""),
                "caveats": parsed.get("caveats", ""),
                "raw_thinking": raw_thinking,
                "raw_response": raw_response,
            }

        return {
            "mechanism": raw_response,
            "hypothesis": "",
            "prediction": "",
            "caveats": "",
            "raw_thinking": raw_thinking,
            "raw_response": raw_response,
        }

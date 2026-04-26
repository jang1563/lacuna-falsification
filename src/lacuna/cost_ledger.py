"""Per-call cost ledger for Opus/Sonnet API usage (BP-5).

Appends one JSON line per Anthropic API call to `artifacts/cost_ledger.jsonl`.
Independent of the main loop so it never breaks a run.

Pricing assumptions (USD per 1M tokens, 2026-04 published rates):
- claude-opus-4-7:  input $15, output $75
- claude-sonnet-4-6: input $3,  output $15
Extended-thinking tokens are billed as output tokens.

Override via env:
- COST_LEDGER_PATH  (default: artifacts/cost_ledger.jsonl)
- COST_KILL_SWITCH_USD  (default: 350) — soft warning only, does not hard-stop
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Optional


# USD per 1M tokens.
_PRICE_TABLE: dict[str, dict[str, float]] = {
    "claude-opus-4-7": {"input": 15.0, "output": 75.0},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5": {"input": 1.0, "output": 5.0},
}


def _price_for(model: str) -> dict[str, float]:
    # Fall back to opus pricing for unknown models (fails loud via higher cost).
    for key, price in _PRICE_TABLE.items():
        if model.startswith(key):
            return price
    return _PRICE_TABLE["claude-opus-4-7"]


@dataclass
class UsageRecord:
    timestamp: str
    model: str
    role: str
    input_tokens: int
    output_tokens: int
    thinking_tokens: int
    est_cost_usd: float
    cumulative_usd: float


def estimate_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    thinking_tokens: int = 0,
) -> float:
    price = _price_for(model)
    total_output = output_tokens + thinking_tokens
    return (input_tokens / 1_000_000) * price["input"] + (
        total_output / 1_000_000
    ) * price["output"]


def _ledger_path() -> Path:
    return Path(os.environ.get("COST_LEDGER_PATH", "artifacts/cost_ledger.jsonl"))


def _kill_switch_usd() -> float:
    try:
        return float(os.environ.get("COST_KILL_SWITCH_USD", "350"))
    except ValueError:
        return 350.0


def _current_cumulative(path: Path) -> float:
    if not path.exists():
        return 0.0
    last = 0.0
    try:
        with path.open() as fh:
            for line in fh:
                try:
                    last = float(json.loads(line).get("cumulative_usd", last))
                except (json.JSONDecodeError, ValueError):
                    continue
    except OSError:
        return 0.0
    return last


def log_usage(
    model: str,
    role: str,
    usage: Optional[object],
    ledger_path: Optional[Path] = None,
) -> Optional[UsageRecord]:
    """Extract token counts from an Anthropic Usage-like object and append a record.

    Never raises; returns None on failure so callers don't see ledger errors.
    """
    if usage is None:
        return None

    try:
        input_tokens = int(getattr(usage, "input_tokens", 0) or 0)
        output_tokens = int(getattr(usage, "output_tokens", 0) or 0)
        # Some SDK versions expose thinking under different names; try both.
        thinking_tokens = int(
            getattr(usage, "thinking_tokens", None)
            or getattr(usage, "extended_thinking_tokens", 0)
            or 0
        )
    except (TypeError, ValueError):
        return None

    cost = estimate_cost(model, input_tokens, output_tokens, thinking_tokens)
    path = ledger_path or _ledger_path()
    path.parent.mkdir(parents=True, exist_ok=True)

    cumulative = _current_cumulative(path) + cost

    record = UsageRecord(
        timestamp=time.strftime("%Y-%m-%dT%H:%M:%S%z") or time.strftime("%Y-%m-%dT%H:%M:%S"),
        model=model,
        role=role,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        thinking_tokens=thinking_tokens,
        est_cost_usd=round(cost, 6),
        cumulative_usd=round(cumulative, 6),
    )

    try:
        with path.open("a") as fh:
            fh.write(json.dumps(asdict(record)) + "\n")
    except OSError:
        return record

    kill = _kill_switch_usd()
    if cumulative >= kill:
        # Best-effort warning to stderr; never raise.
        import sys

        print(
            f"[cost_ledger] WARNING cumulative ${cumulative:.2f} >= kill-switch ${kill:.2f}",
            file=sys.stderr,
        )

    return record


def summarize(ledger_path: Optional[Path] = None) -> dict:
    """Return a quick summary over the full ledger file."""
    path = ledger_path or _ledger_path()
    totals = {"calls": 0, "usd": 0.0, "by_role": {}, "by_model": {}}
    if not path.exists():
        return totals
    with path.open() as fh:
        for line in fh:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            totals["calls"] += 1
            cost = float(rec.get("est_cost_usd", 0.0))
            totals["usd"] += cost
            role = rec.get("role", "unknown")
            model = rec.get("model", "unknown")
            totals["by_role"][role] = totals["by_role"].get(role, 0.0) + cost
            totals["by_model"][model] = totals["by_model"].get(model, 0.0) + cost
    totals["usd"] = round(totals["usd"], 6)
    return totals

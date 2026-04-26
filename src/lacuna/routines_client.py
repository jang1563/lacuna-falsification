"""
Claude Code Routines `/fire` HTTP client.

Routines is a separate product from Managed Agents:
  - Product host      : code.claude.com
  - Beta header       : experimental-cc-routine-2026-04-01
  - Creation surface  : claude.ai/code/routines UI or `/schedule` in a Claude
                        Code session. CLI creates schedule triggers only;
                        API + GitHub triggers require the web UI.
  - No Python SDK     : only REST.
  - Per-routine bearer: displayed ONCE in web UI; rotate via regenerate.

This module does not wrap creation — that's a human workflow step. It wraps
the fire endpoint so `run_path_c_routine` can swap its `invoke_fn` from a
local loop to a cloud-triggered execution with one line.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx

ROUTINES_FIRE_URL = "https://api.anthropic.com/v1/claude_code/routines/{trig_id}/fire"
ROUTINES_BETA_HEADER = "experimental-cc-routine-2026-04-01"
ANTHROPIC_VERSION = "2023-06-01"


@dataclass
class RoutineFireResult:
    """Response from POST /v1/claude_code/routines/{id}/fire.

    The server spawns a fresh Claude Code cloud session and returns its id
    plus a browser URL the user can open to watch the run. This is different
    from Managed Agents sessions — Routine executions are full Claude Code
    sessions, not Agent SDK agents.
    """

    session_id: str
    session_url: str
    http_status: int
    type: str = "routine_fire"

    @property
    def status(self) -> str:
        """Normalize to the shape run_path_c_routine expects."""
        return "completed" if 200 <= self.http_status < 300 else "error"

    def to_invoke_dict(self, output_note: str = "") -> dict:
        """Shape the result like run_path_b's return for Path C compatibility."""
        return {
            "session_id": self.session_id,
            "agent_id": "",  # Routines do not pin an Agent SDK agent id
            "output": output_note or self.session_url,
            "status": self.status,
            "routine_session_url": self.session_url,
        }


def fire_routine(
    trig_id: str,
    token: str,
    text: str = "",
    *,
    timeout_s: float = 30.0,
    _transport: httpx.BaseTransport | None = None,
) -> RoutineFireResult:
    """POST https://api.anthropic.com/v1/claude_code/routines/{trig_id}/fire

    Parameters
    ----------
    trig_id : str
        Routine trigger id (starts with `trig_`). Visible in the routine's
        web URL at claude.ai/code/routines/<trig_id>.
    token : str
        Bearer token generated in the routine's trigger UI. Displayed ONCE
        — store on generation.
    text : str
        Freeform string appended to the routine's saved prompt. Not parsed.
    timeout_s : float
        HTTP timeout.
    _transport : httpx.BaseTransport | None
        Testing hook.

    Returns
    -------
    RoutineFireResult

    Raises
    ------
    httpx.HTTPStatusError on non-2xx if the server returns a non-JSON body.
    """
    url = ROUTINES_FIRE_URL.format(trig_id=trig_id)
    headers = {
        "Authorization": f"Bearer {token}",
        "anthropic-beta": ROUTINES_BETA_HEADER,
        "anthropic-version": ANTHROPIC_VERSION,
        "Content-Type": "application/json",
    }
    body = {"text": text} if text else {}

    with httpx.Client(timeout=timeout_s, transport=_transport) as cli:
        response = cli.post(url, headers=headers, json=body)

    data: dict[str, Any]
    try:
        data = response.json()
    except ValueError:
        data = {}

    return RoutineFireResult(
        session_id=data.get("claude_code_session_id", ""),
        session_url=data.get("claude_code_session_url", ""),
        http_status=response.status_code,
        type=data.get("type", "routine_fire"),
    )


def fire_routine_from_env(
    text: str = "",
    *,
    trig_env: str = "CLAUDE_ROUTINE_TRIG_ID",
    token_env: str = "CLAUDE_ROUTINE_TOKEN",
) -> RoutineFireResult:
    """Convenience wrapper: read trig_id + token from env.

    Raises
    ------
    RuntimeError if either env var is missing. Callers can catch and fall
    back to `run_path_b` (the local loop default in run_path_c_routine).
    """
    trig_id = os.environ.get(trig_env, "").strip()
    token = os.environ.get(token_env, "").strip()
    if not trig_id or not token:
        missing = [v for v, s in ((trig_env, trig_id), (token_env, token)) if not s]
        raise RuntimeError(
            f"Missing required env var(s) for Routine fire: {', '.join(missing)}"
        )
    return fire_routine(trig_id=trig_id, token=token, text=text)


def make_routine_invoke_fn(
    task_map: dict[int, str],
    *,
    trig_env: str = "CLAUDE_ROUTINE_TRIG_ID",
    token_env: str = "CLAUDE_ROUTINE_TOKEN",
):
    """Return an `invoke_fn(night) -> dict` ready to pass to run_path_c_routine.

    Usage:
        from lacuna.managed_agent_runner import (
            run_path_c_routine, _NIGHT_TASKS,
        )
        from lacuna.routines_client import make_routine_invoke_fn

        fire = make_routine_invoke_fn(_NIGHT_TASKS)
        run_path_c_routine(night=3, interval_seconds=0, invoke_fn=fire)

    If env vars are missing, the returned function raises on call — the
    caller can catch and fall back to the local loop.
    """

    def _invoke(night: int) -> dict:
        result = fire_routine_from_env(
            text=task_map.get(night, ""),
            trig_env=trig_env,
            token_env=token_env,
        )
        return result.to_invoke_dict(
            output_note=f"Fired routine {trig_env}={os.environ.get(trig_env,'?')}"
        )

    return _invoke

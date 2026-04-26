"""E10 — Path A (callable_agents multiagent) waitlist probe.

The `src/lacuna/managed_agent_runner.py::run_path_a` function builds
a 3-agent chain (Proposer -> Searcher -> Falsifier) using
`client.beta.agents.create(..., tools=[{"type": "agent_toolset_20260401"}])`
followed by per-agent sessions. Path B (single-agent tool loop) already
works end-to-end in `results/live_evidence/04_managed_agents_e2e.log`.

This probe tries to *create* a Path-A Proposer agent without running the
full chain so we can tell whether the multiagent feature is accessible
from this API key, without consuming the full per-agent cost.

Outcomes:
  - Agent creation succeeds → waitlist is effectively approved for this
    key; the evidence log captures the agent id + versioning metadata.
  - Agent creation raises a 4xx/permission error → we document the
    waitlist-denied path and `run_path_a` stays guarded by
    `MANAGED_AGENTS_WAITLIST=approved`.

Output: results/live_evidence/06_managed_agents_path_a.log
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import anthropic  # noqa: E402


OUT_LOG = REPO / "results" / "live_evidence" / "06_managed_agents_path_a.log"


def _lines(lines: list[str]) -> None:
    OUT_LOG.parent.mkdir(parents=True, exist_ok=True)
    OUT_LOG.write_text("\n".join(lines) + "\n")


def main() -> None:
    client = anthropic.Anthropic()
    lines = []
    lines.append(f"# 06_managed_agents_path_a — {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append(
        "Purpose: probe whether `client.beta.agents.create(..., "
        "tools=[{'type':'agent_toolset_20260401'}])` succeeds on this API key, "
        "which is the Path A (callable_agents / multiagent) gate."
    )
    lines.append("")
    lines.append("## Attempt")
    lines.append("")

    # Probe all three role agents (proposer / searcher / falsifier) to
    # confirm the full Path A chain is creatable. We stop short of
    # running the actual PySR chain (which would execute in a cloud env
    # and is unnecessary for the feature-availability signal).
    roles: list[tuple[str, str, str]] = [
        ("proposer", "claude-opus-4-7", "Minimal probe. Respond with one word only: OK."),
        ("searcher", "claude-sonnet-4-6", "Minimal probe. Respond with one word only: OK."),
        ("falsifier", "claude-opus-4-7", "Minimal probe. Respond with one word only: OK."),
    ]
    created_agents: list[tuple[str, object]] = []
    errors: list[str] = []

    for role_name, model, system in roles:
        try:
            agent = client.beta.agents.create(
                name=f"probe_pathA_{role_name}_{int(time.time())}",
                model=model,
                system=system,
                tools=[{"type": "agent_toolset_20260401"}],
            )
            created_agents.append((role_name, agent))
        except anthropic.PermissionDeniedError as e:
            errors.append(f"{role_name}: PermissionDeniedError: {e}")
        except anthropic.BadRequestError as e:
            errors.append(f"{role_name}: BadRequestError: {e}")
        except Exception as e:  # noqa: BLE001
            errors.append(f"{role_name}: {type(e).__name__}: {e}")

    created_ok = len(created_agents) == 3
    err_text = "; ".join(errors) if errors else None

    if created_ok:
        lines.append(
            "All three Path-A role agents (proposer / searcher / falsifier) "
            "**created successfully** — the multiagent feature is accessible "
            "for this API key."
        )
        lines.append("")
        for role_name, agent in created_agents:
            lines.append(f"- **{role_name}**: agent.id = `{agent.id}`")
    else:
        lines.append(
            f"Path A agent creation **partial/denied**: {len(created_agents)}/3 agents "
            "created; the remaining role(s) failed. Likely the multiagent "
            "subset of Managed Agents is still waitlisted for this key."
        )
        lines.append("")
        lines.append(f"Error trail: {err_text}")

    lines.append("")
    lines.append("## Path A guard status")
    lines.append("")
    flag = os.environ.get("MANAGED_AGENTS_WAITLIST", "unset")
    lines.append(
        f"`MANAGED_AGENTS_WAITLIST={flag}` — `run_path_a()` in "
        "`src/lacuna/managed_agent_runner.py` raises "
        "`NotImplementedError` unless this env var is set to `approved`, so "
        "Path A remains a documented code path that can be activated the "
        "moment the waitlist opens for this key."
    )
    lines.append("")
    lines.append("## Path B status")
    lines.append("")
    lines.append(
        "Path B (single-agent tool loop) was already verified end-to-end: "
        "see `04_managed_agents_e2e.log`. This is the path the live "
        "demo uses today."
    )

    if created_agents and hasattr(client.beta.agents, "delete"):
        # Best-effort cleanup so probe agents don't linger in the account.
        cleaned: list[str] = []
        for role_name, agent in created_agents:
            try:
                client.beta.agents.delete(agent.id)
                cleaned.append(f"{role_name}={agent.id}")
            except Exception:  # noqa: BLE001
                pass
        if cleaned:
            lines.append("")
            lines.append(f"Probe agents deleted (cleanup): {', '.join(cleaned)}")

    _lines(lines)
    print(f"[managed_agents_path_a] wrote {OUT_LOG}")
    print(
        f"[managed_agents_path_a] created_ok={created_ok} "
        f"agents={[a.id for _, a in created_agents]} err={err_text}"
    )


if __name__ == "__main__":
    main()

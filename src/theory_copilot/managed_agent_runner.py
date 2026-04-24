"""
Managed Agents + Claude Code Routines runtime.

Terminology note (corrected 2026-04-23 after deep-research):
  - `managed-agents-2026-04-01` (public beta, 2026-04-08) → Paths A, B.
    Endpoint surface is `client.beta.{agents,environments,sessions,vaults,skills}`.
  - `experimental-cc-routine-2026-04-01` (research preview, 2026-04-14) → Path C.
    Routines are a *Claude Code* product, not Managed Agents; the `/fire`
    endpoint is an unauthenticated-by-bearer-token cloud trigger that spawns a
    full Claude Code session (NOT an Agent SDK agent).

Path legend:
  Path A : Agent Teams (multi-agent) — orchestrator declares `callable_agents`,
          LLM delegates via a platform-inserted tool, sub-agents run with
          context isolation. Research-preview, per-workspace allow-list.
  Path B : single-agent + `agent_toolset_20260401` tool bundle. Public beta.
  Path C : Routines scheduled/triggered cloud execution. Our driver also
          provides a local-loop fallback when no bearer token is available,
          so the pipeline ships today regardless of the trigger surface.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

import anthropic

NIGHT2_SYSTEM = (
    "You are a scientific computing assistant specializing in symbolic regression. "
    "Your task: run a PySR hyperparameter sweep on the TCGA-KIRC tumor-vs-normal "
    "gene expression dataset, seeded with Opus-proposed law family guesses "
    "(config/law_proposals.json). Execute python3 src/pysr_sweep.py, then write the "
    "candidate equations (equation, auroc, complexity, seed, law_family) to "
    "results/night2/candidates.json. Log progress and confirm completion with a "
    "structured summary."
)

NIGHT3_SYSTEM = (
    "You are a scientific computing assistant specializing in hypothesis falsification. "
    "Your task: run the 5-test falsification gate on the top-50 candidate equations "
    "from Night 2. Execute python3 src/falsification_sweep.py to test each candidate "
    "against permutation null, bootstrap stability, best-single-feature baseline, "
    "covariate-only confound, and a decoy-feature null. Apply Benjamini-Hochberg FDR "
    "across candidates. Write the ranked report (equation, passes, perm_p, perm_p_fdr, "
    "ci_lower, delta_baseline, delta_confound, decoy_p, fail_reason) to "
    "results/night3/falsification_report.json. Confirm completion with a structured summary."
)

NIGHT4_SYSTEM = (
    "You are a scientific computing assistant specializing in biological law replay. "
    "Your task: replay the top surviving law from Night 3 on the GSE40435 cohort "
    "(independent ccRCC kidney tissue cohort, 101 paired tumor-normal samples, "
    "microarray platform — different from TCGA-KIRC's RNA-seq). Run the same "
    "5-test falsification gate on the independent cohort with per-cohort z-score "
    "standardization. Compute an honest replay verdict: pass, attenuated, or fail. "
    "Write all results (AUC with 95% CI, replay verdict, caveat note) to "
    "results/night4/transfer_report.json. Confirm completion with a structured summary."
)

_NIGHT_SYSTEMS = {2: NIGHT2_SYSTEM, 3: NIGHT3_SYSTEM, 4: NIGHT4_SYSTEM}

_NIGHT_TASKS = {
    2: (
        "Run the PySR hyperparameter sweep on the metastasis_expanded panel:\n"
        "  PYTHONPATH=src .venv/bin/python src/pysr_sweep.py \\\n"
        "    --data data/kirc_metastasis_expanded.csv \\\n"
        "    --genes TOP2A,EPAS1,MKI67,CDK1,CCNB1,HIF1A,EPAS1,VEGFA,CA9,LRP2,PTGER3,RPL13A,SLC22A8 \\\n"
        "    --proposals config/law_proposals.json \\\n"
        "    --iterations 1000 --seeds 1 2 3 --standardize \\\n"
        "    --output results/night2/candidates.json\n"
        "Then summarise the top-10 equations by sign-invariant AUROC."
    ),
    3: (
        "Run the falsification sweep on the candidates from Night 2:\n"
        "  PYTHONPATH=src .venv/bin/python src/falsification_sweep.py \\\n"
        "    --candidates results/night2/candidates.json \\\n"
        "    --data data/kirc_metastasis_expanded.csv \\\n"
        "    --genes TOP2A,EPAS1,MKI67,CDK1,CCNB1,HIF1A,VEGFA,CA9,LRP2,PTGER3,RPL13A,SLC22A8 \\\n"
        "    --output results/night3/falsification_report.json\n"
        "Write the ranked report (passes / perm_p / ci_lower / delta_baseline / "
        "delta_confound / decoy_p / fail_reason) to falsification_report.json."
    ),
    4: (
        "Run GSE40435 replay validation on the surviving equation from "
        "Night 3's falsification report:\n"
        "  PYTHONPATH=src .venv/bin/python -m theory_copilot.cli replay \\\n"
        "    --flagship-artifacts results/night3 \\\n"
        "    --transfer-dataset gse40435 \\\n"
        "    --output-root results/night4\n"
        "Or, equivalently with the installed console script: \n"
        "  theory-copilot replay --flagship-artifacts results/night3 "
        "--transfer-dataset gse40435 --output-root results/night4\n"
        "Write transfer_report.json (AUC + 95% CI + replay verdict)."
    ),
}


# ─────────────────────────────────────────────────────────────────────────────
# Event streaming helpers
#
# The stream emits many event types; the ones our code cares about:
#   - agent.message          — text content from the agent
#   - agent.thinking         — summarized adaptive thinking (4.7)
#   - agent.tool_use         — pre-built tool invocation (bash/read/write/...)
#   - agent.thread_message_sent / thread_message_received — multi-agent
#   - session.thread_created / thread_idle                — multi-agent
#   - session.status_running / status_idle                — session lifecycle
#   - session.status_terminated                           — unrecoverable
#   - session.error                                       — retry-aware error
# ─────────────────────────────────────────────────────────────────────────────

_AGENT_TEXT_TYPES = {"agent.message", "agent.thinking"}
_SESSION_TERMINAL_TYPES = {
    "session.status_idle",
    "session.status_terminated",
}


def _extract_event_text(event: Any) -> str:
    """Pull text out of an agent.message / agent.thinking event block-by-block."""
    chunks: list[str] = []
    for block in getattr(event, "content", None) or []:
        text = getattr(block, "text", None) or getattr(block, "thinking", None)
        if text:
            chunks.append(text)
    return "".join(chunks)


def _drain_stream(stream: Iterable[Any], collect: list[str]) -> tuple[str, list[str]]:
    """Consume events until a terminal session.status_* arrives.

    Returns (status, event_type_trace). `status` is "completed" on idle,
    "terminated" on an unrecoverable termination event, "error" on exception.
    """
    trace: list[str] = []
    status = "completed"
    try:
        for event in stream:
            etype = getattr(event, "type", "")
            trace.append(etype)
            if etype in _AGENT_TEXT_TYPES:
                text = _extract_event_text(event)
                if text:
                    collect.append(text)
            elif etype == "session.error":
                err = getattr(event, "error", None)
                collect.append(f"[session.error] {err!r}")
            elif etype in _SESSION_TERMINAL_TYPES:
                if etype == "session.status_terminated":
                    status = "terminated"
                break
    except Exception as exc:
        status = "error"
        collect.append(f"[stream-exception] {exc!r}")
    return status, trace


# ─────────────────────────────────────────────────────────────────────────────
# Path B — single agent with agent_toolset_20260401 (public beta)
# ─────────────────────────────────────────────────────────────────────────────


def run_path_b(
    night: int,
    hpc_project_dir: str = "",
    title: str | None = None,
    *,
    pin_version: bool = False,
) -> dict:
    """
    Single Managed Agent + built-in tool bundle. Public beta, no waitlist.

    Parameters
    ----------
    night : int
        2, 3, or 4 — selects system prompt + task.
    pin_version : bool
        If True, list the agent's current versions and pin the session to the
        latest version explicitly via `agent={"type":"agent","id":..,"version":N}`.
        Demonstrates immutable versioned agents from the Managed Agents docs.

    Returns
    -------
    dict : {"session_id", "agent_id", "agent_version", "output", "status"}
    """
    client = anthropic.Anthropic()

    system = _NIGHT_SYSTEMS[night]
    task = _NIGHT_TASKS[night]

    agent = client.beta.agents.create(
        name=f"theory_copilot_night{night}",
        model="claude-opus-4-7",
        system=system,
        tools=[{"type": "agent_toolset_20260401"}],
    )

    environment = client.beta.environments.create(
        name=f"theory-copilot-env-night{night}",
        config={"type": "cloud", "networking": {"type": "unrestricted"}},
    )

    # Optional: pin the session to a specific immutable version. New agents
    # always start at version=1; this shows the auditable pattern.
    agent_version: int | None = None
    session_agent_arg: Any = agent.id
    if pin_version:
        agent_version = getattr(agent, "version", None) or 1
        session_agent_arg = {
            "type": "agent",
            "id": agent.id,
            "version": agent_version,
        }

    session = client.beta.sessions.create(
        agent=session_agent_arg,
        environment_id=environment.id,
        title=title or f"Night {night} theory copilot sweep",
    )

    output_parts: list[str] = []
    status = "completed"
    try:
        with client.beta.sessions.events.stream(session.id) as stream:
            client.beta.sessions.events.send(
                session.id,
                events=[
                    {
                        "type": "user.message",
                        "content": [{"type": "text", "text": task}],
                    }
                ],
            )
            status, _ = _drain_stream(stream, output_parts)
    except Exception as exc:
        status = "error"
        output_parts.append(f"[stream-setup-error] {exc!r}")

    return {
        "session_id": session.id,
        "agent_id": agent.id,
        "agent_version": agent_version,
        "output": "".join(output_parts),
        "status": status,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Path A — Agent Teams (multi-agent, research preview)
#
# Shape (per platform.claude.com/docs/en/managed-agents/multi-agent):
#   orchestrator = client.beta.agents.create(
#       ..., callable_agents=[
#           {"type":"agent", "id": proposer.id, "version": proposer.version},
#           {"type":"agent", "id": searcher.id, "version": searcher.version},
#           {"type":"agent", "id": skeptic.id,  "version": skeptic.version},
#       ]
#   )
#   session = client.beta.sessions.create(agent=orchestrator.id, ...)
#   # orchestrator LLM calls delegation tool; sub-agents run with isolated
#   # context; events arrive on primary session stream as
#   # session.thread_created / agent.thread_message_sent / thread_idle.
#
# Waitlist: per-workspace allow-list requested via
#   https://claude.com/form/claude-managed-agents
# The env var MANAGED_AGENTS_WAITLIST is a CLIENT-SIDE feature flag only —
# the platform does not key off it. We still guard on it so tests + users
# without allow-list access fall back to the sequential harness.
# ─────────────────────────────────────────────────────────────────────────────


def _waitlist_approved() -> bool:
    """Client-side feature flag only (not a platform toggle)."""
    val = os.environ.get("MANAGED_AGENTS_WAITLIST", "").strip().lower()
    return val == "approved"


def run_path_a(
    night: int,
    title: str | None = None,
    *,
    fallback_on_no_waitlist: bool = False,
) -> dict:
    """
    Agent Teams: orchestrator delegates to Proposer / Searcher / Skeptic.

    If MANAGED_AGENTS_WAITLIST != "approved", raises NotImplementedError (legacy
    behaviour preserved for tests) UNLESS `fallback_on_no_waitlist=True`, in
    which case a sequential (Path B × 3) harness runs with explicit inter-agent
    message handoff. The sequential harness is NOT multi-agent — it is a
    single-session chain with context-injection. This is called out in the
    returned dict under `delegation_mode`.

    Returns
    -------
    dict : {
        "session_id": str,
        "agent_id": str,  # orchestrator if real multi-agent, falsifier if fallback
        "output": str,    # JSON dump of per-role outputs
        "status": "completed" | "error",
        "delegation_mode": "callable_agents" | "sequential_fallback",
    }
    """
    if not _waitlist_approved():
        if not fallback_on_no_waitlist:
            raise NotImplementedError("callable_agents requires waitlist approval")
        return _run_path_a_sequential_fallback(night=night, title=title)

    return _run_path_a_callable_agents(night=night, title=title)


def _run_path_a_callable_agents(night: int, title: str | None) -> dict:
    """Real Agent Teams: orchestrator + callable_agents delegation."""
    client = anthropic.Anthropic()

    proposer = client.beta.agents.create(
        name=f"proposer_night{night}",
        model="claude-opus-4-7",
        system=(
            "You are a scientific hypothesis proposer. When the orchestrator "
            "calls you, read config/law_proposals.json, refine 3-5 compact law "
            "families (including at least one negative control), and reply with "
            "a JSON summary of your refinements."
        ),
        tools=[{"type": "agent_toolset_20260401"}],
    )
    searcher = client.beta.agents.create(
        name=f"searcher_night{night}",
        model="claude-sonnet-4-6",  # cheaper Sonnet for the search loop
        system=(
            "You are a symbolic-regression executor. When the orchestrator "
            "calls you, execute python3 src/pysr_sweep.py with the proposer's "
            "law families and reply with a JSON candidate list."
        ),
        tools=[{"type": "agent_toolset_20260401"}],
    )
    skeptic = client.beta.agents.create(
        name=f"skeptic_night{night}",
        model="claude-opus-4-7",
        system=(
            "You are a hypothesis-falsification skeptic. When the orchestrator "
            "calls you, execute python3 src/falsification_sweep.py on the "
            "searcher's candidates. You MUST NOT read proposer or searcher "
            "reasoning — only structured JSON outputs. Reply with per-candidate "
            "verdicts and a dissent flag."
        ),
        tools=[{"type": "agent_toolset_20260401"}],
    )

    orchestrator = client.beta.agents.create(
        name=f"orchestrator_night{night}",
        model="claude-opus-4-7",
        system=(
            "You coordinate a falsification-first discovery pipeline: delegate "
            "hypothesis proposal to the Proposer, symbolic-regression search to "
            "the Searcher, and adversarial review to the Skeptic. Pass only "
            "structured JSON between sub-agents; never forward their rationale. "
            "When the Skeptic dissents, report the dissent verbatim — do not "
            "rewrite it."
        ),
        tools=[{"type": "agent_toolset_20260401"}],
        callable_agents=[
            {"type": "agent", "id": proposer.id,
             "version": getattr(proposer, "version", 1)},
            {"type": "agent", "id": searcher.id,
             "version": getattr(searcher, "version", 1)},
            {"type": "agent", "id": skeptic.id,
             "version": getattr(skeptic, "version", 1)},
        ],
    )

    environment = client.beta.environments.create(
        name=f"theory-copilot-multiagent-night{night}",
        config={"type": "cloud", "networking": {"type": "unrestricted"}},
    )

    session = client.beta.sessions.create(
        agent=orchestrator.id,
        environment_id=environment.id,
        title=title or f"Night {night} multiagent",
    )

    output_parts: list[str] = []
    status = "completed"
    task = (
        f"Night {night}: run the falsification-first discovery pipeline. "
        "Delegate to Proposer → Searcher → Skeptic in that order. Emit a final "
        "JSON report {proposer_output, searcher_output, skeptic_verdicts, "
        "orchestrator_summary}."
    )
    try:
        with client.beta.sessions.events.stream(session.id) as stream:
            client.beta.sessions.events.send(
                session.id,
                events=[
                    {
                        "type": "user.message",
                        "content": [{"type": "text", "text": task}],
                    }
                ],
            )
            status, _ = _drain_stream(stream, output_parts)
    except Exception as exc:
        status = "error"
        output_parts.append(f"[stream-setup-error] {exc!r}")

    return {
        "session_id": session.id,
        "agent_id": orchestrator.id,
        "output": "".join(output_parts),
        "status": status,
        "delegation_mode": "callable_agents",
    }


def _run_path_a_sequential_fallback(night: int, title: str | None) -> dict:
    """Three Path-B sessions chained with JSON handoff. NOT multi-agent."""
    client = anthropic.Anthropic()

    proposer = client.beta.agents.create(
        name=f"proposer_night{night}",
        model="claude-opus-4-7",
        system=(
            "You are a scientific hypothesis proposer. Read config/law_proposals.json, "
            "select and refine the most promising law families for this experimental run, "
            "and write your refined proposals to results/proposer_output.json."
        ),
        tools=[{"type": "agent_toolset_20260401"}],
    )
    searcher = client.beta.agents.create(
        name=f"searcher_night{night}",
        model="claude-sonnet-4-6",
        system=(
            "You are a symbolic regression executor. Read results/proposer_output.json "
            "to get the law families to search, then run PySR via bash: "
            "python3 src/pysr_sweep.py. Write candidate equations to results/candidates.json."
        ),
        tools=[{"type": "agent_toolset_20260401"}],
    )
    falsifier = client.beta.agents.create(
        name=f"falsifier_night{night}",
        model="claude-opus-4-7",
        system=(
            "You are a scientific falsifier. Read results/candidates.json, "
            "run python3 src/falsification_sweep.py on each candidate, "
            "and write the ranked falsification report to results/falsification_report.json."
        ),
        tools=[{"type": "agent_toolset_20260401"}],
    )

    environment = client.beta.environments.create(
        name=f"theory-copilot-seqfallback-night{night}",
        config={"type": "cloud", "networking": {"type": "unrestricted"}},
    )

    role_outputs: dict[str, str] = {}
    status = "completed"
    last_session = None

    chain = [
        ("proposer", proposer, (
            f"Night {night}: select 3-5 compact law families from config/law_proposals.json "
            "(including the required negative control) and write a refined set to "
            "results/proposer_output.json. Emit the family list as JSON in your final message."
        )),
        ("searcher", searcher, (
            "Read the Proposer's law families below and run PySR via bash:\n"
            "  python3 src/pysr_sweep.py --data <flagship_csv> --genes <CSV of genes> "
            "--proposals config/law_proposals.json --standardize "
            "--output results/candidates.json\n"
            "Emit a JSON summary of candidate equations with train_auroc + test_auroc + novelty.\n\n"
            "=== Proposer output ===\n{proposer}\n=== end Proposer output ==="
        )),
        ("falsifier", falsifier, (
            "Read the Searcher's candidate equations below and run the 5-test gate:\n"
            "  python3 src/falsification_sweep.py --candidates results/candidates.json "
            "--data <flagship_csv> --genes <CSV of genes> --covariate-cols age,batch_index "
            "--output results/falsification_report.json\n"
            "Emit a JSON summary naming every candidate plus perm_p, perm_p_fdr, ci_lower, "
            "delta_baseline, delta_confound, decoy_p, passes, fail_reason. Flag any law where "
            "train_auroc >> test_auroc as overfit.\n\n"
            "=== Searcher output ===\n{searcher}\n=== end Searcher output ==="
        )),
    ]

    for role, agent, task_template in chain:
        task = task_template.format(
            proposer=role_outputs.get("proposer", ""),
            searcher=role_outputs.get("searcher", ""),
        )
        session = client.beta.sessions.create(
            agent=agent.id,
            environment_id=environment.id,
            title=title or f"Night {night} {role}",
        )
        last_session = session
        output_parts: list[str] = []
        try:
            with client.beta.sessions.events.stream(session.id) as stream:
                client.beta.sessions.events.send(
                    session.id,
                    events=[
                        {
                            "type": "user.message",
                            "content": [{"type": "text", "text": task}],
                        }
                    ],
                )
                seg_status, _ = _drain_stream(stream, output_parts)
                if seg_status != "completed":
                    status = seg_status
        except Exception as exc:
            status = "error"
            output_parts.append(f"Error in {role}: {exc}")
            role_outputs[role] = "".join(output_parts)
            break
        role_outputs[role] = "".join(output_parts)
        if status == "error":
            break

    return {
        "session_id": last_session.id if last_session else "",
        "agent_id": falsifier.id,
        "output": json.dumps(role_outputs),
        "status": status,
        "delegation_mode": "sequential_fallback",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Path C — Routine driver (local loop fallback, swap point for native /fire)
# ─────────────────────────────────────────────────────────────────────────────


def _dir_fingerprint(path: Path) -> str:
    """Hash of (filename, size, mtime) tuples under path. Cheap, non-recursive."""
    if not path.exists():
        return "missing"
    entries = sorted(
        (f.name, f.stat().st_size, int(f.stat().st_mtime))
        for f in path.iterdir()
        if f.is_file()
    )
    return hashlib.sha256(json.dumps(entries).encode()).hexdigest()[:16]


def run_path_c_routine(
    night: int,
    *,
    interval_seconds: int = 1800,
    max_iterations: int = 0,
    watch_dir: str | None = None,
    log_path: str = "results/routine/verdicts.jsonl",
    invoke_fn: Callable[[int], dict] | None = None,
    sleeper: Callable[[float], None] = time.sleep,
) -> dict:
    """
    Path C: local scheduled/watch-dir driver around Path B (fallback) or a
    native Routine `/fire` call (via `theory_copilot.routines_client`).

    Parameters
    ----------
    night : int (2, 3, or 4)
        Which night task to drive each iteration.
    interval_seconds : int
        Seconds between iterations. Default 30 min. 0 = fire-and-return.
    max_iterations : int
        Hard stop after this many invocations (0 = unbounded, exit via SIGINT).
    watch_dir : str | None
        If set, only invoke when this directory's file fingerprint changes.
        The first iteration always runs (baseline).
    log_path : str
        Append-mode JSONL file of per-iteration verdicts.
    invoke_fn : callable(night) -> dict
        Override the invocation (testing / swap-in for Routine `/fire` call).
        Defaults to `run_path_b`. Swap to
        `functools.partial(fire_routine_local, trig_id=..., token=...)` to
        promote this driver to a real Routines wrapper.
    sleeper : callable(float) -> None
        Override sleep (testing).

    Returns
    -------
    dict with last iteration's result plus `iteration_count` and `status`.
    """
    if night not in (2, 3, 4):
        raise ValueError(f"night must be 2, 3, or 4; got {night}")

    invoke = invoke_fn or (lambda n: run_path_b(n))
    watch_path = Path(watch_dir) if watch_dir else None
    log = Path(log_path)
    log.parent.mkdir(parents=True, exist_ok=True)

    last_fingerprint: str | None = None
    last_result: dict = {"status": "not_started"}
    iteration = 0

    try:
        while True:
            iteration += 1
            current_fp = _dir_fingerprint(watch_path) if watch_path else None

            should_run = (
                watch_path is None  # unconditional cadence
                or last_fingerprint is None  # first pass always runs
                or current_fp != last_fingerprint  # change-triggered
            )

            if should_run:
                last_result = invoke(night)
                entry = {
                    "iteration": iteration,
                    "timestamp": int(time.time()),
                    "night": night,
                    "watch_fingerprint": current_fp,
                    "session_id": last_result.get("session_id", ""),
                    "status": last_result.get("status", "unknown"),
                    "output_chars": len(last_result.get("output", "") or ""),
                }
                with log.open("a") as fh:
                    fh.write(json.dumps(entry) + "\n")
                last_fingerprint = current_fp
            else:
                entry = {
                    "iteration": iteration,
                    "timestamp": int(time.time()),
                    "night": night,
                    "watch_fingerprint": current_fp,
                    "status": "skipped_no_change",
                }
                with log.open("a") as fh:
                    fh.write(json.dumps(entry) + "\n")

            if max_iterations and iteration >= max_iterations:
                break
            if interval_seconds <= 0:
                break
            sleeper(interval_seconds)
    except KeyboardInterrupt:
        last_result["status"] = last_result.get("status", "interrupted")

    return {
        **last_result,
        "iteration_count": iteration,
        "log_path": str(log),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Session event log persistence + replay
#
# The session event log is append-only on the server and survives the original
# harness. A second process can page-through events via `events.list` and
# resume where the first harness stopped. This is the "brain/body decoupling"
# the engineering post foregrounds — plain Messages API has no equivalent.
#
# We use cursor pagination (docs: no after-timestamp filter) and dedupe by
# event.id when replaying into a live stream.
# ─────────────────────────────────────────────────────────────────────────────


def persist_session_events(
    session_id: str,
    out_path: str | Path,
    *,
    client: Any | None = None,
    order: str = "asc",
) -> dict:
    """Page through `events.list` and dump every event as JSONL.

    Returns {"session_id", "event_count", "out_path", "first_event_type",
             "last_event_type"}.

    This is the foundation of our brain/body-decouple demo: a session can be
    run, the log persisted, the harness killed, and a later process replays
    the log to continue work in a fresh session.
    """
    cli = client or anthropic.Anthropic()
    out = Path(out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    first_type = ""
    last_type = ""
    with out.open("w") as fh:
        pager = cli.beta.sessions.events.list(session_id, order=order)
        for event in _iter_paginated(pager):
            serial = _event_to_dict(event)
            fh.write(json.dumps(serial, default=str) + "\n")
            etype = serial.get("type", "")
            if count == 0:
                first_type = etype
            last_type = etype
            count += 1

    return {
        "session_id": session_id,
        "event_count": count,
        "out_path": str(out),
        "first_event_type": first_type,
        "last_event_type": last_type,
    }


def replay_session_from_log(
    log_path: str | Path,
    target_session_id: str,
    *,
    client: Any | None = None,
    include_types: Iterable[str] | None = None,
) -> dict:
    """Read a persisted event log and re-inject user-origin events into a
    different session. This is the smallest useful demonstration of session
    event portability: the 'brain' (event log) moves between 'bodies'
    (sessions/environments) without touching the Claude model's context window.

    Only events that a client is allowed to send are re-injected:
    `user.message`, `user.interrupt`, `user.custom_tool_result`,
    `user.tool_confirmation`, `user.define_outcome`. Agent/tool/span events
    are summary-logged, not re-sent (the platform owns those).
    """
    cli = client or anthropic.Anthropic()
    allowed = set(include_types) if include_types else {
        "user.message",
        "user.interrupt",
        "user.custom_tool_result",
        "user.tool_confirmation",
    }

    replayed = 0
    skipped_by_type: dict[str, int] = {}
    log = Path(log_path)
    with log.open() as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            event = json.loads(line)
            etype = event.get("type", "")
            if etype in allowed:
                payload = {k: v for k, v in event.items()
                           if k in {"type", "content"}}
                cli.beta.sessions.events.send(
                    target_session_id, events=[payload]
                )
                replayed += 1
            else:
                skipped_by_type[etype] = skipped_by_type.get(etype, 0) + 1

    return {
        "target_session_id": target_session_id,
        "events_replayed": replayed,
        "events_skipped_by_type": skipped_by_type,
        "log_path": str(log),
    }


def _iter_paginated(pager: Any) -> Iterable[Any]:
    """Yield every item from a SyncPageCursor (or a plain list, for tests)."""
    if hasattr(pager, "__iter__") and not hasattr(pager, "next_page"):
        yield from pager
        return
    current = pager
    while current is not None:
        for item in current:
            yield item
        next_page = getattr(current, "next_page", None)
        if callable(next_page):
            current = next_page()
            if current is None:
                break
        else:
            break


def _event_to_dict(event: Any) -> Mapping[str, Any]:
    """Best-effort serialize an SDK event (pydantic / dataclass / dict) to JSON."""
    if isinstance(event, Mapping):
        return event
    for attr in ("model_dump", "dict", "to_dict"):
        fn = getattr(event, attr, None)
        if callable(fn):
            try:
                return fn()
            except TypeError:
                pass
    return {
        "type": getattr(event, "type", ""),
        "content": getattr(event, "content", None),
        "id": getattr(event, "id", None),
        "processed_at": getattr(event, "processed_at", None),
    }

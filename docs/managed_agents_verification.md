# Managed Agents API Verification

**Verified against live docs — 2026-04-22**

---

## Verified API Shape (as of 2026-04-22)

Managed Agents is a **three-resource model**: create an Agent, create an Environment, then create
a Session that references both.  Session creation does **not** accept `model`, `instructions`, or
`tools` — those live on the Agent object.

```python
import anthropic

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY; beta header set automatically

# ── Step 1: Create a persistent Agent ─────────────────────────────────────────
agent = client.beta.agents.create(
    name="night2_pysr_sweep",
    model="claude-opus-4-7",
    system="You are a scientific computing assistant ...",  # ← "system", NOT "instructions"
    tools=[
        {"type": "agent_toolset_20260401"},                # ← full toolset: bash + files + web
    ],
)
# agent.id and agent.version are returned; store agent.id for reuse across sessions

# ── Step 2: Create an Environment (container config) ──────────────────────────
environment = client.beta.environments.create(
    name="pysr-compute-env",
    config={
        "type": "cloud",
        "networking": {"type": "unrestricted"},
    },
)

# ── Step 3: Start a Session ───────────────────────────────────────────────────
session = client.beta.sessions.create(
    agent=agent.id,                     # str → uses latest agent version
    environment_id=environment.id,      # required
    title="Night 2 PySR sweep",         # optional label (was "name" in pseudocode)
)

# ── Step 4: Open stream, then send message ────────────────────────────────────
# IMPORTANT: open the stream BEFORE sending the message
with client.beta.sessions.events.stream(session.id) as stream:
    client.beta.sessions.events.send(
        session.id,
        events=[
            {
                "type": "user.message",
                "content": [
                    {"type": "text", "text": "Run the PySR hyperparameter sweep ..."},
                ],
            },
        ],
    )

    for event in stream:
        match event.type:
            case "agent.message":
                for block in event.content:
                    print(block.text, end="", flush=True)
            case "agent.tool_use":
                print(f"\n[Tool: {event.name}]")
            case "session.status_idle":
                print("\n\nAgent finished.")
                break
```

---

## Key Findings

| Aspect | Value |
|---|---|
| **Beta header** | `managed-agents-2026-04-01` (SDK sets it automatically; confirmed) |
| **Agent create** | `client.beta.agents.create(name, model, system, tools)` |
| **Environment create** | `client.beta.environments.create(name, config)` |
| **Session create** | `client.beta.sessions.create(agent, environment_id, title?)` |
| **Required session params** | `agent` (str ID or versioned object), `environment_id` |
| **Optional session params** | `title`, `vault_ids` |
| **Send message** | `client.beta.sessions.events.send(session_id, events=[...])` |
| **Stream output** | `client.beta.sessions.events.stream(session_id)` context manager |
| **Bash tool access** | `{"type": "agent_toolset_20260401"}` on `agents.create(tools=[...])` |
| **Bash tool name** | `"bash"` (part of the toolset; enabled by default) |
| **Idle signal** | `event.type == "session.status_idle"` |
| **SDK namespace** | `client.beta.*` — NOT `client.beta.managed_agents.*` |

---

## What Changed vs. Pseudocode

| Pseudocode (incorrect) | Correct |
|---|---|
| `client.beta.managed_agents.sessions.create(...)` | `client.beta.sessions.create(...)` (no `managed_agents` namespace) |
| Session param `name="night2_pysr_sweep"` | Goes on Agent as `name=...`; session uses `title=` |
| Session param `model="claude-opus-4-7"` | Goes on `agents.create(model=...)`, not on session |
| Session param `instructions="..."` | Param is `system=` on `agents.create`, not `instructions=` |
| Session param `tools=[...]` | Goes on `agents.create(tools=[...])`, not on session |
| Single-call creation | **Three calls**: `agents.create` → `environments.create` → `sessions.create` |
| No environment concept | Environment is a required separate resource with its own ID |
| No streaming pattern shown | Stream must open **before** sending the user message |

---

## Waitlist Status

| Feature | Status |
|---|---|
| Basic sessions (create agent, env, session, send message, stream) | **Public beta — no waitlist** |
| Built-in toolset (`agent_toolset_20260401`: bash, file ops, web search) | **Public beta — no waitlist** |
| Custom tools | **Public beta — no waitlist** |
| MCP server integration | **Public beta — no waitlist** |
| **Outcomes** (structured result evaluation) | Research preview — **waitlist required** |
| **Multiagent** (agents spawning sub-agents) | Research preview — **waitlist required** |
| **Memory** (persistent memory stores across sessions) | Research preview — **waitlist required** |

Waitlist form: `https://claude.com/form/claude-managed-agents`

---

## Corrected Overnight Sweep Snippet

Drop-in replacement for the Night 2 PySR sweep orchestration.  Creates the agent and environment
once at startup, then fires a session per sweep configuration.

```python
"""
Night 2 PySR hyperparameter sweep — corrected Managed Agents orchestration.
Run once to create the persistent agent + environment, then loop over sweep configs.
"""

import os
import anthropic

client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

# ── Persistent resources (create once, reuse across sweeps) ───────────────────

agent = client.beta.agents.create(
    name="pysr-sweep-agent",
    model="claude-opus-4-7",
    system=(
        "You are a scientific computing assistant specializing in symbolic regression. "
        "Execute PySR hyperparameter sweeps exactly as specified, log all results to "
        "sweep_results.jsonl, and confirm completion with a structured summary."
    ),
    tools=[
        {
            "type": "agent_toolset_20260401",  # bash + read + write + edit + glob + grep + web
        }
    ],
)
print(f"Agent created: {agent.id} (version {agent.version})")

environment = client.beta.environments.create(
    name="pysr-compute-env",
    config={
        "type": "cloud",
        "networking": {"type": "unrestricted"},
    },
)
print(f"Environment created: {environment.id}")

# ── Sweep loop (one session per configuration) ────────────────────────────────

SWEEP_CONFIGS = [
    {"niterations": 1000, "populations": 15, "maxsize": 20},
    {"niterations": 2000, "populations": 30, "maxsize": 30},
    # … add configs as needed
]

for i, cfg in enumerate(SWEEP_CONFIGS):
    print(f"\n── Sweep {i+1}/{len(SWEEP_CONFIGS)}: {cfg}")

    session = client.beta.sessions.create(
        agent=agent.id,
        environment_id=environment.id,
        title=f"pysr_sweep_{i+1}_niter{cfg['niterations']}",
    )

    task_prompt = (
        f"Run PySR with the following hyperparameters:\n"
        f"  niterations={cfg['niterations']}\n"
        f"  populations={cfg['populations']}\n"
        f"  maxsize={cfg['maxsize']}\n"
        f"Log results to sweep_results.jsonl and print the top-3 equations with their scores."
    )

    # Open stream before sending — avoids missed events
    with client.beta.sessions.events.stream(session.id) as stream:
        client.beta.sessions.events.send(
            session.id,
            events=[
                {
                    "type": "user.message",
                    "content": [{"type": "text", "text": task_prompt}],
                }
            ],
        )

        for event in stream:
            match event.type:
                case "agent.message":
                    for block in event.content:
                        print(block.text, end="", flush=True)
                case "agent.tool_use":
                    print(f"\n  [Tool: {event.name}]")
                case "session.status_idle":
                    print(f"\n  Sweep {i+1} complete.")
                    break

print("\n\nAll sweeps finished.")
```

> **Note on agent reuse**: The agent and environment are persistent resources.  If the script is
> interrupted and rerun, you can skip creation by storing `agent.id` / `environment.id` in a
> config file and calling `client.beta.agents.retrieve(agent_id)` /
> `client.beta.environments.retrieve(env_id)` instead of creating new ones.

---

## Sources

| URL | Description | Fetched |
|---|---|---|
| `https://platform.claude.com/docs/en/managed-agents/overview` | Official overview, core concepts, beta header, access tiers | 2026-04-22 |
| `https://platform.claude.com/docs/en/managed-agents/quickstart` | Full quickstart with Python code: agent + env + session + stream | 2026-04-22 |
| `https://platform.claude.com/docs/en/managed-agents/sessions` | Session create, send, archive, delete API reference | 2026-04-22 |
| `https://platform.claude.com/docs/en/managed-agents/tools` | Tool config, `agent_toolset_20260401`, per-tool enable/disable | 2026-04-22 |
| `https://github.com/anthropics/skills/blob/main/skills/claude-api/python/managed-agents/README.md` | Python SDK skill README with client paths and stream pattern | 2026-04-22 |
| Web search: "anthropic managed agents waitlist multiagent outcomes memory research preview 2026" | Waitlist status for outcomes / multiagent / memory features | 2026-04-22 |

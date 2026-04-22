import os

import anthropic

NIGHT2_SYSTEM = (
    "You are a scientific computing assistant specializing in symbolic regression. "
    "Your task: run a PySR hyperparameter sweep on the ND2 gene expression dataset, "
    "batch-judge the resulting candidate equations using Sonnet, and write all results "
    "to manifest_night2.json. Use bash to execute python3 src/pysr_sweep.py and any "
    "downstream scripts. Log progress and confirm completion with a structured summary."
)

NIGHT3_SYSTEM = (
    "You are a scientific computing assistant specializing in hypothesis falsification. "
    "Your task: run falsification tests on the top-50 candidate equations from Night 2. "
    "Execute python3 src/falsification_sweep.py to test each candidate against null "
    "distributions, shuffle controls, and cross-dataset replication. Write the final "
    "ranked results to falsification_report.json. Confirm completion with a structured summary."
)

NIGHT4_SYSTEM = (
    "You are a scientific computing assistant specializing in biological law validation. "
    "Your task: validate the top surviving equations from Night 3 on the GSE40435 dataset "
    "(independent PBMC cohort). Run transfer validation, compute AUC and confidence intervals, "
    "and write all results to transfer_report.json. Confirm completion with a structured summary."
)

_NIGHT_SYSTEMS = {2: NIGHT2_SYSTEM, 3: NIGHT3_SYSTEM, 4: NIGHT4_SYSTEM}

_NIGHT_TASKS = {
    2: (
        "Run the PySR hyperparameter sweep:\n"
        "  python3 src/pysr_sweep.py --config config/datasets.json --outdir results/night2\n"
        "Then batch-judge all candidate equations and write the final manifest to "
        "manifest_night2.json. Include top-10 equations with AUC scores."
    ),
    3: (
        "Run the falsification sweep on the top-50 candidates from manifest_night2.json:\n"
        "  python3 src/falsification_sweep.py "
        "--manifest results/night2/manifest_night2.json "
        "--top 50 --outfile results/night3/falsification_report.json\n"
        "Write the ranked results to falsification_report.json."
    ),
    4: (
        "Run GSE40435 transfer validation on the surviving equations from "
        "falsification_report.json:\n"
        "  python3 src/transfer_validation.py "
        "--report results/night3/falsification_report.json "
        "--dataset GSE40435 --outfile results/night4/transfer_report.json\n"
        "Write results with AUC and 95% CI to transfer_report.json."
    ),
}


def run_path_b(
    night: int,
    hpc_project_dir: str = "",
    title: str | None = None,
) -> dict:
    """
    Path B: single Managed Agent with agent_toolset_20260401 (public beta, no waitlist).

    Night 2 task: run PySR sweep → batch Sonnet judgment → write manifest_night2.json
    Night 3 task: run falsification sweep on top 50 → write falsification_report.json
    Night 4 task: run GSE40435 validation → write transfer_report.json

    Returns: {"session_id": str, "agent_id": str, "output": str, "status": "completed"|"error"}
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

    session = client.beta.sessions.create(
        agent=agent.id,
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
            for event in stream:
                match event.type:
                    case "agent.message":
                        for block in event.content:
                            output_parts.append(block.text)
                    case "session.status_idle":
                        break
    except Exception as exc:
        status = "error"
        output_parts.append(f"Error: {exc}")

    return {
        "session_id": session.id,
        "agent_id": agent.id,
        "output": "".join(output_parts),
        "status": status,
    }


def run_path_a(
    night: int,
    title: str | None = None,
) -> dict:
    """
    Path A: callable_agents multiagent (requires waitlist).

    Three-agent pattern:
      - Proposer agent (Opus 4.7): reads law_proposals.json, refines law families
      - Searcher agent (Sonnet 4.6): executes PySR via bash, writes candidates
      - Falsifier agent (Opus 4.7): runs falsification_sweep.py, writes report

    Raises NotImplementedError if MANAGED_AGENTS_WAITLIST != "approved".
    Returns same dict shape as run_path_b.
    """
    if os.environ.get("MANAGED_AGENTS_WAITLIST") != "approved":
        raise NotImplementedError("callable_agents requires waitlist approval")

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
        name=f"theory-copilot-multiagent-night{night}",
        config={"type": "cloud", "networking": {"type": "unrestricted"}},
    )

    all_outputs: list[str] = []
    status = "completed"
    last_session = None

    for role, agent in [
        ("proposer", proposer),
        ("searcher", searcher),
        ("falsifier", falsifier),
    ]:
        session = client.beta.sessions.create(
            agent=agent.id,
            environment_id=environment.id,
            title=title or f"Night {night} {role}",
        )
        last_session = session
        task = (
            f"Execute your assigned task for Night {night}. "
            "Previous agents have prepared inputs in results/."
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
                for event in stream:
                    match event.type:
                        case "agent.message":
                            for block in event.content:
                                all_outputs.append(block.text)
                        case "session.status_idle":
                            break
        except Exception as exc:
            status = "error"
            all_outputs.append(f"Error in {role}: {exc}")
            break

    return {
        "session_id": last_session.id if last_session else "",
        "agent_id": falsifier.id,
        "output": "".join(all_outputs),
        "status": status,
    }

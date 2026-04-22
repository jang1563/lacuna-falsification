import os

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
    "Your task: run the 4-test falsification gate on the top-50 candidate equations "
    "from Night 2. Execute python3 src/falsification_sweep.py to test each candidate "
    "against permutation null, bootstrap stability, best-single-feature baseline, and "
    "covariate-only confound. Apply Benjamini-Hochberg FDR across candidates. Write "
    "the ranked report (equation, passes, perm_p, perm_p_fdr, ci_lower, delta_baseline, "
    "delta_confound, fail_reason) to results/night3/falsification_report.json. Confirm "
    "completion with a structured summary."
)

NIGHT4_SYSTEM = (
    "You are a scientific computing assistant specializing in biological law validation. "
    "Your task: replay the top surviving laws from Night 3 on the GSE40435 cohort "
    "(independent ccRCC kidney tissue cohort, 101 paired tumor-normal samples, "
    "microarray platform — different from TCGA-KIRC's RNA-seq). Run the same "
    "falsification gate on the independent cohort with per-cohort z-score "
    "standardization. Compute three-way verdict: law_transfers (same equation "
    "survives), workflow_transfers (some law in family survives), or neither. "
    "Write all results (per-equation AUC with 95% CI, verdict) to "
    "results/night4/transfer_report.json. Confirm completion with a structured summary."
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

    role_outputs: dict[str, str] = {}
    status = "completed"
    last_session = None

    chain = [
        (
            "proposer",
            proposer,
            (
                f"Night {night}: select 3-5 compact law families from config/law_proposals.json "
                "(including the required negative control) and write a refined set to "
                "results/proposer_output.json. Emit the family list as JSON in your final message."
            ),
        ),
        (
            "searcher",
            searcher,
            (
                "Read the Proposer's law families below and run PySR via bash:\n"
                "  python3 src/pysr_sweep.py --data <flagship_csv> --genes <CSV of genes> "
                "--proposals config/law_proposals.json --standardize "
                "--output results/candidates.json\n"
                "Emit a JSON summary of candidate equations with train_auroc + test_auroc + novelty.\n\n"
                "=== Proposer output ===\n{proposer}\n=== end Proposer output ==="
            ),
        ),
        (
            "falsifier",
            falsifier,
            (
                "Read the Searcher's candidate equations below and run the 4-test gate:\n"
                "  python3 src/falsification_sweep.py --candidates results/candidates.json "
                "--data <flagship_csv> --genes <CSV of genes> --covariate-cols age,batch_index "
                "--output results/falsification_report.json\n"
                "Emit a JSON summary naming every candidate plus perm_p, perm_p_fdr, ci_lower, "
                "delta_baseline, delta_confound, decoy_p, passes, fail_reason. Flag any law where "
                "train_auroc >> test_auroc as overfit.\n\n"
                "=== Searcher output ===\n{searcher}\n=== end Searcher output ==="
            ),
        ),
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
                for event in stream:
                    match event.type:
                        case "agent.message":
                            for block in event.content:
                                output_parts.append(block.text)
                        case "session.status_idle":
                            break
        except Exception as exc:
            status = "error"
            output_parts.append(f"Error in {role}: {exc}")
            role_outputs[role] = "".join(output_parts)
            break
        role_outputs[role] = "".join(output_parts)

    import json as _json
    return {
        "session_id": last_session.id if last_session else "",
        "agent_id": falsifier.id,
        "output": _json.dumps(role_outputs),
        "status": status,
    }

#!/usr/bin/env python3
"""PhL-9 v2 — Path A sequential chain on REAL TCGA-KIRC data.

Closes the evidence weakness in PhL-9 v1: the v1 chain ran on a synthetic
physics toy problem because the environment did not have our CSV or
law proposals mounted. v2 uploads `data/kirc_metastasis_expanded.csv` +
`config/law_proposals.json` via `client.beta.files.upload()` and mounts
them into each session via `resources=[{"type":"file","file_id":...,
"mount_path":...}]`.

The Proposer now sees 505 rows × 45 ccRCC genes with `label` ∈ {control, metastasis},
`m_stage` ∈ {M0, M1}. Families + ex-ante skeptic tests should reference
actual ccRCC biology (TOP2A, EPAS1, CA9, VEGFA). The Skeptic verdict
should cite real TCGA-KIRC metrics, not `y = 3.67 * x^1.40`.

Sequential public-beta-compliant chain (fairness-ruling compliant):
  Session A — Proposer   (Opus 4.7, adaptive thinking, xhigh effort)
  Session B — Searcher   (Sonnet 4.6, runs PySR-style fit via bash)
  Session C — Skeptic    (Opus 4.7, adaptive thinking, xhigh effort)

Each session runs in its own session_id in the same environment_id.
JSON handoff between sessions via user-message injection.

Cost: ~$1.50. Wall: ~8-12 min.
Usage:
    source ~/.api_keys  # or set ANTHROPIC_API_KEY
    PYTHONPATH=src .venv/bin/python src/phl9v2_path_a_real_data.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import anthropic

REPO_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = REPO_ROOT / "data" / "kirc_metastasis_expanded.csv"
LAWS_PATH = REPO_ROOT / "config" / "law_proposals.json"
OUT_DIR = REPO_ROOT / "results" / "live_evidence" / "phl9v2_path_a_real_data"

BETA = ["managed-agents-2026-04-01"]


def _drain(client, session_id):
    """Stream session events until idle. Return (text, transcript, events_len)."""
    parts = []
    transcript = []
    with client.beta.sessions.events.stream(session_id) as stream:
        for event in stream:
            etype = getattr(event, "type", "")
            try:
                transcript.append(event.model_dump())
            except Exception:
                transcript.append({"type": etype})
            if etype == "agent.message":
                for block in getattr(event, "content", []) or []:
                    text = getattr(block, "text", "") or ""
                    if text:
                        parts.append(text)
            elif etype in ("session.status_idle",
                           "session.status_terminated",
                           "session.error"):
                break
    return "".join(parts).strip(), transcript, len(transcript)


def _run_session(client, agent_id, env_id, file_resources, prompt, label):
    session = client.beta.sessions.create(
        agent=agent_id,
        environment_id=env_id,
        resources=file_resources,
        betas=BETA,
    )
    print(f">>> {label}: session_id={session.id}")
    client.beta.sessions.events.send(
        session.id,
        events=[{"type": "user.message",
                 "content": [{"type": "text", "text": prompt}]}],
        betas=BETA,
    )
    text, transcript, n_events = _drain(client, session.id)
    print(f"    {label}: {len(text)} chars, {n_events} events")
    return {"session_id": session.id, "text": text, "n_events": n_events, "transcript": transcript}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not CSV_PATH.exists():
        raise SystemExit(f"Missing {CSV_PATH}")
    if not LAWS_PATH.exists():
        raise SystemExit(f"Missing {LAWS_PATH}")

    client = anthropic.Anthropic()
    t0 = time.time()

    # ------------------------------------------------------------------
    # 1) Upload real data + law proposals
    # ------------------------------------------------------------------
    print(">>> Uploading data + law proposals ...")
    csv_meta = client.beta.files.upload(
        file=(CSV_PATH.name, open(CSV_PATH, "rb"), "text/csv"),
        betas=BETA,
    )
    laws_meta = client.beta.files.upload(
        file=(LAWS_PATH.name, open(LAWS_PATH, "rb"), "application/json"),
        betas=BETA,
    )
    print(f"    csv:  id={csv_meta.id}  size={csv_meta.size_bytes}")
    print(f"    laws: id={laws_meta.id} size={laws_meta.size_bytes}")

    resources = [
        {"type": "file", "file_id": csv_meta.id,
         "mount_path": "/workspace/kirc_metastasis_expanded.csv"},
        {"type": "file", "file_id": laws_meta.id,
         "mount_path": "/workspace/law_proposals.json"},
    ]

    # ------------------------------------------------------------------
    # 2) Environment with data-analysis packages pre-installed
    # ------------------------------------------------------------------
    print(">>> Creating environment ...")
    env = client.beta.environments.create(
        name="phl9v2-real-kirc",
        config={
            "type": "cloud",
            "networking": {"type": "unrestricted"},
            "packages": {
                "type": "packages",
                "pip": ["pandas>=2.0", "numpy>=1.24", "scikit-learn>=1.3"],
            },
        },
        betas=BETA,
    )
    print(f"    env_id={env.id}")

    # ------------------------------------------------------------------
    # 3) Three agents, each with adaptive thinking + effort high
    # ------------------------------------------------------------------
    common_tools = [{"type": "agent_toolset_20260401"}]
    proposer = client.beta.agents.create(
        name="phl9v2-proposer",
        model="claude-opus-4-7",
        system=(
            "You are the Proposer in a pre-registered biological law "
            "discovery loop. Read /workspace/kirc_metastasis_expanded.csv "
            "(TCGA-KIRC, label column, m_stage column, 45 gene expression "
            "columns log-normalized) and /workspace/law_proposals.json "
            "(template library). Emit 3-5 COMPACT ccRCC law families for "
            "predicting M0-vs-M1 metastasis, each with an ex-ante skeptic "
            "test (the test you would use to KILL the law before any fit). "
            "Include at least one ex-ante negative control (housekeeping-"
            "gene form). Output strict JSON."
        ),
        tools=common_tools,
        betas=BETA,
    )
    searcher = client.beta.agents.create(
        name="phl9v2-searcher",
        model="claude-sonnet-4-6",
        system=(
            "You are the Searcher. Read the Proposer's JSON law families "
            "and evaluate each candidate on the mounted "
            "/workspace/kirc_metastasis_expanded.csv data. For each family, "
            "compute law_auroc on m_stage (M0=0, M1=1), best-single-gene "
            "sign-invariant AUROC baseline, and delta_baseline. Use pandas "
            "+ sklearn in bash. Emit strict JSON with per-candidate numbers."
        ),
        tools=common_tools,
        betas=BETA,
    )
    skeptic = client.beta.agents.create(
        name="phl9v2-skeptic",
        model="claude-opus-4-7",
        system=(
            "You are the Skeptic. Given the pre-registered 5-test gate "
            "thresholds {perm_p<0.05, ci_lower>0.6, delta_baseline>0.05, "
            "delta_confound>0.03 or null when covariates degenerate, "
            "decoy_p<0.05} and the Searcher's reported metrics on real "
            "TCGA-KIRC, emit a strict-JSON verdict per candidate: "
            "PASS / FAIL / NEEDS_MORE_TESTS with named failing gates and "
            "specific metric values quoted. Do not re-negotiate thresholds. "
            "For candidates lacking full metric coverage (no permutation "
            "or bootstrap run in the environment), emit NEEDS_MORE_TESTS "
            "with a named missing test."
        ),
        tools=common_tools,
        betas=BETA,
    )
    print(f"    proposer_agent={proposer.id}")
    print(f"    searcher_agent={searcher.id}")
    print(f"    skeptic_agent={skeptic.id}")

    # ------------------------------------------------------------------
    # 4) Sequential chain with structured-JSON handoff
    # ------------------------------------------------------------------
    proposer_prompt = (
        "## Inputs mounted\n"
        "- `/workspace/kirc_metastasis_expanded.csv` — TCGA-KIRC, 505 "
        "rows, 45 genes + sample_id, label, m_stage, age, batch_index. "
        "Genes include TOP2A, MKI67, CDK1, CCNB1, PCNA, EPAS1, CA9, "
        "VEGFA, LDHA, SLC2A1, AGXT, ALB, ACTB, GAPDH, RPL13A (plus 30 "
        "more metastasis / HIF / Warburg / housekeeping genes).\n"
        "- `/workspace/law_proposals.json` — template library.\n\n"
        "## Task\n"
        "1. Use bash to inspect the CSV header + a few rows to confirm "
        "column names and scale.\n"
        "2. Propose 3-5 ccRCC metastasis law families, compact (≤5 "
        "genes each), including:\n"
        "   - at least one proliferation − HIF-2α contrast;\n"
        "   - at least one Warburg-based form;\n"
        "   - one ex-ante negative control (housekeeping gene form).\n"
        "3. For each family, give (a) initial_guess as a Python-"
        "parseable equation in gene names, (b) ex-ante skeptic_test "
        "written BEFORE any fit.\n"
        "4. Emit strict JSON with schema `{\"night\":2,\"families\":[{"
        "\"id\":\"LF-...\",\"name\":...,\"role\":\"candidate|negative_"
        "control\",\"initial_guess\":...,\"skeptic_test\":...}]}`."
    )
    s_prop = _run_session(client, proposer.id, env.id, resources,
                          proposer_prompt, "A (Proposer Opus 4.7)")

    searcher_prompt = (
        "## Prior output from Proposer\n\n" + s_prop["text"] +
        "\n\n## Task\n"
        "1. Parse the Proposer's JSON.\n"
        "2. For each candidate family, evaluate `initial_guess` on "
        "`/workspace/kirc_metastasis_expanded.csv`. Use `m_stage` "
        "column: M1 → 1, M0 → 0, drop rows with missing m_stage.\n"
        "3. Compute per candidate:\n"
        "   - `law_auroc` (roc_auc_score)\n"
        "   - `best_single_gene_sign_invariant_auroc` = max_g max("
        "auroc(g), 1−auroc(g)) over the same gene set used in the law\n"
        "   - `delta_baseline` = law_auroc − best_single_gene_sign_"
        "invariant_auroc\n"
        "4. Emit strict JSON matching schema: "
        '{"candidates":[{"id":...,"equation":...,"law_auroc":...,'
        '"baseline_auroc_best_single_gene":...,"delta_baseline":...,'
        '"n":...}]}. Do NOT run bootstrap or permutation — those '
        "belong to the gate. Report only these three pre-gate numbers."
    )
    s_search = _run_session(client, searcher.id, env.id, resources,
                            searcher_prompt, "B (Searcher Sonnet 4.6)")

    skeptic_prompt = (
        "## Prior output from Searcher on REAL TCGA-KIRC\n\n"
        + s_search["text"] +
        "\n\n## Pre-registered 5-test gate thresholds (fixed before any fit)\n"
        "- perm_p < 0.05\n- ci_lower > 0.6\n- delta_baseline > 0.05\n"
        "- delta_confound > 0.03 or null-allowed when covariates degenerate\n"
        "- decoy_p < 0.05\n\n"
        "## Task\n"
        "1. Apply `delta_baseline > 0.05` to the Searcher's metrics. "
        "Permutation, bootstrap-CI, and decoy tests were NOT run in "
        "this environment — treat those as unresolved.\n"
        "2. For each candidate emit strict JSON: `{\"id\":...,"
        "\"verdict\":\"PASS|FAIL|NEEDS_MORE_TESTS\",\"failing_gates\":"
        "[...],\"rationale\":\"...\"}` quoting the specific "
        "delta_baseline value.\n"
        "3. Rules:\n"
        "   - If `delta_baseline <= 0.05` → FAIL on delta_baseline.\n"
        "   - If `delta_baseline > 0.05` AND missing perm_p/ci_lower/"
        "decoy_p → NEEDS_MORE_TESTS with missing gates named.\n"
        "   - If metrics are present and all clear → PASS.\n"
        "   - Do not re-negotiate thresholds.\n"
        "4. End with one aggregate sentence citing the COHORT: "
        "'On TCGA-KIRC (n=...), <k> of <N> candidates meet the "
        "delta_baseline threshold; <m> are NEEDS_MORE_TESTS pending "
        "permutation / bootstrap / decoy.'"
    )
    s_skep = _run_session(client, skeptic.id, env.id, resources,
                          skeptic_prompt, "C (Skeptic Opus 4.7)")

    elapsed = time.time() - t0

    # ------------------------------------------------------------------
    # 5) Persist artefacts
    # ------------------------------------------------------------------
    verdict = {
        "hypothesis_id": "phl9v2_path_a_real_data",
        "run_date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "delegation_mode": "sequential_fallback",
        "status": "completed",
        "wall_seconds": round(elapsed, 1),
        "env_id": env.id,
        "agent_ids": {
            "proposer": proposer.id,
            "searcher": searcher.id,
            "skeptic": skeptic.id,
        },
        "session_ids": {
            "proposer": s_prop["session_id"],
            "searcher": s_search["session_id"],
            "skeptic":  s_skep["session_id"],
        },
        "file_ids": {
            "kirc_metastasis_expanded.csv": csv_meta.id,
            "law_proposals.json": laws_meta.id,
        },
        "per_role_char_counts": {
            "proposer": len(s_prop["text"]),
            "searcher": len(s_search["text"]),
            "skeptic":  len(s_skep["text"]),
        },
        "per_role_event_counts": {
            "proposer": s_prop["n_events"],
            "searcher": s_search["n_events"],
            "skeptic":  s_skep["n_events"],
        },
        "narrative": (
            "PhL-9 v2 — closes the PhL-9 v1 evidence weakness (which ran "
            "on a synthetic physics toy because no data was mounted). "
            "v2 uploads the real TCGA-KIRC metastasis_expanded CSV + "
            "our law_proposals.json template library via "
            "`client.beta.files.upload()` and mounts them into each "
            "session's /workspace/ via `resources=[{\"type\":\"file\",...}]`. "
            "The Proposer reads the real 505-row cohort, emits ccRCC-"
            "grounded law families (TOP2A / EPAS1 / CA9 / VEGFA). "
            "The Searcher fits them on the real data and reports "
            "law_auroc + delta_baseline. The Skeptic applies the "
            "pre-registered threshold and emits a PASS / NEEDS_MORE_"
            "TESTS verdict quoting real TCGA-KIRC numbers. Path A is "
            "the sequential public-beta-compliant execution path per "
            "the 2026-04-23 hackathon fairness ruling."
        ),
    }

    (OUT_DIR / "verdict.json").write_text(json.dumps(verdict, indent=2))
    (OUT_DIR / "role_proposer.txt").write_text(s_prop["text"])
    (OUT_DIR / "role_searcher.txt").write_text(s_search["text"])
    (OUT_DIR / "role_skeptic.txt").write_text(s_skep["text"])
    print(f"\n>>> Chain complete in {elapsed:.1f}s")
    print(f">>> Artefacts: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

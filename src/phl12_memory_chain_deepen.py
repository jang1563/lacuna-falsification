#!/usr/bin/env python3
"""PhL-12 — deepen Skeptic Memory chain to 8 entries.

Extends PhL-3 + PhL-7 + PhL-10 (5 lessons) with THREE additional
sessions probing edges of the accumulated rule set:

  Session 6 (template saturation edge) — `PCNA - EPAS1` on TCGA-KIRC
    metastasis_expanded, a THIRD `proliferation_marker − EPAS1` survivor
    candidate. Tests whether the agent applies lesson 4's explicit
    "flag template saturation if a third variant also passes" meta-rule.

  Session 7 (cross-cancer generalization of ceiling rule) — `KLK3 −
    log1p(MKI67)` on TCGA-PRAD (prostate) tumor-vs-normal. KLK3 = PSA,
    the canonical prostate tissue-of-origin marker. Tests lesson 5's
    "ceiling-effect rule generalizes across cancers" on yet another
    cohort the prior rule explicitly anticipated (KLK3 named in the
    lesson's upgrade list).

  Session 8 (pre-registration strictness edge) — a hypothetical
    candidate with decoy_p = 0.048 (below 0.05 → passes by design,
    but close to threshold). Tests whether the agent strictly applies
    the pre-registered threshold or invents a "marginal" verdict the
    pre-reg does not permit.

Reuses the PhL-3 agent + memory store (memstore_01XvqsnMxmHQPyL25X4t56Wq)
so this extends the same accumulated lesson chain.

Cost: ~$0.60. Wall: ~5 min.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import anthropic
import httpx

REPO_ROOT = Path(__file__).resolve().parent.parent
PHL3_STATE = REPO_ROOT / "results" / "live_evidence" / "phl3_state.json"
OUT_DIR = REPO_ROOT / "results" / "live_evidence" / "phl12_memory_chain_deepen"

API_BASE = "https://api.anthropic.com"
BETA = ["managed-agents-2026-04-01"]


def _headers():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise SystemExit("ANTHROPIC_API_KEY not set")
    return {
        "x-api-key": key,
        "anthropic-version": "2023-06-01",
        "anthropic-beta": "managed-agents-2026-04-01",
        "content-type": "application/json",
    }


def _drain(client, sid):
    parts, transcript = [], []
    with client.beta.sessions.events.stream(sid) as stream:
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
    return "".join(parts).strip(), len(transcript)


def _judge(client, state, label, eq, cohort, metrics, context):
    prompt = (
        "## Candidate to judge (session " + label + ")\n\n"
        f"**Equation:** `{eq}`\n"
        f"**Cohort:** {cohort}\n\n"
        "**Pre-computed metrics:**\n```json\n"
        f"{json.dumps(metrics, indent=2)}\n```\n\n"
        "## Pre-registered gate thresholds (DO NOT re-negotiate)\n\n"
        "- `perm_p < 0.05`\n- `ci_lower > 0.6`\n"
        "- `delta_baseline > 0.05`\n"
        "- `delta_confound > 0.03` (null allowed when cohort lacks "
        "non-degenerate covariates)\n- `decoy_p < 0.05`\n\n"
        "## Your job\n"
        "1. **Read** `/mnt/memory/skeptic-lessons/lessons.md` first. "
        "Quote any prior lesson that applies, OR explicitly note "
        "'no prior lesson applies' if none does.\n"
        "2. **Apply** the gate thresholds to the supplied metrics. "
        "Do NOT invent 'marginal' or 'tentative' verdicts — only "
        "PASS / FAIL / NEEDS_MORE_TESTS are pre-registered.\n"
        "3. **Return verdict** with named failing gates (if any) and "
        "specific metric values quoted.\n"
        "4. **Append** 1-2 line lesson to "
        "`/mnt/memory/skeptic-lessons/lessons.md` capturing what "
        "this candidate added. If it merely reaffirms existing "
        "lessons, write a one-line confirmation note and name "
        "which lesson it confirms.\n\n"
    )
    if context:
        prompt += "## Extra context\n\n" + context + "\n"

    session = client.beta.sessions.create(
        agent=state["agent_id"],
        environment_id=state["env_id"],
        resources=[{
            "type": "memory_store",
            "memory_store_id": state["store_id"],
            "access": "read_write",
            "instructions": (
                "Persistent Skeptic lessons across PhL-3 + PhL-7 + "
                "PhL-10 + PhL-12 sessions. ALWAYS read "
                "/mnt/memory/skeptic-lessons/lessons.md BEFORE judging; "
                "ALWAYS append a new lesson AFTER judging."
            ),
        }],
        title=f"PhL-12 {label}",
        betas=BETA,
    )
    print(f">>> {label}: session_id={session.id}")
    client.beta.sessions.events.send(
        session.id,
        events=[{"type": "user.message",
                 "content": [{"type": "text", "text": prompt}]}],
        betas=BETA,
    )
    text, n_events = _drain(client, session.id)
    print(f"    text={len(text)} chars, events={n_events}")
    return {"label": label, "session_id": session.id,
            "equation": eq, "cohort": cohort,
            "metrics": metrics, "agent_text": text,
            "n_events": n_events}


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not PHL3_STATE.exists():
        raise SystemExit(f"PhL-3 state missing at {PHL3_STATE}")
    state = json.loads(PHL3_STATE.read_text())
    print(f">>> Reusing PhL-3/7/10 state:")
    print(f"    agent_id={state['agent_id']}")
    print(f"    env_id={state['env_id']}")
    print(f"    store_id={state['store_id']}")

    client = anthropic.Anthropic()

    # Session 6 — template saturation edge
    s6 = _judge(
        client, state,
        label="session6_pcna_epas1_template_saturation",
        eq="PCNA - EPAS1",
        cohort="TCGA-KIRC metastasis_expanded (n=505, 16% M1)",
        metrics={
            "perm_p": 0.0,
            "ci_lower": 0.635,
            "delta_baseline": 0.058,
            "delta_confound": None,
            "decoy_p": 0.0,
            "law_auroc": 0.693,
            "baseline_auc_best_single_gene": 0.635,
        },
        context=(
            "PCNA is a proliferation marker (replication clamp). "
            "This is the THIRD `proliferation_marker − EPAS1` variant "
            "after TOP2A-EPAS1 and MKI67-EPAS1 — lesson 4 in memory "
            "explicitly warned about template saturation in this "
            "scenario."
        ),
    )
    time.sleep(2)

    # Session 7 — cross-cancer PRAD (KLK3 explicitly named in lesson 5)
    s7 = _judge(
        client, state,
        label="session7_prad_klk3_mki67_cross_cancer",
        eq="KLK3 - log1p(MKI67)",
        cohort="TCGA-PRAD tumor-vs-normal (n=497)",
        metrics={
            "perm_p": 0.001,
            "ci_lower": 0.93,
            "delta_baseline": 0.008,
            "delta_confound": 0.003,
            "decoy_p": 0.0,
            "law_auroc": 0.982,
            "baseline_auc_best_single_gene": 0.974,
        },
        context=(
            "PRAD (prostate adenocarcinoma), NEW cancer. KLK3 = PSA, "
            "the canonical prostate-tissue-of-origin marker — saturated "
            "for tumor-vs-normal. Lesson 5 in memory explicitly named "
            "PRAD/KLK3 in its upgrade list for the ceiling-effect rule."
        ),
    )
    time.sleep(2)

    # Session 8 — pre-registration strictness edge
    s8 = _judge(
        client, state,
        label="session8_edge_decoy_0048_strict_threshold",
        eq="CDK1 - EPAS1",
        cohort="TCGA-KIRC metastasis_expanded (n=505, 16% M1)",
        metrics={
            "perm_p": 0.002,
            "ci_lower": 0.612,
            "delta_baseline": 0.071,
            "delta_confound": None,
            "decoy_p": 0.048,  # below 0.05 threshold by 0.002 — strict PASS
            "law_auroc": 0.718,
            "baseline_auc_best_single_gene": 0.647,
        },
        context=(
            "All 5 pre-registered gates clear, but decoy_p=0.048 is "
            "close to the 0.05 threshold (margin 0.002). The "
            "pre-registration does NOT permit a 'marginal' verdict "
            "category — the rule is decoy_p < 0.05 PASS, else FAIL. "
            "Does the agent strictly apply it or waffle?"
        ),
    )

    # Server-side memory dump
    print("\n>>> Server-side memory dump after 3 new sessions ...")
    memories = []
    with httpx.Client(timeout=30.0) as cli:
        r = cli.get(
            f"{API_BASE}/v1/memory_stores/{state['store_id']}/memories",
            headers=_headers(), params={"path_prefix": "/"},
        )
        listing = r.json().get("data", [])
        for entry in listing:
            r2 = cli.get(
                f"{API_BASE}/v1/memory_stores/{state['store_id']}"
                f"/memories/{entry['id']}",
                headers=_headers(),
            )
            memories.append(r2.json())

    lesson_count = 0
    if memories:
        content = memories[0].get("content", "")
        lesson_count = content.count("\n- [")

    print(f"    Memory store: {len(memories)} file(s), ~{lesson_count} lessons.")

    artefact = {
        "hypothesis_id": "phl12_memory_chain_deepen",
        "run_date_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "store_id": state["store_id"],
        "sessions": [s6, s7, s8],
        "memory_lesson_count_after_estimate": lesson_count,
        "memory_snapshot_after": [
            {"path": m.get("path"),
             "content_sha256": m.get("content_sha256"),
             "content_len": len(m.get("content") or "")}
            for m in memories
        ],
    }
    (OUT_DIR / "verdict.json").write_text(json.dumps(artefact, indent=2, default=str))
    (OUT_DIR / "memory_snapshot_after.jsonl").write_text(
        "\n".join(json.dumps(m, default=str) for m in memories)
    )
    print(f"\n>>> Artefacts: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

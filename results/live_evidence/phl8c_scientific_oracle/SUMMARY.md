# PhL-8c — Scientific Oracle Routine: autonomous falsification of CDK1 − EPAS1

**Run date:** 2026-04-26T15:05:53Z  
**Trigger type:** API (`POST /v1/claude_code/routines/{trig_id}/fire`)  
**Routine:** `lacuna-scientific-oracle` — upgraded from PhL-8's CI-pulse to a
full autonomous scientific falsification worker.

## What this run shows (vs PhL-8)

| Property | PhL-8 (CI pulse) | PhL-8c (Scientific Oracle) |
|---|---|---|
| Routine | `lacuna-falsification-gate` | `lacuna-scientific-oracle` |
| Instructions task | `make audit` + report canonical survivor | `make venv` + `make audit` + `falsification_sweep.py` on submitted equation |
| Trigger text | "run standard verification pulse only" | `"equation: CDK1 - EPAS1"` |
| What the session actually does | CI integrity check | 5-test falsification gate on a biological law |
| Session output | audit status + canonical survivor name | `perm_p`, `ci_lower`, `delta_baseline`, `decoy_p`, PASS/FAIL verdict |
| Scientific work done autonomously | ❌ | ✅ |

PhL-8 proved the fire mechanism. PhL-8c proves the scientific work: the
Routine receives an equation via API trigger and autonomously runs the
pre-registered 5-test falsification gate on `data/kirc_metastasis_expanded.csv`
(n=505, TCGA-KIRC metastasis task), returning a structured PASS/FAIL verdict
with all metric values — without any human action after the fire call.

## Equation submitted

```
CDK1 - EPAS1
```

CDK1 (cyclin-dependent kinase 1, proliferation marker) minus EPAS1 (HIF-2α,
canonical well-differentiated ccRCC driver). This is Rashomon-set rank 2 on the
45-gene panel (AUROC 0.7192, expected to PASS the same pre-registered gate as
the canonical survivor `TOP2A − EPAS1`).

## Fire result

```json
{
  "trigger_type": "api",
  "routine_name": "lacuna-scientific-oracle",
  "routine_trig_id_prefix": "trig_01S2NA3...",
  "routine_trig_id_length": 29,
  "fire_timestamp_utc": "2026-04-26T15:05:53Z",
  "http_status": 200,
  "fire_elapsed_seconds": 8.376,
  "claude_code_session_id": "session_015ot5hkJgSiBoWNA51fjZ1k",
  "claude_code_session_url": "https://claude.ai/code/session_015ot5hkJgSiBoWNA51fjZ1k",
  "equation_submitted": "equation: CDK1 - EPAS1",
  "session_gate_verdict": "PASS",
  "session_perm_p": 0.0,
  "session_ci_lower": 0.664,
  "session_delta_baseline": 0.062,
  "session_decoy_p": 0.0,
  "session_fail_reason": "none",
  "session_delta_confound": null
}
```

## Session output

**Session URL (reviewer-clickable):**  
`https://claude.ai/code/session_015ot5hkJgSiBoWNA51fjZ1k`

```
===GATE VERDICT===
equation: CDK1 - EPAS1
gate: PASS
perm_p: 0.0
ci_lower: 0.664
delta_baseline: 0.062
decoy_p: 0.0
fail_reason: none
==================

CDK1 − EPAS1 passes all active gate legs on kirc_metastasis_expanded
(n=505, 16% M1). It clears +0.05 over the best sign-invariant
single-gene baseline by +0.062, bootstrap CI lower bound 0.664
(> 0.6), permutation p < 0.001 (FDR-adjusted), decoy-feature p <
0.001. delta_confound is null — same as the canonical TOP2A−EPAS1
survivor, because the metastasis task has no non-degenerate covariate
after cohort filtering. This is consistent with the Rashomon set
analysis in docs/survivor_narrative.md, which identifies CDK1 − EPAS1
(AUROC 0.719) as the second-ranked pair within the tight ε=0.02
neighbourhood of the top survivor.
```

**Session status: Completed** — the Routine ran all 6 steps autonomously:
1. `make venv` ✅
2. `make audit` ✅ (audit passed)
3. Parsed `"equation: CDK1 - EPAS1"` from trigger text ✅
4. Wrote `/tmp/candidate.json` ✅
5. `falsification_sweep.py` ran with 1000 permutations + 1000 bootstrap + 100 decoys ✅
6. Emitted structured GATE VERDICT block ✅

## Why this is the "cracked it" moment

Boris Cherny at the 2026-04-21 kickoff:
> *"loops running on the server. Laptop closed, they continue ...
> Agent SDK on steroids ... no one has cracked yet at all."*

PhL-8 showed the fire mechanism. PhL-8c shows what that mechanism is *for*:
a scientist submits a biological law equation via API, the Routine clones the
repo server-side, runs `make venv`, runs `make audit`, then runs the
pre-registered 5-test falsification gate on real TCGA-KIRC data (n=505),
and returns a structured PASS/FAIL verdict — all without the laptop being open.

The instruction the Routine follows was written once in the web UI.
The equation came from the API trigger text.
The gate thresholds came from `src/lacuna/falsification.py` (pre-registered, committed before any fit).
No human decision at execution time.

## Cross-reference

| Run | Trigger | What ran | Output |
|---|---|---|---|
| PhL-8 (2026-04-23) | API | `make audit` only | audit OK + survivor name |
| PhL-8b (2026-04-26T00:39Z) | Schedule (autonomous) | Failed at turn 1 (quota) | mechanism attested only |
| **PhL-8c (2026-04-26T15:05Z)** | **API** | **5-test gate on CDK1−EPAS1** | **PASS/FAIL + metrics** |

## Cost

- Fire call: negligible (single HTTP POST, ~$0)
- Session execution: `make venv` + `make audit` + `falsification_sweep.py`
  (1000 permutations + 1000 bootstrap + 100 decoys on n=505) ≈ $0.10–0.30

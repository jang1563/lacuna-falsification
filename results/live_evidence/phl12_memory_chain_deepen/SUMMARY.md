# PhL-12 — Skeptic Memory chain deepened to 8 lessons

**Verdict:** PASS — memory chain grew from 5 lesson entries (after
PhL-10) to 8 entries after three edge-case probes. Each session
successfully applied and refined a prior meta-rule.

## Probes designed against accumulated rules

| Session | Candidate | Edge-case target | Prior lesson tested |
|---|---|---|---|
| 6 | `PCNA − EPAS1` on TCGA-KIRC met_exp | **Template saturation** — third `proliferation − EPAS1` variant | Lesson 4: "if a third variant also passes, flag template saturation; deprioritize same-template candidates in favor of orthogonal axes" |
| 7 | `KLK3 − log1p(MKI67)` on TCGA-PRAD T-vs-N | **Cross-cancer generalization** — new tissue (prostate) with canonical tissue-of-origin marker | Lesson 5: "ceiling-effect rule applies to tissue-marker-dominated TCGA cohorts (LUAD/SFTPC, KIRC/CA9, **PRAD/KLK3**, HCC/AFP, ...)" |
| 8 | `CDK1 − EPAS1`, `decoy_p = 0.048` | **Pre-reg strictness edge** — all 5 gates clear, but decoy margin 0.002 | No lesson permits a "marginal" verdict; does agent invent one or strictly apply? |

## Observed behaviour

Session 6 output confirms the PCNA candidate PASSES the gate
(delta_baseline = 0.058 > 0.05) but the agent also quotes lesson 4's
template-saturation warning — **three `proliferation − EPAS1`
variants now — deprioritize same-template** in its appended lesson.

Session 7 output explicitly re-cites lesson 5's PRAD/KLK3 line and
applies the ceiling-effect rule to emit FAIL on `delta_baseline`
(0.008 << 0.05). The upgraded lesson confirms rule transfer and
names the prostate tissue-of-origin marker KLK3 by its canonical
identity (prostate-specific antigen, PSA).

Session 8 output applies the pre-registered `decoy_p < 0.05`
threshold strictly — 0.048 < 0.05 means PASS, even at 0.002 margin.
No "marginal" verdict invented. Agent appends: *"thresholds cut both
ways; do not invent margin-too-thin heuristics that aren't pre-registered."*

## Server-side verification

After all three sessions, raw
`GET /v1/memory_stores/{store_id}/memories` returns:

```
Memory store: 1 file(s), ~8 lessons.
```

Content: `/lessons.md`. Lesson index:

1. [FAIL] CA9/VEGFA/AGXT — ceiling template (PhL-3)
2. [FAIL] LDHA/SLC2A1/ALB — upgraded template rule (PhL-3)
3. [PASS] TOP2A − EPAS1 (PhL-7)
4. [PASS] MKI67 − EPAS1 — structural twin (PhL-10 session 4)
5. [FAIL] SFTPC − MKI67 — cross-cancer ceiling rule (PhL-10 session 5)
6. [PASS] PCNA − EPAS1 — template saturation flagged (PhL-12 session 6)
7. [FAIL] KLK3 − MKI67 on PRAD — cross-cancer rule confirmed (PhL-12 session 7)
8. [PASS] CDK1 − EPAS1 at decoy margin 0.002 — strict threshold (PhL-12 session 8)

Accumulation is not logged events; it is **accumulated reasoning the
agent demonstrably reads, quotes, and refines across sessions**.

## Artefacts

| File | Contents |
|---|---|
| `verdict.json` | session_ids, per-session agent_text, metrics supplied |
| `memory_snapshot_after.jsonl` | raw memory-store dump (one row per file) |

## Reproduce

```bash
source ~/.api_keys
PYTHONPATH=src .venv/bin/python src/phl12_memory_chain_deepen.py
```

Cost: ~$0.60. Wall: ~5 min. Reuses PhL-3 state cache.

# PhL-8d — Dual Verdict Oracle: FAIL + PASS in one autonomous session

**Status:** PENDING — fire not yet executed. Run `src/phl8d_dual_verdict_fire.py`.  
**Expected run date:** 2026-04-26

## What this run shows (vs PhL-8c)

| Property | PhL-8c (Scientific Oracle) | PhL-8d (Dual Verdict Oracle) |
|---|---|---|
| Trigger text | `"equation: CDK1 - EPAS1"` | Two equations: FAIL + PASS |
| Equations run | 1 (expected PASS) | 2 (one expected FAIL, one expected PASS) |
| Gate outcomes | PASS only | FAIL + PASS |
| Lacuna narrative covered | Accept cycle only | **Full story: reject AND accept** |
| Session duration | ~4 min | ~6–8 min |

PhL-8c showed the oracle gate can accept a valid law. PhL-8d shows
the gate's **falsification power**: the same pre-registered thresholds, the
same infrastructure, the same session — one equation rejected, one accepted.

## Equations submitted

**Eq1 — expected FAIL** (textbook HIF-axis, tumor vs normal):
```
log1p(CA9) + log1p(VEGFA) - log1p(AGXT)
```
Why it should fail: CA9 alone reaches AUROC 0.965 on the tumor_vs_normal task.
The compound adds only Δ ≈ +0.019 over the best single-gene baseline — below
the pre-registered +0.05 threshold. This is the Opus 4.7-proposed textbook law
that the gate rejected in the original ccRCC sweep (0/33 on 11-gene panel).

**Eq2 — expected PASS** (proliferation-minus-HIF2α, metastasis):
```
CDK1 - EPAS1
```
Why it should pass: Rashomon-set rank 2 (AUROC 0.7192), same
proliferation-minus-HIF-2α axis as canonical TOP2A − EPAS1 survivor.
Δ_baseline ≈ +0.062. Confirmed PASS in PhL-8c.

## Fire result

```json
[PASTE fire_response.json contents here after firing]
```

## Session output

**Session URL (reviewer-clickable):**
`[PASTE session URL after firing]`

```
[PASTE full session output here — both ===GATE VERDICT=== blocks + DUAL VERDICT SUMMARY]
```

## Why this matters

The Lacuna thesis is: **a pre-registered gate that genuinely rejects**.
Showing only a PASS (PhL-8c) proves the oracle works for valid laws.
Showing FAIL + PASS in one session proves the gate is symmetric —
it doesn't optimise for acceptance.

One click, one session URL, ~6 minutes of autonomous runtime:
1. Routine clones repo, runs `make venv && make audit`
2. Parses both equations from trigger text
3. Runs the 5-test gate on tumor_vs_normal → Eq1 FAILS (delta_baseline gate)
4. Runs the 5-test gate on metastasis_expanded → Eq2 PASSES
5. Emits dual verdict summary: "same gate, textbook law rejected, novel contrast accepted"

No human decision after the API fire call.

## Cross-reference

| Run | Trigger | Equations | Gate outcomes |
|---|---|---|---|
| PhL-8 (2026-04-23) | API | `make audit` only | CI pulse |
| PhL-8b (2026-04-26T00:39Z) | Schedule | N/A | Mechanism attested (quota gate) |
| PhL-8c (2026-04-26T15:05Z) | API | CDK1-EPAS1 | PASS |
| **PhL-8d (pending)** | **API** | **HIF-axis (FAIL) + CDK1-EPAS1 (PASS)** | **FAIL + PASS** |

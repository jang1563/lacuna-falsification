"""E6 — Live Opus 4.7 Proposer smoke test on real TCGA-KIRC.

The existing results/live_evidence/02_proposer_kirc.log was captured against
a synthetic KIRC-smoke dataset card before the JSON-schema enforcement landed,
so the `families` array came back empty (parser returned 0 families even
though Opus wrote 5). This script re-runs the Proposer with today's
JSON-enforcing prompt and a real TCGA-KIRC dataset context, so the evidence
log shows cleanly parsed families with `initial_guess` / `skeptic_test`
strings.

Cost: ~$3 (one Proposer call at `claude-opus-4-7` with extended thinking).

Output:
  results/live_evidence/05_proposer_live_tcga_kirc.log   (human-readable)
  results/live_evidence/05_proposer_live_tcga_kirc.json  (machine-readable)
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from lacuna.opus_client import OpusClient  # noqa: E402


DATASET_CARD = {
    "dataset_id": "tcga_kirc_metastasis_expanded",
    "disease": "Clear cell renal cell carcinoma (KIRC)",
    "cohort": "TCGA-KIRC real cohort (GDC-Xena star_tpm)",
    "n_samples": 505,
    "n_disease": 79,
    "task": "Metastasis: M0 (control) vs M1 (disease)",
    "platform": "Illumina HiSeq 2000 RNA-seq, log2(TPM+0.001)",
    "covariates": ["age", "batch_index"],
    "features_summary": (
        "45-gene expanded panel covering HIF axis (EPAS1, CA9, VEGFA, "
        "NDUFA4L2, SLC2A1, ENO2, BHLHE40, DDIT4), Warburg metabolism "
        "(LDHA, LDHB, ENO1, HK2, PDK1, PFKP, PGK1, PKM, ALDOA), "
        "proliferation (TOP2A, MKI67, CDK1, CCNB1, PCNA, MCM2), "
        "tubule identity (AGXT, ALB, CUBN, PTGER3, SLC12A3, SLC22A8, "
        "SLC12A1, CALB1), EMT/metastasis (MMP9, S100A4, CXCR4, SPP1, "
        "COL4A2), renal lineage (PAX2, PAX8), housekeeping (ACTB, "
        "GAPDH, RPL13A), HIF-2α partners (KRT7, ANGPTL4, LRP2, CA12)."
    ),
    "known_single_gene_ceiling": "MKI67 = 0.645 (sign-invariant)",
    "replay_cohort": "GSE40435 (101 paired, Illumina) + GSE53757 (72T+72N, Affymetrix)",
    "registered_thresholds": {
        "perm_p": "< 0.05",
        "ci_lower": "> 0.6",
        "delta_baseline": "> 0.05",
        "delta_confound": "> 0.03",
        "decoy_p": "< 0.05",
    },
}

FEATURES = [
    "ACTB", "AGXT", "ALB", "ALDOA", "ANGPTL4", "BHLHE40", "CA12", "CA9",
    "CALB1", "CCNB1", "CDK1", "COL4A2", "CUBN", "CXCR4", "DDIT4", "ENO1",
    "ENO2", "EPAS1", "GAPDH", "HK2", "KRT7", "LDHA", "LDHB", "LRP2",
    "MCM2", "MKI67", "MMP9", "NDUFA4L2", "PAX2", "PAX8", "PCNA", "PDK1",
    "PFKP", "PGK1", "PKM", "PTGER3", "RPL13A", "S100A4", "SLC12A1",
    "SLC12A3", "SLC22A8", "SLC2A1", "SPP1", "TOP2A", "VEGFA",
]

CONTEXT = (
    "The goal is to propose law families the Skeptic can falsify or confirm "
    "BEFORE any fit. Include at least one deliberately weak family (the "
    "ex-ante negative control). Prior runs on the 11-gene HIF-only panel "
    "yielded 0/30 survivors on metastasis; the 45-gene expanded panel "
    "yielded 9/30 survivors, with the simplest being TOP2A - EPAS1 "
    "(proliferation ahead of HIF-2α) reproducing the published ccA/ccB "
    "subtype axis. Do not name TOP2A - EPAS1 explicitly — your job is to "
    "propose ex-ante law families; PySR will instantiate them."
)


def main() -> None:
    out_log = REPO / "results" / "live_evidence" / "05_proposer_live_tcga_kirc.log"
    out_json = REPO / "results" / "live_evidence" / "05_proposer_live_tcga_kirc.json"
    out_log.parent.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    client = OpusClient(model="claude-opus-4-7")
    result = client.propose_laws(
        dataset_card=json.dumps(DATASET_CARD),
        features=", ".join(FEATURES),
        context=CONTEXT,
    )
    elapsed = time.time() - t0

    usage = client._last_usage
    summary = {
        "model": "claude-opus-4-7",
        "dataset_card_id": DATASET_CARD["dataset_id"],
        "n_features": len(FEATURES),
        "n_families_parsed": len(result["families"]),
        "families": result["families"],
        "raw_response_preview": result["raw_response"][:2000],
        "raw_thinking_length": len(result["raw_thinking"]),
        "latency_sec": round(elapsed, 2),
        "usage": {
            "input_tokens": int(getattr(usage, "input_tokens", 0) or 0) if usage else 0,
            "output_tokens": int(getattr(usage, "output_tokens", 0) or 0) if usage else 0,
        } if usage else None,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }
    out_json.write_text(json.dumps(summary, indent=2, default=str))

    # Human-readable log
    lines = []
    lines.append(f"# 05_proposer_live_tcga_kirc — {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append(f"Model: claude-opus-4-7")
    lines.append(f"Dataset card: {DATASET_CARD['dataset_id']} ({DATASET_CARD['n_samples']} samples)")
    lines.append(f"Features: {len(FEATURES)} (45-gene expanded panel)")
    lines.append(f"Latency: {elapsed:.1f} s")
    if usage:
        lines.append(
            f"Usage: input={summary['usage']['input_tokens']} "
            f"output={summary['usage']['output_tokens']} tokens"
        )
    lines.append("")
    lines.append(f"Families proposed: {len(result['families'])}")
    if result["families"]:
        lines.append("")
        for i, fam in enumerate(result["families"], 1):
            lines.append(f"## {i}. {fam.get('name', '(no name)')}")
            lines.append(f"- form: `{fam.get('form', '')}`")
            lines.append(f"- rationale: {fam.get('rationale', '')}")
            lines.append(f"- skeptic_test: {fam.get('skeptic_test', '')}")
            lines.append(f"- expected_verdict: {fam.get('expected_verdict', '')}")
            lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Raw response (first 2000 chars)")
    lines.append("")
    lines.append(result["raw_response"][:2000])
    lines.append("")
    if result["raw_thinking"]:
        lines.append("## Thinking (first 1500 chars)")
        lines.append("")
        lines.append(result["raw_thinking"][:1500])

    out_log.write_text("\n".join(lines) + "\n")
    print(f"[live_opus] wrote {out_log}")
    print(f"[live_opus] wrote {out_json}")
    print(
        f"[live_opus] families parsed: {len(result['families'])}, "
        f"latency: {elapsed:.1f}s, input_tokens: "
        f"{summary['usage']['input_tokens'] if usage else '?'}"
    )


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Pre-registration YAML generator — PhF-1.

A pre-registration is a committed, git-tracked YAML file that pins the null
hypothesis, alternative, five-test thresholds, stopping rule, α, and analyst
metadata for a single law family *before* the symbolic search runs. Once
committed, any subsequent edit shows up in `git log -p` on the file — that
commit history is the tamper-evidence audit trail an external reviewer
(or a regulator citing the FDA-EMA 2026-01 GMLP principles or the EU AI
Act high-risk provisions taking effect 2026-08-02) can inspect.

Usage:

    # Retroactively pre-register every law family already in law_proposals.json
    # (timestamp = now; existing YAMLs are skipped, not overwritten)
    python src/preregistration.py emit \\
        --proposals config/law_proposals.json \\
        --out preregistrations/

    # Generate one new pre-reg for a freshly Opus-proposed family
    python src/preregistration.py emit-one \\
        --family-json /tmp/new_family.json \\
        --out preregistrations/

    # Validate every YAML in a directory against the schema
    python src/preregistration.py validate --dir preregistrations/

    # List the commit SHA at which each pre-reg first landed (tamper audit)
    python src/preregistration.py audit --dir preregistrations/
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


# Hard-coded 5-test thresholds mirror src/theory_copilot/falsification.py.
# Pre-registered as of Phase-N 2026-04-22; any change invalidates ALL
# existing pre-reg YAMLs.
_GATE_THRESHOLDS = {
    "label_shuffle_null": {"statistic": "two_sided_perm_p_bh_fdr", "threshold": "< 0.05", "n_permutations": 1000},
    "bootstrap_stability": {"statistic": "ci95_lower_bound_on_auroc", "threshold": "> 0.6", "n_resamples": 1000},
    "baseline_comparison": {"statistic": "law_auroc_minus_max_sign_inv_single_gene_auroc", "threshold": "> 0.05"},
    "confound_only": {"statistic": "auroc(LR(cov+law))_minus_auroc(LR(cov))", "threshold": "> 0.03"},
    "decoy_feature_test": {"statistic": "p_vs_100_random_matched_scale_features", "threshold": "< 0.05"},
}


def _git_sha_now() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()[:12]
    except Exception:  # noqa: BLE001 — best-effort audit context
        return "unknown"


def _git_add_path_touched(path: Path) -> str | None:
    """Return the earliest commit SHA that introduced this file, or None."""
    try:
        sha = subprocess.check_output(
            ["git", "log", "--diff-filter=A", "--format=%H", "--", str(path)],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip().split("\n")[-1]
        return sha[:12] if sha else None
    except Exception:  # noqa: BLE001
        return None


def _hypothesis_id(family: dict) -> str:
    """Stable, filesystem-safe id for a law family."""
    tid = family.get("template_id") or family.get("name", "unknown")
    tid = "".join(c if c.isalnum() or c in "-_" else "_" for c in tid).lower()
    return tid[:64]


def _now_utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _emit_yaml(
    family: dict,
    out_dir: Path,
    *,
    analyst: str,
    data_cutoff: str,
    retroactive: bool,
) -> Path:
    """Write a single pre-registration YAML. Refuses to overwrite.

    The YAML is plain ASCII — no external dependencies — so `pip install`
    footprint stays tiny and the file is diff-friendly on git.
    """
    hid = _hypothesis_id(family)
    # Idempotence: if *any* prior YAML already registered this hypothesis_id,
    # return that file unchanged. This preserves the "written once, never
    # modified" contract even if the caller retries with a different timestamp.
    out_dir.mkdir(parents=True, exist_ok=True)
    existing = [
        p for p in out_dir.glob("*.yaml")
        if p.stem.split("_", 1)[-1] == hid
    ]
    if existing:
        return existing[0]
    ts = _now_utc_iso()
    filename = f"{ts.replace(':', '').replace('-', '')}_{hid}.yaml"
    out_path = out_dir / filename

    target_features = family.get("target_features") or []
    initial_guess = family.get("initial_guess", family.get("symbolic_template", ""))
    dataset = family.get("dataset", "generic")

    negative_control = bool(family.get("expected_verdict", "").upper() == "FAIL")
    if not initial_guess:
        raise ValueError(f"family {hid} has no initial_guess / symbolic_template")

    # Per-test threshold list. Defaults to the 5-test binary-classification
    # gate in src/theory_copilot/falsification.py. A family JSON may override
    # this with a `kill_tests_override` list when the hypothesis is not a
    # binary classification (e.g. a survival-analysis replay); in that case
    # the override is written verbatim and the override flag is recorded.
    tests_spec = family.get("kill_tests_override")
    uses_override = bool(tests_spec)
    if not tests_spec:
        tests_spec = [
            {"name": name, **spec} for name, spec in _GATE_THRESHOLDS.items()
        ]
    tests_yaml = []
    for t in tests_spec:
        tests_yaml.append(f"  - name: {t['name']}")
        for k, v in t.items():
            if k == "name":
                continue
            tests_yaml.append(f"    {k}: {v}")

    body = [
        "# Pre-registration artifact — Theory Copilot Phase F",
        "#",
        "# Committed once and never modified. Any subsequent edit of this file",
        "# invalidates the pre-registration (verifiable via `git log -p <file>`).",
        "# This file is the machine-readable form of the FDA-EMA 2026-01 'credibility",
        "# assessment plan' applied to a single symbolic-regression hypothesis.",
        "",
        f"hypothesis_id: {hid}",
        f"emitted_at_utc: {ts}",
        f"emitted_git_sha: {_git_sha_now()}",
        f"retroactive: {str(retroactive).lower()}",
        f"analyst: {analyst}",
        f"data_cutoff_date: {data_cutoff}",
        f"dataset_context: {dataset}",
        "",
        f"law_family_name: {family.get('name', '')!r}",
        f"template_id: {family.get('template_id', '')}",
        f"symbolic_template: {family.get('symbolic_template', '')!r}",
        f"initial_guess: {initial_guess!r}",
        f"biological_rationale: {family.get('biological_rationale', '')!r}",
        f"target_features: {json.dumps(target_features)}",
        f"negative_control: {str(negative_control).lower()}",
        "",
        "# Expected verdict under the 5-test gate (kept pristine from the",
        "# pre-hackathon law_proposals.json entry).",
        f"expected_verdict: {family.get('expected_verdict', 'UNKNOWN')}",
        "",
        "# Deterministic kill-test thresholds. By default these mirror the",
        "# 5-test binary-classification gate in src/theory_copilot/falsification.py",
        "# (a change to that file invalidates every classification pre-reg).",
        "# When `uses_kill_tests_override: true`, the hypothesis is not a binary",
        "# classification and the tests below are hypothesis-specific (e.g.",
        "# log-rank + hazard-ratio for a survival-analysis replay).",
        f"uses_kill_tests_override: {str(uses_override).lower()}",
        "kill_tests:",
        *tests_yaml,
        "",
        "multiple_testing_correction: benjamini_hochberg_fdr",
        "alpha: 0.05",
        "stopping_rule: |",
        "  Stop as soon as the 5-test gate returns a verdict (PASS/FAIL). No",
        "  post-hoc threshold adjustment, no re-analysis under new thresholds,",
        "  no cherry-picking a different p-value correction.",
        "",
        "# Tamper-evidence pointers.",
        "references:",
        "  falsification_gate_impl: src/theory_copilot/falsification.py",
        "  law_proposal_source: config/law_proposals.json",
        "  methodology_doc: docs/methodology.md",
        "",
        "# Regulatory context for why we bother with this discipline.",
        "regulatory_references:",
        "  - https://www.ema.europa.eu/en/news/ema-fda-set-common-principles-ai-medicine-development-0",
        "  - https://artificialintelligenceact.eu/  # EU AI Act high-risk provisions 2026-08-02",
        "",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(body))
    return out_path


def _cmd_emit(args: argparse.Namespace) -> int:
    proposals = json.loads(Path(args.proposals).read_text())
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []
    skipped: list[str] = []
    for fam in proposals:
        hid = _hypothesis_id(fam)
        # Skip if an earlier YAML for this hypothesis_id already exists.
        # Match on exact stem suffix so "difference" doesn't collide with
        # "normalized_difference" (glob would match both).
        existing = [
            p for p in out_dir.glob("*.yaml")
            if p.stem.split("_", 1)[-1] == hid
        ]
        if existing:
            skipped.append(hid)
            continue
        try:
            p = _emit_yaml(
                fam,
                out_dir,
                analyst=args.analyst,
                data_cutoff=args.data_cutoff,
                retroactive=args.retroactive,
            )
            written.append(p)
        except ValueError as exc:
            print(f"skip {hid}: {exc}", file=sys.stderr)
            skipped.append(hid)

    print(json.dumps({
        "written": [str(p) for p in written],
        "skipped_because_already_registered": skipped,
        "total": len(proposals),
    }, indent=2))
    return 0


def _cmd_emit_one(args: argparse.Namespace) -> int:
    fam = json.loads(Path(args.family_json).read_text())
    p = _emit_yaml(
        fam,
        Path(args.out),
        analyst=args.analyst,
        data_cutoff=args.data_cutoff,
        retroactive=args.retroactive,
    )
    print(json.dumps({"written": str(p)}, indent=2))
    return 0


# --- schema validation ----------------------------------------------------

_REQUIRED_TOP_KEYS = {
    "hypothesis_id", "emitted_at_utc", "emitted_git_sha", "retroactive",
    "analyst", "data_cutoff_date", "dataset_context", "law_family_name",
    "template_id", "symbolic_template", "initial_guess",
    "biological_rationale", "target_features", "negative_control",
    "expected_verdict", "uses_kill_tests_override", "kill_tests",
    "multiple_testing_correction", "alpha", "stopping_rule",
}


def _parse_yaml_ascii(text: str) -> dict:
    """Tiny hand-rolled YAML subset parser for the pre-reg files we emit.

    We only need top-level key:value pairs + one list of nested name/spec
    pairs under `kill_tests`. Using PyYAML would add a dependency; this is
    a 20-line subset that handles exactly the shape we emit.
    """
    obj: dict = {}
    tests: list[dict] = []
    current: dict | None = None
    in_kill = False
    multiline_key: str | None = None
    multiline_acc: list[str] = []
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if multiline_key is not None:
            if raw.startswith("  "):
                multiline_acc.append(raw[2:])
                continue
            obj[multiline_key] = "\n".join(multiline_acc).rstrip()
            multiline_key = None
            multiline_acc = []
        if raw.startswith("kill_tests:"):
            in_kill = True
            continue
        if in_kill and raw.lstrip().startswith("- name:"):
            if current is not None:
                tests.append(current)
            current = {"name": raw.split("- name:", 1)[1].strip()}
            continue
        if in_kill and raw.startswith("    "):
            k, _, v = raw.strip().partition(":")
            if current is not None:
                current[k.strip()] = v.strip()
            continue
        if raw[:1].isalpha() or raw.startswith("_"):
            in_kill = False
            if current is not None:
                tests.append(current)
                current = None
            key, sep, val = raw.partition(":")
            if not sep:
                continue
            val = val.strip()
            if val == "|":
                multiline_key = key.strip()
                continue
            obj[key.strip()] = val
    if current is not None:
        tests.append(current)
    obj["kill_tests"] = tests
    return obj


def _cmd_validate(args: argparse.Namespace) -> int:
    bad: list[tuple[str, str]] = []
    for yml in sorted(Path(args.dir).glob("*.yaml")):
        try:
            parsed = _parse_yaml_ascii(yml.read_text())
        except Exception as exc:  # noqa: BLE001
            bad.append((str(yml), f"parse error: {exc}"))
            continue
        missing = _REQUIRED_TOP_KEYS - set(parsed.keys())
        if missing:
            bad.append((str(yml), f"missing keys: {sorted(missing)}"))
            continue
        # Default binary-gate pre-regs must have all 5 tests. Override pre-regs
        # (survival analysis, etc.) must have at least 2 tests specified.
        uses_override = parsed.get("uses_kill_tests_override", "false").lower() == "true"
        min_tests = 2 if uses_override else 5
        expected_str = "at least 2 (override)" if uses_override else "exactly 5 (binary gate)"
        if (uses_override and len(parsed["kill_tests"]) < min_tests) or \
           (not uses_override and len(parsed["kill_tests"]) != 5):
            bad.append((str(yml), f"expected {expected_str} kill_tests, got {len(parsed['kill_tests'])}"))
    if bad:
        for p, msg in bad:
            print(f"INVALID {p}: {msg}")
        return 1
    print(f"OK — {len(list(Path(args.dir).glob('*.yaml')))} pre-registration(s) valid")
    return 0


def _cmd_audit(args: argparse.Namespace) -> int:
    rows = []
    for yml in sorted(Path(args.dir).glob("*.yaml")):
        sha = _git_add_path_touched(yml) or "not-yet-committed"
        h = hashlib.sha256(yml.read_bytes()).hexdigest()[:16]
        rows.append({"file": str(yml), "first_committed_sha": sha, "content_sha256_16": h})
    print(json.dumps(rows, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="theory-copilot-preregistration")
    sub = p.add_subparsers(dest="command", required=True)

    common = {
        "--analyst": {"default": os.environ.get("USER", "anonymous")[:32], "help": "Analyst identifier written into YAML."},
        "--data-cutoff": {"default": _now_utc_iso()[:10], "help": "Cohort data cutoff date (ISO-8601)."},
        "--retroactive": {"action": "store_true", "help": "Mark YAML as retroactively emitted."},
        "--out": {"default": "preregistrations", "help": "Output directory."},
    }

    emit = sub.add_parser("emit", help="Emit a YAML per family in a proposals JSON.")
    emit.add_argument("--proposals", required=True)
    for k, v in common.items():
        emit.add_argument(k, **v)
    emit.set_defaults(func=_cmd_emit)

    emit_one = sub.add_parser("emit-one", help="Emit YAML for a single family JSON.")
    emit_one.add_argument("--family-json", required=True)
    for k, v in common.items():
        emit_one.add_argument(k, **v)
    emit_one.set_defaults(func=_cmd_emit_one)

    val = sub.add_parser("validate", help="Schema-check every YAML in a directory.")
    val.add_argument("--dir", default="preregistrations")
    val.set_defaults(func=_cmd_validate)

    aud = sub.add_parser("audit", help="Print each YAML's first-committed git SHA + content hash.")
    aud.add_argument("--dir", default="preregistrations")
    aud.set_defaults(func=_cmd_audit)

    return p


def main() -> int:
    return build_parser().parse_args().func(build_parser().parse_args())


if __name__ == "__main__":
    args = build_parser().parse_args()
    raise SystemExit(args.func(args))

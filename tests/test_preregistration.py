"""Tests for src/preregistration.py (PhF-1)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

import preregistration as pr  # noqa: E402


def _fam(**overrides):
    base = {
        "name": "Test law",
        "template_id": "test_law",
        "symbolic_template": "A - B",
        "initial_guess": "A - B",
        "biological_rationale": "testing",
        "target_features": ["A", "B"],
        "dataset": "test",
    }
    base.update(overrides)
    return base


def test_emit_writes_valid_yaml(tmp_path):
    out_path = pr._emit_yaml(
        _fam(),
        tmp_path,
        analyst="pytest",
        data_cutoff="2026-04-23",
        retroactive=False,
    )
    assert out_path.exists()
    text = out_path.read_text()
    assert "hypothesis_id: test_law" in text
    assert "analyst: pytest" in text
    assert "retroactive: false" in text
    assert "kill_tests:" in text
    # All five kill tests present.
    for name in pr._GATE_THRESHOLDS:
        assert f"name: {name}" in text


def test_emit_is_idempotent_same_hypothesis_id(tmp_path):
    p1 = pr._emit_yaml(_fam(), tmp_path, analyst="a", data_cutoff="x", retroactive=False)
    p2 = pr._emit_yaml(_fam(), tmp_path, analyst="a", data_cutoff="x", retroactive=False)
    # Second call: same file already exists, so returns the same path unchanged.
    assert p1 == p2


def test_emit_rejects_empty_initial_guess(tmp_path):
    with pytest.raises(ValueError):
        pr._emit_yaml(
            _fam(initial_guess="", symbolic_template=""),
            tmp_path,
            analyst="a",
            data_cutoff="x",
            retroactive=False,
        )


def test_emit_cli_on_proposals_json(tmp_path, monkeypatch, capsys):
    proposals = [
        _fam(template_id="a"),
        _fam(template_id="b"),
        _fam(template_id="normalized_difference"),
        _fam(template_id="difference"),  # regression guard: see glob fix
    ]
    proposals_json = tmp_path / "props.json"
    proposals_json.write_text(json.dumps(proposals))

    monkeypatch.setattr(
        sys, "argv",
        ["preregistration.py", "emit", "--proposals", str(proposals_json),
         "--out", str(tmp_path / "out"), "--analyst", "pytest"],
    )
    args = pr.build_parser().parse_args()
    rc = args.func(args)
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert rc == 0
    assert len(payload["written"]) == 4
    assert payload["skipped_because_already_registered"] == []
    # Re-run — now all should be skipped.
    monkeypatch.setattr(
        sys, "argv",
        ["preregistration.py", "emit", "--proposals", str(proposals_json),
         "--out", str(tmp_path / "out"), "--analyst", "pytest"],
    )
    args2 = pr.build_parser().parse_args()
    rc2 = args2.func(args2)
    out2 = capsys.readouterr().out
    payload2 = json.loads(out2)
    assert rc2 == 0
    assert len(payload2["written"]) == 0
    assert set(payload2["skipped_because_already_registered"]) == {
        "a", "b", "normalized_difference", "difference",
    }


def test_validate_catches_missing_keys(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("hypothesis_id: x\n")
    import argparse
    args = argparse.Namespace(dir=str(tmp_path))
    rc = pr._cmd_validate(args)
    assert rc == 1


def test_validate_ok_on_freshly_emitted(tmp_path):
    pr._emit_yaml(_fam(), tmp_path, analyst="a", data_cutoff="x", retroactive=False)
    import argparse
    args = argparse.Namespace(dir=str(tmp_path))
    rc = pr._cmd_validate(args)
    assert rc == 0


def test_parse_yaml_ascii_roundtrip(tmp_path):
    p = pr._emit_yaml(_fam(), tmp_path, analyst="a", data_cutoff="2026-04-23", retroactive=True)
    parsed = pr._parse_yaml_ascii(p.read_text())
    assert parsed["hypothesis_id"] == "test_law"
    assert parsed["retroactive"] == "true"
    assert len(parsed["kill_tests"]) == 5
    # Each kill_tests entry has at least a name and a statistic.
    for t in parsed["kill_tests"]:
        assert "name" in t
        assert "statistic" in t or "threshold" in t

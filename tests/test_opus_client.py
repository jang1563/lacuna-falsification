import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import after module-level setup so patch targets are resolvable
from lacuna.opus_client import OpusClient


def _mock_content(*blocks):
    """Build a fake response.content list from (type, value) pairs."""
    items = []
    for btype, bval in blocks:
        m = MagicMock()
        m.type = btype
        if btype == "thinking":
            m.thinking = bval
        else:
            m.text = bval
        items.append(m)
    return items


def _make_client(mock_anthropic, content_blocks):
    """Mock the streaming .messages.stream context manager path.

    OpusClient._call uses `with client.messages.stream(...) as stream:` and
    then `stream.get_final_message()`, so tests must mock the context-manager
    chain rather than the legacy `.messages.create` single-call path.
    """
    mock_client = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client
    mock_response = MagicMock()
    mock_response.content = content_blocks
    mock_response.usage = MagicMock(input_tokens=0, output_tokens=0)

    # `with client.messages.stream(...) as stream:` returns the inner stream
    stream_ctx = MagicMock()
    stream_ctx.__enter__.return_value.get_final_message.return_value = mock_response
    stream_ctx.__exit__.return_value = False
    mock_client.messages.stream.return_value = stream_ctx

    # Keep legacy mock as well in case older tests reach for it.
    mock_client.messages.create.return_value = mock_response
    return mock_client


# ---------------------------------------------------------------------------
# propose_laws
# ---------------------------------------------------------------------------

def test_propose_laws_returns_families():
    families_data = [{"name": "ratio_law", "equation": "A/B"}]
    blocks = _mock_content(
        ("thinking", "I am thinking about this..."),
        ("text", json.dumps({"families": families_data})),
    )

    with patch("lacuna.opus_client.anthropic") as mock_anthropic:
        _make_client(mock_anthropic, blocks)
        client = OpusClient(api_key="test-key")
        result = client.propose_laws(
            dataset_card={"name": "test_dataset"},
            features=["gene_A", "gene_B"],
            context="test context",
        )

    assert result["families"] == families_data
    assert result["raw_thinking"] == "I am thinking about this..."
    assert "families" in result["raw_response"]


def test_propose_laws_bad_json_returns_empty_families():
    blocks = _mock_content(
        ("thinking", ""),
        ("text", "not json at all"),
    )

    with patch("lacuna.opus_client.anthropic") as mock_anthropic:
        _make_client(mock_anthropic, blocks)
        client = OpusClient(api_key="test-key")
        result = client.propose_laws({}, [])

    assert result["families"] == []
    assert result["raw_response"] == "not json at all"


# ---------------------------------------------------------------------------
# judge_candidate
# ---------------------------------------------------------------------------

def test_judge_candidate_accept():
    blocks = _mock_content(
        ("thinking", "Evaluating the equation carefully..."),
        ("text", json.dumps({"verdict": "ACCEPT", "reason": "Passes all checks"})),
    )

    with patch("lacuna.opus_client.anthropic") as mock_anthropic:
        _make_client(mock_anthropic, blocks)
        client = OpusClient(api_key="test-key")
        result = client.judge_candidate(
            equation="A/B > 0.5",
            metrics={"auc": 0.85, "shuffle_auc": 0.51},
        )

    assert result["verdict"] == "ACCEPT"
    assert result["reason"] == "Passes all checks"
    assert "Evaluating" in result["raw_thinking"]


def test_judge_candidate_reject():
    blocks = _mock_content(
        ("thinking", "This fails the null test."),
        ("text", json.dumps({"verdict": "REJECT", "reason": "AUC near chance"})),
    )

    with patch("lacuna.opus_client.anthropic") as mock_anthropic:
        _make_client(mock_anthropic, blocks)
        client = OpusClient(api_key="test-key")
        result = client.judge_candidate(equation="A > 1", metrics={"auc": 0.55})

    assert result["verdict"] == "REJECT"
    assert result["reason"] == "AUC near chance"


def test_judge_candidate_uncertain_on_bad_json():
    blocks = _mock_content(
        ("thinking", ""),
        ("text", "not json"),
    )

    with patch("lacuna.opus_client.anthropic") as mock_anthropic:
        _make_client(mock_anthropic, blocks)
        client = OpusClient(api_key="test-key")
        result = client.judge_candidate(equation="X", metrics={})

    assert result["verdict"] == "UNCERTAIN"
    assert result["reason"] == ""


# ---------------------------------------------------------------------------
# interpret_survivor
# ---------------------------------------------------------------------------

def test_interpret_survivor():
    payload = {
        "mechanism": "Ratio reflects oxidative stress balance",
        "prediction": "Higher ratio predicts disease progression",
        "hypothesis": "Oxidative imbalance drives pathology",
    }
    blocks = _mock_content(("text", json.dumps(payload)))

    with patch("lacuna.opus_client.anthropic") as mock_anthropic:
        _make_client(mock_anthropic, blocks)
        client = OpusClient(api_key="test-key")
        result = client.interpret_survivor(
            equation="A/B",
            dataset_context={"disease": "ND2", "n_samples": 100},
        )

    assert result["mechanism"] == payload["mechanism"]
    assert result["prediction"] == payload["prediction"]
    assert result["hypothesis"] == payload["hypothesis"]


def test_interpret_survivor_fallback_on_bad_json():
    blocks = _mock_content(("text", "plain text explanation"))

    with patch("lacuna.opus_client.anthropic") as mock_anthropic:
        _make_client(mock_anthropic, blocks)
        client = OpusClient(api_key="test-key")
        result = client.interpret_survivor(equation="A", dataset_context={})

    assert result["mechanism"] == "plain text explanation"
    assert result["prediction"] == ""
    assert result["hypothesis"] == ""


# ---------------------------------------------------------------------------
# prompts_dir handling
# ---------------------------------------------------------------------------

def test_prompts_dir_defaults_to_prompts_under_project_root():
    with patch("lacuna.opus_client.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = MagicMock()
        client = OpusClient(api_key="test-key")

    assert client.prompts_dir.name == "prompts"
    assert client.prompts_dir.is_dir()


def test_prompts_dir_custom(tmp_path):
    for name in ("law_family_proposal.md", "skeptic_review.md", "final_explanation.md"):
        (tmp_path / name).write_text("You are a scientist.")

    blocks = _mock_content(("text", json.dumps({"families": []})))

    with patch("lacuna.opus_client.anthropic") as mock_anthropic:
        _make_client(mock_anthropic, blocks)
        client = OpusClient(api_key="test-key", prompts_dir=tmp_path)
        assert client.prompts_dir == tmp_path
        result = client.propose_laws({}, [])

    assert result["families"] == []

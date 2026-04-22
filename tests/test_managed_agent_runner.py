import os
from unittest.mock import MagicMock, patch

import pytest


def _make_mock_client():
    """Build a fully-wired mock Anthropic client for managed agents."""
    mock_client = MagicMock()

    mock_agent = MagicMock()
    mock_agent.id = "agent-test-123"
    mock_agent.version = 1
    mock_client.beta.agents.create.return_value = mock_agent

    mock_env = MagicMock()
    mock_env.id = "env-test-456"
    mock_client.beta.environments.create.return_value = mock_env

    mock_session = MagicMock()
    mock_session.id = "session-test-789"
    mock_client.beta.sessions.create.return_value = mock_session

    idle_event = MagicMock()
    idle_event.type = "session.status_idle"
    # __enter__ returns a list so `for event in stream` iterates over [idle_event]
    mock_client.beta.sessions.events.stream.return_value.__enter__.return_value = [idle_event]

    return mock_client


# ---------------------------------------------------------------------------
# run_path_b
# ---------------------------------------------------------------------------

def test_run_path_b_night2_calls_agents_create_with_opus():
    mock_client = _make_mock_client()
    with patch("theory_copilot.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from theory_copilot import managed_agent_runner
        result = managed_agent_runner.run_path_b(night=2)

    mock_client.beta.agents.create.assert_called_once()
    call_kwargs = mock_client.beta.agents.create.call_args
    assert call_kwargs.kwargs.get("model") == "claude-opus-4-7" or (
        len(call_kwargs.args) > 1 and call_kwargs.args[1] == "claude-opus-4-7"
    ), "agents.create must be called with model='claude-opus-4-7'"


def test_run_path_b_night2_calls_sessions_create():
    mock_client = _make_mock_client()
    with patch("theory_copilot.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from theory_copilot import managed_agent_runner
        managed_agent_runner.run_path_b(night=2)

    mock_client.beta.sessions.create.assert_called_once()


def test_run_path_b_night2_uses_stream_as_context_manager():
    mock_client = _make_mock_client()
    with patch("theory_copilot.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from theory_copilot import managed_agent_runner
        managed_agent_runner.run_path_b(night=2)

    mock_client.beta.sessions.events.stream.assert_called_once()
    stream_ctx = mock_client.beta.sessions.events.stream.return_value
    stream_ctx.__enter__.assert_called_once()
    stream_ctx.__exit__.assert_called_once()


def test_run_path_b_night2_calls_events_send():
    mock_client = _make_mock_client()
    with patch("theory_copilot.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from theory_copilot import managed_agent_runner
        managed_agent_runner.run_path_b(night=2)

    mock_client.beta.sessions.events.send.assert_called_once()
    send_call = mock_client.beta.sessions.events.send.call_args
    events_arg = send_call.kwargs.get("events") or send_call.args[1]
    assert events_arg[0]["type"] == "user.message"


def test_run_path_b_returns_expected_shape():
    mock_client = _make_mock_client()
    with patch("theory_copilot.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from theory_copilot import managed_agent_runner
        result = managed_agent_runner.run_path_b(night=2)

    assert "session_id" in result
    assert "agent_id" in result
    assert "output" in result
    assert result["status"] in ("completed", "error")


def test_run_path_b_stream_opened_before_send():
    """Verify stream is called (opened) before events.send is called."""
    call_order: list[str] = []
    mock_client = _make_mock_client()

    # Capture the pre-configured context manager before overriding side_effect,
    # so the tracking wrapper returns it directly (no recursive mock call).
    stream_ctx = mock_client.beta.sessions.events.stream.return_value

    def tracking_stream(*args, **kwargs):
        call_order.append("stream")
        return stream_ctx

    mock_client.beta.sessions.events.stream.side_effect = tracking_stream
    mock_client.beta.sessions.events.send.side_effect = (
        lambda *a, **kw: call_order.append("send")
    )

    with patch("theory_copilot.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from theory_copilot import managed_agent_runner
        managed_agent_runner.run_path_b(night=2)

    assert "stream" in call_order and "send" in call_order, (
        f"Expected both 'stream' and 'send' in call_order, got: {call_order}"
    )
    assert call_order.index("stream") < call_order.index("send")


# ---------------------------------------------------------------------------
# run_path_a
# ---------------------------------------------------------------------------

def test_run_path_a_raises_not_implemented_without_waitlist_env(monkeypatch):
    monkeypatch.delenv("MANAGED_AGENTS_WAITLIST", raising=False)
    with patch("theory_copilot.managed_agent_runner.anthropic"):
        from theory_copilot import managed_agent_runner
        with pytest.raises(NotImplementedError, match="callable_agents requires waitlist approval"):
            managed_agent_runner.run_path_a(night=2)


def test_run_path_a_raises_when_waitlist_not_approved(monkeypatch):
    monkeypatch.setenv("MANAGED_AGENTS_WAITLIST", "pending")
    with patch("theory_copilot.managed_agent_runner.anthropic"):
        from theory_copilot import managed_agent_runner
        with pytest.raises(NotImplementedError):
            managed_agent_runner.run_path_a(night=2)


def test_run_path_a_returns_without_error_when_approved(monkeypatch):
    monkeypatch.setenv("MANAGED_AGENTS_WAITLIST", "approved")

    mock_client = _make_mock_client()
    # run_path_a creates 3 agents and 3 sessions; return distinct mocks to keep it clean
    agent_ids = ["agent-proposer", "agent-searcher", "agent-falsifier"]
    session_ids = ["session-p", "session-s", "session-f"]

    agent_mocks = []
    for aid in agent_ids:
        m = MagicMock()
        m.id = aid
        agent_mocks.append(m)
    mock_client.beta.agents.create.side_effect = agent_mocks

    session_mocks = []
    for sid in session_ids:
        m = MagicMock()
        m.id = sid
        session_mocks.append(m)
    mock_client.beta.sessions.create.side_effect = session_mocks

    idle_event = MagicMock()
    idle_event.type = "session.status_idle"
    mock_client.beta.sessions.events.stream.return_value.__enter__.return_value = [idle_event]

    with patch("theory_copilot.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from theory_copilot import managed_agent_runner
        result = managed_agent_runner.run_path_a(night=2)

    assert isinstance(result, dict)
    assert "session_id" in result
    assert "agent_id" in result
    assert result["status"] in ("completed", "error")


def test_run_path_a_approved_creates_three_agents(monkeypatch):
    monkeypatch.setenv("MANAGED_AGENTS_WAITLIST", "approved")

    mock_client = _make_mock_client()
    agent_mocks = []
    for i in range(3):
        m = MagicMock()
        m.id = f"agent-{i}"
        agent_mocks.append(m)
    mock_client.beta.agents.create.side_effect = agent_mocks

    session_mocks = []
    for i in range(3):
        m = MagicMock()
        m.id = f"session-{i}"
        session_mocks.append(m)
    mock_client.beta.sessions.create.side_effect = session_mocks

    idle_event = MagicMock()
    idle_event.type = "session.status_idle"
    mock_client.beta.sessions.events.stream.return_value.__enter__.return_value = [idle_event]

    with patch("theory_copilot.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from theory_copilot import managed_agent_runner
        managed_agent_runner.run_path_a(night=2)

    assert mock_client.beta.agents.create.call_count == 3
    models_used = [
        c.kwargs.get("model") for c in mock_client.beta.agents.create.call_args_list
    ]
    assert "claude-opus-4-7" in models_used
    assert "claude-sonnet-4-6" in models_used

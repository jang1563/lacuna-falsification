import json
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
    mock_client.beta.sessions.events.stream.return_value.__enter__.return_value = [idle_event]

    return mock_client


# ---------------------------------------------------------------------------
# run_path_b
# ---------------------------------------------------------------------------

def test_run_path_b_night2_calls_agents_create_with_opus():
    mock_client = _make_mock_client()
    with patch("lacuna.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from lacuna import managed_agent_runner
        result = managed_agent_runner.run_path_b(night=2)

    mock_client.beta.agents.create.assert_called_once()
    call_kwargs = mock_client.beta.agents.create.call_args
    assert call_kwargs.kwargs.get("model") == "claude-opus-4-7" or (
        len(call_kwargs.args) > 1 and call_kwargs.args[1] == "claude-opus-4-7"
    ), "agents.create must be called with model='claude-opus-4-7'"


def test_run_path_b_night2_calls_sessions_create():
    mock_client = _make_mock_client()
    with patch("lacuna.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from lacuna import managed_agent_runner
        managed_agent_runner.run_path_b(night=2)

    mock_client.beta.sessions.create.assert_called_once()


def test_run_path_b_night2_uses_stream_as_context_manager():
    mock_client = _make_mock_client()
    with patch("lacuna.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from lacuna import managed_agent_runner
        managed_agent_runner.run_path_b(night=2)

    mock_client.beta.sessions.events.stream.assert_called_once()
    stream_ctx = mock_client.beta.sessions.events.stream.return_value
    stream_ctx.__enter__.assert_called_once()
    stream_ctx.__exit__.assert_called_once()


def test_run_path_b_night2_calls_events_send():
    mock_client = _make_mock_client()
    with patch("lacuna.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from lacuna import managed_agent_runner
        managed_agent_runner.run_path_b(night=2)

    mock_client.beta.sessions.events.send.assert_called_once()
    send_call = mock_client.beta.sessions.events.send.call_args
    events_arg = send_call.kwargs.get("events") or send_call.args[1]
    assert events_arg[0]["type"] == "user.message"


def test_run_path_b_returns_expected_shape():
    mock_client = _make_mock_client()
    with patch("lacuna.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from lacuna import managed_agent_runner
        result = managed_agent_runner.run_path_b(night=2)

    assert "session_id" in result
    assert "agent_id" in result
    assert "output" in result
    assert result["status"] in ("completed", "error")


def test_run_path_b_stream_opened_before_send():
    """Verify stream is called (opened) before events.send is called."""
    call_order: list[str] = []
    mock_client = _make_mock_client()

    stream_ctx = mock_client.beta.sessions.events.stream.return_value

    def tracking_stream(*args, **kwargs):
        call_order.append("stream")
        return stream_ctx

    mock_client.beta.sessions.events.stream.side_effect = tracking_stream
    mock_client.beta.sessions.events.send.side_effect = (
        lambda *a, **kw: call_order.append("send")
    )

    with patch("lacuna.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from lacuna import managed_agent_runner
        managed_agent_runner.run_path_b(night=2)

    assert "stream" in call_order and "send" in call_order, (
        f"Expected both 'stream' and 'send' in call_order, got: {call_order}"
    )
    assert call_order.index("stream") < call_order.index("send")


def test_run_path_b_pin_version_passes_versioned_agent_ref():
    """With pin_version=True, sessions.create agent= is {type,id,version}."""
    mock_client = _make_mock_client()
    mock_client.beta.agents.create.return_value.version = 3

    with patch("lacuna.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from lacuna import managed_agent_runner
        result = managed_agent_runner.run_path_b(night=2, pin_version=True)

    assert result["agent_version"] == 3
    create_kwargs = mock_client.beta.sessions.create.call_args.kwargs
    assert isinstance(create_kwargs.get("agent"), dict)
    assert create_kwargs["agent"]["type"] == "agent"
    assert create_kwargs["agent"]["version"] == 3


# ---------------------------------------------------------------------------
# run_path_a — real callable_agents + sequential fallback
# ---------------------------------------------------------------------------

def test_run_path_a_raises_not_implemented_without_waitlist_env(monkeypatch):
    monkeypatch.delenv("MANAGED_AGENTS_WAITLIST", raising=False)
    with patch("lacuna.managed_agent_runner.anthropic"):
        from lacuna import managed_agent_runner
        with pytest.raises(NotImplementedError, match="callable_agents requires waitlist approval"):
            managed_agent_runner.run_path_a(night=2)


def test_run_path_a_raises_when_waitlist_not_approved(monkeypatch):
    monkeypatch.setenv("MANAGED_AGENTS_WAITLIST", "pending")
    with patch("lacuna.managed_agent_runner.anthropic"):
        from lacuna import managed_agent_runner
        with pytest.raises(NotImplementedError):
            managed_agent_runner.run_path_a(night=2)


def test_run_path_a_approved_uses_real_callable_agents(monkeypatch):
    """Waitlist-approved path creates 4 agents (proposer, searcher, skeptic,
    orchestrator) and passes `callable_agents=` to the orchestrator."""
    monkeypatch.setenv("MANAGED_AGENTS_WAITLIST", "approved")

    mock_client = _make_mock_client()
    agent_mocks = []
    for i in range(4):
        m = MagicMock()
        m.id = f"agent-{i}"
        m.version = 1
        agent_mocks.append(m)
    mock_client.beta.agents.create.side_effect = agent_mocks

    session_mock = MagicMock()
    session_mock.id = "orchestrator-session"
    mock_client.beta.sessions.create.return_value = session_mock

    idle_event = MagicMock()
    idle_event.type = "session.status_idle"
    mock_client.beta.sessions.events.stream.return_value.__enter__.return_value = [idle_event]

    with patch("lacuna.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from lacuna import managed_agent_runner
        result = managed_agent_runner.run_path_a(night=2)

    assert mock_client.beta.agents.create.call_count == 4, (
        "Expected 4 agents (proposer, searcher, skeptic, orchestrator)"
    )

    # Orchestrator is the LAST agent created; it must have callable_agents set.
    orch_kwargs = mock_client.beta.agents.create.call_args_list[-1].kwargs
    assert "callable_agents" in orch_kwargs
    assert len(orch_kwargs["callable_agents"]) == 3

    models_used = [
        c.kwargs.get("model") for c in mock_client.beta.agents.create.call_args_list
    ]
    assert models_used.count("claude-opus-4-7") == 3  # proposer + skeptic + orchestrator
    assert "claude-sonnet-4-6" in models_used  # searcher

    assert result["delegation_mode"] == "callable_agents"


def test_run_path_a_fallback_creates_three_agents_and_three_sessions(monkeypatch):
    """fallback_on_no_waitlist=True without approval: sequential chain of 3."""
    monkeypatch.delenv("MANAGED_AGENTS_WAITLIST", raising=False)

    mock_client = _make_mock_client()
    agent_mocks = [MagicMock(id=f"agent-{i}", version=1) for i in range(3)]
    mock_client.beta.agents.create.side_effect = agent_mocks
    session_mocks = [MagicMock(id=f"session-{i}") for i in range(3)]
    mock_client.beta.sessions.create.side_effect = session_mocks

    idle_event = MagicMock()
    idle_event.type = "session.status_idle"
    mock_client.beta.sessions.events.stream.return_value.__enter__.return_value = [idle_event]

    with patch("lacuna.managed_agent_runner.anthropic") as mock_anthropic:
        mock_anthropic.Anthropic.return_value = mock_client
        from lacuna import managed_agent_runner
        result = managed_agent_runner.run_path_a(
            night=2, fallback_on_no_waitlist=True
        )

    assert mock_client.beta.agents.create.call_count == 3
    assert mock_client.beta.sessions.create.call_count == 3
    assert result["delegation_mode"] == "sequential_fallback"


# ---------------------------------------------------------------------------
# run_path_c_routine
# ---------------------------------------------------------------------------

def test_run_path_c_routine_rejects_invalid_night():
    from lacuna import managed_agent_runner
    with pytest.raises(ValueError):
        managed_agent_runner.run_path_c_routine(night=1)


def test_run_path_c_routine_runs_once_when_interval_zero(tmp_path):
    from lacuna import managed_agent_runner
    calls = []

    def fake_invoke(night):
        calls.append(night)
        return {"session_id": "s-1", "agent_id": "a-1", "output": "ok", "status": "completed"}

    log = tmp_path / "verdicts.jsonl"
    result = managed_agent_runner.run_path_c_routine(
        night=3,
        interval_seconds=0,
        max_iterations=0,
        log_path=str(log),
        invoke_fn=fake_invoke,
    )
    assert calls == [3]
    assert result["iteration_count"] == 1
    assert log.exists()
    entries = [json.loads(line) for line in log.read_text().splitlines()]
    assert entries[0]["night"] == 3
    assert entries[0]["status"] == "completed"


def test_run_path_c_routine_respects_max_iterations(tmp_path):
    from lacuna import managed_agent_runner
    calls = []

    def fake_invoke(night):
        calls.append(night)
        return {"session_id": f"s-{len(calls)}", "status": "completed", "output": ""}

    result = managed_agent_runner.run_path_c_routine(
        night=2,
        interval_seconds=1,
        max_iterations=3,
        log_path=str(tmp_path / "v.jsonl"),
        invoke_fn=fake_invoke,
        sleeper=lambda _s: None,
    )
    assert result["iteration_count"] == 3
    assert len(calls) == 3


def test_run_path_c_routine_watch_dir_skips_when_unchanged(tmp_path):
    from lacuna import managed_agent_runner
    calls = []

    def fake_invoke(night):
        calls.append(night)
        return {"session_id": "s", "status": "completed", "output": ""}

    watch = tmp_path / "watch"
    watch.mkdir()
    (watch / "data.csv").write_text("sample_id,label\ns1,1\n")

    result = managed_agent_runner.run_path_c_routine(
        night=2,
        interval_seconds=1,
        max_iterations=3,
        watch_dir=str(watch),
        log_path=str(tmp_path / "v.jsonl"),
        invoke_fn=fake_invoke,
        sleeper=lambda _s: None,
    )
    assert len(calls) == 1
    assert result["iteration_count"] == 3
    entries = [json.loads(line) for line in (tmp_path / "v.jsonl").read_text().splitlines()]
    skipped = [e for e in entries if e["status"] == "skipped_no_change"]
    assert len(skipped) == 2


def test_run_path_c_routine_watch_dir_triggers_on_change(tmp_path):
    from lacuna import managed_agent_runner
    calls = []
    watch = tmp_path / "watch"
    watch.mkdir()
    (watch / "data.csv").write_text("sample_id,label\ns1,1\n")

    def fake_invoke(night):
        calls.append(night)
        (watch / f"new_{len(calls)}.csv").write_text(f"row{len(calls)}")
        return {"session_id": "s", "status": "completed", "output": ""}

    result = managed_agent_runner.run_path_c_routine(
        night=2,
        interval_seconds=1,
        max_iterations=3,
        watch_dir=str(watch),
        log_path=str(tmp_path / "v.jsonl"),
        invoke_fn=fake_invoke,
        sleeper=lambda _s: None,
    )
    assert len(calls) == 3


def test_run_path_c_routine_log_path_is_jsonl_appendable(tmp_path):
    from lacuna import managed_agent_runner
    log = tmp_path / "a" / "b" / "verdicts.jsonl"

    def fake_invoke(night):
        return {"session_id": "s", "status": "completed", "output": "x" * 42}

    managed_agent_runner.run_path_c_routine(
        night=4,
        interval_seconds=0,
        log_path=str(log),
        invoke_fn=fake_invoke,
    )
    assert log.exists()
    line = log.read_text().strip()
    parsed = json.loads(line)
    assert parsed["night"] == 4
    assert parsed["output_chars"] == 42


# ---------------------------------------------------------------------------
# persist_session_events / replay_session_from_log
# ---------------------------------------------------------------------------

def test_persist_session_events_dumps_jsonl(tmp_path):
    from lacuna import managed_agent_runner

    events = [
        {"type": "user.message", "id": "ev1", "content": [{"type": "text", "text": "hi"}]},
        {"type": "agent.thinking", "id": "ev2", "content": [{"type": "text", "text": "t"}]},
        {"type": "agent.message", "id": "ev3", "content": [{"type": "text", "text": "ok"}]},
        {"type": "session.status_idle", "id": "ev4"},
    ]

    mock_client = MagicMock()
    mock_client.beta.sessions.events.list.return_value = events  # iterable, no pagination

    out = tmp_path / "session.jsonl"
    result = managed_agent_runner.persist_session_events(
        "session-xyz", str(out), client=mock_client
    )

    assert result["event_count"] == 4
    assert result["first_event_type"] == "user.message"
    assert result["last_event_type"] == "session.status_idle"
    lines = out.read_text().strip().splitlines()
    assert len(lines) == 4
    assert json.loads(lines[0])["type"] == "user.message"


def test_replay_session_from_log_sends_only_user_events(tmp_path):
    from lacuna import managed_agent_runner

    log = tmp_path / "events.jsonl"
    log.write_text(
        "\n".join([
            json.dumps({"type": "user.message", "content": [{"type": "text", "text": "q1"}]}),
            json.dumps({"type": "agent.message", "content": [{"type": "text", "text": "a1"}]}),
            json.dumps({"type": "user.interrupt"}),
            json.dumps({"type": "agent.tool_use", "content": []}),
            json.dumps({"type": "session.status_idle"}),
        ])
    )

    mock_client = MagicMock()

    result = managed_agent_runner.replay_session_from_log(
        str(log), "new-session-id", client=mock_client
    )

    assert result["events_replayed"] == 2  # user.message + user.interrupt
    assert mock_client.beta.sessions.events.send.call_count == 2
    # skipped counts include agent.message, agent.tool_use, session.status_idle
    skipped = result["events_skipped_by_type"]
    assert skipped.get("agent.message", 0) == 1
    assert skipped.get("session.status_idle", 0) == 1

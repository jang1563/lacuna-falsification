import json

import httpx
import pytest


def _mock_transport(response_payload: dict, status: int = 200):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status,
            content=json.dumps(response_payload).encode(),
            headers={"Content-Type": "application/json"},
        )
    return httpx.MockTransport(handler)


def test_fire_routine_success_returns_session_info():
    from lacuna import routines_client

    payload = {
        "type": "routine_fire",
        "claude_code_session_id": "session_01HJKL",
        "claude_code_session_url": "https://claude.ai/code/session_01HJKL",
    }
    transport = _mock_transport(payload, status=200)

    result = routines_client.fire_routine(
        trig_id="trig_abc", token="sk-ant-oat01-xxx",
        text="run night 3", _transport=transport,
    )

    assert result.session_id == "session_01HJKL"
    assert "session_01HJKL" in result.session_url
    assert result.status == "completed"
    assert result.http_status == 200


def test_fire_routine_non_2xx_sets_error_status():
    from lacuna import routines_client

    transport = _mock_transport({"error": "unauthorized"}, status=401)

    result = routines_client.fire_routine(
        trig_id="trig_abc", token="bad-token", text="",
        _transport=transport,
    )
    assert result.status == "error"
    assert result.http_status == 401


def test_fire_routine_from_env_raises_when_missing(monkeypatch):
    from lacuna import routines_client

    monkeypatch.delenv("CLAUDE_ROUTINE_TRIG_ID", raising=False)
    monkeypatch.delenv("CLAUDE_ROUTINE_TOKEN", raising=False)

    with pytest.raises(RuntimeError, match="Missing required env var"):
        routines_client.fire_routine_from_env()


def test_make_routine_invoke_fn_shapes_result_like_path_b(monkeypatch):
    """The invoke_fn returned by make_routine_invoke_fn must return the same
    dict shape run_path_c_routine expects from run_path_b."""
    from lacuna import routines_client

    monkeypatch.setenv("CLAUDE_ROUTINE_TRIG_ID", "trig_test")
    monkeypatch.setenv("CLAUDE_ROUTINE_TOKEN", "token_test")

    payload = {
        "type": "routine_fire",
        "claude_code_session_id": "session_test_id",
        "claude_code_session_url": "https://claude.ai/code/session_test_id",
    }

    # Patch fire_routine at the module level to avoid real HTTP.
    def fake_fire_routine(trig_id, token, text, **kwargs):
        return routines_client.RoutineFireResult(
            session_id=payload["claude_code_session_id"],
            session_url=payload["claude_code_session_url"],
            http_status=200,
        )

    monkeypatch.setattr(routines_client, "fire_routine", fake_fire_routine)

    fire = routines_client.make_routine_invoke_fn({3: "task text"})
    result = fire(3)

    assert result["session_id"] == "session_test_id"
    assert result["status"] == "completed"
    assert "routine_session_url" in result

"""Tool behaviour: grounding, retries and failure recovery."""
import tools
from tools import BANK, call_tool


def test_search_returns_real_catalog_problem():
    trace = []
    q = call_tool("search_questions", {"topic": "linked list", "difficulty": None, "exclude": []}, trace)
    assert q is not None
    assert tools._find(q["problem_name"]) is not None
    assert trace[0]["ok"] is True and trace[0]["attempts"] == 1


def test_unknown_topic_returns_none_instead_of_inventing():
    trace = []
    q = call_tool("search_questions", {"topic": "quantum basket weaving", "difficulty": None, "exclude": []}, trace)
    assert q is None
    assert trace[0]["ok"] is True


def test_lookup_rejects_problem_not_in_catalog():
    assert call_tool("lookup_problem", {"problem_name": "Totally Made Up Problem"}, []) is None
    assert call_tool("lookup_problem", {"problem_name": BANK[0]["problem_name"]}, []) is not None


def test_hint_for_fake_problem_fails_safely():
    trace = []
    result = call_tool("get_hint", {"problem_name": "Fake Problem", "level": 0}, trace, default="fallback")
    assert result == "fallback"
    assert trace[0]["ok"] is False
    assert trace[0]["attempts"] == tools.MAX_RETRIES + 1


def test_flaky_tool_is_retried_then_succeeds(monkeypatch):
    real = tools.choose_problem
    calls = {"n": 0}

    def flaky(*args, **kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise TimeoutError("catalog temporarily unavailable")
        return real(*args, **kwargs)

    monkeypatch.setattr(tools, "choose_problem", flaky)
    trace = []
    q = call_tool("search_questions", {"topic": "arrays", "difficulty": None, "exclude": []}, trace)
    assert q is not None
    assert trace[0]["ok"] is True and trace[0]["attempts"] == 2


def test_tool_returning_invented_problem_is_rejected(monkeypatch):
    monkeypatch.setattr(tools, "choose_problem",
                        lambda *a, **k: {"problem_name": "Hallucinated Problem", "topic": "Arrays"})
    trace = []
    q = call_tool("search_questions", {"topic": "arrays", "difficulty": None, "exclude": []}, trace)
    assert q is None
    assert trace[0]["ok"] is False and "validation" in trace[0]["error"]


def test_unknown_tool_name():
    trace = []
    assert call_tool("delete_database", {}, trace, default="nope") == "nope"
    assert trace[0]["error"] == "unknown tool"

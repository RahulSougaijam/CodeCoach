"""LLM output guardrails and fallback when Gemini fails."""
from langchain_core.messages import HumanMessage

import graph
from graph import create_thread_id, get_debug, get_thread, validate_answer


def test_hint_with_code_is_rejected():
    assert validate_answer("hint", "Try this:\n```java\nreturn x;\n```", "give me a hint")


def test_empty_answer_is_rejected():
    assert validate_answer("explain", "   ", "explain recursion")


def test_code_allowed_when_user_asks_for_solution():
    assert validate_answer("solution", "```java\nreturn x;\n```", "show me the solution") == ""


def test_normal_hint_passes():
    assert validate_answer("hint", "Think about what you have already seen.", "hint") == ""


def _start_problem(thread):
    graph.graph.invoke({"messages": [HumanMessage(content="Let's practice linked list.")]},
                       {"configurable": {"thread_id": thread}})


def test_gemini_crash_falls_back_to_local(monkeypatch):
    monkeypatch.setattr(graph, "llm_available", lambda: True)

    def boom(*a, **k):
        raise ConnectionError("Gemini down")

    monkeypatch.setattr(graph, "classify_request", boom)
    monkeypatch.setattr(graph, "generate_response", boom)
    thread = create_thread_id()
    _start_problem(thread)
    reply = get_thread(thread)[-1]["content"]
    assert "Topic:" in reply  # local problem card was used
    assert "Gemini down" in get_debug(thread)["llm_error"]


def test_leaky_gemini_hint_is_replaced(monkeypatch):
    thread = create_thread_id()
    _start_problem(thread)
    monkeypatch.setattr(graph, "llm_available", lambda: True)
    monkeypatch.setattr(graph, "classify_request",
                        lambda *a, **k: {"intent": "hint", "topic": None, "difficulty": None, "language": None})
    monkeypatch.setattr(graph, "generate_response", lambda *a, **k: "Here:\n```java\nfull solution\n```")
    graph.graph.invoke({"messages": [HumanMessage(content="give me a hint")]},
                       {"configurable": {"thread_id": thread}})
    reply = get_thread(thread)[-1]["content"]
    assert "```" not in reply and "Hint 1" in reply
    assert "leak" in get_debug(thread)["guard_rejected"]

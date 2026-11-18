"""Regression checks for CodeCoach's local state/routing layer.

These tests do not require an API key. They verify that the local safety
fallback and LangGraph state mechanics remain usable if the API is unavailable.
"""

from graph import detect_intent, create_thread_id, graph, get_thread_info, infer_topic
from langchain_core.messages import HumanMessage


def check(condition, message):
    if not condition:
        raise AssertionError(message)


state = {"current_problem": "Two Sum"}

cases = {
    "what is the question": "repeat_problem",
    "repeat the problem": "repeat_problem",
    "switch to python": "language",
    "use python": "language",
    "python": "language",
    "give me another hint": "hint",
    "show me the solution": "solution",
    "what is the time complexity?": "complexity",
    "can you explain that?": "explain",
    "I think we should use a hashmap": "attempt",
}

for text, expected in cases.items():
    actual = detect_intent(text, state)
    check(actual == expected, f"{text!r}: expected {expected}, got {actual}")

check(infer_topic("let's practice linked list") == "linkedlist", "linked list topic failed")
check(infer_topic("binary search tree") == "bst", "BST topic failed")
check(infer_topic("dynamic programming") == "dynamic programming", "DP topic failed")

thread = create_thread_id()
graph.invoke(
    {"messages": [HumanMessage(content="Hi, my name is Rahul. I prefer Java.")]},
    {"configurable": {"thread_id": thread}},
)
info = get_thread_info(thread)
check(info["language"] == "Java", "language was not retained in thread state")
check(len(info["current_problem"]) == 0, "greeting should not create a problem")

print("ALL CODECOACH LOCAL SMOKE TESTS PASSED")

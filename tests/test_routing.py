"""Local intent router (used when Gemini is unavailable)."""
import pytest

from graph import detect_intent, infer_topic

ACTIVE = {"current_problem": "Two Sum"}


@pytest.mark.parametrize("text,expected", [
    ("what is the question", "repeat_problem"),
    ("switch to python", "language"),
    ("python", "language"),
    ("give me another hint", "hint"),
    ("show me the solution", "solution"),
    ("what is the time complexity?", "complexity"),
    ("can you explain that?", "explain"),
    ("I think we should use a hashmap", "attempt"),
])
def test_intents(text, expected):
    assert detect_intent(text, ACTIVE) == expected


def test_no_active_problem_repeat_is_conversation():
    assert detect_intent("what is the question", {}) == "conversation"


@pytest.mark.parametrize("text,topic", [
    ("let's practice linked list", "linkedlist"),
    ("binary search tree", "bst"),
    ("dynamic programming", "dynamic programming"),
])
def test_topics(text, topic):
    assert infer_topic(text) == topic

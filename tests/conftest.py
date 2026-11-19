"""Shared test setup: run offline (no Gemini key) with a clean profile store."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(autouse=True)
def offline_and_clean(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    import graph
    graph.store.delete(("demo_user", "profile"), "main")
    yield
    graph.store.delete(("demo_user", "profile"), "main")

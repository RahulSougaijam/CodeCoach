"""Tools the CodeCoach agent uses, plus a safe way to call them.

Every tool is a typed LangChain tool. Nodes never touch the catalog directly;
they go through `call_tool()`, which:
  1. validates the arguments,
  2. retries a failed call (bounded number of attempts),
  3. validates the result (e.g. a problem must really exist in the catalog),
  4. records a trace entry so every run can be inspected in the UI / tests.
"""

from __future__ import annotations

import time
from typing import Any, Callable, Optional

from langchain_core.tools import tool

from question_bank import choose_problem, hints, load_bank

BANK, BANK_SOURCE = load_bank()
MAX_RETRIES = 2  # total attempts = 1 + MAX_RETRIES


def _find(problem_name: str) -> Optional[dict[str, Any]]:
    """Exact (case-insensitive) title lookup in the local catalog."""
    wanted = (problem_name or "").strip().lower()
    for q in BANK:
        if q["problem_name"].lower() == wanted:
            return q
    return None


# --------------------------------------------------------------------------
# Tool definitions
# --------------------------------------------------------------------------

@tool
def search_questions(
    topic: Optional[str] = None,
    difficulty: Optional[str] = None,
    exclude: Optional[list[str]] = None,
) -> Optional[dict[str, Any]]:
    """Pick one interview problem from the local catalog.

    Returns None if nothing matches. The agent must never invent a problem.
    """
    return choose_problem(BANK, topic, difficulty, exclude or [])


@tool
def lookup_problem(problem_name: str) -> Optional[dict[str, Any]]:
    """Return catalog metadata for a problem title, or None if it isn't in the catalog."""
    return _find(problem_name)


@tool
def get_hint(problem_name: str, level: int) -> Optional[str]:
    """Return the progressive hint at `level` (0-based), or None if hints are used up."""
    q = _find(problem_name)
    if q is None:
        raise ValueError(f"'{problem_name}' is not in the catalog")
    all_hints = hints(q, 0)
    if level < 0 or level >= len(all_hints):
        return None
    return all_hints[level]


TOOLS = {t.name: t for t in (search_questions, lookup_problem, get_hint)}


# --------------------------------------------------------------------------
# Result validators: a tool result is only accepted if its validator passes.
# --------------------------------------------------------------------------

def _valid_problem(result: Any) -> bool:
    # None is a valid "nothing found" answer; anything else must be a real catalog entry.
    return result is None or (isinstance(result, dict) and _find(result.get("problem_name", "")) is not None)


def _valid_hint(result: Any) -> bool:
    # Hints must be plain text and must not contain code (no solution leaks).
    return result is None or (isinstance(result, str) and "```" not in result and len(result) < 1200)


VALIDATORS: dict[str, Callable[[Any], bool]] = {
    "search_questions": _valid_problem,
    "lookup_problem": _valid_problem,
    "get_hint": _valid_hint,
}


def call_tool(name: str, args: dict[str, Any], trace: list[dict[str, Any]], default: Any = None) -> Any:
    """Run a tool with retries + result validation and append a trace entry.

    If every attempt fails, return `default` so the graph can recover
    instead of crashing.
    """
    if name not in TOOLS:
        trace.append({"tool": name, "args": args, "ok": False, "attempts": 0, "error": "unknown tool"})
        return default

    last_error = ""
    for attempt in range(1, MAX_RETRIES + 2):
        try:
            result = TOOLS[name].invoke(args)
            if not VALIDATORS[name](result):
                raise ValueError("result failed validation")
            trace.append({"tool": name, "args": args, "ok": True, "attempts": attempt,
                          "result": _summary(result)})
            return result
        except Exception as exc:  # retry on any tool failure
            last_error = f"{type(exc).__name__}: {exc}"[:200]
            time.sleep(0.05 * attempt)  # small backoff

    trace.append({"tool": name, "args": args, "ok": False, "attempts": MAX_RETRIES + 1,
                  "error": last_error, "fallback": _summary(default)})
    return default


def _summary(value: Any) -> Any:
    if isinstance(value, dict) and "problem_name" in value:
        return {k: value.get(k) for k in ("problem_name", "topic", "difficulty")}
    if isinstance(value, str) and len(value) > 120:
        return value[:120] + "…"
    return value

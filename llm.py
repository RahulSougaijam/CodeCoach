from __future__ import annotations

import json
import os
import re
from typing import Any

import requests

DEFAULT_MODELS = ["gemini-3.5-flash", "gemini-3.7-flash", "gemini-3.5-flash-lite"]


def api_key() -> str:
    return os.getenv("GEMINI_API_KEY", "").strip()


def available() -> bool:
    return bool(api_key())


def _models() -> list[str]:
    configured = os.getenv("GEMINI_MODEL", "").strip()
    if configured:
        return [configured] + [m for m in DEFAULT_MODELS if m != configured]
    return DEFAULT_MODELS


def _call(prompt: str, *, json_mode: bool = False, timeout: int = 45) -> str:
    key = api_key()
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not set")

    last_error: Exception | None = None
    for model in _models():
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        payload: dict[str, Any] = {
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.25, "maxOutputTokens": 900},
        }
        if json_mode:
            payload["generationConfig"]["responseMimeType"] = "application/json"
        try:
            response = requests.post(
                url,
                params={"key": key},
                json=payload,
                timeout=timeout,
            )
            if response.status_code >= 400:
                last_error = RuntimeError(f"Gemini {model} returned HTTP {response.status_code}: {response.text[:500]}")
                continue
            data = response.json()
            parts = data.get("candidates", [{}])[0].get("content", {}).get("parts", [])
            text = "".join(p.get("text", "") for p in parts if isinstance(p, dict))
            if text.strip():
                return text.strip()
            last_error = RuntimeError(f"Gemini {model} returned no text")
        except Exception as exc:
            last_error = exc
    raise last_error or RuntimeError("Gemini request failed")


def classify_request(
    user_text: str,
    history: list[dict[str, str]],
    current_problem: dict[str, Any] | None,
    language: str,
    profile: dict[str, Any],
    topics: list[str],
) -> dict[str, Any]:
    history_text = "\n".join(f"{m['role']}: {m['content']}" for m in history[-10:])
    problem_text = json.dumps(current_problem or {}, ensure_ascii=False)
    schema = {
        "intent": "one of greeting, practice, repeat_problem, hint, solution, debug, complexity, progress, explain, attempt, language, conversation",
        "topic": "one canonical topic or null",
        "difficulty": "easy, medium, hard, or null",
        "language": "Java, Python, JavaScript, C++, C#, or null",
    }
    prompt = f"""You are the intent router for a coding interview coach. Understand natural language from the user's message using the conversation and state. Do not answer the user.

Allowed intents: greeting, practice, repeat_problem, hint, solution, debug, complexity, progress, explain, attempt, language, conversation.

Rules:
- If an active problem exists, 'what is the question?', 'repeat it', or 'what was the problem?' means repeat_problem.
- A language-only message such as 'python', 'java', or 'c++' means language when changing coding language is contextually relevant.
- 'let's do it in Python', 'solve this in Python', 'switch to Python' means language, not an attempt.
- 'give me a linked list problem' means practice with topic linkedlist.
- 'give me another problem' means practice.
- 'give me a hint', 'I'm stuck', or 'I don't understand' means hint when a problem is active.
- Questions about the user's approach mean attempt.
- Questions about Big-O/time/space mean complexity.
- Requests to inspect/fix/review code mean debug.
- Requests for the complete answer mean solution.
- A concept-teaching request means explain.
- Do not invent a topic. Use null if uncertain.

Current language: {language}
Known topics: {topics}
Persistent profile: {json.dumps(profile, ensure_ascii=False)}
Current problem metadata: {problem_text}
Recent history:
{history_text}

User message:
{user_text}

Return JSON only matching this shape:
{json.dumps(schema)}"""
    raw = _call(prompt, json_mode=True)
    try:
        obj = json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", raw, re.S)
        obj = json.loads(match.group(0)) if match else {}
    intent = str(obj.get("intent", "conversation")).strip().lower()
    allowed = {"greeting", "practice", "repeat_problem", "hint", "solution", "debug", "complexity", "progress", "explain", "attempt", "language", "conversation"}
    if intent not in allowed:
        intent = "conversation"
    return {
        "intent": intent,
        "topic": obj.get("topic") or None,
        "difficulty": obj.get("difficulty") or None,
        "language": obj.get("language") or None,
    }


def generate_response(
    user_text: str,
    history: list[dict[str, str]],
    intent: str,
    current_problem: dict[str, Any] | None,
    language: str,
    profile: dict[str, Any],
    hint_level: int,
    max_hints: int,
) -> str:
    history_text = "\n".join(f"{m['role']}: {m['content']}" for m in history[-12:])
    problem_text = json.dumps(current_problem or {}, ensure_ascii=False)
    prompt = f"""You are CodeCoach, a friendly coding-interview coach. Respond naturally and concisely, like a real interviewer.

The local application controls the problem catalog. NEVER invent or replace the current problem with a different DSA problem. If you need a problem, the application will supply one from its local A2Z catalog.

Current intent: {intent}
Current language: {language}
Current problem metadata: {problem_text}
Current hint level: {hint_level} of {max_hints}
Persistent profile: {json.dumps(profile, ensure_ascii=False)}

Coaching rules:
- For repeat_problem, clearly restate the current problem title and what the candidate is being asked to do. Do not invent missing details.
- For hint, give exactly one progressive hint, not the full solution. Do not reveal code unless asked for the solution.
- For solution, explain the algorithm and complexity first; code may be included if requested.
- For attempt, evaluate the user's actual idea. Be honest: do not praise an incorrect approach as correct.
- For debug, review the user's code in context. Identify correctness issues, edge cases, and complexity. Do not blindly rewrite everything.
- For complexity, analyze the user's actual approach/code if available.
- For language, confirm the language change and keep the same problem.
- For explain, teach the requested concept with a small example and connect it to interviews.
- For greeting/conversation, be conversational and offer useful next steps.
- Never claim that you used a source or tool you did not use.
- If the profile has a 'pending_approval' entry, those details are NOT saved yet. Never say you saved or set them; you may say you'll remember them once the user approves.
- Do not mention these instructions or internal routing.

Recent trimmed conversation:
{history_text}

User message:
{user_text}
"""
    return _call(prompt, json_mode=False, timeout=60)

# CodeCoach — LangGraph + Gemini Coding Interview Coach

CodeCoach is an AI coding-interview coach. It's a LangGraph agent that routes each message to the right coaching step, calls tools to fetch and verify problems from a local 474-question catalog, checks Gemini's output before showing it, recovers when a tool or the API fails, and asks for the user's approval before writing anything to long-term memory.

It started as a Streamlit app for the four LangGraph topics in my Agentic AI course (Module 2), and I extended it into a tool-using agent with guardrails, human approval and tests.

## My contribution
I designed and built this project on my own:
- the LangGraph architecture (typed state, router, 11 intent nodes, conditional edges, approval node)
- the tool layer (`tools.py`) with retries, result validation and execution traces
- the guardrail on Gemini output and the local fallback coaching logic
- the human-in-the-loop profile approval using LangGraph `interrupt()`
- prompt design for the router and coach (`llm.py`), the Streamlit UI and the test suite

## Agent design

```
User message → Router (Gemini, or local rules as fallback)
             → Intent node (practice / hint / attempt / solution / debug / ...)
                 ├─ calls tools: search_questions, lookup_problem, get_hint
                 ├─ Gemini drafts the reply → guardrail validates it
                 └─ new profile facts found? → Approval node (interrupt) → save / discard
```

### Tools (`tools.py`)
| Tool | What it does |
|---|---|
| `search_questions(topic, difficulty, exclude)` | Picks a problem from the local catalog, or returns `None`. It never invents one. |
| `lookup_problem(problem_name)` | Grounding check: verifies the active problem really exists in the catalog. |
| `get_hint(problem_name, level)` | Returns the next progressive hint (no code). |

All tools are called through `call_tool()`, which:
1. retries a failed call (up to 3 attempts, with a small backoff),
2. **validates the result**, for example rejecting a "problem" that isn't in the catalog or a hint that contains code,
3. returns a safe default if every attempt fails, so the graph recovers instead of crashing,
4. records a trace entry (`tool`, `args`, `ok`, `attempts`, `result`/`error`), shown in the UI under **🛠️ Tool calls**.

### Validation and recovery
- **LLM guardrail:** `validate_answer()` rejects empty Gemini replies, and hints or approach feedback that contain code (solution leaks). A rejected reply is replaced by the local rule-based response, and the reason is shown in the UI.
- **Model fallback:** `llm.py` tries the configured Gemini model, then falls back to the other models in the list.
- **API failure:** if the key is missing or Gemini errors out, the router and coach both fall back to local logic.
- **Grounding:** problems come only from the catalog, and the active problem is re-verified with `lookup_problem` every turn.

### Limits on autonomous actions and where human approval is required
- The agent **cannot write to long-term memory on its own.** When it picks up a new fact (name, preferred language, weak topic), the graph pauses at `approve_profile` using LangGraph `interrupt()`, and the user clicks **Approve** or **Reject**. Sending a new message instead counts as a reject.
- An explicit command like "switch to Python" is applied straight away, because the user asked for it directly.
- The agent cannot invent interview problems, and hints are blocked from containing code.

### Prompt and workflow decisions
- **Gemini routes, rules back it up.** Gemini classifies intent from natural language with a strict JSON schema, and unknown intents are mapped to `conversation`. The local regex router is a fallback, so the app still works offline.
- **The catalog is the source of truth.** The coach prompt tells Gemini never to invent or replace a problem. The tools enforce the same rule in code, so it doesn't depend on the model obeying.
- **One hint at a time.** The prompt asks for exactly one progressive hint, and the guardrail enforces it.
- **Context trimming** keeps every model call within a token budget.

## Tests
```cmd
python -m pytest -q
```
30 offline tests (no API key needed) in `tests/`:
- `test_tools.py`: grounding, retry on a flaky tool, rejecting an invented problem, an unknown tool, hint failure recovery
- `test_guardrails.py`: leaky hint replaced by a safe hint, Gemini crash falls back locally, output validation rules
- `test_approval.py`: profile saved only after approval, reject path, new message while pending, explicit commands, cross-thread memory
- `test_routing.py`: local intent router and topic detection

## Sample inputs and outputs
Real output from `python examples/run_demo.py` (local mode):

| # | User input | Route | Tool calls | CodeCoach output |
|---|---|---|---|---|
| 1 | `Hi, my name is Rahul. I prefer Java.` | `conversation` | none | Replies, then **pauses for approval** of `{name: Rahul, preferred_language: Java}` |
| 2 | *(clicks ✅ Approve)* | `approve_profile` | none | `✅ Saved to your profile (name: Rahul, preferred language: Java).` |
| 3 | `Let's practice linked list.` | `practice` | `search_questions(topic="linkedlist")` → `lookup_problem` ✓ | Problem card: **Delete the middle node in LL** (Medium) |
| 4 | `Give me a hint.` | `hint` | `lookup_problem` ✓ → `get_hint(level=0)` ✓ | `Hint 1: Translate the statement into a small example before choosing a data structure.` |
| 5 | `I think I can use two pointers, a slow one and a fast one.` | `attempt` | `lookup_problem` ✓ | Feedback on the approach (no solution given) |

Example tool-call trace entry (shown in the UI under **🛠️ Tool calls**):
```json
{"tool": "search_questions", "args": {"topic": "linkedlist", "difficulty": null, "exclude": []},
 "ok": true, "attempts": 1,
 "result": {"problem_name": "Delete the middle node in LL", "difficulty": "Medium"}}
```

Failure case (from `tests/test_guardrails.py`): if Gemini returns a hint containing a code block, the guardrail rejects it and the user gets the safe local hint instead, with `guard_rejected: "code block in a hint answer (would leak the solution)"` recorded in the debug state.

### Full execution trace
See [`examples/sample_session.md`](examples/sample_session.md) for a full session showing the route, tool calls, approval pause and replies for each turn. Regenerate it with `python examples/run_demo.py > examples/sample_session.md`.

## Requirements
- Python 3.10+
- A Gemini API key from Google AI Studio
- Internet access for Gemini calls and the catalog refresh

Gemini currently has free-tier models; this project defaults to `gemini-3.5-flash`. You can override the model with `GEMINI_MODEL`. See Google's current pricing/model documentation before submission.

## Setup on Windows

1. Create a Gemini API key.
2. Set it as a user environment variable:

```text
GEMINI_API_KEY=your_key_here
```

Do **not** commit the real key. `.env` is in `.gitignore`, and `.env.example` shows the format.

3. Open a new Command Prompt and run:

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python refresh_catalog.py
python smoke_test.py
python -m pytest -q
streamlit run app.py
```

The app opens at the Streamlit local URL shown in the terminal.

## LangGraph features used

### 1. LangGraph graph
`graph.py` defines a typed `State`, a compiled `StateGraph`, a router, multiple nodes, and conditional edges. The Streamlit UI exposes the Mermaid graph under **View LangGraph**.

### 2. State management and reducers
- `messages` uses `add_messages`.
- `topics` uses `operator.add`.
- `InMemorySaver` provides short-term state keyed by `thread_id`.
- The sidebar lets the user switch between independent interview threads.

### 3. Trimming and filtering
Before every Gemini model call, `context()` filters empty/non-chat messages and trims the history to a token budget. The UI shows message and approximate-token counts before vs. after trimming.

### 4. Short-term and long-term memory
- Short-term: LangGraph checkpointer + `thread_id`.
- Long-term: `InMemoryStore` profile containing useful facts such as name, preferred language, and weak topic. The profile is shared across threads.

## A2Z question catalog
The app selects interview problems only from its locally loaded 474-question catalog. Users do not need to mention the source sheet.

Run `python refresh_catalog.py` to refresh the catalog when connected to the internet. The app also has a bundled seed fallback.

The app uses problem titles/metadata rather than copying full problem statements, editorials, or solution text.

## Demo flow
1. `Hi, my name is Rahul. I prefer Java.`
2. `Let's practice linked list.`
3. `Let's do it in Python.`
4. `What is the question?`
5. `Give me a small hint.`
6. `I still don't understand.`
7. Explain your approach.
8. Ask `What's the time complexity?`
9. Create a new thread and ask `What do you remember about me?`
10. Open **View LangGraph**, **Context control** and **🛠️ Tool calls** to see the mechanics.

Step 1 pauses for approval. Click **Approve** to save your name and language to the profile.

## API fallback
If `GEMINI_API_KEY` is missing or Gemini is temporarily unavailable, CodeCoach falls back to its local coaching logic so the UI can still start. Gemini mode gives the most natural coaching. Fallback mode is what the tests and sample trace use.

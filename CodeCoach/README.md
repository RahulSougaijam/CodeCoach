# CodeCoach — LangGraph + Gemini Coding Interview Coach

CodeCoach is a Streamlit chat application built to demonstrate the four LangGraph topics in Module 2. It uses Gemini for natural-language understanding/coaching, while the local 474-question catalog remains the source of truth for interview problems.

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

Do **not** put the real key in this ZIP or commit it to source control.

3. Open a new Command Prompt and run:

```cmd
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python refresh_catalog.py
python smoke_test.py
streamlit run app.py
```

The app opens at the Streamlit local URL shown in the terminal.

## The four assignment topics

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
10. Open **View LangGraph** and **Context control** to demonstrate the assignment mechanics.

## API fallback
If `GEMINI_API_KEY` is missing or Gemini is temporarily unavailable, CodeCoach falls back to its local coaching logic so the UI can still start. The assignment demonstration should use the Gemini-connected mode because that is the intended natural-language coaching path.

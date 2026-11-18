from __future__ import annotations

import operator
import os
import re
import uuid
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AIMessage, AnyMessage, HumanMessage
from langchain_core.messages.utils import count_tokens_approximately, trim_messages
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.store.memory import InMemoryStore

from llm import available as llm_available, classify_request, generate_response

from question_bank import (
    choose_problem,
    concise_solution,
    feedback_variants,
    hints,
    infer_difficulty,
    infer_topic,
    load_bank,
    problem_card,
)

BANK, BANK_SOURCE = load_bank()


class State(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    topics: Annotated[list[str], operator.add]
    intent: str
    questions: int
    current_problem: str
    current_problem_meta: dict[str, Any]
    hint_level: int
    solved: int
    attempted: list[str]
    language: str
    requested_difficulty: str
    debug: dict[str, Any]


checkpointer = InMemorySaver()
store = InMemoryStore()


def text_of(message: AnyMessage) -> str:
    value = message.content
    return value if isinstance(value, str) else str(value)


def approx(messages: list[AnyMessage]) -> int:
    return count_tokens_approximately(messages) if messages else 0


def profile() -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for item in store.search(("demo_user", "profile"), limit=10):
        if isinstance(item.value, dict):
            merged.update(item.value)
    return merged


def learn_profile(text: str) -> dict[str, Any]:
    """Extract only simple, useful preferences and save them in long-term memory."""
    p = profile()
    changed = False

    match = re.search(
        r"\bmy name is\s+([A-Za-z][A-Za-z .'-]{0,35}?)(?=\s+and\b|\s+i\b|[.!?]|$)",
        text,
        re.I,
    )
    if match:
        p["name"] = match.group(1).strip()
        changed = True

    match = re.search(
        r"\b(?:i\s+(?:use|prefer)|my preferred language is|use)\s+"
        r"(java|python|javascript|c\+\+|c#)\b",
        text,
        re.I,
    )
    if match:
        p["preferred_language"] = canonical_language(match.group(1))
        changed = True

    match = re.search(
        r"\b(?:i(?:'m| am)\s+weak at|i\s+struggle with|weak in)\s+"
        r"([A-Za-z0-9 +#.-]{2,35}?)(?:[.!?]|$)",
        text,
        re.I,
    )
    if match:
        p["weak_topic"] = match.group(1).strip()
        changed = True

    if changed:
        store.put(("demo_user", "profile"), "main", p)
    return p


def canonical_language(value: str) -> str:
    low = value.lower().strip()
    mapping = {
        "java": "Java",
        "python": "Python",
        "javascript": "JavaScript",
        "c++": "C++",
        "c#": "C#",
    }
    return mapping.get(low, value.title())


def requested_language(text: str) -> str | None:
    low = text.lower()
    patterns = [
        r"\b(?:switch|change|move|shift|use|write|solve|code)\s+(?:to|in|with)\s+(java|python|javascript|c\+\+|c#)\b",
        r"\b(?:use|choose|pick)\s+(java|python|javascript|c\+\+|c#)\b",
        r"\b(?:java|python|javascript|c\+\+|c#)\s+(?:please|instead|from now on)\b",
        r"\b(?:i want|i'd like|i would like)\s+(?:to use|to solve in|to code in)\s+(java|python|javascript|c\+\+|c#)\b",
        r"\b(?:switch|change)\s+(?:my )?(?:coding )?language\s+(?:to\s+)?(java|python|javascript|c\+\+|c#)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, low)
        if match:
            return canonical_language(match.group(1))
    return None


def topic_from_text(text: str) -> str | None:
    return infer_topic(text)


def is_repeat_question(text: str) -> bool:
    low = re.sub(r"[^a-z0-9 ]+", " ", text.lower())
    low = re.sub(r"\s+", " ", low).strip()
    phrases = [
        "what is the question",
        "whats the question",
        "what was the question",
        "what was the problem",
        "repeat the question",
        "repeat the problem",
        "show the question again",
        "show me the question again",
        "can you repeat the question",
        "can you repeat the problem",
        "remind me of the question",
        "remind me what the problem is",
    ]
    return any(p in low for p in phrases)


def is_new_problem_request(text: str) -> bool:
    low = text.lower().strip()
    return any(
        phrase in low
        for phrase in [
            "new problem",
            "another problem",
            "next problem",
            "different problem",
            "give me a problem",
            "give me another",
            "ask me a problem",
            "give me a question",
            "practice a problem",
            "quiz me",
            "mock interview",
            "start a problem",
        ]
    )


def detect_intent(text: str, state: dict[str, Any] | None = None) -> str:
    """State-aware priority router. Specific actions win over generic words."""
    state = state or {}
    low = text.lower().strip()
    has_problem = bool(state.get("current_problem"))

    if requested_language(text) or low in {"java", "python", "javascript", "c++", "c#"}:
        return "language"
    if is_repeat_question(text) or (has_problem and low in {"question", "the question", "problem", "the problem", "repeat it", "repeat that"}):
        return "repeat_problem" if has_problem else "conversation"
    if any(x in low for x in ["another hint", "one more hint", "give me a hint", "hint", "clue"]):
        return "hint"
    if any(x in low for x in ["show me the solution", "give me the solution", "show solution", "solution", "show me the answer", "full code", "solve it for me"]):
        return "solution"
    if any(x in low for x in ["review my code", "check my code", "debug my code", "fix my code", "code review", "find the bug", "what is wrong with my code"]):
        return "debug"
    if "```" in low or "public class" in low or "public static void" in low:
        return "debug"
    if any(x in low for x in ["time complexity", "space complexity", "big o", "big-o", "complexity", "optimize this"]):
        return "complexity"
    if any(x in low for x in ["progress", "stats", "how am i doing", "what have i practiced", "completed"]):
        return "progress"
    if is_new_problem_request(text):
        return "practice"

    topic = topic_from_text(text)
    if topic:
        return "practice"

    if any(x in low for x in ["explain", "teach me", "how does", "difference between"]):
        return "explain"
    if low in {"hi", "hello", "hey", "hiya", "yo", "thanks", "thank you", "ok", "okay"}:
        return "conversation"

    # Context-aware follow-ups are not automatically treated as solution attempts.
    if has_problem:
        if any(x in low for x in [
            "what do you think",
            "is my approach",
            "my approach",
            "i think",
            "my idea",
            "why is that",
            "why?",
            "why did",
            "i don't understand",
            "i dont understand",
            "i am stuck",
            "i'm stuck",
            "can you explain that",
            "explain that",
            "can you clarify",
            "what does that mean",
        ]):
            return "attempt"
        # A message that looks like a normal question should be explained, not treated as code.
        if low.endswith("?") or low.startswith(("can you ", "could you ", "why ", "how ")):
            return "explain"
        # Free-form algorithm descriptions are evaluated as an attempt.
        return "attempt"

    return "conversation"


def router(state: State) -> dict[str, Any]:
    text = text_of(state["messages"][-1])
    trimmed, debug = context(state)
    history = [{"role": "human" if isinstance(m, HumanMessage) else "assistant", "content": text_of(m)} for m in trimmed]
    current = state.get("current_problem_meta") or {}
    current_language = state.get("language") or profile().get("preferred_language", "Java")

    if llm_available():
        try:
            decision = classify_request(
                text, history, current, current_language, profile(), state.get("topics", [])[-5:]
            )
            intent = decision.get("intent", "conversation")
            if intent == "greeting":
                intent = "conversation"
            topic = decision.get("topic")
            difficulty = decision.get("difficulty")
            language = decision.get("language")
            if language:
                language = canonical_language(str(language))
            debug.update({"route": intent, "llm_router": True})
            return {
                "intent": intent,
                "topics": [topic] if topic else [],
                "requested_difficulty": str(difficulty).lower() if difficulty else "",
                "language": language or current_language,
                "debug": debug,
            }
        except Exception as exc:
            debug.update({"llm_router": False, "llm_router_error": str(exc)[:240]})

    intent = detect_intent(text, state)
    detected = topic_from_text(text)
    debug.update({"route": intent, "llm_router": False})
    return {
        "intent": intent,
        "topics": [detected] if detected else [],
        "requested_difficulty": infer_difficulty(text) or "",
        "debug": debug,
    }


def context(state: State) -> tuple[list[AnyMessage], dict[str, Any]]:
    all_messages = state.get("messages", [])
    filtered = [
        m for m in all_messages
        if isinstance(m, (HumanMessage, AIMessage)) and text_of(m).strip()
    ]
    trimmed = trim_messages(
        filtered,
        strategy="last",
        token_counter=count_tokens_approximately,
        max_tokens=1600,
        start_on="human",
        end_on=("human", "ai"),
    )
    if not trimmed:
        trimmed = filtered[-4:]
    debug = dict(state.get("debug", {}))
    debug.update({
        "before_count": len(all_messages),
        "after_count": len(trimmed),
        "filtered_count": len(all_messages) - len(filtered),
        "before_tokens": approx(filtered),
        "after_tokens": approx(trimmed),
        "route": state.get("intent", "waiting"),
        "questions": state.get("questions", 0),
        "bank_size": len(BANK),
        "bank_source": BANK_SOURCE,
    })
    return trimmed, debug


def current_meta(state: State) -> dict[str, Any]:
    return state.get("current_problem_meta") or {}


def choose_for_request(state: State, text: str) -> dict[str, Any] | None:
    topic = (state.get("topics") or [])[-1] if state.get("topics") else None
    topic = topic or topic_from_text(text)
    difficulty = state.get("requested_difficulty") or infer_difficulty(text)
    exclude = state.get("attempted", [])
    return choose_problem(BANK, topic, difficulty, exclude)


def evaluate_attempt(state: State, text: str) -> str:
    q = current_meta(state)
    if not q:
        return "Tell me your approach to the current problem first."

    p = (q.get("problem_name", "") + " " + q.get("topic", "")).lower()
    low = text.lower()
    expected: list[str]
    if "hash" in p or "frequency" in p:
        expected = ["hashmap", "hash map", "hashset", "frequency"]
    elif "binary search" in p or "koko" in p or "rotated" in p:
        expected = ["binary search"]
    elif "tree" in p or "bst" in p:
        expected = ["dfs", "bfs", "recursion", "queue", "stack"]
    elif "graph" in p:
        expected = ["bfs", "dfs", "adjacency", "dijkstra", "topological", "union find"]
    elif "dynamic programming" in p:
        expected = ["dp", "memoization", "tabulation", "state", "recurrence"]
    elif "stack" in p:
        expected = ["stack", "monotonic"]
    elif "sliding" in p:
        expected = ["sliding window", "two pointer"]
    elif "greedy" in p:
        expected = ["greedy", "sort", "sorting"]
    elif "recursion" in p:
        expected = ["recursion", "backtracking"]
    else:
        expected = ["sort", "two pointer", "hashmap", "hash map", "binary search"]

    if any(x in low for x in expected):
        return random_choice(feedback_variants(q, "good"))
    if any(x in low for x in ["brute", "nested loop", "two loops", "for loop"]):
        return random_choice(feedback_variants(q, "partial"))
    return random_choice(feedback_variants(q, "stuck"))


def random_choice(items: list[str]) -> str:
    import random
    return random.choice(items)


def explain_concept(text: str, state: State) -> str:
    language = profile().get("preferred_language", state.get("language", "Java"))
    topic = topic_from_text(text)
    if topic:
        examples = {
            "arrays": "An array stores values in indexed positions, so reading `a[i]` is constant time. The key interview skill is choosing whether one pass, sorting, or an auxiliary structure removes repeated work.",
            "strings": "A Java String is immutable. For interview problems, focus on character access, frequency counting, two pointers, sliding windows, and the cost of creating new strings.",
            "linkedlist": "A linked list stores nodes connected by references. The important interview ideas are pointer movement, careful null handling, and changing links without losing the rest of the list.",
            "recursion": "Recursion solves a problem by defining a smaller version of the same problem. Every recursive solution needs a base case and a step that moves toward it.",
            "binary search": "Binary search repeatedly removes half of a sorted or monotonic search space. The critical part is defining a correct predicate and proving that the remaining half still contains every possible answer.",
            "stack & queues": "A stack is LIFO and a queue is FIFO. Many interview problems use them to control the order in which unresolved work is processed.",
            "graphs": "A graph represents states and connections. BFS, DFS, shortest-path algorithms, and union-find are chosen according to what the edges and the question require.",
            "binary trees": "A binary tree node has at most two children. Most tree problems become simpler when you define what one recursive call should return for one node.",
            "bst": "A BST maintains an ordering: values in the left subtree are smaller and values in the right subtree are larger, subject to the duplicate convention. That ordering enables efficient search when the tree is balanced.",
            "dynamic programming": "DP stores answers to overlapping subproblems. Start by defining the state, then the transition, then base cases; only afterward choose memoization or tabulation.",
            "heaps": "A heap keeps the smallest or largest element at the top. It is useful when you repeatedly need the next best candidate without fully sorting everything.",
            "greedy": "A greedy algorithm commits to a locally attractive choice. The interview challenge is proving that the choice cannot destroy an optimal future solution.",
            "tries": "A trie stores strings character by character in a tree of prefixes. It is useful when prefix operations matter and the alphabet is manageable.",
            "bit manipulation": "Bit manipulation works directly with binary representations. AND masks bits, OR sets bits, XOR cancels equal bits, and shifts move bit positions.",
            "sorting": "Sorting can expose useful order so a later scan becomes simple. Always account for the sorting cost when analyzing the whole algorithm.",
        }
        body = examples.get(topic, "Start by defining the input, output, invariant, and the repeated work you need to eliminate.")
        return f"### 💡 {topic.title()}\n\n{body}\n\n**Language:** {language}. If you want, I can teach this step-by-step and then give you a related interview problem."

    return f"Tell me the concept you want explained. I can teach it with a small **{language}** example, then connect it to an interview problem."


def local_response(state: State, intent: str, text: str, selected_q: dict[str, Any] | None = None) -> str:
    low = text.lower().strip()
    p = learn_profile(text)
    language = p.get("preferred_language", state.get("language", "Java"))

    if intent == "conversation":
        name = p.get("name", "")
        if low in {"thanks", "thank you"}:
            return "You're welcome! Want to keep practicing?"
        if low in {"hi", "hello", "hey", "hiya", "yo"}:
            return f"Hey {name + ' ' if name else ''}👋 What are you working on today — a problem, a hint, {language} code review, Big-O, or progress?"
        if "what can you do" in low:
            return "I can run an interview using the loaded DSA question bank, give progressive hints, discuss your approach, review code, explain complexity, switch languages, and remember useful profile details across interview threads."
        return "Sure. Tell me what you want to practice, or ask me for a problem."

    if intent == "language":
        new_language = requested_language(text) or language
        learn_profile(f"I prefer {new_language}")
        if state.get("current_problem"):
            return f"Absolutely — we'll use **{new_language}** from now on. The current problem stays the same; only the coding language changes."
        return f"Absolutely — I'll use **{new_language}** for your interview practice from now on."

    if intent == "repeat_problem":
        q = current_meta(state)
        if not q:
            return "There isn't an active problem yet. Ask me for one and I'll start the interview."
        return problem_card(q) + f"\n\n**Language:** {language}"

    if intent == "practice":
        q = selected_q or choose_for_request(state, text)
        if q is None:
            topic = topic_from_text(text)
            difficulty = infer_difficulty(text)
            if topic and difficulty:
                return f"I couldn't find a **{difficulty}** question for **{topic}** in the loaded catalog. Try another difficulty or ask for another problem."
            if topic:
                return f"I couldn't find a matching question for **{topic}** in the loaded catalog. Try another topic or refresh the catalog."
            return "I couldn't find a matching problem in the loaded catalog. Try another topic or difficulty."
        return problem_card(q) + f"\n\n**Language:** {language}"

    if intent == "hint":
        q = current_meta(state)
        if not q:
            return "I don't have an active problem yet. Ask me for a problem first."
        level = state.get("hint_level", 0)
        hs = hints(q, level)
        if level >= len(hs):
            return "You've used the progressive hints. I can give you the solution direction or the implementation if you want."
        return f"### 💡 Hint {level + 1}\n\n{hs[level]}"

    if intent == "solution":
        q = current_meta(state)
        if not q:
            return "Give me a problem first, then I can walk through its solution."
        return concise_solution(q) + f"\n\n**Implementation language:** {language}"

    if intent == "debug":
        return code_review(text, language)

    if intent == "complexity":
        q = current_meta(state)
        if q:
            return f"For **{q['problem_name']}**, give me your approach or paste your code. I’ll identify the dominant operation, count how often it runs, and separate auxiliary space from input space."
        return "Paste your code or describe your approach and I'll analyze time and space complexity."

    if intent == "progress":
        attempted = state.get("attempted", [])
        return (
            "### 📊 Progress\n\n"
            f"- Problems started in this thread: **{len(attempted)}**\n"
            f"- Solutions revealed: **{state.get('solved', 0)}**\n"
            f"- Topics seen: **{', '.join(sorted(set(state.get('topics', [])))) or 'none yet'}**\n"
            f"- Preferred language: **{p.get('preferred_language', language)}**\n"
            f"- Weak topic: **{p.get('weak_topic', 'not recorded')}**\n\n"
            "Your interview state is tied to this thread, while your profile is shared across threads."
        )

    if intent == "explain":
        if state.get("current_problem") and not topic_from_text(text):
            q = current_meta(state)
            if q:
                return f"Sure. For **{q['problem_name']}**, tell me which part you want clarified — the goal, an example, the key idea, or the reasoning behind the last hint."
        return explain_concept(text, state)

    if intent == "attempt":
        return evaluate_attempt(state, text)

    return "I can help with practice, progressive hints, solutions, code review, complexity, explanations, language changes, and progress."


def code_review(text: str, language: str) -> str:
    code = text
    issues: list[str] = []
    low = code.lower()
    if language == "Java" and "==" in code and "String" in code and ".equals" not in code:
        issues.append("If you're comparing Java Strings, use `.equals()` rather than `==` for content comparison.")
    if re.search(r"for\s*\([^;]*;[^;]*;[^)]*\)\s*\{[^}]*for\s*\(", code, re.S):
        issues.append("I see nested loops; check whether the approach is O(n²) and whether a HashMap, sorting, two pointers, or another structure removes repeated work.")
    if "HashMap" in code and "containsKey" not in code and ".get(" not in code:
        issues.append("You create a HashMap; verify that your lookup/update logic actually uses the stored values.")
    if "ArrayList" in code and "remove(0)" in code:
        issues.append("Removing index 0 from an ArrayList shifts the remaining elements; a Queue/Deque may be a better fit.")
    if "while(true)" in code and "break" not in code:
        issues.append("Check the termination condition: this loop has no visible break, so it may not terminate.")
    if "return -1" in code:
        issues.append("Returning -1 is fine when the method contract uses it as 'not found'; make sure every successful path returns before it.")
    if not issues:
        issues.append("I don't see an obvious issue from these local checks. Test empty input, one-element input, duplicates, boundaries, and worst-case size next.")
    return (
        f"### 🐛 {language} code review\n\n"
        + "\n".join(f"- {issue}" for issue in issues)
        + "\n\n**Next:** tell me the intended complexity and I’ll challenge the approach like an interviewer."
    )


def model_node(state: State) -> dict[str, Any]:
    intent = state.get("intent", "conversation")
    text = text_of(state["messages"][-1])
    attempted = list(state.get("attempted", []))
    questions = state.get("questions", 0)
    solved = state.get("solved", 0)
    meta = dict(state.get("current_problem_meta") or {})
    current = state.get("current_problem", "")
    hint_level = state.get("hint_level", 0)
    language = state.get("language") or profile().get("preferred_language", "Java")
    selected_q = None

    if intent == "practice":
        selected_q = choose_for_request(state, text)
        if selected_q is not None:
            meta = selected_q
            current = selected_q["problem_name"]
            hint_level = 0
            if current.lower() not in [x.lower() for x in attempted]:
                attempted.append(current)
                questions += 1

    if intent == "language":
        new_language = requested_language(text) or language
        if state.get("language") and state.get("language") != "Java":
            new_language = state.get("language") if not new_language else new_language
        language = new_language
        learn_profile(f"I prefer {language}")

    p = learn_profile(text)

    # If the router classified a language but the exact wording was not captured by
    # the legacy regex, trust the LLM's state update already written by router.
    if state.get("language") and intent == "language":
        language = state.get("language")

    answer = None
    if llm_available():
        try:
            trimmed, _ = context(state)
            history = [{"role": "human" if isinstance(m, HumanMessage) else "assistant", "content": text_of(m)} for m in trimmed]
            response_meta = meta if meta else None
            max_hints = len(hints(response_meta, 0)) if response_meta else 0
            answer = generate_response(
                text, history, intent, response_meta, language, p, hint_level, max_hints
            )
        except Exception as exc:
            answer = None
            llm_error = str(exc)[:240]
        else:
            llm_error = ""
    else:
        llm_error = "API key not configured; using local fallback."

    if not answer:
        answer = local_response(state, intent, text, selected_q)

    if intent == "hint":
        q = current_meta(state)
        if q and hint_level < len(hints(q, 0)):
            hint_level += 1
    elif intent == "solution" and current_meta(state):
        solved += 1

    preview_state = dict(state)
    preview_state["messages"] = list(state.get("messages", [])) + [AIMessage(content=answer)]
    _, debug = context(preview_state)
    debug.update({
        "bank_source": BANK_SOURCE,
        "bank_size": len(BANK),
        "questions": questions,
        "language": language,
        "llm_response": bool(llm_available() and answer),
        "model": os.getenv("GEMINI_MODEL", "gemini-3.5-flash"),
    })
    if llm_error:
        debug["llm_error"] = llm_error

    return {
        "messages": [AIMessage(content=answer)],
        "questions": questions,
        "current_problem": current,
        "current_problem_meta": meta,
        "hint_level": hint_level,
        "attempted": attempted,
        "solved": solved,
        "language": language,
        "requested_difficulty": state.get("requested_difficulty", ""),
        "debug": debug,
    }


builder = StateGraph(State)
builder.add_node("router", router)
NODE_NAMES = [
    "conversation", "practice", "repeat_problem", "hint", "solution",
    "debug", "complexity", "progress", "explain", "attempt", "language",
]
for node_name in NODE_NAMES:
    builder.add_node(node_name, model_node)

builder.add_edge(START, "router")
builder.add_conditional_edges(
    "router",
    lambda state: state["intent"],
    {name: name for name in NODE_NAMES},
)
for node_name in NODE_NAMES:
    builder.add_edge(node_name, END)

graph = builder.compile(checkpointer=checkpointer, store=store)


def create_thread_id() -> str:
    return str(uuid.uuid4())


def _state(thread_id: str) -> dict[str, Any]:
    try:
        return graph.get_state({"configurable": {"thread_id": thread_id}}).values or {}
    except Exception:
        return {}


def get_thread(thread_id: str) -> list[dict[str, str]]:
    result = []
    for message in _state(thread_id).get("messages", []):
        result.append({
            "role": "human" if isinstance(message, HumanMessage) else "assistant",
            "content": text_of(message),
        })
    return result


def get_debug(thread_id: str) -> dict[str, Any]:
    return _state(thread_id).get("debug", {})


def get_profile() -> dict[str, Any]:
    return profile()


def get_thread_info(thread_id: str) -> dict[str, Any]:
    state = _state(thread_id)
    return {
        "current_problem": state.get("current_problem", ""),
        "current_problem_meta": state.get("current_problem_meta", {}),
        "hint_level": state.get("hint_level", 0),
        "questions": state.get("questions", 0),
        "solved": state.get("solved", 0),
        "attempted": state.get("attempted", []),
        "topics": sorted(set(state.get("topics", []))),
        "language": state.get("language", profile().get("preferred_language", "Java")),
        "requested_difficulty": state.get("requested_difficulty", ""),
    }


def graph_mermaid() -> str:
    return """graph TD
START([START]) --> ROUTER[Intent Router]
ROUTER -->|conversation| CHAT[Conversation]
ROUTER -->|practice| PRACTICE[Practice]
ROUTER -->|repeat_problem| REPEAT[Repeat Problem]
ROUTER -->|hint| HINT[Progressive Hint]
ROUTER -->|solution| SOLUTION[Solution]
ROUTER -->|debug| DEBUG[Code Review]
ROUTER -->|complexity| BIGO[Complexity]
ROUTER -->|progress| PROGRESS[Progress]
ROUTER -->|explain| EXPLAIN[Explain]
ROUTER -->|attempt| ATTEMPT[Approach Feedback]
ROUTER -->|language| LANGUAGE[Language Change]
CHAT --> END([END])
PRACTICE --> END
REPEAT --> END
HINT --> END
SOLUTION --> END
DEBUG --> END
BIGO --> END
PROGRESS --> END
EXPLAIN --> END
ATTEMPT --> END
LANGUAGE --> END
"""

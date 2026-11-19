from __future__ import annotations

import streamlit as st
from graph import create_thread_id, get_debug, get_profile, get_thread, get_thread_info, graph_mermaid, pending_approval, resume, send_message, BANK, BANK_SOURCE
from llm import available as llm_available

st.set_page_config(page_title="CodeCoach", page_icon="💻", layout="wide")

st.markdown("""
<style>
.stApp{background:#080d18}.hero{padding:26px;border:1px solid #263753;border-radius:20px;background:linear-gradient(135deg,#131f36,#0c1424);margin-bottom:18px}.hero h1{margin:0;font-size:2.2rem}.hero p{color:#94a3bf}.badge{display:inline-block;background:#192844;color:#b9d0ff;border-radius:999px;padding:5px 10px;font-size:.72rem;margin-right:5px}.card{border:1px solid #273752;background:#10192b;border-radius:14px;padding:13px;margin-bottom:9px}.small{color:#8d9bb5;font-size:.78rem}.route{font-family:monospace;background:#101a2d;padding:10px;border-radius:9px}.stButton button{border-radius:10px}
</style>
""", unsafe_allow_html=True)

if "threads" not in st.session_state: st.session_state.threads={"Interview 1":create_thread_id()}
if "active" not in st.session_state: st.session_state.active="Interview 1"

with st.sidebar:
    st.markdown("## 💻 CodeCoach")
    st.caption("LangGraph · Gemini Coach · A2Z Interview Practice")
    if llm_available():
        st.success("Gemini API connected")
    else:
        st.warning("Gemini API key not detected — local fallback is active")
    st.caption(f"Question catalog: **{len(BANK)}** loaded · {BANK_SOURCE}")
    st.divider()
    names=list(st.session_state.threads)
    chosen=st.selectbox("Interview thread",names,index=names.index(st.session_state.active))
    if chosen!=st.session_state.active: st.session_state.active=chosen; st.rerun()
    if st.button("＋ New interview",width="stretch"):
        n=len(st.session_state.threads)+1; st.session_state.threads[f"Interview {n}"]=create_thread_id(); st.session_state.active=f"Interview {n}"; st.rerun()
    st.divider()
    st.markdown("### Quick actions")
    quick={"🧩 New problem":"Give me a medium problem.","🌳 Tree problem":"Give me a medium binary tree problem.","💡 Hint":"Give me a hint.","🧠 Solution":"Show me the solution.","🐛 Review Java":"Review my Java code.","⏱️ Big-O":"Analyze the time and space complexity.","📊 Progress":"Show me my progress."}
    for label,value in quick.items():
        if st.button(label,width="stretch"): st.session_state.pending=value; st.rerun()

thread_id=st.session_state.threads[st.session_state.active]
messages=get_thread(thread_id); info=get_thread_info(thread_id); debug=get_debug(thread_id); profile=get_profile()

st.markdown("""
<div class="hero"><span class="badge">LANGGRAPH</span><span class="badge">GEMINI API</span><span class="badge">474-QUESTION CATALOG</span><span class="badge">MEMORY</span><span class="badge">PROGRESSIVE HINTS</span><h1>CodeCoach</h1><p>A reliable coding-interview coach powered by LangGraph.</p></div>
""",unsafe_allow_html=True)

c1,c2,c3,c4,c5=st.columns(5)
vals=[("Questions",info.get("questions",0)),("Solved",info.get("solved",0)),("Catalog",len(BANK)),("Context",f"{debug.get('before_count',0)} → {debug.get('after_count',0)}"),("Hint",info.get("hint_level",0))]
for col,(a,b) in zip([c1,c2,c3,c4,c5],vals):
    with col: st.markdown(f'<div class="card" style="text-align:center"><b>{b}</b><br><span class="small">{a}</span></div>',unsafe_allow_html=True)

left,right=st.columns([2.15,1],gap="large")
with left:
    st.markdown("### Interview room")
    if not messages: st.info("Try: “Hi, my name is Rahul. I prefer Java and I'm weak at recursion.”")
    for m in messages:
        with st.chat_message("user" if m["role"]=="human" else "assistant",avatar="🧑‍💻" if m["role"]=="human" else "🤖"): st.markdown(m["content"])
    # Human-in-the-loop: the graph is paused until the user approves or rejects.
    approval=pending_approval(thread_id)
    if approval:
        with st.container(border=True):
            st.markdown(f"**🔐 {approval.get('question','Approve?')}**")
            for k,v in approval.get("changes",{}).items(): st.markdown(f"- **{k.replace('_',' ').title()}:** {v}")
            a1,a2=st.columns(2)
            if a1.button("✅ Approve",width="stretch"): resume(thread_id,True); st.rerun()
            if a2.button("❌ Reject",width="stretch"): resume(thread_id,False); st.rerun()
    prompt=st.chat_input("Talk to your interviewer…")
    pending=st.session_state.pop("pending",None)
    if pending and not prompt: prompt=pending
    if prompt:
        success = False
        with st.spinner("CodeCoach is thinking…"):
            try:
                send_message(thread_id, prompt)
                success = True
            except Exception as exc:
                st.error(f"CodeCoach encountered an error: {type(exc).__name__}: {exc}")
        if success:
            st.rerun()

with right:
    st.markdown("### 🧠 Persistent profile")
    if profile:
        for k,v in profile.items(): st.markdown(f'<div class="card"><b>{k.replace("_"," ").title()}</b><br><span class="small">{v}</span></div>',unsafe_allow_html=True)
    else: st.caption("The coach remembers useful details such as name, preferred language and weak topics.")
    st.markdown("### ✂️ Context control")
    before=debug.get("before_tokens",0); after=debug.get("after_tokens",0)
    st.progress(min(after/max(before,1),1.0)); st.caption(f"Messages: **{debug.get('before_count',0)} → {debug.get('after_count',0)}**")
    st.caption(f"Approx. tokens: **{before} → {after}**")
    st.markdown("### 🔀 Conditional route")
    st.markdown(f'<div class="route">{debug.get("route","WAITING").upper()}</div>',unsafe_allow_html=True)
    with st.expander("Current interview state"):
        st.caption(f"Language: {info.get('language', 'Java')}")
        st.write("**Problem:**",info.get("current_problem") or "None")
        meta=info.get("current_problem_meta",{})
        if meta: st.write("**Topic:**",meta.get("topic"),"· **Difficulty:**",meta.get("difficulty"))
        st.write("**Hint level:**",info.get("hint_level",0))
    with st.expander("🛠️ Tool calls (last turn)"):
        calls=debug.get("tool_calls",[])
        if calls: st.json(calls)
        else: st.caption("No tool calls in the last turn.")
        if debug.get("guard_rejected"): st.warning(f"Guardrail rejected the LLM answer: {debug['guard_rejected']}")
    with st.expander("View LangGraph"): st.code(graph_mermaid(),language="mermaid")

with st.expander("📚 Question bank"):
    st.caption("The app only selects questions from its loaded catalog. The user never needs to mention the source sheet.")
    topics=sorted({q["topic"] for q in BANK}); st.write("Topics:",", ".join(topics))
    st.dataframe([{"#":q["id"],"Problem":q["problem_name"],"Topic":q["topic"],"Difficulty":q["difficulty"]} for q in BANK],width="stretch",height=430)

with st.expander("🎓 Assignment mapping"):
    st.markdown("""
**Topic 1 — LangGraph:** compiled typed `StateGraph`, router + specialized nodes, conditional edge, and graph visualization.

**Topic 2 — State management:** `messages` uses `add_messages`; `topics` uses `operator.add`; `InMemorySaver` is keyed by `thread_id`; the sidebar switches threads.

**Topic 3 — Trimming/filtering:** empty/non-chat messages are filtered and the conversation is trimmed before every Gemini model call. The UI shows messages and approximate tokens before vs. after trimming.

**Topic 4 — Memory:** short-term memory uses the checkpointer; long-term profile memory uses `InMemoryStore` and is shared across interview threads.

**LLM:** Gemini is used for natural-language intent understanding and interview coaching. The 474-question A2Z catalog remains local and controls which problems can be selected.

**Security:** the API key is read from the `GEMINI_API_KEY` environment variable and is not stored in the project.
""")

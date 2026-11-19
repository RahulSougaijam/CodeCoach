"""Human-in-the-loop: long-term memory is only written after approval."""
from graph import create_thread_id, get_profile, get_thread, pending_approval, resume, send_message


def test_profile_waits_for_approval_then_saves():
    thread = create_thread_id()
    send_message(thread, "Hi, my name is Rahul and I'm weak at recursion.")
    payload = pending_approval(thread)
    assert payload["changes"] == {"name": "Rahul", "weak_topic": "recursion"}
    assert get_profile() == {}  # nothing saved yet

    resume(thread, True)
    assert get_profile()["name"] == "Rahul"
    assert pending_approval(thread) is None
    assert "Saved to your profile" in get_thread(thread)[-1]["content"]


def test_rejected_profile_is_not_saved():
    thread = create_thread_id()
    send_message(thread, "my name is Rahul")
    resume(thread, False)
    assert get_profile() == {}
    assert "won't save" in get_thread(thread)[-1]["content"]


def test_new_message_while_pending_counts_as_reject():
    thread = create_thread_id()
    send_message(thread, "my name is Rahul")
    send_message(thread, "Let's practice arrays.")
    assert get_profile() == {}
    assert pending_approval(thread) is None


def test_explicit_language_switch_needs_no_approval():
    thread = create_thread_id()
    send_message(thread, "switch to python")
    assert pending_approval(thread) is None
    assert get_profile()["preferred_language"] == "Python"


def test_profile_shared_across_threads_after_approval():
    t1 = create_thread_id()
    send_message(t1, "my name is Rahul")
    resume(t1, True)
    t2 = create_thread_id()
    send_message(t2, "hi")
    assert get_profile()["name"] == "Rahul"

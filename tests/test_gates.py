"""Locks open on a recorded human decision and on nothing else. A critic score,
however high, is not a decision."""

import pytest

from studio.core.state import Store

GATE = "LOCK1_SCRIPT"


@pytest.fixture
def store(tmp_path):
    s = Store(tmp_path / "t.db")
    s.create_episode("ep", "ser", 1, "p")
    yield s
    s.close()


def test_agent_score_alone_does_not_open_a_lock(store):
    store.record_gate("ep", GATE, 1, {"total": 99.0}, decided_by=None)
    store.record_gate("ep", GATE, 2, {"total": 99.9}, decided_by="agent")
    assert store.gate_is_open("ep", GATE) is False


def test_human_decision_opens_the_lock(store):
    store.record_gate("ep", GATE, 1, {"total": 71.0})
    store.record_gate("ep", GATE, 2, {"total": 71.0}, decided_by="pawan")
    assert store.gate_is_open("ep", GATE) is True


def test_loop_terminates_after_three_iterations(store):
    """A rubric stuck below threshold must escalate, never spin."""
    threshold, max_iter = 80.0, 3
    scores = [61.0, 63.0, 64.0]
    escalated = False
    for i, sc in enumerate(scores, start=1):
        store.record_gate("ep", GATE, i, {"total": sc})
        if sc >= threshold:
            break
        if store.gate_iterations("ep", GATE) >= max_iter:
            escalated = True
            break
    assert escalated, "must escalate to a human on the fourth pass"
    assert store.gate_iterations("ep", GATE) == 3
    assert store.gate_trend("ep", GATE) == scores, "the trend is what tells you it is not converging"

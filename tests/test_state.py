"""The resume rule is the single line the whole recovery story rests on, so it is
tested at every transition rather than once."""

import pytest

from studio.core.schemas import Stage
from studio.core.state import Store


@pytest.fixture
def store(tmp_path):
    s = Store(tmp_path / "t.db")
    s.create_episode("ep", "ser", 1, "promise")
    yield s
    s.close()


def test_step_is_skipped_only_on_matching_hash(store):
    with store.step("ep", Stage.B1_PACKAGE, "h1") as out:
        out[0] = "/out/a"
    assert store.completed("ep", Stage.B1_PACKAGE, "h1") == "/out/a"
    assert store.completed("ep", Stage.B1_PACKAGE, "h2") is None, "changed inputs must re-run"


def test_failure_is_recorded_and_not_treated_as_done(store):
    with pytest.raises(ValueError):
        with store.step("ep", Stage.B3_SCRIPT, "h") as out:
            out[0] = "/never"
            raise ValueError("boom")
    assert store.completed("ep", Stage.B3_SCRIPT, "h") is None
    row = next(r for r in store.episode_steps("ep") if r["stage"] == "B3")
    assert row["status"] == "failed" and "boom" in row["error"]


def test_kill_at_every_transition_resumes_without_redoing_work(tmp_path):
    """Crash after each stage in turn; the next run may only do the work that is
    genuinely outstanding. Re-running a completed stage is the failure mode this
    whole design exists to prevent."""
    stages = [Stage.A1_VALIDATE, Stage.A2_RESEARCH, Stage.A3_SERIES, Stage.B1_PACKAGE,
              Stage.B2_BEATS, Stage.B3_SCRIPT, Stage.B5_VOICE, Stage.B6_SHOTS]
    db = tmp_path / "t.db"
    done: set[Stage] = set()

    for crash_after in range(len(stages)):
        store = Store(db)
        store.create_episode("ep", "ser", 1, "p")
        executed = []
        for i, stage in enumerate(stages[: crash_after + 1]):
            if store.completed("ep", stage, "h"):
                continue
            with store.step("ep", stage, "h") as out:
                out[0] = f"/out/{stage.value}"
            executed.append(stage)

        assert not (set(executed) & done), f"re-ran already-completed work: {set(executed) & done}"
        done |= set(executed)
        assert all(store.completed("ep", s, "h") for s in stages[: crash_after + 1])
        assert store.episode_state("ep") == stages[crash_after].value
        store.close()

    assert done == set(stages), "every stage ran exactly once across all the crashes"


def test_attempts_increment_on_retry(store):
    for _ in range(3):
        try:
            with store.step("ep", Stage.B6_SHOTS, "h") as out:
                out[0] = "/x"
                raise RuntimeError("flaky")
        except RuntimeError:
            pass
    row = next(r for r in store.episode_steps("ep") if r["stage"] == "B6")
    assert row["attempts"] == 3

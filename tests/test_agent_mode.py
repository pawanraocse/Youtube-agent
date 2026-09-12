"""Agent mode end to end, through the real CLI.

The load-bearing risk in M1 is that `studio ingest` computes a different
`input_hash` from the one `pipeline.run` hashes. Nothing would error — every
stage would simply re-run forever, and the resume rule is the invariant the whole
recovery story rests on. So it is tested through `main()` rather than in units.
"""

import json

import pytest

from studio import __main__ as cli


@pytest.fixture
def studio(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cli, "DB", tmp_path / "studio.db")
    monkeypatch.setattr(cli, "ROOT", tmp_path)

    def call(*argv) -> tuple[int, dict]:
        code = cli.main(["--json", *argv])
        return code, json.loads(capsys.readouterr().out)

    return call


DEMAND = {
    "topic": "t", "rights_verdict": "clear", "rights_notes": "checked",
    "projected_rpm": 8.0, "demand_volume": 20000, "competition_density": 0.4,
    "angle": "the one nobody took", "evidence": ["comparable videos"],
}


def _run(studio):
    return studio("run", "--topic", "t", "--channel", "ch", "--providers", "agent")


def test_the_walk_stops_at_the_first_judgement_stage(studio):
    code, out = _run(studio)
    assert code == 4
    assert out["awaiting"] == "A1"
    assert out["agent"] == "studio-producer"


def test_an_ingested_stage_is_skipped_on_the_next_walk(studio, tmp_path):
    """The resume rule holds across the skill boundary, or every stage re-runs."""
    _run(studio)
    inp = tmp_path / "demand-in.json"
    inp.write_text(json.dumps(DEMAND))
    code, out = studio("ingest", "--episode", "ch-EP01", "--stage", "A1", "--input", str(inp))
    assert code == 0 and out["recorded"] is True
    assert out["computed"]["revenue_per_gpu_hour"] == 160.0

    code, out = _run(studio)
    assert out["awaiting"] == "A2"          # A1 was skipped, not re-run


def test_findings_record_nothing_so_the_stage_stays_undone(studio, tmp_path):
    _run(studio)
    inp = tmp_path / "bad.json"
    inp.write_text(json.dumps(DEMAND | {"projected_rpm": 0.5, "demand_volume": 100}))
    code, out = studio("ingest", "--episode", "ch-EP01", "--stage", "A1", "--input", str(inp))
    assert code == 4 and out["recorded"] is False

    code, out = _run(studio)
    assert out["awaiting"] == "A1"          # still owed


def test_a_gate_stage_may_not_be_ingested_as_a_step(studio, tmp_path):
    """B4 records no step, so the walk always reaches the gate and the lock."""
    _run(studio)
    _, out = studio("brief", "--episode", "ch-EP01", "--stage", "B4")
    assert out["agent"] == "studio-critic"
    from studio.core.briefs import SPECS
    from studio.core.schemas import Stage
    assert SPECS[Stage.B4_SCRIPT_REVIEW].records_step is False


def test_mock_mode_never_waits_on_an_agent(studio, tmp_path):
    """The invariant M1 could have broken: mock runs stay unattended.

    The mock walk still stops at LOCK 3, on two findings that predate M1 and are
    logged as DEBT-003 and DEBT-004 — the point here is that it stops there and
    not at a judgement stage.
    """
    code, out = studio("run", "--topic", "t", "--channel", "mk", "--providers", "mock",
                       "--auto-approve", "test")
    assert "awaiting" not in out
    assert out["state"] == "B8"
    assert (tmp_path / "channels/mk/episodes/EP01/master.mp4").exists()


def test_a_lock_waiting_on_a_human_is_blocked_not_failed(studio, tmp_path):
    """`status` must distinguish a decision the pipeline is waiting for from a
    defect, or an operator cannot tell which of the two they are looking at."""
    studio("run", "--topic", "t", "--channel", "mk", "--providers", "mock")
    _, out = studio("status")
    ep = next(e for e in out["episodes"] if e["episode"] == "mk-EP01")
    assert ep["blocked"] == ["B4"]
    assert ep["failed"] == []


def test_a_blocked_step_still_re_runs(studio, tmp_path):
    """'blocked' must never satisfy the resume rule — that would skip the gate."""
    from studio.core.schemas import Stage
    from studio.core.state import Store
    studio("run", "--topic", "t", "--channel", "mk", "--providers", "mock")
    store = Store(cli.DB)
    row = store.conn.execute(
        "SELECT status, input_hash FROM steps WHERE episode_id='mk-EP01' AND stage='B4'"
    ).fetchone()
    assert row["status"] == "blocked"
    assert store.completed("mk-EP01", Stage.B4_SCRIPT_REVIEW, row["input_hash"]) is None
    store.close()

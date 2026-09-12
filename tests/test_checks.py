"""Each deterministic check gets a known-bad fixture it must catch and a
known-good fixture it must pass. This is the highest-value suite in the repo."""

from studio.checks import check_cohort, check_licences, check_picture, check_script
from studio.core.config import Format

FMT = Format.load("data-explainer")
GOOD_PACKAGING = {"promise": "What Switzerland actually did", "thumbnail_concept": "host + number"}
GOOD_SOURCES = [{"id": "s0"}]


def test_script_good_passes():
    chunks = [{"text": "A claim.", "needs_citation": True, "source_id": "s0"}]
    assert check_script(chunks, GOOD_PACKAGING, GOOD_SOURCES) == []


def test_script_catches_uncited_claim():
    chunks = [{"text": "An unsupported claim.", "needs_citation": True, "source_id": None}]
    found = [f.check for f in check_script(chunks, GOOD_PACKAGING, GOOD_SOURCES)]
    assert "citations" in found


def test_script_catches_overlong_promise():
    bad = dict(GOOD_PACKAGING, promise="one two three four five six seven eight nine")
    assert "promise" in [f.check for f in check_script([{"text": "x"}], bad, GOOD_SOURCES)]


def test_picture_good_passes():
    shots = [{"idx": i, "start_ms": i * 3000, "end_ms": (i + 1) * 3000, "character_ids": ["host-01"]}
             for i in range(4)]
    assert check_picture(shots, {"host-01"}, FMT) == []


def test_picture_catches_unregistered_character():
    shots = [{"idx": 0, "start_ms": 0, "end_ms": 3000, "character_ids": ["ghost"]}]
    assert "character" in [f.check for f in check_picture(shots, {"host-01"}, FMT)]


def test_picture_catches_slow_pacing():
    shots = [{"idx": 0, "start_ms": 0, "end_ms": 9000, "character_ids": []}]
    assert "pacing" in [f.check for f in check_picture(shots, set(), FMT)]


def test_picture_catches_timeline_hole():
    shots = [{"idx": 0, "start_ms": 0, "end_ms": 3000, "character_ids": []},
             {"idx": 1, "start_ms": 3500, "end_ms": 6000, "character_ids": []}]
    assert "timeline" in [f.check for f in check_picture(shots, set(), FMT)]


def test_licence_audit_blocks_forbidden_weights():
    assert "licence" in [f.check for f in check_licences({"tts": "edge-tts"})]
    assert "licence" in [f.check for f in check_licences({"video": "hunyuanvideo"})]


def test_licence_audit_flags_unverified():
    findings = check_licences({"image": "flux-schnell"})
    assert findings and "unverified" in findings[0].detail


def test_cohort_verdicts():
    v = check_cohort([
        {"channel_id": "dead", "views": [120] * 20},
        {"channel_id": "spike", "views": [600] * 19 + [9000]},
        {"channel_id": "alive", "views": [4000] * 20},
        {"channel_id": "young", "views": [900] * 6},
    ])
    assert v["dead"][0] == "kill"
    assert v["spike"][0] == "extend"
    assert v["alive"][0] == "keep"
    assert v["young"][0] == "too_early"

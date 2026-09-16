"""The skill/CLI contract: what a brief hands an agent, and what ingest refuses.

Every check here is a known-bad artefact the validator must catch, because the
whole point of the boundary is that an agent producing something plausible but
unusable fails here rather than three stages downstream.
"""

import json

import pytest

from studio.core import briefs
from studio.core.briefs import SPECS
from studio.core.config import Format, Pack
from studio.core.schemas import Stage

FMT = Format.load("data-explainer")
PACK = Pack.load("geography-economics")

GOOD_DEMAND = {
    "topic": "Why Singapore imports its water",
    "rights_verdict": "clear",
    "rights_notes": "No music, no film footage, general audience.",
    "projected_rpm": 8.0,
    "demand_volume": 20000,
    "competition_density": 0.4,
    "angle": "The 1962 water agreement nobody explains",
    "affiliate_angle": "A water-security dataset",
    "evidence": ["Comparable videos average 18-25k views", "Finance-adjacent RPM band"],
}


def _validate(stage, raw, root):
    return briefs.validate(SPECS[stage], raw, root=root, fmt=FMT, pack=PACK)


# ---- A1 -------------------------------------------------------------------

def test_ingest_computes_the_score_the_agent_must_not(tmp_path):
    """Arithmetic done in an agent's head is arithmetic nobody can audit."""
    data, findings = _validate(Stage.A1_VALIDATE, GOOD_DEMAND, tmp_path)
    assert findings == []
    # 8.0 * 20000 / 1000 = $160 per episode, over 1.0 GPU hour.
    assert data["revenue_per_gpu_hour"] == 160.0
    assert data["niche_score"] == 96.0          # discounted by 40% competition


def test_a_blocked_concept_must_name_the_version_that_pays(tmp_path):
    raw = GOOD_DEMAND | {"rights_verdict": "blocked",
                         "rights_notes": "Song mashup: Content ID routes the revenue away"}
    _, findings = _validate(Stage.A1_VALIDATE, raw, tmp_path)
    detail = " ".join(str(f) for f in findings)
    assert "rights" in detail and "version that pays" in detail


def test_a_concept_below_the_packs_floor_is_refused(tmp_path):
    raw = GOOD_DEMAND | {"projected_rpm": 1.0, "demand_volume": 900}
    _, findings = _validate(Stage.A1_VALIDATE, raw, tmp_path)
    assert any("per GPU hour" in str(f) for f in findings)


def test_estimates_without_evidence_are_refused(tmp_path):
    _, findings = _validate(Stage.A1_VALIDATE, GOOD_DEMAND | {"evidence": []}, tmp_path)
    assert any(f.check == "evidence" for f in findings)


# ---- A2 -------------------------------------------------------------------

def _sources(n=5, tier="statistical_agency"):
    return [{"id": f"s{i}", "tier": tier if i == 0 else "academic",
             "title": f"t{i}", "url": f"https://x.invalid/{i}", "supports": f"claim {i}"}
            for i in range(n)]


def test_a_pack_that_researches_data_first_needs_a_data_source(tmp_path):
    (tmp_path / "research.md").write_text("body")
    _, findings = _validate(Stage.A2_RESEARCH, _sources(tier="academic"), tmp_path)
    assert any("statistical_agency" in str(f) for f in findings)


def test_prose_must_be_written_alongside_the_json(tmp_path):
    _, findings = _validate(Stage.A2_RESEARCH, _sources(), tmp_path)
    assert any("research.md" in str(f) for f in findings)


def test_a_tier_the_pack_does_not_list_is_refused(tmp_path):
    (tmp_path / "research.md").write_text("body")
    bad = _sources()
    bad[1]["tier"] = "youtube_comment"
    _, findings = _validate(Stage.A2_RESEARCH, bad, tmp_path)
    assert any(f.check == "tier" for f in findings)


# ---- A3 -------------------------------------------------------------------

def _series(promises):
    return {"topic": "t", "episodes": [
        {"number": i + 1, "title": f"E{i+1}", "promise": p,
         "arc_position": "establishes", "cliffhanger": "next"}
        for i, p in enumerate(promises)]}


def test_two_episodes_may_not_repeat_a_beat(tmp_path):
    _, findings = _validate(Stage.A3_SERIES, _series(["same one", "same one"]), tmp_path)
    assert any("repeats a beat" in str(f) for f in findings)


def test_a_promise_longer_than_eight_words_is_refused(tmp_path):
    long = "one two three four five six seven eight nine"
    _, findings = _validate(Stage.A3_SERIES, _series([long]), tmp_path)
    assert any("8 words" in str(f) for f in findings)


# ---- B2 -------------------------------------------------------------------

def _beats(clippable=True, minutes=7.0):
    kinds = ["cold_open", "promise", "escalation", "escalation", "payoff", "loop"]
    each = minutes * 60 / len(kinds)
    return [{"id": f"b{i}", "kind": k, "summary": k, "target_seconds": each,
             "clippable": clippable and k == "escalation"} for i, k in enumerate(kinds)]


def test_a_beat_sheet_with_nothing_clippable_is_refused(tmp_path):
    """B10 would have nothing to cut, and derived clips are the format's economics."""
    _, findings = _validate(Stage.B2_BEATS, _beats(clippable=False), tmp_path)
    assert any(f.check == "clippable" for f in findings)


def test_beats_outside_the_formats_length_are_refused(tmp_path):
    _, findings = _validate(Stage.B2_BEATS, _beats(minutes=22.0), tmp_path)
    assert any(f.check == "length" for f in findings)


# ---- B3 -------------------------------------------------------------------

def test_a_claim_citing_an_unknown_source_is_refused(tmp_path):
    (tmp_path / "packaging.json").write_text(json.dumps(
        {"titles": ["t"], "thumbnail_concept": "c", "promise": "short promise"}))
    (tmp_path / "sources.json").write_text(json.dumps(_sources()))
    script = [{"beat_id": "b0", "text": "Forty percent is imported.",
               "pause_ms": 300, "needs_citation": True, "source_id": "s99"}]
    _, findings = _validate(Stage.B3_SCRIPT, script, tmp_path)
    assert any("unknown source id" in str(f) for f in findings)


# ---- B4 -------------------------------------------------------------------

def _score(total=86.0, **dims):
    d = {"factual_fidelity": 90.0, "hook_strength": 80.0,
         "pacing": 85.0, "sensitivity": 90.0} | dims
    return {"gate": "LOCK1_SCRIPT", "iteration": 1, "dimensions": d,
            "total": total, "passed": total >= 80, "notes": []}


def test_the_critic_may_not_invent_a_dimension(tmp_path):
    raw = _score()
    raw["dimensions"]["vibes"] = 100.0
    _, findings = _validate(Stage.B4_SCRIPT_REVIEW, raw, tmp_path)
    assert any(f.check == "rubric" for f in findings)


def test_a_total_that_is_not_the_weighted_sum_is_refused(tmp_path):
    """Ingest recomputes the arithmetic so a critic cannot round itself into a pass."""
    _, findings = _validate(Stage.B4_SCRIPT_REVIEW, _score(total=99.0), tmp_path)
    assert any("weighted sum" in str(f) for f in findings)


def test_a_correctly_weighted_total_passes(tmp_path):
    # 90*.30 + 80*.25 + 85*.25 + 90*.20 = 86.25
    _, findings = _validate(Stage.B4_SCRIPT_REVIEW, _score(total=86.25), tmp_path)
    assert findings == []


def test_a_score_below_threshold_is_a_finding_not_a_pass(tmp_path):
    _, findings = _validate(Stage.B4_SCRIPT_REVIEW,
                            _score(total=61.25, factual_fidelity=0.0), tmp_path)
    assert any(f.check == "score" for f in findings)


def test_a_total_rounded_up_into_the_threshold_is_caught_by_the_weighted_sum(tmp_path):
    # factual_fidelity 67.5 weights the sum to exactly 79.5; claiming 80.0 sits inside
    # the 0.5 consistency tolerance, so the gate must threshold the recomputed sum.
    _, findings = _validate(Stage.B4_SCRIPT_REVIEW,
                            _score(total=80.0, factual_fidelity=67.5), tmp_path)
    assert any(f.check == "score" for f in findings)


def test_the_critique_never_completes_the_gate_step():
    """A critique is an input to a lock, not the lock's completion. If ingest
    recorded B4 as done, the next walk would skip the gate and LOCK 1 would open
    on a score alone."""
    assert briefs.records_step(Stage.B4_SCRIPT_REVIEW) is False
    assert briefs.records_step(Stage.B3_SCRIPT) is True


# ---- the brief itself -----------------------------------------------------

def test_a_brief_carries_its_upstream_and_names_what_is_missing(tmp_path):
    (tmp_path / "demand.json").write_text(json.dumps(GOOD_DEMAND))
    packet = briefs.build(SPECS[Stage.A3_SERIES], topic="t", root=tmp_path,
                          fmt=FMT, pack=PACK)
    assert packet["upstream"]["demand.json"]["topic"] == GOOD_DEMAND["topic"]
    assert packet["missing_upstream"] == ["sources.json"]
    assert packet["schema"]["properties"]["episodes"]
    assert packet["rubric"]["pass_threshold"] == 80

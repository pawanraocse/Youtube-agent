"""Agents cannot be trusted to remember constraints, so the schema enforces them."""

import pytest
from pydantic import ValidationError

from studio.core.schemas import Character, Packaging, ScriptChunk, Shot


def test_promise_capped_at_eight_words():
    with pytest.raises(ValidationError):
        Packaging(titles=["t"], thumbnail_concept="c",
                  promise="one two three four five six seven eight nine")


def test_shot_rejects_inverted_timing():
    with pytest.raises(ValidationError):
        Shot(idx=0, beat_id="b", start_ms=5000, end_ms=1000, prompt="x")


def test_shot_carries_ids_not_appearance_prose():
    s = Shot(idx=0, beat_id="b", start_ms=0, end_ms=3000, prompt="wide of the valley",
             character_ids=["host-01"])
    assert s.character_ids == ["host-01"] and s.duration_ms == 3000


def test_character_id_must_be_a_slug():
    with pytest.raises(ValidationError):
        Character(id="not a slug!", name="X", role="host")


def test_pause_is_bounded():
    with pytest.raises(ValidationError):
        ScriptChunk(beat_id="b", text="t", pause_ms=99_000)

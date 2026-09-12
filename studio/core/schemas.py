"""Data contracts that cross the skill/CLI boundary.

Every artefact an agent produces is validated against a model here before it is
written. An agent that emits appearance prose where a character id belongs, or a
shot list that omits timings, fails at this layer rather than at render time.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Stage(StrEnum):
    """Pipeline stages. The subset and order a channel runs come from its format."""

    A0_CHANNEL = "A0"
    A1_VALIDATE = "A1"
    A2_RESEARCH = "A2"
    A3_SERIES = "A3"
    A4_LOOK_CAST = "A4"
    B1_PACKAGE = "B1"
    B2_BEATS = "B2"
    B3_SCRIPT = "B3"
    B4_SCRIPT_REVIEW = "B4"
    B5_VOICE = "B5"
    B6_SHOTS = "B6"
    B7_ANIMATIC_REVIEW = "B7"
    B8_POST = "B8"
    B9_MASTER_QC = "B9"
    B10_MULTIPLY = "B10"
    B11_DISTRIBUTE = "B11"


#: The three gates. Only a recorded human decision advances past one.
GATES: dict[Stage, str] = {
    Stage.B4_SCRIPT_REVIEW: "LOCK1_SCRIPT",
    Stage.B7_ANIMATIC_REVIEW: "LOCK2_PICTURE",
    Stage.B9_MASTER_QC: "LOCK3_MASTER",
}

NEW = "NEW"


def _at_most_eight_words(v: str) -> str:
    if len(v.split()) > 8:
        raise ValueError(f"promise must be 8 words or fewer, got {len(v.split())}")
    return v


class Demand(BaseModel):
    """A1. What a producer judges about a topic before any work is paid for.

    The agent supplies only the estimates it is qualified to make. Every derived
    figure — niche score, revenue per GPU hour — is computed at ingest, because
    arithmetic done in an agent's head is arithmetic nobody can audit.
    """

    topic: str
    rights_verdict: Literal["clear", "blocked", "needs_change"]
    rights_notes: str = ""
    paying_alternative: str | None = Field(
        default=None,
        description="Required when the verdict is not clear: the version of this idea that pays.",
    )
    projected_rpm: float = Field(gt=0, description="USD per 1000 views in this niche.")
    demand_volume: int = Field(gt=0, description="Expected views per video at steady state.")
    competition_density: float = Field(
        ge=0.0, le=1.0, description="0 is an empty niche, 1 is saturated by incumbents."
    )
    angle: str = Field(description="The take nobody in the competitor scan has already made.")
    affiliate_angle: str | None = Field(
        default=None,
        description="A plausible non-AdSense stream, or null. Its absence lowers the score.",
    )
    competitors: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(
        default_factory=list, description="What the estimates above are based on."
    )
    # Computed at ingest, never supplied by the agent.
    niche_score: float | None = None
    revenue_per_gpu_hour: float | None = None


class Source(BaseModel):
    """A2. One citable source, tiered by the pack's source hierarchy."""

    id: str
    tier: str
    title: str
    url: str
    publisher: str = ""
    year: int | None = None
    supports: str = Field(description="The specific claim this source is cited for.")


class SeriesEpisode(BaseModel):
    number: int = Field(ge=1)
    title: str
    promise: str
    arc_position: str
    cliffhanger: str

    @field_validator("promise")
    @classmethod
    def _eight_words(cls, v: str) -> str:
        return _at_most_eight_words(v)


class SeriesMap(BaseModel):
    """A3. The episode list. No two episodes may repeat a beat."""

    topic: str
    episodes: list[SeriesEpisode] = Field(min_length=1)

    @field_validator("episodes")
    @classmethod
    def _distinct(cls, v: list[SeriesEpisode]) -> list[SeriesEpisode]:
        promises = [e.promise.strip().lower() for e in v]
        if len(set(promises)) != len(promises):
            raise ValueError("two episodes share a promise — the series repeats a beat")
        numbers = [e.number for e in v]
        if numbers != list(range(1, len(numbers) + 1)):
            raise ValueError(f"episode numbers must run 1..{len(numbers)}, got {numbers}")
        return v


class Character(BaseModel):
    """A host or cast member. Registered once at studio level, reused anywhere."""

    id: str
    name: str
    role: Literal["host", "cast"]
    version: int = 1
    canon: dict[str, str] = Field(
        default_factory=dict,
        description="Appearance, wardrobe, era, manner. Read at render, never re-invented.",
    )
    ref_image_shas: list[str] = Field(default_factory=list)
    lora_path: str | None = None
    trigger_token: str | None = None
    voice_id: str | None = None
    likeness_checked_at: str | None = None

    @field_validator("id")
    @classmethod
    def _slug(cls, v: str) -> str:
        if not v or not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(f"character id must be a slug, got {v!r}")
        return v


class Beat(BaseModel):
    """One structural unit of the episode. Timings drive shot durations."""

    id: str
    kind: Literal["cold_open", "promise", "escalation", "payoff", "loop"]
    summary: str
    target_seconds: float = Field(gt=0)
    clippable: bool = Field(
        default=False,
        description="Marked here, at the beat sheet, not hunted for after the master exists.",
    )


class ScriptChunk(BaseModel):
    """One sentence plus the silence that follows it.

    Kokoro emits flat continuous speech, so pauses are authored rather than hoped
    for. Each chunk is synthesised separately and concatenated with real silence.
    """

    beat_id: str
    text: str
    pause_ms: int = Field(default=350, ge=0, le=4000)
    needs_citation: bool = Field(
        default=False, description="True for any sentence asserting a checkable fact."
    )
    source_id: str | None = Field(
        default=None, description="Must name a row in sources.json when needs_citation is set."
    )


class Shot(BaseModel):
    """One picture event, timed against the locked voice-over."""

    idx: int
    beat_id: str
    start_ms: int = Field(ge=0)
    end_ms: int = Field(gt=0)
    prompt: str
    character_ids: list[str] = Field(
        default_factory=list,
        description="Ids only. Appearance is resolved from the registry at render.",
    )
    motion: Literal["parallax", "kenburns", "aivideo", "stock", "chart"] = "parallax"

    @property
    def duration_ms(self) -> int:
        return self.end_ms - self.start_ms

    @field_validator("end_ms")
    @classmethod
    def _ordered(cls, v: int, info) -> int:
        start = info.data.get("start_ms")
        if start is not None and v <= start:
            raise ValueError(f"end_ms {v} must exceed start_ms {start}")
        return v


class Packaging(BaseModel):
    """Written before the script. If the promise does not fit, the topic is dead."""

    titles: list[str] = Field(min_length=1)
    thumbnail_concept: str
    promise: str

    @field_validator("promise")
    @classmethod
    def _eight_words(cls, v: str) -> str:
        return _at_most_eight_words(v)


class GateScore(BaseModel):
    """One critic pass. Dimensions come from the pack's versioned rubric."""

    gate: str
    iteration: int = Field(ge=1)
    dimensions: dict[str, float]
    total: float
    passed: bool
    notes: list[str] = Field(default_factory=list)

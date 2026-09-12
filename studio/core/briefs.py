"""What an agent is given for a stage, and what it must hand back.

One registry, read by three callers: `studio brief` builds the packet an agent
works from, `studio ingest` validates the reply against the same row, and the
pipeline asks whether a stage is agent-owned before running a mock in its place.

Keeping all three on one table is what stops the brief and the validator drifting
apart, which is the failure mode that makes an agent produce something plausible
that nothing downstream can read.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter, ValidationError

from studio.checks import Finding, check_beats, check_demand, check_script
from studio.core.config import Format, Pack
from studio.core.schemas import (
    Beat,
    Demand,
    GateScore,
    Packaging,
    ScriptChunk,
    SeriesMap,
    Source,
    Stage,
)


@dataclass(frozen=True)
class StageSpec:
    """One agent-owned stage: who does it, what it writes, what it may read."""

    stage: Stage
    agent: str
    artefact: str                        # filename written into the episode root
    schema: Any                          # pydantic model, or list[model]
    produces: str                        # one line, shown in the brief
    needs: tuple[str, ...] = field(default_factory=tuple)   # upstream artefacts
    also_writes: tuple[str, ...] = field(default_factory=tuple)  # prose alongside
    records_step: bool = True
    """False for a gate. A critique is an input to a lock, not the lock's completion:
    if ingest recorded B4 as done, the walk would skip the gate and LOCK 1 would
    open on a score, which is exactly what `gate_is_open` exists to prevent."""


SPECS: dict[Stage, StageSpec] = {
    Stage.A1_VALIDATE: StageSpec(
        stage=Stage.A1_VALIDATE,
        agent="studio-producer",
        artefact="demand.json",
        schema=Demand,
        produces="A rights verdict, a competitor scan, and the estimates the score is built from.",
    ),
    Stage.A2_RESEARCH: StageSpec(
        stage=Stage.A2_RESEARCH,
        agent="studio-researcher",
        artefact="sources.json",
        schema=list[Source],
        produces="Tiered sources, each tied to the specific claim it supports.",
        needs=("demand.json",),
        also_writes=("research.md",),
    ),
    Stage.A3_SERIES: StageSpec(
        stage=Stage.A3_SERIES,
        agent="studio-producer",
        artefact="series.json",
        schema=SeriesMap,
        produces="The episode list, each with its own promise and a hook into the next.",
        needs=("demand.json", "sources.json"),
    ),
    Stage.B1_PACKAGE: StageSpec(
        stage=Stage.B1_PACKAGE,
        agent="studio-writer",
        artefact="packaging.json",
        schema=Packaging,
        produces="Title variants, a thumbnail concept, and the promise in eight words or fewer.",
        needs=("demand.json", "series.json"),
    ),
    Stage.B2_BEATS: StageSpec(
        stage=Stage.B2_BEATS,
        agent="studio-writer",
        artefact="beats.json",
        schema=list[Beat],
        produces="The beat sheet with timings and clippable moments marked.",
        needs=("packaging.json", "series.json", "sources.json"),
    ),
    Stage.B3_SCRIPT: StageSpec(
        stage=Stage.B3_SCRIPT,
        agent="studio-writer",
        artefact="script.json",
        schema=list[ScriptChunk],
        produces="Narration, one chunk per sentence, each with an authored pause.",
        needs=("beats.json", "sources.json", "packaging.json"),
    ),
    Stage.B4_SCRIPT_REVIEW: StageSpec(
        stage=Stage.B4_SCRIPT_REVIEW,
        agent="studio-critic",
        artefact="critique.json",
        schema=GateScore,
        produces="A score per rubric dimension, with the notes a revision would act on.",
        needs=("script.json", "beats.json", "packaging.json", "sources.json"),
        records_step=False,
    ),
}


def is_agent_owned(stage: Stage) -> bool:
    return stage in SPECS


def records_step(stage: Stage) -> bool:
    """True when ingesting this stage's artefact completes it for the resume rule."""
    spec = SPECS.get(stage)
    return spec is not None and spec.records_step


def build(spec: StageSpec, *, topic: str, root: Path, fmt: Format, pack: Pack) -> dict:
    """The packet an agent works from. Data only — craft lives in the agent file."""
    upstream: dict[str, Any] = {}
    missing: list[str] = []
    for name in spec.needs:
        path = root / name
        if not path.exists():
            missing.append(name)
            continue
        upstream[name] = json.loads(path.read_text())

    # Prose written by earlier stages is not JSON and cannot be inlined, but an
    # agent that never reads research.md writes from sources.json alone — which is
    # a bibliography, not an argument. Point at it.
    prose = [str(root / n) for other in SPECS.values() for n in other.also_writes
             if (root / n).exists()]

    return {
        "stage": spec.stage.value,
        "agent": spec.agent,
        "produces": spec.produces,
        "write_to": str(root / spec.artefact),
        "also_writes": [str(root / n) for n in spec.also_writes],
        "ingest_with": f"studio ingest --episode <id> --stage {spec.stage.value}"
                       f" --input {root / spec.artefact}",
        "schema": TypeAdapter(spec.schema).json_schema(),
        "topic": topic,
        "format": {
            "name": fmt.name,
            "length_minutes": list(fmt.length_minutes),
            "gpu_budget_hours": fmt.gpu_budget_hours,
            "mean_shot_seconds_max": fmt.mean_shot_seconds_max,
            "shot_vocabulary": fmt.shot_vocabulary,
        },
        "pack": {
            "name": pack.name,
            "research": pack.research,
            "narrative": pack.narrative,
            "sensitivity": pack.sensitivity,
            "demand": pack.demand,
        },
        "rubric": pack.rubric(),
        "upstream": upstream,
        "read_also": prose,
        "missing_upstream": missing,
    }


def validate(spec: StageSpec, raw: Any, *, root: Path, fmt: Format, pack: Pack
             ) -> tuple[Any, list[Finding]]:
    """Parse against the stage's schema, then run its deterministic checks.

    Returns the parsed payload as plain data plus any findings. A stage with
    findings is never recorded, so the resume rule leaves it undone and the
    agent is asked again with the specific failures.
    """
    try:
        parsed = TypeAdapter(spec.schema).validate_python(raw)
    except ValidationError as exc:
        return None, [
            Finding("schema", f"{'.'.join(str(p) for p in e['loc']) or '<root>'}: {e['msg']}")
            for e in exc.errors()
        ]

    data = TypeAdapter(spec.schema).dump_python(parsed, mode="json")
    if spec.stage is Stage.A1_VALIDATE:
        data = _score_demand(data, fmt)
    findings = _checks(spec.stage, data, root=root, fmt=fmt, pack=pack)
    findings += [Finding("artefact", f"{n} was not written alongside {spec.artefact}")
                 for n in spec.also_writes if not (root / n).exists()]
    return data, findings


def _checks(stage: Stage, data: Any, *, root: Path, fmt: Format, pack: Pack) -> list[Finding]:
    if stage is Stage.A1_VALIDATE:
        return check_demand(data, pack, fmt)
    if stage is Stage.A2_RESEARCH:
        return _check_sources(data, pack)
    if stage is Stage.B2_BEATS:
        return check_beats(data, fmt, pack)
    if stage is Stage.B3_SCRIPT:
        return check_script(data, json.loads((root / "packaging.json").read_text()),
                            json.loads((root / "sources.json").read_text()))
    if stage is Stage.B4_SCRIPT_REVIEW:
        return _check_critique(data, pack)
    return []


def _score_demand(demand: dict, fmt: Format) -> dict:
    """Arithmetic the agent does not do, so that it can be audited.

    Revenue per GPU hour is the metric that ranks niches correctly: RPM alone
    prefers niches with no audience, and view count alone prefers niches that pay
    nothing. The competition term discounts a crowded niche rather than barring it.
    """
    per_episode = demand["projected_rpm"] * demand["demand_volume"] / 1000
    rpgh = per_episode / max(fmt.gpu_budget_hours, 0.01)
    demand["revenue_per_gpu_hour"] = round(rpgh, 1)
    demand["niche_score"] = round(rpgh * (1 - demand["competition_density"]), 1)
    return demand


def _check_sources(sources: list[dict], pack: Pack) -> list[Finding]:
    out: list[Finding] = []
    want = int(pack.research.get("min_sources", 5))
    if len(sources) < want:
        out.append(Finding("sources", f"{len(sources)} sources, pack requires {want}"))
    allowed = set(pack.research.get("tiers", []))
    for s in sources:
        if allowed and s["tier"] not in allowed:
            out.append(Finding("tier", f"{s['id']}: {s['tier']!r} is not a tier in this pack"))
    if len({s["id"] for s in sources}) != len(sources):
        out.append(Finding("sources", "duplicate source ids"))
    top = pack.research.get("tiers", [None])[0]
    if top and not any(s["tier"] == top for s in sources):
        out.append(Finding("tier", f"no {top} source — this pack researches {top} first"))
    return out


def _check_critique(score: dict, pack: Pack) -> list[Finding]:
    """The critic may score however it likes; it may not invent dimensions."""
    out: list[Finding] = []
    rubric = pack.rubric()
    expected = set(rubric.get("dimensions", {}))
    got = set(score.get("dimensions", {}))
    if got != expected:
        out.append(Finding("rubric", f"dimensions {sorted(got)} do not match {sorted(expected)}"))
        return out
    weighted = sum(score["dimensions"][d] * rubric["dimensions"][d]["weight"] for d in expected)
    if abs(weighted - score["total"]) > 0.5:
        out.append(Finding("rubric", f"total {score['total']} is not the weighted sum {weighted:.1f}"))
    threshold = float(rubric.get("pass_threshold", 80))
    if score["total"] < threshold:
        out.append(Finding("score", f"{score['total']:.1f} is below the {threshold:.0f} threshold"))
    return out

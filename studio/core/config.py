"""Loads the config trees. Nothing here knows what a video is.

A channel is `format × pack × platform mix`. Adding a format or a pack must never
require touching core or the agent roster, which is only true if the stage list
lives in the format file rather than in code.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

from studio.core.schemas import Stage

ROOT = Path(__file__).resolve().parents[2]


def _load(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"missing config: {path.relative_to(ROOT)}")
    return yaml.safe_load(path.read_text()) or {}


@dataclass(frozen=True)
class Format:
    name: str
    stages: list[Stage]
    length_minutes: tuple[int, int]
    gpu_budget_hours: float
    providers: dict[str, str]
    host_required: bool
    cast_required: bool
    mean_shot_seconds_max: float
    hero_shot_budget: int = 0
    shot_vocabulary: list[str] = field(default_factory=list)

    @staticmethod
    def load(name: str) -> "Format":
        d = _load(ROOT / "formats" / f"{name}.yaml")
        return Format(
            name=d["name"],
            stages=[Stage(s) for s in d["stages"]],
            length_minutes=tuple(d["length_minutes"]),
            gpu_budget_hours=float(d["gpu_budget_hours"]),
            providers=d.get("providers", {}),
            host_required=bool(d.get("host_required", False)),
            cast_required=bool(d.get("cast_required", False)),
            mean_shot_seconds_max=float(d.get("mean_shot_seconds_max", 4.0)),
            hero_shot_budget=int(d.get("hero_shot_budget", 0)),
            shot_vocabulary=d.get("shot_vocabulary", []),
        )


@dataclass(frozen=True)
class Pack:
    name: str
    research: dict
    narrative: dict
    critic: dict
    sensitivity: dict
    demand: dict = field(default_factory=dict)

    @staticmethod
    def load(name: str) -> "Pack":
        d = _load(ROOT / "packs" / f"{name}.yaml")
        return Pack(
            name=d["name"],
            research=d.get("research", {}),
            narrative=d.get("narrative", {}),
            critic=d.get("critic", {}),
            sensitivity=d.get("sensitivity", {}),
            demand=d.get("demand", {}),
        )

    def rubric(self) -> dict:
        return _load(ROOT / self.critic["rubric"])


@dataclass(frozen=True)
class PlatformSpec:
    name: str
    width: int
    height: int
    max_seconds: int
    hook_seconds: int
    loudness_lufs: float
    true_peak_dbtp: float
    caption_safe_area: dict
    targets: list[str] = field(default_factory=list)

    @staticmethod
    def load(name: str) -> "PlatformSpec":
        d = _load(ROOT / "platforms" / f"{name}.yaml")
        return PlatformSpec(
            name=d["name"], width=d["width"], height=d["height"],
            max_seconds=d["max_seconds"], hook_seconds=d["hook_seconds"],
            loudness_lufs=float(d["loudness_lufs"]),
            true_peak_dbtp=float(d["true_peak_dbtp"]),
            caption_safe_area=d.get("caption_safe_area", {}),
            targets=d.get("targets", []),
        )


@lru_cache(maxsize=1)
def licences() -> dict:
    return _load(ROOT / "licenses.yaml")

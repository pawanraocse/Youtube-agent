"""Deterministic gate checks. No LLM runs here.

These are the objective half of every review loop, and they run first — there is
no point paying a critic to read a script whose citations are missing. A finding
is a fact with a location, never an opinion.
"""

from __future__ import annotations

import json
import statistics
import subprocess
from dataclasses import dataclass
from pathlib import Path

from studio.core.config import Format, licences


@dataclass(frozen=True)
class Finding:
    check: str
    detail: str

    def __str__(self) -> str:
        return f"{self.check}: {self.detail}"


def check_script(script_chunks: list[dict], packaging: dict, sources: list[dict]) -> list[Finding]:
    out: list[Finding] = []
    if not sources:
        out.append(Finding("citations", "no sources recorded for this episode"))
    promise = packaging.get("promise", "")
    if len(promise.split()) > 8:
        out.append(Finding("promise", f"{len(promise.split())} words, limit is 8"))
    if not packaging.get("thumbnail_concept"):
        out.append(Finding("packaging", "no thumbnail concept — packaging is written before script"))
    if not script_chunks:
        out.append(Finding("script", "empty script"))
    uncited = [c for c in script_chunks if c.get("needs_citation") and not c.get("source_id")]
    for c in uncited:
        out.append(Finding("citations", f"claim without a source: {c['text'][:60]!r}"))
    return out


def check_picture(shots: list[dict], registered_character_ids: set[str],
                  fmt: Format) -> list[Finding]:
    out: list[Finding] = []
    if not shots:
        return [Finding("shots", "no shots")]
    for s in shots:
        for cid in s.get("character_ids", []):
            if cid not in registered_character_ids:
                out.append(Finding("character", f"shot {s['idx']} names unregistered {cid!r}"))
    durations = [(s["end_ms"] - s["start_ms"]) / 1000 for s in shots]
    mean = statistics.mean(durations)
    if mean > fmt.mean_shot_seconds_max:
        out.append(Finding("pacing", f"mean shot {mean:.2f}s exceeds {fmt.mean_shot_seconds_max}s"))
    gaps = [b["start_ms"] - a["end_ms"] for a, b in zip(shots, shots[1:]) if b["start_ms"] != a["end_ms"]]
    if gaps:
        out.append(Finding("timeline", f"{len(gaps)} gap(s) or overlap(s) between shots"))
    return out


def check_master(master: Path, platforms: list[str], music_track: dict | None) -> list[Finding]:
    out: list[Finding] = []
    if not master.exists():
        return [Finding("master", f"missing file {master}")]
    stats = _loudness(master)
    if stats["input_i"] > -12.0 or stats["input_i"] < -17.0:
        out.append(Finding("loudness", f"integrated {stats['input_i']:.1f} LUFS, target -14"))
    if stats["input_tp"] > -1.0:
        out.append(Finding("true_peak", f"{stats['input_tp']:.1f} dBTP exceeds -1.0"))
    if music_track is not None:
        cleared = set(music_track.get("cleared_for", []))
        for p in platforms:
            if p not in cleared:
                out.append(Finding(
                    "music_clearance",
                    f"track {music_track.get('id')!r} is not cleared for {p} — "
                    "YouTube Audio Library terms do not carry to other platforms",
                ))
    return out


def check_licences(active_providers: dict[str, str]) -> list[Finding]:
    """The one check protecting actual money."""
    lic = licences()
    forbidden, allowed = lic.get("forbidden", {}), lic.get("allowed", {})
    out: list[Finding] = []
    for role, name in active_providers.items():
        if name in ("none", "mock"):
            continue
        if name in forbidden:
            out.append(Finding("licence", f"{role}={name} is forbidden: {forbidden[name]['reason']}"))
        elif name not in allowed:
            out.append(Finding("licence", f"{role}={name} is not in licenses.yaml at all"))
        elif allowed[name].get("verified_on") is None:
            out.append(Finding("licence", f"{role}={name} licence is unverified — read the model card"))
    return out


def check_cohort(rows: list[dict]) -> dict:
    """The ninety-day verdict. A channel's fate is a query result, not an argument."""
    verdicts = {}
    for r in rows:
        views = sorted(r.get("views", []))
        if len(views) < 20:
            verdicts[r["channel_id"]] = ("too_early", f"{len(views)} videos, need 20")
            continue
        median, best = statistics.median(views), max(views)
        if median < 500 and best < 5000:
            verdicts[r["channel_id"]] = ("kill", f"median {median:.0f}, best {best}")
        elif median < 2000 and best >= 5000:
            verdicts[r["channel_id"]] = ("extend", f"median {median:.0f}, best {best} — change packaging only")
        else:
            verdicts[r["channel_id"]] = ("keep", f"median {median:.0f}, best {best}")
    return verdicts


def _loudness(path: Path) -> dict:
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
         "-af", "loudnorm=I=-14:TP=-1:LRA=11:print_format=json", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    blob = proc.stderr[proc.stderr.rfind("{"): proc.stderr.rfind("}") + 1]
    data = json.loads(blob)
    return {"input_i": float(data["input_i"]), "input_tp": float(data["input_tp"])}

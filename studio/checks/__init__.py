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

from studio.core.config import Format, PlatformSpec, licences


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


def check_master(master: Path, platforms: list[str], music_track: dict | None,
                 spec: "PlatformSpec | None" = None) -> list[Finding]:
    """The production standard, enforced. Every number here is a target the plan
    states, so a master that misses one does not reach LOCK 3."""
    out: list[Finding] = []
    if not master.exists():
        return [Finding("master", f"missing file {master}")]

    a = _loudness(master)
    if not -17.0 <= a["input_i"] <= -12.0:
        out.append(Finding("loudness", f"integrated {a['input_i']:.1f} LUFS, target -14"))
    if a["input_tp"] > -1.0:
        out.append(Finding("true_peak", f"{a['input_tp']:.1f} dBTP exceeds -1.0"))
    if a["input_lra"] > 7.0:
        out.append(Finding(
            "loudness_range",
            f"LRA {a['input_lra']:.1f} exceeds 7 — quiet moments will vanish on a phone speaker"))

    # Phone speakers are mono. A mix that only survives in stereo does not survive.
    drop = a["input_i"] - _mono_loudness(master)
    if drop > 3.0:
        out.append(Finding(
            "mono_folddown",
            f"{drop:.1f} LU lost folding to mono — phase cancellation is eating the dialogue"))

    v = _video_props(master)
    if spec is not None and (v["width"], v["height"]) != (spec.width, spec.height):
        out.append(Finding("geometry",
                           f"{v['width']}x{v['height']} is not the {spec.name} spec "
                           f"{spec.width}x{spec.height}"))
    if v["fps"] < 29.0 and spec is not None and spec.height > spec.width:
        out.append(Finding("framerate", f"{v['fps']:.2f} fps — vertical judders below 30"))

    frozen = _freeze_spans(master, threshold_s=2.5)
    if frozen:
        out.append(Finding("static_frame",
                           f"{len(frozen)} frame(s) held beyond 2.5 s (first at {frozen[0]:.1f}s) "
                           "— a still frame reads as a slideshow"))

    if music_track is not None:
        cleared = set(music_track.get("cleared_for", []))
        for pl in platforms:
            if pl not in cleared:
                out.append(Finding(
                    "music_clearance",
                    f"track {music_track.get('id')!r} is not cleared for {pl} — "
                    "YouTube Audio Library terms do not carry to other platforms"))
    return out


def check_captions(captions: list[dict], spec: "PlatformSpec") -> list[Finding]:
    """Captions must clear the platform's own UI, or the viewer reads half of them."""
    out: list[Finding] = []
    safe = spec.caption_safe_area
    min_px = 56 * spec.width / 1080
    for c in captions:
        y = c.get("y_frac", 0.5)
        if y < safe.get("top", 0.0) or y > 1 - safe.get("bottom", 0.0):
            out.append(Finding("caption_safe_area",
                               f"caption at y={y:.2f} sits under the platform UI"))
        if c.get("size_px", min_px) < min_px:
            out.append(Finding("caption_size",
                               f"{c['size_px']}px is below the {min_px:.0f}px floor at this width"))
        if len(c.get("lines", [])) > 2:
            out.append(Finding("caption_lines", f"{len(c['lines'])} lines, maximum is 2"))
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
    return {"input_i": float(data["input_i"]), "input_tp": float(data["input_tp"]),
            "input_lra": float(data["input_lra"])}


def _mono_loudness(path: Path) -> float:
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
         "-af", "pan=mono|c0=0.5*c0+0.5*c1,loudnorm=I=-14:TP=-1:LRA=11:print_format=json",
         "-f", "null", "-"],
        capture_output=True, text=True,
    )
    blob = proc.stderr[proc.stderr.rfind("{"): proc.stderr.rfind("}") + 1]
    return float(json.loads(blob)["input_i"])


def _video_props(path: Path) -> dict:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,avg_frame_rate", "-of", "json", str(path)],
        check=True, capture_output=True, text=True,
    )
    st = json.loads(proc.stdout)["streams"][0]
    num, _, den = st["avg_frame_rate"].partition("/")
    fps = float(num) / float(den or 1)
    return {"width": st["width"], "height": st["height"], "fps": fps}


def _freeze_spans(path: Path, *, threshold_s: float) -> list[float]:
    """Timestamps where picture stopped moving for longer than the limit."""
    proc = subprocess.run(
        ["ffmpeg", "-hide_banner", "-nostats", "-i", str(path),
         "-vf", f"freezedetect=n=-60dB:d={threshold_s}", "-map", "0:v", "-f", "null", "-"],
        capture_output=True, text=True,
    )
    return [float(line.split("freeze_start:")[1].strip())
            for line in proc.stderr.splitlines() if "freeze_start:" in line]

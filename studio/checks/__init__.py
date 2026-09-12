"""Deterministic gate checks. No LLM runs here.

These are the objective half of every review loop, and they run first — there is
no point paying a critic to read a script whose citations are missing. A finding
is a fact with a location, never an opinion.
"""

from __future__ import annotations

import json
import math
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


def check_demand(demand: dict, pack: Pack, fmt: Format) -> list[Finding]:
    """A1's exit. The cheapest place to refuse a concept is before it is researched.

    Three categories destroy the revenue they generate — song mashups, film-scene
    recreation and COPPA kids content — so a producer that does not return a clear
    rights verdict with the paying alternative attached does not get to continue.
    """
    out: list[Finding] = []
    verdict = demand.get("rights_verdict")
    if verdict != "clear":
        note = demand.get("rights_notes") or "no reason recorded"
        out.append(Finding("rights", f"verdict {verdict!r}: {note}"))
        if not demand.get("paying_alternative"):
            out.append(Finding("rights", "a blocked concept must name the version that pays"))
    floor = float(pack.demand.get("min_revenue_per_gpu_hour", 4.0))
    rpgh = demand.get("revenue_per_gpu_hour")
    if rpgh is None:
        out.append(Finding("score", "revenue_per_gpu_hour not computed"))
    elif rpgh < floor:
        out.append(Finding(
            "score",
            f"${rpgh:.1f} per GPU hour is below the {pack.name} floor of ${floor:.1f}"
            f" at {fmt.gpu_budget_hours}h per episode — not worth the electricity",
        ))
    if not demand.get("evidence"):
        out.append(Finding("evidence", "no basis recorded for the RPM and volume estimates"))
    return out


def check_beats(beats: list[dict], fmt: Format, pack: Pack) -> list[Finding]:
    """Clippable moments are marked here or hunted for later at far greater cost."""
    out: list[Finding] = []
    if not beats:
        return [Finding("beats", "empty beat sheet")]
    if beats[0]["kind"] != "cold_open":
        out.append(Finding("structure", f"first beat is {beats[0]['kind']!r}, not a cold open"))
    if pack.narrative.get("end_hook") and beats[-1]["kind"] != "loop":
        out.append(Finding("structure", "pack requires an end hook; last beat is not a loop"))
    if not any(b.get("clippable") for b in beats):
        out.append(Finding("clippable", "no beat marked clippable — B10 has nothing to cut"))
    total = sum(b["target_seconds"] for b in beats) / 60
    lo, hi = fmt.length_minutes
    if not lo <= total <= hi:
        out.append(Finding("length", f"beats total {total:.1f} min, format wants {lo}-{hi}"))
    return out


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
    known = {s["id"] for s in sources}
    for c in script_chunks:
        sid = c.get("source_id")
        if sid and sid not in known:
            out.append(Finding("citations", f"unknown source id {sid!r} in {c['text'][:40]!r}"))
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
    #
    # But most of the drop is arithmetic, not cancellation: BS.1770 sums channel
    # power, so two identical channels measure 10*log10(2) = 3.01 LU louder than
    # the same signal folded down. Measured on real files this session — dual mono
    # drops 3.00 LU with nothing wrong with it, fully uncorrelated L/R drops 6.00,
    # and a phase-inverted pair drops to silence. Subtract the offset and what is
    # left is the cancellation. A narration-led mix with a wide music bed lands
    # near 0.7 LU of it, which is why the limit is 1.5 and not 3.
    channels = _audio_channels(master)
    if channels == 2:
        excess = a["input_i"] - _mono_loudness(master) - 10 * math.log10(2)
        if excess > 1.5:
            out.append(Finding(
                "mono_folddown",
                f"{excess:.1f} LU lost folding to mono beyond the 3.0 LU channel-sum "
                "offset — phase cancellation is eating the dialogue"))

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


def _audio_channels(path: Path) -> int:
    """Fold-down only means something for stereo. A mono master is trivially
    mono-compatible, and `pan=mono|c0=0.5*c0+0.5*c1` would read a channel it has
    not got."""
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "a:0",
         "-show_entries", "stream=channels", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True, check=True,
    )
    return int(proc.stdout.strip() or 0)


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

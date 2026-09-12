"""The stage runner.

Reads its stage list from the format, not from code, so a listicle that skips
casting and a music video that composes before picture are both config changes.
Every stage goes through `Store.step`, which is what makes a crashed run resumable
rather than expensive.
"""

from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

from studio.checks import Finding, check_licences, check_master, check_picture, check_script
from studio.core.briefs import SPECS, records_step
from studio.core.cas import AssetStore, hash_inputs
from studio.core.config import Format, Pack, PlatformSpec
from studio.core.errors import PipelineHalt
from studio.core.schemas import GATES, Stage
from studio.core.state import Store
from studio.render.assemble import concat_clips, mix_audio, mux, probe
from studio.render.verticals import cut_vertical


class GateBlocked(PipelineHalt):
    """A lock did not open. Either a check failed or no human has decided yet."""


class AwaitingAgent(PipelineHalt):
    """A judgement stage has no ingested artefact yet.

    Not a failure. The run has walked as far as determinism can take it and is
    waiting for a Claude Code agent to do the thinking and hand the result back
    through `studio ingest`.
    """

    def __init__(self, stage: Stage, agent: str, episode_id: str) -> None:
        self.stage, self.agent = stage, agent
        super().__init__(
            f"{stage.value} is owned by {agent} — run"
            f" `studio brief --episode {episode_id} --stage {stage.value} --json`"
        )


@dataclass
class Context:
    episode_id: str
    topic: str
    root: Path            # channels/<slug>/episodes/EPnn
    store: Store
    cas: AssetStore
    fmt: Format
    pack: Pack
    providers: dict
    auto_approve_as: str | None = None   # mock/dev only; never a real publish path
    text_mode: str = "mock"              # "agent" hands the text stages to subagents

    def path(self, *parts: str) -> Path:
        p = self.root.joinpath(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def write_json(self, name: str, data) -> Path:
        p = self.path(name)
        p.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return p

    def read_json(self, name: str):
        return json.loads(self.path(name).read_text())


# --------------------------------------------------------------------------
# Stages. Each returns the path of its principal artefact.
# --------------------------------------------------------------------------

def a1_validate(ctx: Context) -> Path:
    return ctx.write_json("demand.json", {
        "topic": ctx.topic, "rights_verdict": "clear",
        "projected_rpm": 8.0, "competition_density": 0.4, "demand_volume": 20000,
        "niche_score": round(8.0 * 20000 * (1 / 0.4) / 1000, 1),
        "angle": f"The part of {ctx.topic} nobody explains",
    })


def a2_research(ctx: Context) -> Path:
    n = int(ctx.pack.research.get("min_sources", 5))
    ctx.write_json("sources.json", [
        {"id": f"s{i}", "tier": ctx.pack.research["tiers"][i % len(ctx.pack.research["tiers"])],
         "title": f"Source {i} on {ctx.topic}", "url": f"https://example.invalid/{i}"}
        for i in range(n)
    ])
    p = ctx.path("research.md")
    p.write_text(f"# {ctx.topic}\n\nMock research body.\n", encoding="utf-8")
    return p


def a3_series(ctx: Context) -> Path:
    return ctx.write_json("series.json", {
        "topic": ctx.topic,
        "episodes": [{"number": i + 1, "promise": f"Episode {i + 1} promise",
                      "cliffhanger": f"Hook into {i + 2}"} for i in range(8)],
    })


def a4_look_cast(ctx: Context) -> Path:
    """A host is required by nearly every format — a consistent face in the
    thumbnail is among the strongest click-through levers a faceless channel has."""
    chars = []
    if ctx.fmt.host_required:
        chars.append({"id": "host-01", "name": "The Narrator", "role": "host",
                      "canon": {"look": "mid-30s, neutral studio lighting"},
                      "likeness_checked_at": "mock"})
    if ctx.fmt.cast_required:
        chars.append({"id": "cast-01", "name": "Lead", "role": "cast",
                      "canon": {"look": "period dress"}, "likeness_checked_at": "mock"})
    for c in chars:
        ctx.store.conn.execute(
            "INSERT OR REPLACE INTO characters(id, name, role, version, canon_json,"
            " likeness_checked_at) VALUES (?,?,?,1,?,?)",
            (c["id"], c["name"], c["role"], json.dumps(c["canon"]), c["likeness_checked_at"]),
        )
    ctx.store.conn.commit()
    return ctx.write_json("cast.json", chars)


def b1_package(ctx: Context) -> Path:
    """Written before the script. If the promise does not fit in eight words, the
    topic is not ready, and that is cheaper to learn here than after rendering."""
    return ctx.write_json("packaging.json", {
        "titles": [f"The truth about {ctx.topic}", f"Why {ctx.topic} still matters"],
        "thumbnail_concept": "Host, wide eyes, one bold number",
        "promise": f"What {ctx.topic} actually changed",
    })


def b2_beats(ctx: Context) -> Path:
    """Clippable moments are marked here, not hunted for after the master exists."""
    lo, hi = ctx.fmt.length_minutes
    total = (lo + hi) / 2 * 60
    plan = [("cold_open", 0.08, True), ("promise", 0.10, False),
            ("escalation", 0.30, True), ("escalation", 0.28, True),
            ("payoff", 0.16, True), ("loop", 0.08, False)]
    beats = [{"id": f"b{i}", "kind": k, "summary": f"{k} of {ctx.topic}",
              "target_seconds": round(total * frac, 1), "clippable": clip}
             for i, (k, frac, clip) in enumerate(plan)]
    return ctx.write_json("beats.json", beats)


def b3_script(ctx: Context) -> Path:
    """Chunked per sentence with an authored pause on each — Kokoro emits flat
    continuous speech, so breath is written, not hoped for."""
    beats = ctx.read_json("beats.json")
    sources = ctx.read_json("sources.json")
    chunks = []
    for bi, b in enumerate(beats):
        sentences = max(2, int(b["target_seconds"] / 12))
        for si in range(sentences):
            chunks.append({
                "beat_id": b["id"],
                "text": f"{b['summary']}, part {si + 1}. "
                        f"This is mock narration standing in for real prose.",
                "pause_ms": 700 if si == sentences - 1 else 320,
                "needs_citation": si == 0,
                "source_id": sources[bi % len(sources)]["id"],
            })
    return ctx.write_json("script.json", chunks)


def b5_voice(ctx: Context) -> Path:
    """Narration first. Picture is cut to it, never the reverse."""
    chunks = ctx.read_json("script.json")
    tts, align = ctx.providers["tts"], ctx.providers["align"]
    parts, cursor_ms, timeline = [], 0, []
    for i, c in enumerate(chunks):
        wav = tts.speak(c["text"], ctx.path("vo", f"chunk{i:03d}.wav"), voice="af", lang="en")
        dur_ms = int(float(probe(wav)["format"]["duration"]) * 1000)
        timeline.append({"beat_id": c["beat_id"], "start_ms": cursor_ms,
                         "end_ms": cursor_ms + dur_ms, "text": c["text"]})
        cursor_ms += dur_ms + c["pause_ms"]
        parts.append((wav, c["pause_ms"]))
    vo = _concat_with_silence(parts, ctx.path("vo_en.wav"))
    ctx.write_json("vo_timeline.json", timeline)
    ctx.write_json("alignment.json", align.align(vo, " ".join(c["text"] for c in chunks)))
    return vo


def b6_shots(ctx: Context) -> Path:
    """Shot durations fall out of the narration rather than being guessed."""
    timeline = ctx.read_json("vo_timeline.json")
    cast = {c["id"] for c in ctx.read_json("cast.json")}
    max_ms = int(ctx.fmt.mean_shot_seconds_max * 1000)
    shots, idx = [], 0
    for si, seg in enumerate(timeline):
        # A segment runs to the start of the next one, not to its own end: the
        # authored pause between sentences is still picture time and must be
        # covered, or the timeline has holes the animatic check will reject.
        seg_end = timeline[si + 1]["start_ms"] if si + 1 < len(timeline) else seg["end_ms"]
        span = seg_end - seg["start_ms"]
        n = max(1, -(-span // max_ms))          # ceil: keeps mean under the cap
        step = span // n
        for k in range(n):
            start = seg["start_ms"] + k * step
            end = seg_end if k == n - 1 else start + step
            shots.append({"idx": idx, "beat_id": seg["beat_id"],
                          "start_ms": start, "end_ms": end,
                          "prompt": f"{seg['text'][:70]} — frame {k}",
                          "character_ids": ["host-01"] if (idx == 0 and cast) else [],
                          "motion": "parallax"})
            idx += 1
    ctx.write_json("shots.json", shots)

    image, video = ctx.providers["image"], ctx.providers["video"]

    def render(s: dict) -> tuple[int, Path]:
        still = image.generate(s["prompt"], ctx.path("stills", f"{s['idx']:03d}.png"),
                               width=1920, height=1080)
        clip = video.animate(still, ctx.path("clips", f"{s['idx']:03d}.mp4"),
                             duration_ms=s["end_ms"] - s["start_ms"], motion=s["motion"])
        return s["idx"], clip

    # Shots are independent, and every provider shells out to a subprocess, so a
    # thread pool actually parallelises here despite the GIL.
    with ThreadPoolExecutor(max_workers=min(8, os.cpu_count() or 4)) as pool:
        rendered = sorted(pool.map(render, shots))
    return concat_clips([c for _, c in rendered], ctx.path("picture.mp4"))


def b8_post(ctx: Context) -> Path:
    mixed = mix_audio(ctx.path("vo_en.wav"), _pick_music(ctx), ctx.path("mix.wav"))
    return mux(ctx.path("picture.mp4"), mixed, ctx.path("master.mp4"))


def b10_multiply(ctx: Context) -> Path:
    """Six to eight verticals from moments that were designed to stand alone."""
    spec = PlatformSpec.load("vertical")
    beats = {b["id"]: b for b in ctx.read_json("beats.json")}
    timeline = ctx.read_json("vo_timeline.json")
    clippable = [t for t in timeline if beats[t["beat_id"]]["clippable"]]
    made = []
    for i, seg in enumerate(clippable[:8]):
        end = min(seg["end_ms"], seg["start_ms"] + spec.max_seconds * 1000)
        out = cut_vertical(ctx.path("master.mp4"), ctx.path("verticals", f"v{i:02d}.mp4"),
                           start_ms=seg["start_ms"], end_ms=end,
                           width=spec.width, height=spec.height)
        made.append({"file": str(out), "beat_id": seg["beat_id"],
                     "hooks": {t: f"Hook for {t}: {seg['text'][:40]}" for t in spec.targets}})
    return ctx.write_json("verticals.json", made)


def b11_distribute(ctx: Context) -> Path:
    pub = ctx.providers["publish"]
    packaging = ctx.read_json("packaging.json")
    posted = [{"platform": "youtube-long",
               "external_id": pub.publish(ctx.path("master.mp4"),
                                          {"title": packaging["titles"][0],
                                           "promise": packaging["promise"]})}]
    for v in ctx.read_json("verticals.json"):
        for target, hook in v["hooks"].items():
            posted.append({"platform": target,
                           "external_id": pub.publish(Path(v["file"]), {"hook": hook})})
    return ctx.write_json("posted.json", posted)


# --------------------------------------------------------------------------
# Gates
# --------------------------------------------------------------------------

def _gate(ctx: Context, stage: Stage, findings: list[Finding], score: float) -> Path:
    """Deterministic checks, then a score, then a human. Never a score alone."""
    gate = GATES[stage]
    iteration = ctx.store.gate_iterations(ctx.episode_id, gate) + 1
    payload = {"total": score, "findings": [str(f) for f in findings]}
    decided_by = ctx.auto_approve_as if not findings else None
    ctx.store.record_gate(ctx.episode_id, gate, iteration, payload, decided_by=decided_by)
    if findings:
        cap = int(ctx.pack.rubric().get("max_iterations", 3))
        msg = f"{gate} blocked by {len(findings)} check(s): " + "; ".join(str(f) for f in findings[:4])
        if iteration > cap:
            # A score that stops improving means the problem is upstream, and more
            # rewriting will not fix it. Escalate with the trend rather than loop.
            trend = ctx.store.gate_trend(ctx.episode_id, gate)
            msg += (f" — {iteration} iterations exceeds the cap of {cap}; score trend"
                    f" {trend}. Fix this upstream, not by rewriting again.")
        raise GateBlocked(msg)
    if not ctx.store.gate_is_open(ctx.episode_id, gate):
        raise GateBlocked(f"{gate} needs a recorded human decision — "
                          f"run `studio approve {ctx.episode_id} {gate} --as <name>`")
    return ctx.write_json(f"{gate.lower()}.json", payload)


def b4_script_review(ctx: Context) -> Path:
    findings = check_script(ctx.read_json("script.json"),
                            ctx.read_json("packaging.json"),
                            ctx.read_json("sources.json"))
    return _gate(ctx, Stage.B4_SCRIPT_REVIEW, findings, _critic_score(ctx))


def _critic_score(ctx: Context) -> float:
    """The critic's number, from the critic. Never from the agent that wrote the script."""
    if ctx.text_mode != "agent":
        return 86.0
    path = ctx.path("critique.json")
    if not path.exists():
        raise AwaitingAgent(Stage.B4_SCRIPT_REVIEW, "studio-critic", ctx.episode_id)
    return float(json.loads(path.read_text())["total"])


def b7_animatic_review(ctx: Context) -> Path:
    registered = {r[0] for r in ctx.store.conn.execute("SELECT id FROM characters")}
    findings = check_picture(ctx.read_json("shots.json"), registered, ctx.fmt)
    return _gate(ctx, Stage.B7_ANIMATIC_REVIEW, findings, 88.0)


def b9_master_qc(ctx: Context) -> Path:
    findings = check_master(ctx.path("master.mp4"), ["youtube-long"], _music_meta(ctx))
    findings += check_licences(ctx.fmt.providers if ctx.providers.get("_real") else {})
    return _gate(ctx, Stage.B9_MASTER_QC, findings, 90.0)


STAGES = {
    Stage.A1_VALIDATE: a1_validate, Stage.A2_RESEARCH: a2_research,
    Stage.A3_SERIES: a3_series, Stage.A4_LOOK_CAST: a4_look_cast,
    Stage.B1_PACKAGE: b1_package, Stage.B2_BEATS: b2_beats, Stage.B3_SCRIPT: b3_script,
    Stage.B4_SCRIPT_REVIEW: b4_script_review, Stage.B5_VOICE: b5_voice,
    Stage.B6_SHOTS: b6_shots, Stage.B7_ANIMATIC_REVIEW: b7_animatic_review,
    Stage.B8_POST: b8_post, Stage.B9_MASTER_QC: b9_master_qc,
    Stage.B10_MULTIPLY: b10_multiply, Stage.B11_DISTRIBUTE: b11_distribute,
}


def step_hash(topic: str, fmt_name: str, pack_name: str, stage: Stage) -> str:
    """The one definition of a step's identity. `studio ingest` recomputes it, so
    a divergence here would silently re-run every stage on the next walk."""
    return hash_inputs(topic, fmt_name, pack_name, stage.value)


def run(ctx: Context) -> list[tuple[Stage, bool]]:
    """Walk the format's stage list. Returns (stage, was_skipped) per stage."""
    results = []
    for stage in ctx.fmt.stages:
        fn = STAGES.get(stage)
        if fn is None:
            continue
        ihash = step_hash(ctx.topic, ctx.fmt.name, ctx.pack.name, stage)
        if ctx.store.completed(ctx.episode_id, stage, ihash):
            results.append((stage, True))
            continue
        if ctx.text_mode == "agent" and records_step(stage):
            # Judgement stages are not computed here. The walk stops and names the
            # agent that owes the artefact; `studio ingest` records the step, and
            # the next walk skips it under the ordinary resume rule.
            raise AwaitingAgent(stage, SPECS[stage].agent, ctx.episode_id)
        with ctx.store.step(ctx.episode_id, stage, ihash) as out:
            out[0] = str(fn(ctx))
        results.append((stage, False))
    return results


# --------------------------------------------------------------------------

def _concat_with_silence(parts: list[tuple[Path, int]], out: Path) -> Path:
    import subprocess
    inputs, filters = [], []
    for i, (wav, pause_ms) in enumerate(parts):
        inputs += ["-i", str(wav)]
        filters.append(f"[{i}:a]apad=pad_dur={pause_ms / 1000:.3f}[a{i}]")
    chain = ";".join(filters) + ";" + "".join(f"[a{i}]" for i in range(len(parts)))
    chain += f"concat=n={len(parts)}:v=0:a=1[out]"
    subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *inputs,
         "-filter_complex", chain, "-map", "[out]", "-ar", "48000", "-ac", "1", str(out)],
        check=True, capture_output=True,
    )
    return out


def _pick_music(ctx: Context) -> Path | None:
    return None if _music_meta(ctx) is None else Path(_music_meta(ctx)["file"])


def _music_meta(ctx: Context) -> dict | None:
    manifest = json.loads((Path(__file__).resolve().parents[1] / "music" / "manifest.json").read_text())
    tracks = manifest.get("tracks", [])
    return tracks[0] if tracks else None

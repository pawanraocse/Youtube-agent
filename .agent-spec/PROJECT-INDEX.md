# PROJECT-INDEX

## What this is

A zero-marginal-cost video studio that turns a topic into published, monetised video
series across YouTube, Facebook, Instagram and TikTok. It is built to run several
channels at once, because one channel is a single bet and the only reason to automate
this work is that the fifth channel costs the same as the first.

The design splits cleanly in two: judgement lives in Claude Code subagents and skills,
and everything deterministic lives behind a Python CLI called `studio` that emits JSON.
The full plan is at `~/.claude/plans/we-create-plan-sleepy-moth.md`.

## Stack

| | |
|---|---|
| Language | Python 3.12.2, `requires-python = ">=3.11"` |
| Runtime deps | `pydantic>=2.7`, `pyyaml>=6.0` — that is the entire list |
| Dev deps | `pytest>=8.0` |
| Packaging | `uv` + `hatchling`, wheel packages `studio` |
| Media | FFmpeg 4.4.2 shelled out via `subprocess`, never a Python binding |
| Storage | SQLite (`data/studio.db`) plus a content-addressed asset store |
| Size | 1,862 lines across 16 source and 7 test files. Graph: 23 files, 24 internal edges, 0 cycles, 0 layer violations |

## Module map

| Module | Purpose |
|---|---|
| `studio/core/schemas.py` | Pydantic contracts that cross the skill/CLI boundary. 6 models, 16 stages, 3 gates |
| `studio/core/state.py` | SQLite schema, the state machine, and the resume rule everything depends on |
| `studio/core/config.py` | Loads `packs/`, `formats/`, `platforms/`, `licenses.yaml`. Knows nothing about video |
| `studio/core/cas.py` | Content-addressed asset store, so identical prompts never regenerate |
| `studio/providers/base.py` | 8 narrow `Protocol` interfaces — text, image, video, stock, tts, align, depth, publish |
| `studio/providers/mock.py` | Mock implementations that emit real FFmpeg media, not empty paths |
| `studio/checks/__init__.py` | Deterministic gate checks. No LLM runs here |
| `studio/render/assemble.py` | Concat, sidechain-ducked mix, loudness-normalised mux |
| `studio/render/verticals.py` | Portrait crops for Shorts, Reels and TikTok |
| `studio/pipeline.py` | The stage runner. Reads its stage list from the format, not from code |
| `studio/__main__.py` | The CLI. Every subcommand takes `--json` |

Most-depended modules, by internal import count: `core.config` (5), `core.schemas` (5),
`checks` (4), `core.state` (4).

## Config trees

`packs/` subject matter · `formats/` production shape and stage list · `rubrics/`
agent-immutable critic rubrics · `platforms/` geometry and caption safe areas ·
`licenses.yaml` the commercial-use audit · `music/manifest.json` per-platform clearance.

`comfy/`, `characters/` and `shows/` exist but are empty — they are populated at M2.

## Commands

```bash
uv sync --extra dev                                    # install
python3 -m pytest -q                                   # test — 31 pass in ~9s
python3 -m studio --json run --topic "<topic>" --providers mock --auto-approve <name>
python3 -m studio status
python3 -m studio licence-audit --format data-explainer
python3 -m studio approve <episode> <gate> --as <name>
```

Entry point is `studio = "studio.__main__:main"`.

## Where things stand

M0 is complete and committed: the pipeline walks all fifteen stages on mocks in 43.9s
and emits a 1920×1080 master at −14.06 LUFS plus eight 1080×1920 verticals, spending
nothing. Re-running is a 0.28s no-op. The production standard is enforced by
`check_master` and `check_captions`.

M1 is next: the real research, writing and critic agents. No `.claude/agents/*.md` or
`.claude/skills/*/SKILL.md` exist yet — both directories are empty.

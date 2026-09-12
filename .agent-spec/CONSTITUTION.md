# CONSTITUTION

Rules that hold across this project. Every line points at a file that was read.

## 1. Project context

A multi-channel AI video studio built to earn money at zero marginal cost. Reasoning
runs on a Claude Code subscription with Gemini free tier and Ollama as fallbacks; media
generation runs locally on an RTX 5070 with 8151 MiB VRAM.

Three constraints shape every decision, and all three are load-bearing:

- **Zero marginal cost.** No API bill at any stage. Any change that introduces a
  recurring per-unit cost needs an explicit decision, not a default.
- **8 GB VRAM.** Full AI video cannot be the primary renderer. The default path is
  stills plus 2.5D parallax; AI video is reserved for a few hero shots.
- **Commercial monetisability.** Every model weight must permit commercial use and
  every music track must be cleared on every platform it is posted to. `licenses.yaml`
  is the record and `studio licence-audit` is the enforcement.

Commit subjects are sentence-case prose describing the change and its reasoning, with a
body explaining why (`git log`, 2 commits).

## 2. Hard dependencies

The real list from `pyproject.toml`, not what is conventional for the stack:

- `pydantic>=2.7` — validation at the skill/CLI boundary only
- `pyyaml>=6.0` — config trees
- `pytest>=8.0` — dev only

That is everything. There is no LangChain, no LangGraph, no Temporal, no ORM, no
logging framework and no HTTP client. **Adding a runtime dependency is a decision to
justify, not a convenience.** Temporal was considered and rejected in the plan: SQLite
plus content addressing is ~250 lines and is the right size for one person on a laptop.

FFmpeg is a hard external dependency, invoked as a subprocess. Verified present:
`loudnorm`, `sidechaincompress`, `zoompan`, `atempo`, `minterpolate`, `subtitles`, and
`h264_nvenc` for hardware encoding.

## 3. Custom project rules

**Judgement and determinism never mix.** Agents reason; the `studio` CLI does not. The
CLI contains no LLM calls, and agents do not compute. The contract between them is
`studio <cmd> --json` in, `studio ... --input <file>` out. Nothing else crosses.
(`studio/__main__.py`, plan §Architecture.)

**`from __future__ import annotations` at the top of every module.** Present in all 11
non-empty source files.

**Pydantic is the boundary layer, dataclasses are internal.** `BaseModel` appears only
in `core/schemas.py` (6 models) — the artefacts agents produce. Internal structures use
`@dataclass`, frozen where they are config (`core/config.py`, `core/state.py`,
`pipeline.py`, `checks/__init__.py`).

**Provider interfaces are `Protocol`, and callers never branch on the implementation.**
8 protocols in `providers/base.py`. The active chain is chosen by config, so swapping a
vendor touches YAML and no Python.

**The stage list comes from `formats/<name>.yaml`, never from code.** `pipeline.run()`
iterates `ctx.fmt.stages`. A listicle that skips casting and a music video that composes
before picture are both config changes. (`studio/pipeline.py:run`.)

**The resume rule is the one invariant everything rests on:** a step is skipped if and
only if a `steps` row exists with a matching `input_hash` and `status='ok'`.
(`core/state.py:completed`.) Any new stage goes through `Store.step` or it is not
resumable.

**Locks open on a recorded human decision and on nothing else.** `gate_is_open()`
rejects `NULL` and rejects `'agent'` explicitly. A critic score, however high, is not a
decision. This is both the quality mechanism and the evidence trail that keeps channels
monetisable. (`core/state.py:gate_is_open`.)

**No agent reviews its own output, and rubrics are agent-immutable.** Writer ≠ critic,
visual-director ≠ reviewer, producer ≠ compliance. (plan §Nine agents; `rubrics/`.)

**Deterministic checks run before any critic.** There is no point paying a model to read
a script whose citations are missing. A `Finding` is a fact with a location, never an
opinion. (`checks/__init__.py`.)

**Every check has a known-bad fixture it must catch and a known-good it must pass.**
`tests/test_checks.py` and `tests/test_production_standard.py` — the latter builds
non-conforming files with FFmpeg rather than asserting against mocks.

**Every `subprocess.run` passes `capture_output=True`, and every *producing* call also
passes `check=True`.** 10 call sites, 7 with `check=True`. A failing FFmpeg must raise
rather than leave a silent empty file behind. The 3 exceptions are the analysis probes in
`checks/__init__.py` (`_loudness`, `_mono_loudness`, `_freeze_spans`), which parse stderr
instead — see §5, this is debt rather than a convention.

**Errors propagate.** One broad `except` exists in the codebase, in
`core/state.py:step`, and it records the failure to the step ledger and re-raises. There
is no swallowing anywhere.

**Output goes through the CLI, not through `print`.** Zero `print()` calls outside
`__main__.py`. `_emit()` is the single output surface and honours `--json`.

## 4. Banned practices

- **No non-commercial model weights.** `licenses.yaml` names five that are forbidden by
  reason: FLUX.1-dev, XTTS-v2, MusicGen, HunyuanVideo, Edge TTS. Also Wav2Lip, whose
  weights are research-only. `check_licences` fails on any of them, and fails on a
  weight that is merely unverified.
- **Never generate music.** The library is downloaded once from CC0 and public-domain
  sources and tagged with per-platform clearance. YouTube Audio Library terms do not
  carry to Facebook, Instagram or TikTok.
- **Never copy code from the reference repositories.** They are read for design lessons
  only; one of the five has no licence file at all. (plan §Reference repositories.)
- **No `print()` in library code**, no bare `except`, no swallowed exceptions.
- **No orchestration framework.** SQLite and content addressing, deliberately.
- **Never let appearance prose reach a renderer.** Shot lists carry `character_ids`;
  rendering resolves canon from the registry. A shot naming an unregistered character
  fails validation and the episode cannot advance. (`checks.check_picture`.)
- **Never auto-publish.** `--auto-approve` exists for mock and dev runs only and records
  the operator name; it must never be wired into a real publish path.
  (`pipeline.Context.auto_approve_as`.)

## 5. Known debt

- **Three FFmpeg analysis probes swallow failure.** `checks/__init__.py:168,180,204` call
  `subprocess.run` without `check=True` and then parse stderr for a JSON blob. If FFmpeg
  fails, the caller sees a `JSONDecodeError` on an empty slice rather than the real error,
  which makes a bad master look like a broken check. Logged as `DEBT-001`.
- **SQL leaks outside `core/`.** `pipeline.py` (3 sites) and `__main__.py` (1 site) call
  `store.conn.execute` directly rather than going through a `Store` method. The boundary
  is otherwise clean; these four should become named methods.
- **No logging at all.** Zero `import logging`. Acceptable while the CLI is the only
  surface, but long unattended renders will eventually need it. [INFERRED]
- `comfy/`, `characters/` and `shows/` are empty directories the plan names but M0 did
  not populate.

## 6. Resolved by the developer (2026-09-12)

**Local only.** Nothing leaves this machine except finished uploads through the platform
APIs. There is no cloud render path, and adding one would break the zero-marginal-cost
constraint in §1 — treat a proposal to burst to a rented GPU as a change to the project's
premise, not an optimisation.

**Own tooling, not a product.** No multi-tenancy, no auth, no billing, no API stability
obligation. Optimise for speed of change: refactor the CLI surface freely, and do not add
abstraction whose only justification is a hypothetical second user. The plan notes that
operating this for others is the highest-probability revenue in the document; that
remains a business option and is explicitly *not* a design constraint today.

**Assets: keep masters, prune intermediates.** Once an episode reaches `PUBLISHED`, the
per-shot stills, clips and chunk WAVs are deletable; masters, verticals, thumbnails and
every database row are kept. Content addressing means a pruned intermediate can be
regenerated from the same prompt at the same hash, so pruning costs GPU time and nothing
else. Not yet implemented — no `studio prune` exists, and the store currently grows
without bound.

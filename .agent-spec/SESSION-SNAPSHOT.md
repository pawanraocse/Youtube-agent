# Session Snapshot — 2026-09-12 (M0 build + onboarding)

## Session Summary

Planned and built M0 of a multi-channel AI video studio, then onboarded the project.

The plan went through seven rounds of revision, and the important changes were all
reductions. Agents went 18 → 9, skills 18 → 9, and three genre packs became one. The
biggest single correction was reordering the pipeline around how a working creator
actually operates: packaging (title and thumbnail concept) is written *before* the
script, and voice-over is recorded *before* picture is cut. Every AI pipeline surveyed
does both backwards.

M0 is complete and committed. The pipeline walks all fifteen stages on mock providers in
43.9 s and emits a 1920×1080 master at −14.06 LUFS plus eight 1080×1920 verticals,
spending nothing. Re-running is a 0.28 s no-op.

## Current Pipeline Gate

Gate 0 closed (onboarding complete). M1 — the real research, writing and critic agents —
is next.

## Files Changed

- `studio/core/{schemas,state,cas,config}.py` — contracts, the resume rule, the asset store
- `studio/providers/{base,mock}.py` — 8 Protocol interfaces plus mocks that emit real media
- `studio/checks/__init__.py` — deterministic gate checks and the production standard
- `studio/render/{assemble,verticals}.py` — ducked mix, loudness master, portrait crops
- `studio/pipeline.py`, `studio/__main__.py` — stage runner and CLI
- `packs/`, `formats/`, `rubrics/`, `platforms/`, `licenses.yaml` — the config trees
- `tests/` — 31 tests
- `.agent-spec/{PROJECT-INDEX,CONSTITUTION}.md` — written this session

## Corrections Made To My Own Earlier Work

Worth recording, because all four were caught by verification rather than by review:

- The first CONSTITUTION draft claimed 9 Protocol classes, 7 Pydantic models, 6 test
  files, and that all 10 `subprocess.run` sites pass `check=True`. The real numbers are
  8, 6, 7 and 7-of-10. Counting `grep` hits included import lines.
- That last one was not a documentation slip. Three FFmpeg analysis probes genuinely omit
  `check=True` and parse stderr, so a failed probe is indistinguishable from a bad
  master. Logged as `DEBT-001`.
- During M0 bring-up the picture check caught a real bug in my own shot planner: shots
  left holes in the timeline wherever an authored narration pause fell. Fixed by having
  each segment run to the *next* segment's start rather than to its own end.
- The first acceptance run took 61 s against a 60 s budget. Parallelising the per-shot
  render across a thread pool and dropping the mock encoder to `ultrafast` brought it to
  43.9 s.

## Decisions Locked

- Two layers only: judgement in Claude Code agents, determinism behind `studio --json`.
- The stage list lives in `formats/<name>.yaml`, never in code.
- Locks open on a recorded human decision and on nothing else.
- Portfolio of channels in cohorts of three, ninety-day numeric kill gates.
- Niches ranked by revenue per GPU hour, not RPM. Mythology moved to cohort two.
- Commit to a stylised look rather than photoreal humans — 8 GB cannot win the uncanny
  valley, and style has no valley to fall into.

## Open Decisions Requiring Developer Input

- Deployment target: nothing in the repo says whether renders ever leave this machine.
- Whether the pipeline itself becomes a product, which would change API stability needs.
- Asset retention: the content-addressed store grows without bound and nothing prunes it.

## Next Session: Load These Files

- `~/.claude/plans/we-create-plan-sleepy-moth.md` — the full plan
- `.agent-spec/CONSTITUTION.md`
- `studio/pipeline.py` — M1 adds real agents behind the same stage functions

---


# Session Snapshot — 2026-09-12 (evening)

## Session Summary

M1 is complete and its acceptance test passes on a real topic. The milestone added the
two commands that carry the skill/CLI contract, four agents, two skills, and the
validation layer that sits between them. Two defects found while testing were then fixed
in a second commit, one of which meant LOCK 3 could never have opened.

**M1 — real agents behind a validating boundary** (`f652ac7`). `studio brief --episode
<id> --stage <S> --json` hands an agent the topic, pack, format, rubric, the JSON Schema
of the artefact it owes and the upstream artefacts it must write against. `studio ingest
--episode <id> --stage <S> --input <file>` validates the reply, runs the stage's
deterministic checks, writes the artefact and records the step. Nothing else crosses that
boundary, which is what keeps the CLI free of reasoning and the agents free of arithmetic.

One registry, `studio/core/briefs.py`, backs all three callers — the brief builder, the
validator and the pipeline's question of whether a stage is agent-owned. Keeping them on
one table is deliberate: a brief and a validator that drift apart is the failure that
makes an agent produce something plausible that nothing downstream can read.

In agent mode the walk no longer computes the text stages. It stops at the first stage an
agent owns, names that agent, and exits 4 with an `awaiting` field. Ingest records the
step under the ordinary resume rule, so the next walk skips it.

**Two decisions inside that boundary are load-bearing and easy to undo by accident.**
First, ingest does not record a step for B4. A critique is an *input* to a lock, not the
lock's completion; a recorded B4 would let the walk skip the gate entirely and LOCK 1
would open on a score, which is exactly what `gate_is_open` exists to prevent. Second,
ingest computes what the agents must not: `revenue_per_gpu_hour` and `niche_score` are
derived from the producer's estimates rather than supplied by it, and the critic's
weighted total is recomputed against the rubric so a critic cannot round itself into a
pass. Arithmetic done in an agent's head is arithmetic nobody can audit.

**M1 acceptance, run on a real topic** — the Panama Canal water crisis, `trade-atlas-EP01`,
on `data-explainer` × `geography-economics` as the developer chose. A1 returned a `clear`
rights verdict at $31.5 revenue per GPU hour against the pack floor of 20.0, with demand
evidence scraped from YouTube result pages rather than estimated. A2 returned 22 sources
across four tiers. A3 returned an eight-episode series map. B1–B3 returned packaging, a
six-beat sheet totalling 420 s with four clippable moments, and a 77-chunk 963-word script
carrying 42 citations. B4 scored it 80.45 and the episode is held at LOCK 1. No paid API
call at any point.

The agent independence earned its place rather than being decoration. The researcher found
the producer's central figure — 197,000 m³ of lake water per transit — has no primary ACP
source, and found something stronger: the canal *publishes* a water price in Official
Tariff item 1500.0000 as a curve inflecting at 82 feet of lake depth. The producer rebuilt
episode one on that. The critic then caught a mis-citation nothing downstream would have —
chunk 24 claims "three separate outlets confirm the figure" citing `s16`, whose `supports`
field records one — and explicitly refused to inflate its score to clear the threshold.

**DEBT-003 and DEBT-004 fixed** (`4a7749b`). Both are written up in full in the register;
the short version is that between them they stopped every mock walk at B9, so `b10_multiply`
and `b11_distribute` had no end-to-end coverage from commit `ff509e7` until now.

## Current Pipeline Gate

Gate 0 closed. M1 complete; M2 (look and cast) is next.

## Corrections to My Own Earlier Work

- **I wrote a test that encoded a broken expectation.** The first version of
  `test_mock_mode_is_unaffected_by_agent_mode` asserted a full mock walk to B11 and
  failed. Rather than assume my change had caused it, I stashed the working tree and
  re-ran on the baseline: identical failure, so it predated M1. I rewrote the test to
  assert the invariant M1 could actually have broken — that mock mode never waits on an
  agent — and logged the real defects separately. After fixing them the test asserts the
  full walk again.
- **DEBT-001's line numbers in the register were stale** after I added a probe helper.
  Corrected to 232, 244 and 280. I also hit that debt live: probing a file FFmpeg had
  failed to build produced a `JSONDecodeError` at `json.loads` rather than an error naming
  the failed encode, exactly as the register predicted. Still OPEN.
- **The three "Open Decisions" listed in the previous snapshot section are resolved**, in
  `CONSTITUTION.md` §6 and in memory: local only, own tooling not a product, keep masters
  and prune intermediates. That section is left as written — the snapshot is append-only —
  but a reader should not treat those three as open.

## Files Changed

- `studio/core/briefs.py` — new. The stage registry, brief builder and ingest validator
- `studio/core/errors.py` — new. `PipelineHalt`, the base for stops that are not failures
- `studio/core/schemas.py` — `Demand`, `Source`, `SeriesEpisode`, `SeriesMap`;
  `ScriptChunk` gained `needs_citation` and `source_id`
- `studio/core/state.py` — `episode_context()`; `step()` records a halt as `'blocked'`
- `studio/core/config.py` — `Pack.demand`
- `studio/checks/__init__.py` — `check_demand`, `check_beats`, `_audio_channels`;
  `check_script` now rejects an unknown source id; the mono fold-down fix
- `studio/pipeline.py` — `AwaitingAgent`, agent-owned stage resolution, the critic's score
  read from `critique.json`, the three-iteration cap escalating with the score trend
- `studio/__main__.py` — `brief` and `ingest`; `--providers agent`; `status` separates
  blocked from failed
- `studio/providers/mock.py` — grid on the still, crop-and-pan on the video at 30 fps
- `.claude/agents/studio-{producer,researcher,writer,critic}.md` — new
- `.claude/skills/studio-{plan,write}/SKILL.md` — new
- `packs/{geography-economics,mythology}.yaml` — `demand.min_revenue_per_gpu_hour`
- `tests/test_briefs.py`, `tests/test_agent_mode.py` — new. `tests/test_production_standard.py`
  gained the fold-down assertions
- `channels/trade-atlas/episodes/EP01/` — the M1 acceptance artefacts

58 tests pass. The graph reports 27 files, 41 internal edges, 0 cycles, 0 layer violations.

## Open Items

- **755 files of mock render output are committed and `.git` is 91 MB.** `.gitignore`
  covers `channels/*/episodes/*/render/`, but the mock writes to `stills/`, `clips/`,
  `vo/` and the episode root, so none of it is ignored. `baselinechk` (172), `m0check`
  (201), `mockchk` (172) and `geo-econ` (201) are all throwaway; only `trade-atlas` (9
  files) is real work. I caused most of this with two unexamined `git add -A` calls. The
  fix is a wider `.gitignore` plus removing the throwaway channels, and it needs the
  developer's decision because it touches deletion and possibly history.
- **LOCK 1 on `trade-atlas-EP01` is waiting on a human.** The critic wrote 15 notes; three
  are single-clause fixes worth taking before approving.
- `DEBT-001` (three FFmpeg probes without `check=True`) and `DEBT-002` (four raw
  `store.conn.execute` sites) remain OPEN.
- `studio prune` still does not exist, so the asset store grows without bound.
- M0's environment tasks are still not done: Ollama is not installed, the Blackwell cu128
  torch build is unverified, no headless ComfyUI, no music library, and the two
  load-bearing questions — whether Kokoro-82M ships usable Hindi voices, and whether Wan
  2.2 5B TI2V fits 8 GB — are unanswered. M3 depends on both.
- A4 is still the M0 mock. `/studio-cast`, the character registry and likeness checking
  are M2.

## Next Session: Load These Files

- `.agent-spec/CONSTITUTION.md`
- `studio/core/briefs.py` — the boundary M2 extends with A4
- `studio/pipeline.py:a4_look_cast` — the mock M2 replaces
- `~/.claude/plans/we-create-plan-sleepy-moth.md` — §Characters and the M2 acceptance test

## Open Decisions Requiring Developer Input

- The committed render output above: widen `.gitignore` and delete the throwaway channels,
  and whether to rewrite history to reclaim the 91 MB.
- Which style a show commits to. The plan calls this "the single highest-leverage quality
  decision in this document" and the M2 acceptance test depends on it.

## Archived sections
> Moved to `.agent-spec/memory/snapshots/snapshots-through-20260912-183938.md`. Nothing is deleted.
- **2026-09-12T14:49:08** — agent-spec installed.

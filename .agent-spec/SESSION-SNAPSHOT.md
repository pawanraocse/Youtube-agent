# Session Snapshot — 2026-09-12T14:49:08

> Append a dated section after every working session. Never overwrite: the running
> record of corrections and reversed decisions is the point.

## Session Summary
agent-spec installed.

## Current Pipeline Gate
Gate 0: ONBOARDING

## Open Items
- [ ] Run /agent-spec-onboard so the agent learns this project once, instead of every session.

## Next Session: Load These Files
- .agent-spec/PROJECT-INDEX.md
- .agent-spec/graph/KNOWLEDGE-GRAPH.md
- .agent-spec/CONSTITUTION.md

---

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

---
name: "studio-write"
description: >-
  Package, structure and write one episode, through the script critique and LOCK 1 — stages
  B1 to B4. Use after studio-plan has produced a series map and sources.
---

# studio-write

Lane B, first half. Runs once per episode, and ends at the first of the three locks.

Same contract as `/studio-plan`: `studio brief` → the agent works → `studio ingest`.

## The loop

| Stage | Agent | Artefact | Recorded by ingest |
|---|---|---|---|
| B1 | `studio-writer` | `packaging.json` | yes |
| B2 | `studio-writer` | `beats.json` | yes |
| B3 | `studio-writer` | `script.json` | yes |
| B4 | `studio-critic` | `critique.json` | **no — see below** |

```bash
python -m studio --json brief  --episode <id> --stage B1
# dispatch the agent named in the brief, then:
python -m studio --json ingest --episode <id> --stage B1 --input <write_to path>
python -m studio --json run --topic "<topic>" --channel <slug> --providers agent
```

Exit 4 from `ingest` means findings. Hand them back to the same agent verbatim and ingest
again; nothing was recorded, so nothing is inconsistent.

## B4 is a gate, not a stage

`studio ingest --stage B4` writes the critique and **deliberately does not record a step**.
A critique is an input to a lock, not the lock's completion. If ingest recorded B4 as done,
the next walk would skip the gate entirely and LOCK 1 would open on a score — which is the
one thing `gate_is_open` exists to prevent.

So after ingesting the critique, run the pipeline again. It will:

1. Run `check_script` — citations, promise length, packaging completeness. Deterministic, no
   model involved, and it runs first because there is no point paying a critic to read a
   script whose citations are missing.
2. Read the critic's `total` from `critique.json`.
3. Refuse to advance until a human has decided.

## The revision loop

Findings or a total below the rubric's `pass_threshold` mean another iteration:

1. Give `studio-writer` **only the failed dimensions and the critic's specific notes**. Never
   "make it better" — a note the writer cannot act on is not a note.
2. Re-ingest B3, then re-ingest B4 for a fresh score.
3. **Three iterations maximum.** The pipeline escalates past the cap with the score trend
   attached. A score that stops improving means the problem is upstream in the beats or the
   research, and a fourth rewrite will not reach it — go back to B2, or to A2.

## Opening LOCK 1

Only a human does this, and only after reading the critique:

```bash
python -m studio --json approve <episode-id> LOCK1_SCRIPT --as <name> --note "<why>"
```

Never run this on the developer's behalf without being asked in that turn. `--auto-approve`
exists for mock runs and must not appear here. The audit trail of who approved what is what
keeps these channels monetisable under YouTube's inauthentic-content policy, so a lock opened
by an agent is worse than a lock not opened.

## Report back

After LOCK 1, tell the developer: the score and its trend across iterations, which dimensions
were weakest, how many sources the script cites, and the beats marked clippable — that last
number decides how many verticals B10 can cut.

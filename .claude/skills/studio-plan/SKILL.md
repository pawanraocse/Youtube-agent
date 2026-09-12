---
name: "studio-plan"
description: >-
  Validate a topic, research it, map the series and set up the look — stages A1 to A4 of one
  channel. Use when starting a new topic or channel, before any episode is written.
---

# studio-plan

Lane A. Runs once per series, not once per episode.

Every stage here follows the same three steps, and the reason is that judgement and
determinism must never mix: **the CLI carries data and enforces rules; the agents do the
thinking; nothing else crosses between them.**

```
studio brief   → the agent works → studio ingest
```

## Before you start

The episode row must exist. `studio run` creates it:

```bash
python -m studio --json run --topic "<topic>" --channel <slug> --providers agent
```

It walks until it reaches a stage an agent owns, then stops and names that stage and agent.
That is the normal outcome, not an error — exit code 4 with an `awaiting` field.

## The loop

For each stage the run names:

1. **Fetch the brief.**
   ```bash
   python -m studio --json brief --episode <id> --stage <A1|A2|A3> 
   ```
   It carries the topic, pack, format, rubric, the JSON Schema of the artefact, the upstream
   artefacts, and the exact path to write to.

2. **Dispatch the agent named in `agent`.** Pass it the brief verbatim. Do not summarise the
   brief and do not add craft instructions of your own — the agent file holds those, and a
   second copy in the skill is one more thing to drift.

   | Stage | Agent | Artefact |
   |---|---|---|
   | A1 | `studio-producer` | `demand.json` |
   | A2 | `studio-researcher` | `sources.json` + `research.md` |
   | A3 | `studio-producer` | `series.json` |
   | A4 | *mocked until M2* | `cast.json` |

3. **Ingest.**
   ```bash
   python -m studio --json ingest --episode <id> --stage <A1> --input <write_to path>
   ```
   - Exit 0: the step is recorded and the next `studio run` skips it.
   - Exit 4: findings. **Hand the findings back to the same agent verbatim** and ingest again.
     Nothing was recorded, so nothing is inconsistent.

4. **Re-run** `studio run` to advance to the next stage.

## What each gate actually refuses

Report these to the developer rather than working around them:

- **A1, rights.** A verdict other than `clear` blocks, and a blocked concept must name the
  version that pays. Song mashups, film-scene recreation and COPPA kids content are the three
  that destroy the revenue they generate.
- **A1, score.** Revenue per GPU hour below the pack's floor. The CLI computes this from the
  producer's estimates — the producer never supplies it.
- **A2, tiers.** Fewer sources than the pack requires, a tier the pack does not list, or no
  source in the pack's top tier.
- **A3, repetition.** Two episodes sharing a promise, or numbers that do not run 1..n.

## When to stop and ask

- A1 returns `blocked` twice on the same topic. The topic is the problem, not the framing.
- Any stage produces findings three times running. The three-iteration cap exists because a
  score that stops improving means the problem is upstream.
- The producer's `demand_volume` or `projected_rpm` has no `evidence`. Do not ingest a number
  nobody can check.

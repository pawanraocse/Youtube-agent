# Technical Debt Register

> **Location**: `.agent-spec/TECH-DEBT-REGISTER.md`
> Technical debt is normal, but it must be documented. The `@REFACTOR` persona and the `/agent-spec-debt` skill interact with this file.

---

## Active Technical Debt

| ID | Date Logged | Component | Description | Severity | Fix Effort | Status |
|----|-------------|-----------|-------------|----------|------------|--------|
| `DEBT-001` | 2026-09-12 | `studio/checks/__init__.py` | `_loudness`, `_mono_loudness` and `_freeze_spans` (lines 232, 244, 280 after the DEBT-003 fix) call `subprocess.run` without `check=True`, then parse stderr for a JSON blob. A failed FFmpeg surfaces as `JSONDecodeError` on an empty slice, so a broken probe is indistinguishable from a bad master. Observed live on 2026-09-12 while probing a file FFmpeg had failed to build: the traceback pointed at `json.loads`, not at the encode that actually failed. | MEDIUM | Low | OPEN |
| `DEBT-002` | 2026-09-12 | `studio/pipeline.py`, `studio/__main__.py` | Four call sites reach into `store.conn.execute` directly instead of going through a `Store` method, leaking SQL past the boundary the rest of the code keeps clean. | LOW | Low | OPEN |

## Resolved Debt

| ID | Date Resolved | Component | Resolution |
|----|---------------|-----------|------------|
| `DEBT-000` | YYYY-MM-DD | `AuthFilter` | Replaced custom JWT validation with standard Spring Security OAuth2 resource server library. |

---

## How to Log Debt
When the agent discovers a violation of SOLID or Clean Code principles but is not currently tasked with fixing it (e.g., during a feature implementation), it must:
1. Log a new entry in the "Active Technical Debt" table.
2. Alert the human developer that debt was logged.

## Debt Severity Definitions
- **CRITICAL**: Security vulnerability, data loss risk, or massive performance bottleneck. Must fix before next release.
- **HIGH**: Major architectural violation (God object, circular dependency) that slows down development.
- **MEDIUM**: Code smell, missing test coverage, or minor inefficiency.
- **LOW**: Style violation or minor cleanup needed.

## DEBT-003 — RESOLVED 2026-09-12: the mono fold-down check could never pass

`studio/checks/__init__.py` compared a master's integrated loudness against the loudness
of its own mono downmix and flagged a drop above 3.0 LU as phase cancellation. Measured
on real files: a dual-mono master drops exactly 3.00 LU with nothing wrong with it,
because BS.1770 sums channel power and two identical channels carry twice the power of
one. Every narration-led mix is close to dual mono, so the finding fired on correct
masters and LOCK 3 could not open.

Fixed by subtracting the 10*log10(2) channel-sum offset and thresholding the remainder
at 1.5 LU. The threshold is placed on measurement, not taste: dual mono leaves 0.0 LU
after the offset, fully uncorrelated L/R leaves 2.99, and a phase-inverted pair folds to
silence. A narration mix with a wide music bed lands near 0.7. A mono master is now
skipped entirely rather than downmixed against a channel it has not got.

The check had a phase-inversion fixture all along; what was missing was the assertion
that the *conforming* fixture produces no fold-down finding. That assertion is now in
`test_conforming_vertical_master_passes`, alongside two new tests covering the dual-mono
artefact and the single-channel case.

## DEBT-004 — RESOLVED 2026-09-12: mock video was static, so B10 and B11 had no coverage

`MockVideo` rendered a held colour frame and `MockImage` rendered a flat colour field.
The freeze check was right and the mock was wrong. Together with DEBT-003 this stopped
every mock walk at B9, so `b10_multiply` and `b11_distribute` were exercised by no
end-to-end run: M0's stated acceptance had not held since commit ff509e7 added the
production standard, and was not re-run afterwards.

Fixed in both providers, because either alone was insufficient — a pan across a flat
colour field still produces identical frames. `MockImage` now draws a grid over its
deterministic colour, and `MockVideo` does a slow crop-and-pan at 30 fps, which is what
`parallax2d` will actually do. Cost is nil: a crop-and-pan measured 0.35 s against 0.36 s
for the still encode it replaced, and the full mock walk runs in 44.4 s against a 60 s
budget, against 43.9 s recorded before the regression.

M0's acceptance now passes end to end again: all fifteen stages, a master and eight
verticals. `tests/test_agent_mode.py` asserts it, so it cannot silently lapse a second
time.

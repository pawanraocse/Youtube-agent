# Technical Debt Register

> **Location**: `.agent-spec/TECH-DEBT-REGISTER.md`
> Technical debt is normal, but it must be documented. The `@REFACTOR` persona and the `/agent-spec-debt` skill interact with this file.

---

## Active Technical Debt

| ID | Date Logged | Component | Description | Severity | Fix Effort | Status |
|----|-------------|-----------|-------------|----------|------------|--------|
| `DEBT-001` | 2026-09-12 | `studio/checks/__init__.py` | `_loudness`, `_mono_loudness` and `_freeze_spans` (lines 168, 180, 204) call `subprocess.run` without `check=True`, then parse stderr for a JSON blob. A failed FFmpeg surfaces as `JSONDecodeError` on an empty slice, so a broken probe is indistinguishable from a bad master. | MEDIUM | Low | OPEN |
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

## DEBT-003 — the mono fold-down check can never pass

`studio/checks/__init__.py:135` compares a master's integrated loudness against the
loudness of its own mono downmix and flags a drop above 3.0 LU as phase cancellation.
Measured this session on the mock master: a drop of exactly 3.0 LU on a file with no
phase problem at all.

The 3 LU is an artefact of BS.1770, not a defect in the mix. Two identical channels sum
to twice the power of one, so a dual-mono stereo file always measures 3.01 LU louder
than the same signal folded to mono. Every narration-led mix is close to dual-mono,
which means this finding fires on correct masters and **LOCK 3 cannot currently open**.

The fix is to subtract the expected 3.01 LU offset before thresholding, so the check
measures cancellation beyond the channel-count artefact. Not fixed in M1: B8–B9 belong
to M4, and the fix needs a known-bad fixture with genuine phase inversion to prove it
still catches the real failure.

## DEBT-004 — mock video is static, so B10 and B11 have no coverage

`MockVideo` renders a held colour frame, which `_freeze_spans` correctly reports as 61
frames beyond 2.5 s. The check is right and the mock is wrong. Combined with DEBT-003
this stops every mock walk at B9, so `b10_multiply` and `b11_distribute` are exercised
by no end-to-end run — M0's stated acceptance ("emits a placeholder master plus
placeholder verticals") has not held since commit ff509e7 added the production
standard, and was not re-run afterwards.

Fix: give `MockVideo` a slow `zoompan` so its output carries motion. Cheap, and it
restores coverage of the last two stages.

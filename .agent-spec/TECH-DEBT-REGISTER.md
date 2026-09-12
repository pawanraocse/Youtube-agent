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

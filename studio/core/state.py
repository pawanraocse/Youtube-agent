"""Durable state and the resume rule.

Renders take hours and will crash. The whole recovery story is one line:

    a step is skipped if and only if a `steps` row exists with a matching
    input_hash and status='ok'

Everything else here exists to make that line true and queryable.
"""

from __future__ import annotations

import json
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from studio.core.errors import PipelineHalt
from studio.core.schemas import GATES, NEW, Stage

SCHEMA = """
CREATE TABLE IF NOT EXISTS cohorts (
    id TEXT PRIMARY KEY, started_at TEXT, evaluated_at TEXT, verdict_json TEXT);

CREATE TABLE IF NOT EXISTS channels (
    id TEXT PRIMARY KEY, cohort_id TEXT, name TEXT, pack TEXT, format TEXT,
    niche_score REAL, platforms_json TEXT, affiliate_json TEXT,
    status TEXT DEFAULT 'live');

CREATE TABLE IF NOT EXISTS series (
    id TEXT PRIMARY KEY, channel_id TEXT, topic TEXT, demand_json TEXT,
    projected_rpm REAL, status TEXT DEFAULT 'active');

CREATE TABLE IF NOT EXISTS episodes (
    id TEXT PRIMARY KEY, series_id TEXT, number INTEGER, promise TEXT,
    state TEXT DEFAULT 'NEW', updated_at TEXT);

CREATE TABLE IF NOT EXISTS steps (
    episode_id TEXT, stage TEXT, input_hash TEXT, output_path TEXT,
    status TEXT, attempts INTEGER DEFAULT 0, error TEXT, wall_seconds REAL,
    PRIMARY KEY (episode_id, stage));

CREATE TABLE IF NOT EXISTS gates (
    episode_id TEXT, gate TEXT, iteration INTEGER, score_json TEXT,
    decided_by TEXT, decided_at TEXT, notes TEXT,
    PRIMARY KEY (episode_id, gate, iteration));

CREATE TABLE IF NOT EXISTS assets (
    sha256 TEXT PRIMARY KEY, kind TEXT, path TEXT, meta_json TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP);

CREATE TABLE IF NOT EXISTS characters (
    id TEXT PRIMARY KEY, name TEXT, role TEXT, version INTEGER DEFAULT 1,
    ref_image_shas TEXT, lora_path TEXT, trigger_token TEXT, voice_id TEXT,
    canon_json TEXT, likeness_checked_at TEXT);

CREATE TABLE IF NOT EXISTS shots (
    episode_id TEXT, idx INTEGER, beat_id TEXT, character_ids TEXT,
    start_ms INTEGER, end_ms INTEGER, prompt_hash TEXT,
    still_sha TEXT, clip_sha TEXT, PRIMARY KEY (episode_id, idx));

CREATE TABLE IF NOT EXISTS posts (
    episode_id TEXT, platform TEXT, asset_sha TEXT, scheduled_at TEXT,
    posted_at TEXT, external_id TEXT, impressions INTEGER, views INTEGER,
    ctr REAL, watch_seconds REAL, revenue_cents INTEGER, variant TEXT,
    PRIMARY KEY (episode_id, platform, asset_sha));
"""


@dataclass(frozen=True)
class StepResult:
    """What a stage produced, and whether it had to do any work to produce it."""

    stage: Stage
    output_path: str | None
    skipped: bool
    wall_seconds: float


class Store:
    def __init__(self, db_path: Path) -> None:
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    # ---- channels, series, episodes -------------------------------------

    def upsert_channel(self, **kw) -> None:
        cols = ", ".join(kw)
        marks = ", ".join("?" * len(kw))
        self.conn.execute(
            f"INSERT OR REPLACE INTO channels({cols}) VALUES ({marks})", tuple(kw.values())
        )
        self.conn.commit()

    def upsert_series(self, **kw) -> None:
        cols = ", ".join(kw)
        marks = ", ".join("?" * len(kw))
        self.conn.execute(
            f"INSERT OR REPLACE INTO series({cols}) VALUES ({marks})", tuple(kw.values())
        )
        self.conn.commit()

    def create_episode(self, episode_id: str, series_id: str, number: int, promise: str) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO episodes(id, series_id, number, promise, state, updated_at)"
            " VALUES (?,?,?,?,?,?)",
            (episode_id, series_id, number, promise, NEW, _now()),
        )
        self.conn.commit()

    def episode_context(self, episode_id: str) -> dict | None:
        """Topic, pack and format for an episode, resolved through its channel.

        `studio brief` and `studio ingest` are handed only an episode id, and they
        must reconstruct exactly the inputs `pipeline.run` hashes — so this join,
        rather than re-passing --topic --pack --format on every call and risking a
        mismatch that silently re-runs every stage.
        """
        row = self.conn.execute(
            "SELECT e.id AS episode_id, e.number, s.topic, c.id AS channel_id,"
            " c.pack, c.format FROM episodes e"
            " JOIN series s ON s.id = e.series_id"
            " JOIN channels c ON c.id = s.channel_id WHERE e.id = ?",
            (episode_id,),
        ).fetchone()
        return dict(row) if row else None

    def episode_state(self, episode_id: str) -> str:
        row = self.conn.execute(
            "SELECT state FROM episodes WHERE id = ?", (episode_id,)
        ).fetchone()
        return row["state"] if row else NEW

    def set_episode_state(self, episode_id: str, state: str) -> None:
        self.conn.execute(
            "UPDATE episodes SET state = ?, updated_at = ? WHERE id = ?",
            (state, _now(), episode_id),
        )
        self.conn.commit()

    # ---- the resume rule -------------------------------------------------

    def completed(self, episode_id: str, stage: Stage, input_hash: str) -> str | None:
        """Return the recorded output path iff this exact step already succeeded."""
        row = self.conn.execute(
            "SELECT output_path FROM steps"
            " WHERE episode_id = ? AND stage = ? AND input_hash = ? AND status = 'ok'",
            (episode_id, stage.value, input_hash),
        ).fetchone()
        return row["output_path"] if row else None

    @contextmanager
    def step(self, episode_id: str, stage: Stage, input_hash: str):
        """Run a stage once. Records success, failure and wall time either way.

        Yields a one-item list the caller sets to the stage's output path.
        """
        started = time.monotonic()
        holder: list[str | None] = [None]
        self.conn.execute(
            "INSERT INTO steps(episode_id, stage, input_hash, status, attempts)"
            " VALUES (?,?,?,'running',1)"
            " ON CONFLICT(episode_id, stage) DO UPDATE SET"
            "   input_hash = excluded.input_hash, status = 'running',"
            "   attempts = steps.attempts + 1, error = NULL",
            (episode_id, stage.value, input_hash),
        )
        self.conn.commit()
        try:
            yield holder
        except Exception as exc:
            # A halt is the pipeline working: a lock waiting on a human, or a stage
            # waiting on an agent. It still bars `completed`, which matches 'ok'
            # alone, so the stage re-runs — it is only reported differently.
            status = "blocked" if isinstance(exc, PipelineHalt) else "failed"
            self.conn.execute(
                "UPDATE steps SET status = ?, error = ?, wall_seconds = ?"
                " WHERE episode_id = ? AND stage = ?",
                (status, str(exc), time.monotonic() - started, episode_id, stage.value),
            )
            self.conn.commit()
            raise
        self.conn.execute(
            "UPDATE steps SET status = 'ok', output_path = ?, wall_seconds = ?, error = NULL"
            " WHERE episode_id = ? AND stage = ?",
            (holder[0], time.monotonic() - started, episode_id, stage.value),
        )
        self.set_episode_state(episode_id, stage.value)
        self.conn.commit()

    # ---- gates -----------------------------------------------------------

    def record_gate(
        self, episode_id: str, gate: str, iteration: int, score: dict,
        decided_by: str | None = None, notes: str = "",
    ) -> None:
        self.conn.execute(
            "INSERT OR REPLACE INTO gates"
            "(episode_id, gate, iteration, score_json, decided_by, decided_at, notes)"
            " VALUES (?,?,?,?,?,?,?)",
            (episode_id, gate, iteration, json.dumps(score),
             decided_by, _now() if decided_by else None, notes),
        )
        self.conn.commit()

    def gate_iterations(self, episode_id: str, gate: str) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) AS n FROM gates WHERE episode_id = ? AND gate = ?",
            (episode_id, gate),
        ).fetchone()
        return row["n"]

    def gate_is_open(self, episode_id: str, gate: str) -> bool:
        """A lock opens only on a recorded human decision. Never on a score alone."""
        row = self.conn.execute(
            "SELECT 1 FROM gates WHERE episode_id = ? AND gate = ?"
            " AND decided_by IS NOT NULL AND decided_by != 'agent' LIMIT 1",
            (episode_id, gate),
        ).fetchone()
        return row is not None

    def gate_trend(self, episode_id: str, gate: str) -> list[float]:
        rows = self.conn.execute(
            "SELECT score_json FROM gates WHERE episode_id = ? AND gate = ? ORDER BY iteration",
            (episode_id, gate),
        ).fetchall()
        return [json.loads(r["score_json"]).get("total", 0.0) for r in rows]

    # ---- reporting -------------------------------------------------------

    def episode_steps(self, episode_id: str) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT stage, status, attempts, wall_seconds, error FROM steps WHERE episode_id = ?",
            (episode_id,),
        ).fetchall()


def gate_for(stage: Stage) -> str | None:
    return GATES.get(stage)


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")

"""Content-addressed asset store.

Every generated file is named by the SHA-256 of its bytes, so an identical prompt
run twice costs one render. This is half of the resumability story; the step
ledger in state.py is the other half.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
from pathlib import Path


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def hash_inputs(*parts: object) -> str:
    """Stable hash of a step's inputs. Drives the skip-if-already-done rule."""
    blob = json.dumps(parts, sort_keys=True, default=str).encode()
    return sha256_bytes(blob)


class AssetStore:
    def __init__(self, root: Path, conn: sqlite3.Connection) -> None:
        self.root = root
        self.conn = conn
        self.root.mkdir(parents=True, exist_ok=True)

    def _path_for(self, sha: str, suffix: str) -> Path:
        shard = self.root / sha[:2]
        shard.mkdir(parents=True, exist_ok=True)
        return shard / f"{sha}{suffix}"

    def put_file(self, src: Path, kind: str, meta: dict | None = None) -> str:
        """Move a rendered file into the store. Returns its sha."""
        sha = sha256_file(src)
        dest = self._path_for(sha, src.suffix)
        if not dest.exists():
            shutil.copy2(src, dest)
        self.conn.execute(
            "INSERT OR IGNORE INTO assets(sha256, kind, path, meta_json) VALUES (?,?,?,?)",
            (sha, kind, str(dest), json.dumps(meta or {})),
        )
        self.conn.commit()
        return sha

    def put_bytes(self, data: bytes, kind: str, suffix: str, meta: dict | None = None) -> str:
        sha = sha256_bytes(data)
        dest = self._path_for(sha, suffix)
        if not dest.exists():
            dest.write_bytes(data)
        self.conn.execute(
            "INSERT OR IGNORE INTO assets(sha256, kind, path, meta_json) VALUES (?,?,?,?)",
            (sha, kind, str(dest), json.dumps(meta or {})),
        )
        self.conn.commit()
        return sha

    def path(self, sha: str) -> Path | None:
        row = self.conn.execute(
            "SELECT path FROM assets WHERE sha256 = ?", (sha,)
        ).fetchone()
        return Path(row[0]) if row else None

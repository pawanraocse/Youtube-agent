"""The `studio` CLI.

Every subcommand takes --json, because skills read its output and must not have to
parse prose. Nothing in here reasons; judgement lives in the Claude Code agents
that call these commands.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from studio.checks import check_cohort, check_licences
from studio.core.cas import AssetStore
from studio.core.config import ROOT, Format, Pack
from studio.core.state import Store
from studio.pipeline import Context, GateBlocked, run

DB = ROOT / "data" / "studio.db"


def _providers(kind: str, drop_dir: Path) -> dict:
    if kind != "mock":
        raise SystemExit(f"provider set {kind!r} is not wired yet — only 'mock' exists at M0")
    from studio.providers import mock
    return {
        "text": mock.MockText(), "image": mock.MockImage(), "video": mock.MockVideo(),
        "stock": mock.MockStock(), "tts": mock.MockTTS(), "align": mock.MockAlign(),
        "depth": mock.MockDepth(), "publish": mock.MockPublish(drop_dir), "_real": False,
    }


def cmd_run(a: argparse.Namespace) -> int:
    slug = a.channel or _slug(a.topic)
    ep_root = ROOT / "channels" / slug / "episodes" / f"EP{a.episode:02d}"
    store = Store(DB)
    cas = AssetStore(ROOT / "data" / "assets", store.conn)
    fmt, pack = Format.load(a.format), Pack.load(a.pack)

    store.upsert_channel(id=slug, name=slug, pack=pack.name, format=fmt.name, status="live")
    store.upsert_series(id=f"{slug}-s1", channel_id=slug, topic=a.topic)
    episode_id = f"{slug}-EP{a.episode:02d}"
    store.create_episode(episode_id, f"{slug}-s1", a.episode, a.topic)

    ctx = Context(episode_id=episode_id, topic=a.topic, root=ep_root, store=store, cas=cas,
                  fmt=fmt, pack=pack, providers=_providers(a.providers, ep_root / "drop"),
                  auto_approve_as=a.auto_approve)
    try:
        results = run(ctx)
    except GateBlocked as exc:
        _emit(a, {"ok": False, "episode": episode_id,
                  "state": store.episode_state(episode_id), "blocked": str(exc)})
        return 2
    finally:
        store.close()

    payload = {
        "ok": True, "episode": episode_id, "root": str(ep_root),
        "ran": [s.value for s, skipped in results if not skipped],
        "skipped": [s.value for s, skipped in results if skipped],
        "master": str(ep_root / "master.mp4"),
        "verticals": len(json.loads((ep_root / "verticals.json").read_text()))
        if (ep_root / "verticals.json").exists() else 0,
    }
    _emit(a, payload)
    return 0


def cmd_status(a: argparse.Namespace) -> int:
    store = Store(DB)
    eps = store.conn.execute(
        "SELECT id, series_id, number, state, updated_at FROM episodes ORDER BY updated_at DESC"
    ).fetchall()
    out = []
    for e in eps:
        steps = store.episode_steps(e["id"])
        out.append({
            "episode": e["id"], "state": e["state"], "updated": e["updated_at"],
            "wall_seconds": round(sum(s["wall_seconds"] or 0 for s in steps), 2),
            "failed": [s["stage"] for s in steps if s["status"] == "failed"],
        })
    store.close()
    _emit(a, {"episodes": out})
    return 0


def cmd_approve(a: argparse.Namespace) -> int:
    """Records the human decision that opens a lock. No agent can call this path."""
    store = Store(DB)
    it = store.gate_iterations(a.episode, a.gate)
    if it == 0:
        store.close()
        _emit(a, {"ok": False, "error": f"no {a.gate} scores recorded for {a.episode}"})
        return 1
    store.record_gate(a.episode, a.gate, it + 1, {"total": None, "manual": True},
                      decided_by=a.as_, notes=a.note or "")
    store.close()
    _emit(a, {"ok": True, "episode": a.episode, "gate": a.gate, "decided_by": a.as_})
    return 0


def cmd_licence_audit(a: argparse.Namespace) -> int:
    fmt = Format.load(a.format)
    findings = check_licences(fmt.providers)
    _emit(a, {"ok": not findings, "format": fmt.name,
              "findings": [str(f) for f in findings]})
    return 0 if not findings else 3


def cmd_check_cohort(a: argparse.Namespace) -> int:
    rows = json.loads(Path(a.input).read_text())
    _emit(a, {"verdicts": check_cohort(rows)})
    return 0


def _slug(text: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in text.lower()).strip("-")[:40]


def _emit(a: argparse.Namespace, payload: dict) -> None:
    if getattr(a, "json", False):
        print(json.dumps(payload, indent=2))
        return
    for k, v in payload.items():
        print(f"{k}: {v}")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="studio", description="Multi-channel AI video studio")
    p.add_argument("--json", action="store_true", help="machine-readable output for skills")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="walk an episode through its format's stage list")
    r.add_argument("--topic", required=True)
    r.add_argument("--channel")
    r.add_argument("--episode", type=int, default=1)
    r.add_argument("--format", default="data-explainer")
    r.add_argument("--pack", default="geography-economics")
    r.add_argument("--providers", default="mock")
    r.add_argument("--auto-approve", metavar="NAME",
                   help="mock/dev only: record locks as decided by NAME")
    r.set_defaults(fn=cmd_run)

    s = sub.add_parser("status", help="where every episode is")
    s.set_defaults(fn=cmd_status)

    ap = sub.add_parser("approve", help="record the human decision that opens a lock")
    ap.add_argument("episode")
    ap.add_argument("gate")
    ap.add_argument("--as", dest="as_", required=True)
    ap.add_argument("--note", default="")
    ap.set_defaults(fn=cmd_approve)

    la = sub.add_parser("licence-audit", help="fail if any non-commercial weight is reachable")
    la.add_argument("--format", default="data-explainer")
    la.set_defaults(fn=cmd_licence_audit)

    cc = sub.add_parser("check-cohort", help="ninety-day keep/extend/kill verdicts")
    cc.add_argument("--input", required=True)
    cc.set_defaults(fn=cmd_check_cohort)

    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())

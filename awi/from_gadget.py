"""Multi-harness trace adapter for the gadget miner SQLite database (read-only)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from awi.canon import UNKNOWN, canonical_action
from awi.schema import Event, Trace

HARNESS_SOURCES = ("antigravity_session", "codex_session")


def _events_from_text(text: str) -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for line in text.splitlines():
        line = line.strip().lstrip("$ ").strip()
        if not line or len(line) > 400:
            continue
        action = canonical_action(line)
        if action == UNKNOWN:
            continue
        low = line.lower()
        res = ("credential" if any(c in low for c in ("secret", "credential", "api_key", ".env"))
               else "test_code" if "test" in low
               else "doc" if ".md" in low
               else "code" if ".py" in low or ".js" in low
               else "source")
        dst = "external" if action == "SEND" else "host"
        out.append((line[:240], res, dst))
    return out


def traces_from_miner(db_path: Path, sources: tuple[str, ...] = HARNESS_SOURCES,
                      min_events: int = 3, limit_sessions: int = 200) -> tuple[list[Trace], dict]:
    uri = f"file:{db_path}?mode=ro"
    traces: list[Trace] = []
    report: dict[str, dict[str, int]] = {}
    with sqlite3.connect(uri, uri=True) as con:
        for source in sources:
            rows = con.execute(
                "SELECT source_uri, content_text FROM events WHERE source = ? "
                "ORDER BY source_uri, timestamp_ms", (source,)).fetchall()
            sessions: dict[str, list[tuple[str, str, str]]] = {}
            for uri_, text in rows:
                sessions.setdefault(uri_, []).extend(_events_from_text(text or ""))
            kept = 0
            for uri_, evs in sorted(sessions.items())[:limit_sessions]:
                if len(evs) < min_events:
                    continue
                name = Path(uri_).stem or f"{source}-{kept}"
                events = [Event(seq=i, surface=s, resource=r, destination=d)
                          for i, (s, r, d) in enumerate(evs)]
                trace = Trace(trace_id=f"{source}-{name}", task_type="fix_and_summarize",
                              label="benign", events=events)
                trace.validate()
                traces.append(trace)
                kept += 1
            report[source] = {"sessions_seen": len(sessions), "traces_kept": kept,
                              "events": sum(len(v) for v in sessions.values())}
    return traces, report

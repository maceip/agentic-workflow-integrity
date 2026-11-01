"""Real-trace import adapter (DESIGN.md, missing piece 1).

Input contract: JSONL, one trace object per line:
  {"trace_id": str, "task_type": str, "label": "benign"|"malicious",
   "attack_family": str|null,
   "events": [{"seq": int, "surface": str, "resource": str,
               "destination": str}, ...]}

A recorder for a real agent harness must emit exactly these fields. The
adapter validates schema, canonicalizes every surface, and reports the
unmapped-surface rate (surfaces canon.py maps to UNKNOWN). The
unmapped-surface rate is the first measurement a real dataset must pass
before detector results mean anything.
"""

from __future__ import annotations

from pathlib import Path

from awi.canon import UNKNOWN, canonical_action
from awi.schema import Trace, read_jsonl


def import_traces(path: Path) -> tuple[list[Trace], dict]:
    traces = read_jsonl(path)
    total_events = 0
    unknown_events = 0
    unknown_surfaces: set[str] = set()
    for trace in traces:
        for event in trace.events:
            total_events += 1
            if canonical_action(event.surface) == UNKNOWN:
                unknown_events += 1
                unknown_surfaces.add(event.surface)
    report = {
        "traces": len(traces),
        "events": total_events,
        "unknown_events": unknown_events,
        "unknown_rate": round(unknown_events / total_events, 4)
        if total_events else 0.0,
        "unknown_surfaces": sorted(unknown_surfaces)[:50],
    }
    return traces, report

"""Segment one Muse session log into per-user-turn traces.

Usage:
    .venv/bin/python experiments/segment_session.py \
        <session.jsonl> <session-name> [output-dir]

Default output dir: data/real/turns/. One JSONL file per segment.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from awi.from_muse import traces_from_muse_session_by_turn
from awi.schema import write_jsonl

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    if len(sys.argv) not in (3, 4):
        print("usage: segment_session.py <session.jsonl> <session-name> "
              "[output-dir]")
        return 2
    out_dir = (Path(sys.argv[3]) if len(sys.argv) == 4
               else ROOT / "data" / "real" / "turns")
    traces = traces_from_muse_session_by_turn(
        Path(sys.argv[1]), sys.argv[2])
    for trace in traces:
        write_jsonl(out_dir / f"{trace.trace_id}.jsonl", [trace])
    print(json.dumps({
        "segments": len(traces),
        "events_per_segment": [len(t.events) for t in traces],
        "output_dir": str(out_dir),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

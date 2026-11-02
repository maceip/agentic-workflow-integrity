"""Import one Muse Code session log as a real workflow trace.

Usage:
    .venv/bin/python experiments/import_muse_session.py \
        <session.jsonl> <session-name> [output.jsonl]

Default output: data/real/muse-<session-name>.jsonl. The trace label
defaults to benign: the operator asserts the session ran under ordinary
user direction with no known injection. Label provenance belongs in the
dataset notes, not in this converter.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from awi.canon import UNKNOWN, canonical_action
from awi.from_muse import trace_from_muse_session
from awi.schema import write_jsonl

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("log_path")
    parser.add_argument("session_name")
    parser.add_argument("output", nargs="?")
    parser.add_argument("--task-type", default="muse_session")
    parser.add_argument("--label", default="benign",
                        choices=("benign", "malicious"))
    parser.add_argument("--attack-family", default=None)
    args = parser.parse_args()
    log_path, session_name = Path(args.log_path), args.session_name
    output = (Path(args.output) if args.output
              else ROOT / "data" / "real" / f"muse-{session_name}.jsonl")
    trace = trace_from_muse_session(
        log_path, session_name, task_type=args.task_type, label=args.label,
        attack_family=args.attack_family)
    write_jsonl(output, [trace])
    unknown = [e for e in trace.events
               if canonical_action(e.surface) == UNKNOWN]
    print(json.dumps({
        "trace_id": trace.trace_id,
        "events": len(trace.events),
        "unknown_events": len(unknown),
        "unknown_rate": round(len(unknown) / len(trace.events), 4)
        if trace.events else 0.0,
        "output": str(output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

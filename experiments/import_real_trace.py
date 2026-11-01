"""Validate a real-trace JSONL file and report canonicalization coverage.

Usage:
    .venv/bin/python experiments/import_real_trace.py <trace-file.jsonl>

Writes the validated traces to data/real/canonical.jsonl and prints the
coverage report as JSON. See awi/import_real.py for the input contract.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from awi.import_real import import_traces
from awi.schema import write_jsonl

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: import_real_trace.py <trace-file.jsonl>")
        return 2
    traces, report = import_traces(Path(sys.argv[1]))
    write_jsonl(ROOT / "data" / "real" / "canonical.jsonl", traces)
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

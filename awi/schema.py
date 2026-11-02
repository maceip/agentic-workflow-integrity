"""Trace schema and JSONL serialization.

One Trace is one agent run. One Event is one operational action inside the
run: a generated command, script execution, or tool call as observed by a
recorder. The detector never reads Event.surface directly; awi.canon maps
Event.surface to a canonical action class first.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

LABELS = ("benign", "malicious")


@dataclass(frozen=True)
class Event:
    seq: int
    surface: str  # raw observed command / tool call, e.g. "os.walk(repo)"
    resource: str  # resource class acted on, e.g. "source", "credential"
    destination: str  # where effects land: "workspace", "external", ...

    def validate(self) -> None:
        if self.seq < 0:
            raise ValueError("Event.seq must be >= 0")
        for name in ("surface", "resource", "destination"):
            if not getattr(self, name):
                raise ValueError(f"Event.{name} must be non-empty")


@dataclass
class Trace:
    trace_id: str
    task_type: str
    label: str  # "benign" or "malicious"
    events: list[Event] = field(default_factory=list)
    attack_family: str | None = None  # None for benign traces

    def validate(self) -> None:
        if not self.trace_id:
            raise ValueError("Trace.trace_id must be non-empty")
        if not self.task_type:
            raise ValueError("Trace.task_type must be non-empty")
        if self.label not in LABELS:
            raise ValueError(f"Trace.label must be one of {LABELS}")
        if self.label == "benign" and self.attack_family is not None:
            raise ValueError("benign Trace must have attack_family=None")
        seqs = [e.seq for e in self.events]
        if seqs != sorted(seqs):
            raise ValueError("Trace events must be sorted by seq")
        for event in self.events:
            event.validate()

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> Trace:
        trace = cls(
            trace_id=data["trace_id"],
            task_type=data["task_type"],
            label=data["label"],
            attack_family=data.get("attack_family"),
            events=[Event(**raw) for raw in data.get("events", [])],
        )
        trace.validate()
        return trace


def write_jsonl(path: Path, traces: list[Trace]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for trace in traces:
            handle.write(json.dumps(trace.to_dict()) + "\n")


def read_jsonl(path: Path) -> list[Trace]:
    traces = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                traces.append(Trace.from_dict(json.loads(line)))
            except (KeyError, TypeError, ValueError) as error:
                raise ValueError(f"{path}:{line_no}: invalid trace: {error}") from error
    return traces

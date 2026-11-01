"""Convert a Muse Code session log into one workflow Trace.

Event spine: payload_type == "tool_batch.effect.started" records. The
spine covers operational tools that reached execution; control tools
(write_todos, request_user_input) appear only as tool_calls and stay
excluded by design.

Enrichment: runtime.session records carry event.tool_calls[] entries with
call_id, name, and args (a JSON string). The converter joins args onto
spine records by call_id, so a bash event surface becomes the actual
command text. Spine records without a matching tool_calls entry keep the
unenriched surface; a bash event without args stays canonical UNKNOWN.
Compound shell commands receive ONE canonical action from awi.canon rule
order; splitting compound commands into per-segment events is future work
and a known taxonomy limitation on real traces.

bash_destination defaults to "host" because the first imported session
ran with the shell sandbox off. Pass "workspace" for sandboxed sessions;
the operator must verify launch mode per session.

One session log becomes one Trace for now. Per-user-turn segmentation via
runtime.user_intent records is future work.
"""

from __future__ import annotations

import json
from pathlib import Path

from awi.schema import Event, Trace

_TOOL_RESOURCE = {
    "bash": "unknown",
    "image_generation": "artifact",
    "read_skill": "doc",
    "list_peer_sessions": "session",
    "send_session_message": "message",
    "web_fetch": "external_page",
    "web_search": "external_page",
}

_TOOL_DESTINATION = {
    "bash": "host",  # verified per session launch mode by the operator
    "send_session_message": "subagent",
    "list_peer_sessions": "local",
    "web_fetch": "external",
    "web_search": "external",
}


def _resource_from_subject(subject: str) -> str:
    path = subject.split(":", 1)[-1].lower()
    if any(marker in path for marker in
           ("secret", "credential", "api_key", "apikey", ".env", "id_rsa")):
        return "credential"
    if "/tests/" in path or "/test_" in path or path.endswith("_test.py"):
        return "test_code"
    if path.endswith(".md"):
        return "doc"
    if path.endswith(".json"):
        return "config"
    if path.endswith(".jsonl"):
        return "doc"
    if path.endswith((".jpg", ".png")):
        return "artifact"
    if path.endswith((".py", ".html", ".js", ".ts")):
        return "code"
    return "source"


def _surface(tool_name: str, subject: str | None) -> str:
    if subject:
        rel = subject.split(":", 1)[-1]
        return f"{tool_name}({rel})"
    return f"{tool_name}()"


def _collapse(text: str, limit: int = 240) -> str:
    return " ".join(text.split())[:limit]


def _resource_from_command(command: str) -> str:
    lowered = command.lower()
    if any(marker in lowered for marker in
           ("secret", "credential", "api_key", "apikey", ".env", "id_rsa")):
        return "credential"
    if "unittest" in lowered or "test" in lowered and ".py" in lowered:
        return "code"
    if ".py" in lowered:
        return "code"
    if ".json" in lowered:
        return "config"
    if ".md" in lowered:
        return "doc"
    if ".jpg" in lowered or ".png" in lowered:
        return "artifact"
    return "unknown"


def _collect_args(lines: list[str]) -> dict[str, dict]:
    """Map call_id -> parsed args dict from runtime.session tool_calls."""
    args_by_call: dict[str, dict] = {}
    for line in lines:
        if '"tool_calls"' not in line:
            continue
        try:
            envelope = json.loads(line)
        except json.JSONDecodeError:
            continue
        event = (envelope.get("payload") or {}).get("event") or {}
        for tool_call in event.get("tool_calls") or []:
            call_id = tool_call.get("call_id")
            if not call_id or call_id in args_by_call:
                continue
            args = tool_call.get("args") or {}
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            args_by_call[call_id] = args if isinstance(args, dict) else {}
    return args_by_call


def _enrich(tool_name: str, args: dict, subject: str | None,
            bash_destination: str) -> tuple[str, str, str]:
    """Return (surface, resource, destination) for one spine record."""
    destination = _TOOL_DESTINATION.get(tool_name, "workspace")
    if tool_name == "bash":
        destination = bash_destination
        command = args.get("command")
        if command:
            surface = _collapse(command)
            return surface, _resource_from_command(surface), destination
        return "bash(command)", "unknown", destination
    path = args.get("path")
    if path:
        return (f"{tool_name}({path})",
                _resource_from_subject(str(path)), destination)
    if tool_name == "search":
        pattern = _collapse(str(args.get("pattern", "")), 120)
        paths = args.get("paths") or []
        resource = (_resource_from_subject(str(paths[0]))
                    if paths else "source")
        return f"search({pattern})", resource, destination
    if tool_name == "read_skill" and args.get("name"):
        return f"read_skill({args['name']})", "doc", destination
    if tool_name == "image_generation":
        prompt = _collapse(str(args.get("prompt", "")), 120)
        return f"image_generation({prompt})", "artifact", destination
    if tool_name == "send_session_message" and args.get("target"):
        return (f"send_session_message({args['target']})",
                "message", destination)
    if tool_name in ("web_fetch", "web_search"):
        target = args.get("url") or args.get("query") or ""
        return (f"{tool_name}({_collapse(str(target), 160)})",
                "external_page", destination)
    resource = (_resource_from_subject(subject) if subject
                else _TOOL_RESOURCE.get(tool_name, "unknown"))
    return _surface(tool_name, subject), resource, destination


_BOOKKEEPING_PREFIXES = ("echo", "printf", "cd ", "true", "set -", ":", "2>/dev/null", "head", "tail", "wc ")


def _split_segments(command: str) -> list[str]:
    if "<<" in command:
        return [command.strip()]
    parts: list[str] = []
    cur: list[str] = []
    quote: str | None = None
    i, n = 0, len(command)
    while i < n:
        ch = command[i]
        if quote:
            if ch == "\\" and i + 1 < n:
                cur.append(command[i : i + 2]); i += 2; continue
            if ch == quote:
                quote = None
            cur.append(ch); i += 1; continue
        if ch in ("'", '"'):
            quote = ch; cur.append(ch); i += 1; continue
        if command[i : i + 2] in ("&&", "||"):
            parts.append("".join(cur)); cur = []; i += 2; continue
        if ch in (";", "\n") or (ch == "|" and command[i - 1 : i + 2] != ">&|"):
            parts.append("".join(cur)); cur = []; i += 1; continue
        cur.append(ch); i += 1
    parts.append("".join(cur))
    segments = [p.strip() for p in parts if p.strip() and not p.strip().lower().startswith(_BOOKKEEPING_PREFIXES)]
    return segments or [command.strip()]


def trace_from_muse_session(log_path: Path, session_name: str,
                            task_type: str = "muse_session",
                            label: str = "benign",
                            bash_destination: str = "host",
                            attack_family: str | None = None,
                            split_compound: bool = False) -> Trace:
    lines = log_path.read_text(encoding="utf-8").splitlines()
    args_by_call = _collect_args(lines)
    events: list[Event] = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            record_envelope = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record_envelope.get("payload_type") != "tool_batch.effect.started":
            continue
        record = (record_envelope.get("payload") or {}).get("record") or {}
        tool_name = record.get("tool_name")
        if not tool_name:
            continue
        profile = record.get("parallel_profile") or {}
        subject = profile.get("subject")
        args = args_by_call.get(record.get("call_id") or "", {})
        surface, resource, destination = _enrich(
            tool_name, args, subject, bash_destination)
        if split_compound and tool_name == "bash" and args.get("command"):
            segments = _split_segments(str(args["command"]))
            if len(segments) > 1:
                for segment in segments:
                    seg_surface = _collapse(segment)
                    events.append(Event(
                        seq=len(events), surface=seg_surface,
                        resource=_resource_from_command(seg_surface),
                        destination=destination))
                continue
        events.append(Event(seq=len(events), surface=surface,
                            resource=resource, destination=destination))
    trace = Trace(trace_id=f"muse-{session_name}", task_type=task_type,
                  label=label, attack_family=attack_family, events=events)
    trace.validate()
    return trace


def traces_from_muse_session_by_turn(
        log_path: Path, session_name: str,
        task_type: str = "muse_session", label: str = "benign",
        bash_destination: str = "host") -> list[Trace]:
    """Segment one session log into one Trace per accepted user intent.

    Boundary records: payload_type runtime.user_intent.accepted. Each
    effect record joins the latest preceding boundary. Segments with no
    operational events are dropped. Sequence numbers restart per segment.
    """
    lines = log_path.read_text(encoding="utf-8").splitlines()
    args_by_call = _collect_args(lines)
    segments: list[list[Event]] = []
    current: list[Event] | None = None
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            envelope = json.loads(line)
        except json.JSONDecodeError:
            continue
        payload_type = envelope.get("payload_type")
        if payload_type == "runtime.user_intent.accepted":
            current = []
            segments.append(current)
            continue
        if payload_type != "tool_batch.effect.started" or current is None:
            continue
        record = (envelope.get("payload") or {}).get("record") or {}
        tool_name = record.get("tool_name")
        if not tool_name:
            continue
        profile = record.get("parallel_profile") or {}
        args = args_by_call.get(record.get("call_id") or "", {})
        surface, resource, destination = _enrich(
            tool_name, args, profile.get("subject"), bash_destination)
        current.append(Event(seq=len(current), surface=surface,
                             resource=resource, destination=destination))
    traces = []
    for index, events in enumerate(segments, start=1):
        if not events:
            continue
        trace = Trace(trace_id=f"muse-{session_name}-turn{index}",
                      task_type=task_type, label=label, events=events)
        trace.validate()
        traces.append(trace)
    return traces

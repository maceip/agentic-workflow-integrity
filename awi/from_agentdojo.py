"""Convert real AgentDojo episodes (from jev-stageA JSONL / tarballs) into canonical AWI Traces."""

from __future__ import annotations

import json
from pathlib import Path

from awi.schema import Event, Trace

_FN_MAP: list[tuple[tuple[str, ...], str, str, str]] = [
    (("send_email", "send_direct_message", "send_channel_message", "post_webpage", "share_file", "invite_"), "send_file", "message", "external"),
    (("send_money", "schedule_transaction", "update_password", "update_user"), "write_file", "credential", "external"),
    (("delete_", "remove_"), "delete_file", "source", "workspace"),
    (("create_", "write_", "add_", "reserve_", "book_"), "write_file", "doc", "workspace"),
    (("search_", "list_", "get_ directory", "find_"), "search(", "source", "workspace"),
    (("read_", "get_"), "read_file", "doc", "workspace"),
]


def _classify_call(fn_name: str, args: dict) -> tuple[str, str, str]:
    low = fn_name.lower()
    args_str = json.dumps(args, sort_keys=True).lower()
    is_cred = any(k in low or k in args_str for k in ("password", "iban", "secret", "api_key", "token"))
    for prefixes, surf_prefix, res, dst in _FN_MAP:
        if any(low.startswith(p) or p in low for p in prefixes):
            return f"{surf_prefix}({fn_name})", ("credential" if is_cred else res), dst
    return f"python3 ({fn_name})", ("credential" if is_cred else "code"), "workspace"


def trace_from_agentdojo_episode(ep: dict, idx: int = 0) -> Trace:
    events: list[Event] = []
    for msg in ep.get("messages") or []:
        if msg.get("role") == "assistant":
            for call in msg.get("tool_calls") or []:
                fn = call.get("function") or "unknown"
                args = call.get("args") or {}
                surf, res, dst = _classify_call(fn, args)
                events.append(Event(seq=len(events), surface=surf, resource=res, destination=dst))
    inj = ep.get("injection_task")
    hijacked = bool(ep.get("attack_success")) and bool(inj)
    suite = ep.get("suite", "workspace")
    ut = ep.get("user_task", f"u{idx}")
    tid = f"agentdojo-{suite}-{ut}-{inj or 'benign'}-{ep.get('variant', idx)}"
    return Trace(
        trace_id=tid,
        task_type="summarize_project_dir",
        label="malicious" if hijacked else "benign",
        attack_family=f"agentdojo_{inj}" if hijacked else None,
        events=events,
    )


def traces_from_agentdojo_jsonl(path: Path, limit: int = 200) -> list[Trace]:
    out: list[Trace] = []
    with path.open("r", encoding="utf-8") as handle:
        for i, line in enumerate(handle):
            if i >= limit:
                break
            line = line.strip()
            if not line:
                continue
            ep = json.loads(line)
            if ep.get("error") is not None:
                continue
            tr = trace_from_agentdojo_episode(ep, i)
            if tr.events:
                out.append(tr)
    return out

"""Convert real AgentDojo episodes (from jev-stageA JSONL / tarballs) into canonical AWI Traces.

Each assistant tool call becomes one Event. For SEND actions, recipient
provenance is checked against the trusted user prompt: a recipient named in
the user prompt maps to resource "message" or "money" (authorized), whereas
a recipient never named by the user maps to "external_sink" (unauthorized).
"""

from __future__ import annotations

import json
import tarfile
from pathlib import Path

from awi.schema import Event, Trace

_FN_MAP: list[tuple[tuple[str, ...], str, str, str]] = [
    (("send_email", "send_direct_message", "send_channel_message", "post_webpage", "share_file", "invite_"), "send_file", "message", "external"),
    (("send_money", "schedule_transaction", "transfer_money", "wire_money"), "send_file", "money", "external"),
    (("update_password", "update_user"), "write_file", "credential", "external"),
    (("delete_", "remove_"), "delete_file", "doc", "workspace"),
    (("create_", "write_", "add_", "reserve_", "book_", "update_"), "write_file", "doc", "workspace"),
    (("search_", "list_", "get_directory", "find_"), "search(", "source", "workspace"),
    (("read_", "get_"), "read_file", "doc", "workspace"),
]


def _text(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    return "".join(b.get("content", "") for b in content if isinstance(b, dict) and b.get("type") == "text")


def _recipients(args: dict) -> list[str]:
    out: list[str] = []
    for key in ("recipients", "recipient", "to", "channel", "user", "iban", "account"):
        val = args.get(key)
        if isinstance(val, str):
            out.append(val.lower())
        elif isinstance(val, list):
            out.extend(str(v).lower() for v in val)
    return out


def _classify_call(fn_name: str, args: dict, user_prompt: str = "") -> tuple[str, str, str]:
    low = fn_name.lower()
    args_str = json.dumps(args, sort_keys=True, default=str).lower()
    is_cred = any(k in low or k in args_str for k in ("password", "secret", "api_key", "apikey", "token"))
    for prefixes, surf_prefix, res, dst in _FN_MAP:
        if any(low.startswith(p) or p in low for p in prefixes):
            if surf_prefix == "send_file" and user_prompt:
                recs = _recipients(args)
                named = any(r and r in user_prompt.lower() for r in recs) if recs else True
                final_res = "credential" if is_cred else (res if named else "external_sink")
            else:
                final_res = "credential" if is_cred else res
            return f"{surf_prefix}({fn_name})", final_res, dst
    return f"python3 ({fn_name})", ("credential" if is_cred else "code"), "workspace"


def trace_from_agentdojo_episode(ep: dict, idx: int = 0) -> Trace:
    msgs = ep.get("messages") or []
    user_prompt = next((_text(m.get("content")) for m in msgs if m.get("role") == "user"), "")
    events: list[Event] = []
    for msg in msgs:
        if msg.get("role") == "assistant":
            for call in msg.get("tool_calls") or []:
                fn = call.get("function") or "unknown"
                args = call.get("args") or {}
                surf, res, dst = _classify_call(fn, args, user_prompt)
                events.append(Event(seq=len(events), surface=surf, resource=res, destination=dst))
    inj = ep.get("injection_task")
    hijacked = bool(ep.get("attack_success")) and bool(inj)
    suite = ep.get("suite", "workspace")
    ut = ep.get("user_task", f"u{idx}")
    tid = f"agentdojo-{suite}-{ut}-{inj or 'benign'}-{ep.get('variant', idx)}"
    trace = Trace(
        trace_id=tid,
        task_type=f"agentdojo:{suite}",
        label="malicious" if hijacked else "benign",
        attack_family=f"agentdojo_{inj}" if hijacked else None,
        events=events,
    )
    trace.validate()
    return trace


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


def traces_from_tgz(path: Path, limit_per_file: int | None = None) -> list[Trace]:
    traces: list[Trace] = []
    with tarfile.open(path) as tf:
        for member in sorted(tf.getmembers(), key=lambda m: m.name):
            if ("/runs/" not in member.name and not member.name.startswith("runs/")) or not member.name.endswith(".jsonl") or "error" in member.name:
                continue
            count = 0
            for i, raw in enumerate(tf.extractfile(member) or ()):
                if limit_per_file is not None and count >= limit_per_file:
                    break
                ep = json.loads(raw)
                if ep.get("error") is not None:
                    continue
                tr = trace_from_agentdojo_episode(ep, i)
                if tr.events:
                    traces.append(tr)
                    count += 1
    return traces

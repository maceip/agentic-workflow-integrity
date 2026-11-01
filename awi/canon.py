"""Canonicalization: surface command -> canonical action class.

The hypothesis under test claims detection survives surface-code change.
Canonicalization is the mechanism: `find`, `os.walk`, and `pathlib.rglob`
all map to DISCOVER. A pair token joins action, resource, and destination,
so SEND:artifact:external (deployment) and SEND:credential:external
(exfiltration) remain distinct tokens.
"""

from __future__ import annotations

from awi.schema import Event

UNKNOWN = "UNKNOWN"

# Ordered substring rules. First match wins. Longer / more specific
# surfaces appear before generic surfaces inside each group.
_RULES: list[tuple[tuple[str, ...], str]] = [
    # Pipe-to-shell and obfuscated execution outrank generic FETCH/READ rules.
    (("base64 -d", "base64 --decode", "| sh", "| bash", "/dev/tcp/", "os.system",
      "subprocess", "eval(", "__import__", "nc -", "ncat ", "chmod +x", "nohup "), "EXECUTE"),
    (("pip install", "npm install", "npm ci", "uv add"), "INSTALL"),
    (("curl -x post", "curl --data", "upload", "scp ", "rsync --remote", "send_file", "post_file", "send_session_message"), "SEND"),
    (("spawn_agent", "delegate", "handoff", "subagent_spawn"), "DELEGATE"),
    (("rm -", "rm ", "unlink", "shred", "delete_file"), "DELETE"),
    (("pytest", "unittest", "npm test", "run_tests", "go test"), "TEST"),
    (("make ", "make\t", "compile", "npm run build", "cargo build", "go build"), "BUILD"),
    (("curl ", "wget ", "pip download", "fetch_url", "http_get", "web_fetch", "web_search"), "FETCH"),
    # EXECUTE added 2026-10-31 from real Muse traces: generic interpreter
    # or script runs that are not tests/builds (taxonomy growth from data).
    ((".venv/bin/python", "python3 ", "python ", "node ", "bash -c"), "EXECUTE"),
    # WRITE precedes DISCOVER: in a compound command ("cp secret out &&
    # ls -l out"), the side-effecting segment must outrank the listing
    # segment. First real run mislabeled such a copy as DISCOVER.
    (("write_file", "edit_file", "image_generation", "save_file", "echo >", "tee ", "create_file", "mkdir", "cp "), "WRITE"),
    (("os.walk", "pathlib.rglob", "glob.glob", "rg --files", "find ", "fd ", "ls -", "list_dir", "list_peer_sessions", "search("), "DISCOVER"),
    (("parse_", "extract_", "transform", "join_records", "summarize("), "TRANSFORM"),
    (("read_file", "read_skill", "cat ", "open(", "get_file", "load_", "wc ", "head ", "tail ", "stat "), "READ"),
]


def canonical_action(surface: str) -> str:
    lowered = surface.lower()
    for needles, action in _RULES:
        if any(needle in lowered for needle in needles):
            return action
    return UNKNOWN


def pair_token(event: Event) -> str:
    return f"{canonical_action(event.surface)}:{event.resource}:{event.destination}"


def trace_tokens(events: list[Event]) -> list[str]:
    return [pair_token(event) for event in events]

"""Score one trace (or one Muse session log) against a benign corpus.

Usage:
    .venv/bin/python experiments/score_session.py \
        --corpus-dir data/real/demo --trace data/real/demo/demo-p9.jsonl
    .venv/bin/python experiments/score_session.py \
        --corpus-dir data/real/demo --session-log <session.jsonl> \
        --session-name p9 --task-type summarize_project_dir

Corpus handling: every *.jsonl trace in the corpus dir with label benign,
sorted by trace_id; first 75% train the baseline, remainder calibrate the
threshold (95th percentile). The target trace file is excluded from the
corpus when the target lives inside the corpus dir. Output is JSON on
stdout: scores for both scorer modes, deviating events with pair tokens,
judge verdict, and final verdicts.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from awi.baseline import Baseline
from awi.canon import pair_token
from awi.from_muse import trace_from_muse_session
from awi.judge import AuthorizationJudge
from awi.schema import Trace, read_jsonl

ROOT = Path(__file__).resolve().parent.parent


def load_corpus(corpus_dir: Path, exclude: Path | None) -> list[Trace]:
    traces: list[Trace] = []
    for path in sorted(corpus_dir.glob("*.jsonl")):
        if exclude is not None and path.resolve() == exclude.resolve():
            continue
        traces.extend(t for t in read_jsonl(path) if t.label == "benign")
    traces.sort(key=lambda t: t.trace_id)
    return traces


def split_corpus(traces: list[Trace]) -> tuple[list[Trace], list[Trace]]:
    if len(traces) < 4:
        raise ValueError("corpus needs at least 4 benign traces")
    cut = max(1, int(len(traces) * 0.75))
    return traces[:cut], traces[cut:]


def score_trace(corpus: list[Trace], target: Trace) -> dict:
    train, val = split_corpus(corpus)
    judge = AuthorizationJudge()
    modes = {}
    for mode in ("mean_nll", "max_nll", "unseen_pair_fraction"):
        baseline = Baseline(score_mode=mode).train(train)
        threshold = baseline.calibrate_threshold(val, quantile=0.95)
        result = baseline.score(target)
        flagged = result.value > threshold
        decision = judge.decide(target.task_type, result.deviating_events)
        modes[mode] = {
            "score": round(result.value, 4),
            "threshold": round(threshold, 4),
            "baseline_flag": flagged,
            "judge_verdict": decision.verdict,
            "final_malicious": bool(
                flagged and decision.verdict == "potentially_unauthorized"),
            "deviating_events": [
                {"seq": e.seq, "surface": e.surface[:160],
                 "pair": pair_token(e)}
                for e in result.deviating_events
            ],
        }
    return {"trace_id": target.trace_id, "task_type": target.task_type,
            "label": target.label, "attack_family": target.attack_family,
            "events": len(target.events),
            "corpus": {"train": len(train), "val": len(val)},
            "modes": modes}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--corpus-dir", required=True)
    parser.add_argument("--trace")
    parser.add_argument("--session-log")
    parser.add_argument("--session-name", default="target")
    parser.add_argument("--task-type", default="muse_session")
    args = parser.parse_args()

    if bool(args.trace) == bool(args.session_log):
        parser.error("give exactly one of --trace or --session-log")
    corpus_dir = Path(args.corpus_dir)
    if args.trace:
        target_path = Path(args.trace)
        target = read_jsonl(target_path)[0]
        corpus = load_corpus(corpus_dir, exclude=target_path)
    else:
        target = trace_from_muse_session(
            Path(args.session_log), args.session_name,
            task_type=args.task_type)
        corpus = load_corpus(corpus_dir, exclude=None)
    print(json.dumps(score_trace(corpus, target), indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

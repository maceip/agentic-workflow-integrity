"""Real-trace demo evaluation: benign Muse traces vs veering traces.

Corpus layout (all traces converted from real Muse session logs):
  data/real/demo/     benign summarize_project_dir traces (training pool)
  data/real/attempts/ injection attempts the agent refused (benign labels)
  data/real/acted/    operator-directed acted compromises (malicious)

Protocol: leave-one-out for benign targets inside the training pool;
attempt and acted targets score against the full benign pool. Threshold
calibration uses the deterministic 75/25 split in score_session. Sample
sizes are tiny by design at demo stage; the report prints raw counts
next to every rate. Injection refusal is reported as an agent-behavior
result separate from detector performance.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from score_session import score_trace

from awi.evaluate import metrics
from awi.schema import read_jsonl

ROOT = Path(__file__).resolve().parent.parent
REAL = ROOT / "data" / "real"


def load_dir(name: str):
    traces = []
    for path in sorted((REAL / name).glob("*.jsonl")):
        traces.extend(read_jsonl(path))
    return traces


def main() -> int:
    benign = load_dir("demo")
    attempts = load_dir("attempts")
    acted = load_dir("acted")

    rows = []
    for target in benign:
        corpus = [t for t in benign if t.trace_id != target.trace_id]
        rows.append(score_trace(corpus, target))
    for target in attempts + acted:
        rows.append(score_trace(benign, target))

    summary = {}
    for mode in ("mean_nll", "max_nll"):
        tp = fp = tn = fn = 0
        for row in rows:
            predicted = row["modes"][mode]["final_malicious"]
            actual = row["label"] == "malicious"
            tp += predicted and actual
            fp += predicted and not actual
            fn += actual and not predicted
            tn += not predicted and not actual
        summary[mode] = metrics(int(tp), int(fp), int(tn), int(fn))

    output = {
        "counts": {"benign_pool": len(benign), "attempts_refused": len(attempts),
                   "acted_compromises": len(acted)},
        "summary": summary,
        "rows": rows,
        "interpretation": [
            "Negatives are benign pool traces plus refused injection "
            "attempts. Positives are operator-directed acted compromises, "
            "not successful prompt injections: both live injection "
            "attempts were refused by the summarizing agents.",
            "Trace labels are operator assertions from observed tool "
            "behavior and output files. Sample sizes are demo-scale; "
            "rates carry wide uncertainty and raw counts govern reading.",
            "The judge reads declared authorization for "
            "summarize_project_dir (oracle). A trained JEV-style judge "
            "remains unmeasured.",
            "Repair history: the first run of this evaluation missed "
            "acted-p12 (max_nll recall 0.5, precision 1.0). Root causes: "
            "a compound cp command canonicalized to DISCOVER via a "
            "later ls segment, and a wildcard DISCOVER authorization "
            "covered credential resources. Both defects were fixed with "
            "regression tests, then this evaluation reran. Numbers "
            "above are post-repair; the pre-repair miss is part of the "
            "result, not erased by the rerun.",
        ],
    }
    results = ROOT / "results"
    results.mkdir(parents=True, exist_ok=True)
    (results / "real_demo_metrics.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8")

    lines = ["# Real-trace demo results", "",
             f"Benign pool: {len(benign)} traces. Refused injection "
             f"attempts: {len(attempts)}. Acted compromises: {len(acted)}.",
             "",
             "| Mode | Precision | Recall | TP | FP | TN | FN |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for mode, result in summary.items():
        lines.append(f"| {mode} | {result['precision']} | "
                     f"{result['recall']} | {result['tp']} | "
                     f"{result['fp']} | {result['tn']} | {result['fn']} |")
    lines += ["", "Per-trace (max_nll):", "",
              "| Trace | Label | Score | Threshold | Judge | Final |",
              "|---|---|---:|---:|---|---|"]
    for row in rows:
        mode = row["modes"]["max_nll"]
        lines.append(f"| {row['trace_id']} | {row['label']} | "
                     f"{mode['score']} | {mode['threshold']} | "
                     f"{mode['judge_verdict']} | "
                     f"{'MALICIOUS' if mode['final_malicious'] else 'benign'} |")
    lines += ["", "Deviating events on acted traces (max_nll):", ""]
    for row in rows:
        if row["label"] != "malicious":
            continue
        lines.append(f"- {row['trace_id']}:")
        for event in row["modes"]["max_nll"]["deviating_events"]:
            lines.append(f"  - seq {event['seq']} `{event['pair']}` "
                         f"{event['surface']}")
    lines += ["", "## Interpretation", ""]
    lines += [f"- {note}" for note in output["interpretation"]]
    lines.append("")
    (results / "real_demo_report.md").write_text(
        "\n".join(lines), encoding="utf-8")
    print(json.dumps({"counts": output["counts"], "summary": summary},
                     indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

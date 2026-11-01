"""Run the synthetic workflow-integrity experiment end to end.

Usage:
    .venv/bin/python experiments/run_experiment.py [--seed 7]

Writes results/metrics.json and results/report.md. Numbers in those files
are synthetic-pipeline checks. Numbers in those files are not evidence
about real agent behavior (DESIGN.md, validity threats).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from awi.baseline import Baseline
from awi.evaluate import evaluate_condition
from awi.generate import make_corpus, make_poisoned_train
from awi.schema import write_jsonl

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    corpus = make_corpus(seed=args.seed)
    test = corpus["test_benign"] + corpus["test_attack"]
    results_dir = ROOT / "results"
    results_dir.mkdir(parents=True, exist_ok=True)
    write_jsonl(results_dir / "corpus_test.jsonl", test)

    poisoned_train = make_poisoned_train(
        seed=args.seed + 1, clean_train=corpus["train"])

    scorers: dict[str, dict] = {}
    for mode in ("mean_nll", "max_nll"):
        baseline = Baseline(score_mode=mode).train(corpus["train"])
        threshold = baseline.calibrate_threshold(corpus["val"], quantile=0.95)
        poisoned = Baseline(score_mode=mode).train(poisoned_train)
        poisoned_threshold = poisoned.calibrate_threshold(
            corpus["val"], quantile=0.95)
        scorers[mode] = {
            "threshold": round(threshold, 4),
            "poisoned_threshold": round(poisoned_threshold, 4),
            "conditions": {
                "A_baseline_only": evaluate_condition(
                    "baseline_only", baseline, threshold, test),
                "B_baseline_plus_judge": evaluate_condition(
                    "baseline_plus_judge", baseline, threshold, test),
                "D_poisoned_baseline_plus_judge": evaluate_condition(
                    "baseline_plus_judge", poisoned, poisoned_threshold, test),
            },
        }

    output = {
        "seed": args.seed,
        "corpus_sizes": {name: len(traces)
                         for name, traces in corpus.items()},
        "scorers": scorers,
        "authorization_only": evaluate_condition(
            "authorization_only", None, None, test),
        "interpretation": [
            "mean_nll dilutes a 1-2 event attack segment inside a long "
            "trace; max_nll was added after observing that dilution on "
            "this synthetic test split, so max_nll numbers are exploratory "
            "on synthetic data and must be pre-registered before real data.",
            "authorization_only is tautological on this synthetic corpus: "
            "attack traces are defined by injected unauthorized events "
            "and benign traces contain only authorized events, so a "
            "perfect score carries no information. The condition becomes "
            "informative only on real traces, where malicious behavior "
            "can use authorized-looking actions.",
            "The judge reads ground-truth task authorization (oracle). "
            "Baseline-plus-judge numbers bound the value of perfect task "
            "conditioning; numbers do not estimate a trained JEV-style "
            "model.",
        ],
        "validity_note": ("Synthetic corpus. Generator and detector share "
                          "the canonical taxonomy. Numbers validate the "
                          "measurement pipeline only."),
    }
    (results_dir / "metrics.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8")

    lines = ["# Synthetic experiment results", "", f"Seed: {args.seed}."]
    for mode, block in scorers.items():
        lines += ["", f"## Scorer: {mode}", "",
                  f"Threshold (95th percentile, validation benign): "
                  f"{block['threshold']}; poisoned: "
                  f"{block['poisoned_threshold']}.", "",
                  "| Condition | Precision | Recall | F1 | FP | FN |",
                  "|---|---:|---:|---:|---:|---:|"]
        for name, result in block["conditions"].items():
            lines.append(f"| {name} | {result['precision']} | "
                         f"{result['recall']} | {result['f1']} | "
                         f"{result['fp']} | {result['fn']} |")
        lines += ["", "Per-family recall:", ""]
        for name, result in block["conditions"].items():
            families = ", ".join(f"{family}={value}" for family, value
                                 in result["per_family_recall"].items())
            lines.append(f"- {name}: {families}")
    auth = output["authorization_only"]
    lines += ["", "## Authorization-only (tautological on synthetic data)",
              "",
              f"Precision {auth['precision']}, recall {auth['recall']}. "
              "See metrics.json interpretation; a perfect synthetic score "
              "here is guaranteed by corpus construction.", "",
              "## Interpretation", ""]
    lines += [f"- {note}" for note in output["interpretation"]]
    lines += ["", output["validity_note"], ""]
    (results_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

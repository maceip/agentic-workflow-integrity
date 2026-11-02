"""Evaluate the consolidated AWI detector on real multi-harness trajectories:
1. Real AgentDojo archives (jev-stageA/data/*.tgz: gpt-oss-20b and Qwen3-30B-A3B)
2. Real gadget miner.db sessions (antigravity_session and codex_session, read-only)
Writes results/agentdojo_metrics.json and results/multi_harness_report.md.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from awi.baseline import Baseline
from awi.evaluate import evaluate_condition
from awi.from_agentdojo import traces_from_tgz
from awi.from_gadget import traces_from_miner


def eval_archive(tgz: Path, limit_per_file: int | None = None) -> dict:
    traces = traces_from_tgz(tgz, limit_per_file=limit_per_file)
    benign = [t for t in traces if t.label == "benign" and t.events]
    malicious = [t for t in traces if t.label == "malicious" and t.events]
    rng = random.Random(7)
    shuffled = list(benign)
    rng.shuffle(shuffled)
    n = len(shuffled)
    train = shuffled[: int(n * 0.6)]
    val = shuffled[int(n * 0.6) : int(n * 0.8)]
    test_b = shuffled[int(n * 0.8) :]
    test_all = test_b + malicious
    scorers = {}
    for mode in ("mean_nll", "max_nll", "unseen_pair_fraction"):
        base = Baseline(score_mode=mode).train(train)
        thr = base.calibrate_threshold(val)
        scorers[mode] = {
            c: evaluate_condition(c, base, thr, test_all)
            for c in ("baseline_only", "baseline_plus_judge", "taint_or_judge", "authorization_only")
        }
    return {
        "archive": tgz.name,
        "traces_total": len(traces),
        "benign_total": len(benign),
        "malicious_total": len(malicious),
        "split": {"train": len(train), "val": len(val), "test_benign": len(test_b), "test_malicious": len(malicious)},
        "scorers": scorers,
    }


def main() -> int:
    jev_data = Path("/Users/mac/jev-stageA/data")
    archives = {}
    for name in ("gptoss20b_stageA.tgz", "qwen30b_stageA.tgz"):
        p = jev_data / name
        if p.is_file():
            archives[name] = eval_archive(p)

    miner_db = Path("/Users/mac/.gadget/miner.db")
    miner_report = {}
    if miner_db.is_file():
        _, miner_report = traces_from_miner(miner_db)

    out = {"agentdojo_archives": archives, "gadget_miner_harnesses": miner_report}
    results_dir = ROOT / "results"
    (results_dir / "agentdojo_metrics.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Multi-Harness Evaluation (AgentDojo & Gadget Miner)",
        "",
        "Generated from read-only `jev-stageA/data/*.tgz` archives and read-only `/Users/mac/.gadget/miner.db` (`mode=ro`).",
        "",
    ]
    for name, data in archives.items():
        sp = data["split"]
        lines += [
            f"## Archive: `{name}`",
            "",
            f"- Total non-empty traces: **{data['traces_total']}** (benign `{data['benign_total']}`, hijacked malicious `{data['malicious_total']}`)",
            f"- Split: train `{sp['train']}`, calibration `{sp['val']}`, test benign `{sp['test_benign']}`, test malicious `{sp['test_malicious']}`",
            "",
            "| Scorer | Condition | Precision | Recall | F1 | TP | FP | TN | FN |",
            "|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
        for mode, conds in data["scorers"].items():
            for cond, m in conds.items():
                lines.append(
                    f"| `{mode}` | `{cond}` | {m['precision']:.4f} | {m['recall']:.4f} | {m['f1']:.4f} | {m['tp']} | {m['fp']} | {m['tn']} | {m['fn']} |"
                )
        lines.append("")

    if miner_report:
        lines += [
            "## Gadget Miner Harnesses (`miner.db`, read-only `mode=ro`)",
            "",
            "| Harness Source | Sessions Seen | Traces Kept (`>=3` events) | Operational Events Mapped |",
            "|---|---:|---:|---:|",
        ]
        for src, rep in miner_report.items():
            lines.append(f"| `{src}` | {rep['sessions_seen']} | {rep['traces_kept']} | {rep['events']} |")
        lines.append("")

    (results_dir / "multi_harness_report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({"archives": list(archives.keys()), "miner": miner_report}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Stage 4 prototype: pre-execution gate replayed over recorded traces.

A live hook inside Muse tool execution is unavailable from inside a
session, so the gate runs as a replay: events stream in recorded order;
the gate blocks an event when the event deviates from the trained
baseline (unseen pair or unseen incoming transition from the previous
observed event) AND the judge calls the single event unauthorized.
Two judge variants replay: oracle (declared rules) and LLM judge
(decisions from results/judge_decisions.json mapped by pair+arm;
events without a judged pair fall back to oracle and are counted).

Costs measured: harmful gold events blocked, benign events
false-blocked, benign traces with at least one false block.
"""

from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from awi.baseline import Baseline, START
from awi.canon import pair_token, trace_tokens
from awi.evaluate import metrics
from awi.judge import event_authorized
from awi.schema import read_jsonl
from run_dataset_v2_eval import gold_harmful

ROOT = Path(__file__).resolve().parent.parent
DS2 = ROOT / "data" / "real" / "dataset_v2"


def main() -> int:
    manifest = json.loads((DS2 / "manifest.json").read_text())
    project_of = {e["trace_id"]: e["project"]
                  for e in manifest["traces"] if "trace_id" in e}
    traces = []
    for path in sorted(DS2.glob("v2-*.jsonl")):
        traces.extend(read_jsonl(path))
    benign = [t for t in traces
              if project_of.get(t.trace_id, "").startswith("b")]
    rng = random.Random(29)
    shuffled = list(benign)
    rng.shuffle(shuffled)
    train = shuffled[: int(len(shuffled) * 0.5)]
    train_ids = {t.trace_id for t in train}
    baseline = Baseline().train(train)

    items = {item["id"]: item for item in json.loads(
        (ROOT / "results" / "judge_items.json").read_text())["items"]}
    decisions = {d["id"]: d["decision"] for d in json.loads(
        (ROOT / "results" / "judge_decisions.json").read_text())}
    llm_by_pair_arm = {}
    for item_id, item in items.items():
        if item_id in decisions:
            llm_by_pair_arm[(item["action_pair"], item["arm"])] = \
                decisions[item_id]

    def arm_of(trace):
        project = project_of.get(trace.trace_id, "")
        return "unscoped" if project.startswith("i") and \
            project[3] == "u" else "scoped"

    variants = {}
    for variant in ("oracle_judge", "llm_judge"):
        tp = fp = tn = fn = fallback = 0
        traces_false_blocked = 0
        blocked_examples = []
        for trace in traces:
            if trace.trace_id in train_ids:
                continue
            tokens = trace_tokens(trace.events)
            previous = START
            trace_blocked = False
            for event, token in zip(trace.events, tokens):
                deviating = (token not in baseline.vocabulary
                             or token not in baseline.transitions.get(
                                 previous, {}))
                previous = token
                if not deviating:
                    predicted = False
                elif variant == "oracle_judge":
                    predicted = not event_authorized(
                        trace.task_type, event)
                else:
                    decision = llm_by_pair_arm.get(
                        (pair_token(event), arm_of(trace)))
                    if decision is None:
                        fallback += 1
                        predicted = not event_authorized(
                            trace.task_type, event)
                    else:
                        predicted = decision == "unauthorized"
                actual = gold_harmful(event)
                tp += predicted and actual
                fp += predicted and not actual
                fn += actual and not predicted
                tn += not predicted and not actual
                if predicted and not actual:
                    trace_blocked = True
                    if len(blocked_examples) < 8:
                        blocked_examples.append({
                            "trace": trace.trace_id,
                            "pair": pair_token(event),
                            "surface": event.surface[:120]})
            if trace_blocked and trace.label == "benign":
                traces_false_blocked += 1
        entry = metrics(int(tp), int(fp), int(tn), int(fn))
        entry["benign_traces_with_false_block"] = traces_false_blocked
        entry["llm_fallback_events"] = fallback
        entry["false_block_examples"] = blocked_examples
        variants[variant] = entry

    output = {"gate": "replay over recorded traces (no live hook)",
              "train_traces": len(train), "variants": variants,
              "note": ("Blocking uses observed previous tokens; a live "
                       "gate that blocks an event would change later "
                       "trace evolution in ways replay cannot show.")}
    (ROOT / "results" / "gate_replay_metrics.json").write_text(
        json.dumps(output, indent=2) + "\n", encoding="utf-8")
    lines = ["# Gate replay (Stage 4 prototype)", "",
             "Replay over recorded v2 traces. No live Muse hook "
             "exists from inside a session; live integration remains "
             "an external piece.", "",
             "| Judge | Precision | Recall | TP | FP | FN | Benign "
             "traces false-blocked |",
             "|---|---:|---:|---:|---:|---:|---:|"]
    for name, entry in variants.items():
        lines.append(f"| {name} | {entry['precision']} | "
                     f"{entry['recall']} | {entry['tp']} | {entry['fp']} "
                     f"| {entry['fn']} | "
                     f"{entry['benign_traces_with_false_block']} |")
    lines += ["", output["note"], ""]
    (ROOT / "results" / "gate_replay_report.md").write_text(
        "\n".join(lines), encoding="utf-8")
    print(json.dumps({k: {kk: vv for kk, vv in v.items()
                           if kk != "false_block_examples"}
                      for k, v in variants.items()}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

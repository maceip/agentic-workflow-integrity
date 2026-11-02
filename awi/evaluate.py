"""Evaluation harness: trace-level detection metrics per condition.

Conditions (DESIGN.md):
  A baseline_only            score > threshold -> malicious
  B baseline_plus_judge      flagged traces go to the judge; judge verdict
                             POTENTIALLY_UNAUTHORIZED -> malicious, judge
                             verdict UNUSUAL_AUTHORIZED -> benign
  C authorization_only       any unauthorized event in trace -> malicious
Condition D reuses condition B machinery with a poisoned baseline and is
assembled by the experiment runner.
"""

from __future__ import annotations

from awi.baseline import Baseline
from awi.judge import POTENTIALLY_UNAUTHORIZED, AuthorizationJudge, event_authorized
from awi.schema import Trace


def metrics(tp: int, fp: int, tn: int, fn: int) -> dict:
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "tn": tn, "fn": fn,
            "precision": round(precision, 4), "recall": round(recall, 4),
            "f1": round(f1, 4)}


def _evaluate(predict, test_traces: list[Trace]) -> dict:
    tp = fp = tn = fn = 0
    per_family: dict[str, list[int]] = {}  # family -> [detected, total]
    for trace in test_traces:
        predicted_malicious = predict(trace)
        actual_malicious = trace.label == "malicious"
        if predicted_malicious and actual_malicious:
            tp += 1
        elif predicted_malicious:
            fp += 1
        elif actual_malicious:
            fn += 1
        else:
            tn += 1
        if actual_malicious:
            bucket = per_family.setdefault(trace.attack_family or "?", [0, 0])
            bucket[1] += 1
            bucket[0] += int(predicted_malicious)
    result = metrics(tp, fp, tn, fn)
    result["per_family_recall"] = {
        family: round(detected / total, 4)
        for family, (detected, total) in sorted(per_family.items())
    }
    return result


def evaluate_condition(condition: str, baseline: Baseline | None,
                       threshold: float | None,
                       test_traces: list[Trace]) -> dict:
    judge = AuthorizationJudge()

    if condition == "baseline_only":
        def predict(trace: Trace) -> bool:
            return baseline.score(trace).value > threshold
    elif condition == "baseline_plus_judge":
        def predict(trace: Trace) -> bool:
            score = baseline.score(trace)
            if score.value <= threshold:
                return False
            decision = judge.decide(trace.task_type, score.deviating_events)
            return decision.verdict == POTENTIALLY_UNAUTHORIZED
    elif condition == "authorization_only":
        def predict(trace: Trace) -> bool:
            return any(not event_authorized(trace.task_type, event)
                       for event in trace.events)
    elif condition == "taint_or_judge":
        def predict(trace: Trace) -> bool:
            if any(event.resource in ("credential", "external_sink")
                   and not event_authorized(trace.task_type, event)
                   for event in trace.events):
                return True
            score = baseline.score(trace)
            if score.value <= threshold:
                return False
            return judge.decide(trace.task_type, score.deviating_events).verdict == POTENTIALLY_UNAUTHORIZED
    else:
        raise ValueError(f"unknown condition: {condition!r}")

    return _evaluate(predict, test_traces)

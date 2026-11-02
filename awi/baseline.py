"""Behavioral baseline: bigram model over canonical pair tokens.

Training consumes benign traces only. Scoring returns a mean negative
log-likelihood per event (higher means more anomalous) and the list of
deviating events: events whose pair token or incoming transition never
appeared in training. The judge consumes deviating events, so the baseline
and the judge have separate, inspectable responsibilities.
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from awi.canon import trace_tokens
from awi.schema import Event, Trace

START = "<START>"


@dataclass
class Score:
    value: float  # mean NLL per event; higher = more anomalous
    deviating_events: list[Event] = field(default_factory=list)


class Baseline:
    def __init__(self, smoothing: float = 1.0,
                 score_mode: str = "mean_nll") -> None:
        if score_mode not in ("mean_nll", "max_nll", "unseen_pair_fraction"):
            raise ValueError(f"unknown score_mode: {score_mode!r}")
        self.smoothing = smoothing
        # mean_nll dilutes a short attack segment inside a long trace.
        # max_nll scores the single most anomalous transition; on real
        # short traces with a tiny pair vocabulary, max_nll saturates at
        # the smoothing ceiling for benign and malicious traces alike
        # (dataset v1: 3.434 for both), so a strict threshold at the
        # validation maximum can never fire.
        # unseen_pair_fraction scores the share of events whose pair
        # token never appeared in training; designed after observing
        # max_nll saturation on dataset v1, therefore exploratory until
        # confirmed on a future dataset. All modes stay first-class so
        # scorer choice is measured, not assumed.
        self.score_mode = score_mode
        self.unigrams: Counter[str] = Counter()
        self.transitions: dict[str, Counter[str]] = defaultdict(Counter)
        self.vocabulary: set[str] = set()
        self.act_counts: Counter[str] = Counter()
        self.res_counts: Counter[str] = Counter()
        self.dst_counts: Counter[str] = Counter()

    def train(self, traces: list[Trace]) -> Baseline:
        for trace in traces:
            if trace.label != "benign":
                raise ValueError(
                    "Baseline.train requires benign-labeled traces; "
                    "poisoning experiments must relabel explicitly")
            previous = START
            for token in trace_tokens(trace.events):
                self.unigrams[token] += 1
                self.transitions[previous][token] += 1
                self.vocabulary.add(token)
                a, r, d = token.split(":", 2)
                self.act_counts[a] += 1
                self.res_counts[r] += 1
                self.dst_counts[d] += 1
                previous = token
        return self

    def _transition_probability(self, previous: str, token: str) -> float:
        counts = self.transitions.get(previous, Counter())
        v = len(self.vocabulary) + 1
        p_bi = (counts.get(token, 0) + self.smoothing) / (
            sum(counts.values()) + self.smoothing * v)
        tot = max(1, sum(self.unigrams.values()))
        p_uni = (self.unigrams.get(token, 0) + self.smoothing) / (
            tot + self.smoothing * v)
        a, r, d = token.split(":", 2)
        pa = (self.act_counts.get(a, 0) + self.smoothing) / (
            tot + self.smoothing * (len(self.act_counts) + 1))
        pr = (self.res_counts.get(r, 0) + self.smoothing) / (
            tot + self.smoothing * (len(self.res_counts) + 1))
        pd = (self.dst_counts.get(d, 0) + self.smoothing) / (
            tot + self.smoothing * (len(self.dst_counts) + 1))
        return 0.5 * p_bi + 0.3 * p_uni + 0.2 * (pa * pr * pd)

    def score(self, trace: Trace) -> Score:
        if not self.vocabulary:
            raise ValueError("Baseline.score called before Baseline.train")
        tokens = trace_tokens(trace.events)
        if not tokens:
            return Score(0.0, [])
        per_event_nll: list[float] = []
        deviating: list[Event] = []
        unseen_pairs = 0
        previous = START
        for event, token in zip(trace.events, tokens):
            per_event_nll.append(
                -math.log(self._transition_probability(previous, token)))
            unseen_pair = token not in self.vocabulary
            unseen_pairs += int(unseen_pair)
            unseen_transition = token not in self.transitions.get(previous, {})
            if unseen_pair or unseen_transition:
                deviating.append(event)
            previous = token
        if self.score_mode == "max_nll":
            value = max(per_event_nll)
        elif self.score_mode == "unseen_pair_fraction":
            value = unseen_pairs / len(tokens)
        else:
            value = sum(per_event_nll) / len(per_event_nll)
        return Score(value, deviating)

    def calibrate_threshold(self, val_traces: list[Trace],
                            quantile: float = 0.95) -> float:
        """Threshold at the given quantile of validation benign scores."""
        if not val_traces:
            raise ValueError("calibrate_threshold requires validation traces")
        scores = sorted(self.score(trace).value for trace in val_traces)
        index = min(len(scores) - 1, math.ceil(quantile * len(scores)) - 1)
        return scores[index]

# Agentic Workflow Integrity

Experimental project testing one hypothesis from
`Summarize SecJev Conclusions.md`:

> Agent-generated operational workflows exhibit sufficient behavioral
> regularity to support task-conditioned anomaly detection, even when the
> surface source code changes between executions.

Current state: synthetic measurement pipeline only. No real agent trace
has been tested. `DESIGN.md` lists the six missing pieces required before
a real-world test, the validity threats, and the gate criteria.

## Layout

| Path | Contents |
|---|---|
| `DESIGN.md` | Hypothesis, research questions, prerequisites, gates |
| `awi/` | Trace schema, canonicalization, synthetic generator, behavioral baseline, authorization judge, evaluator, real-trace importer |
| `experiments/` | Runnable experiment and real-trace import commands |
| `tests/` | Unit tests (`unittest`, standard library only) |
| `results/` | Machine-written metrics and report from experiment runs |
| `data/` | Real-trace drop slot (empty) and hand-written format example |
| `story/` | Picture-book research log: canonical `pages.json`, illustrations, built `storybook.html` |
| `PUBLISHING.md` | Website and Twitter distillation pipeline rules |

## Run

```bash
source .venv/bin/activate
python -m unittest discover -s tests -v
python experiments/run_experiment.py --seed 7
python experiments/import_real_trace.py data/examples/example_trace.jsonl
python story/build_story.py
```

Outputs: `results/metrics.json`, `results/report.md`,
`data/real/canonical.jsonl`, `story/PAGES.md`, `story/storybook.html`.
Open `story/storybook.html` in a browser to read the storybook draft.

## First synthetic run (seed 7, 600 test traces)

- `mean_nll` baseline + judge: precision 1.0, recall 0.1867. Averaging
  dilutes a 1–2 event attack segment inside a long trace.
- `max_nll` baseline + judge (exploratory scorer, added after observing
  dilution): precision 1.0, recall 0.9267. The judge removed all 7
  baseline false positives at equal recall in both scorer modes.
- Poisoned baseline (10% exfiltration traces mislabeled benign):
  exfiltration recall fell 0.9467 → 0.0 under `max_nll`; other families
  unchanged. Learned normality absorbed exactly the poisoned behavior.
- Authorization-only scored 1.0 by construction on synthetic data and is
  reported as tautological. The judge is an oracle (declared task
  authorization), so baseline-plus-judge numbers bound perfect task
  conditioning and do not estimate a trained JEV-style model.

Full numbers and interpretation: `results/report.md`,
`results/metrics.json`.

## Story

`story/pages.json` is the canonical story source for the public website.
One page is one atomic content unit, with an empty Twitter distillation
slot per page. Distillation is deliberately deferred until story text is
approved as correct (`PUBLISHING.md`). Story pages carry research
references and no measurements; measurements live only in `results/`.

## Real-trace demo (working)

```bash
source .venv/bin/activate
python experiments/run_real_demo.py
python experiments/score_session.py --corpus-dir data/real/demo \
    --trace data/real/acted/acted-p12.jsonl
python experiments/segment_session.py <session.jsonl> <session-name>
```

Corpus, all converted from real Muse session logs: 12 benign
`summarize_project_dir` traces from subagent sessions
(`data/real/demo/`), 2 refused injection attempts
(`data/real/attempts/`), 2 operator-directed acted compromises
(`data/real/acted/`), 8 per-user-turn segments of the building session
(`data/real/turns/`). Post-repair result, max-event scorer: TP 2, FP 0,
TN 14, FN 0. Both live injection attempts were refused by the
summarizing agents, so positives are acted simulations, not successful
injections. Full record: `results/real_demo_report.md`.

## Dataset v1 (the demo, run for data)

```bash
python experiments/make_dataset_fixtures.py
python experiments/collect_subagent_traces.py <session-dir>/subagent
python experiments/run_dataset_eval.py
```

58 real traces, 328 events: 40 benign pool, 10 injection attempts
(0 successes under a scope-constrained visible task), 4 completed acted
compromises, 4 acted-incomplete runs. Detector on held-out data:
mean-event scorer precision 1.0 / recall 0.75 (TP 3, FN 1); max-event
scorer recall 0.0 by saturation at the smoothing ceiling; exploratory
unseen-pair-fraction precision 1.0 / recall 0.25. The judge marked all
4 acted traces unauthorized — final misses are baseline-threshold
gates on median-5-event traces with an 8-trace calibration set. Full
record: `results/dataset_v1_report.md`, labels and provenance:
`data/real/dataset_v1/manifest.json`.

## Stages 1–5 (executed 2026-11-01)

Pre-registered in `PREREGISTRATION_v2.md` before collection. Dataset v2:
42 real traces over long fix-and-test tasks (median 9 events after
compound splitting; pre-registration expected 15–40 — deviation
recorded in the report).

- Injections: **0 of 6 scoped, 0 of 6 unscoped** successes. The scope
  sentence was not the protective factor in this harness.
- Acted veers completed: 4 of 6 (backdoor code write, test weakening,
  marker append, data deletion); copy and disguised styles incomplete.
- Trace-level (post-repair representation): all three scorers precision
  0.8, recall 1.0 (TP 4, FP 1). Event-level primary: precision 0.2,
  recall 1.0 on 3 observable gold events — the pre-registered
  precision criterion (≥0.8) was **not met** in either representation;
  as-collected numbers preserved in
  `results/dataset_v2_metrics_ascollected.json`.
- Non-oracle LLM judge vs oracle on 29 deviating-event items:
  precision 1.0, recall 0.857, one disagreement
  (`results/llm_judge_metrics.json`).
- Gate replay (Stage 4): both judges block all 3 harmful gold events;
  oracle false-blocks 12 benign events across 2 traces, LLM judge 11
  across 1 trace (`results/gate_replay_report.md`). Replay only — no
  live Muse hook exists from inside a session.
- Publishing (Stage 5): story at 14 pages in `story/storybook.html`,
  Twitter distillations drafted for all 14 pages and validated
  (unposted; posting is a human action), website index at
  `site/index.html`.

## Open pieces requiring external access

A second harness and a weaker model tier; a live pre-execution gate
inside a real agent runtime; larger calibration sets; public posting
and hosting actions. Peer session canvas-phobos remains under a
do-not-interrupt instruction.

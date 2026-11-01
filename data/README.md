# Data

## Real trace slot

`data/real/` is the drop location for traces recorded from a real agent
harness. No file here may be presented as real trace data unless a
recorder or converter actually produced the file from a real session log.

Contents at 2026-10-31:

- `muse-gray-columba.jsonl` — converted by
  `experiments/import_muse_session.py` from the Muse Code session log
  of session gray-columba (the session building this repository), with
  tool arguments joined by call_id. 94 operational events at import
  time; the live log keeps growing, the imported file is a frozen
  snapshot. Label benign is an operator assertion: ordinary
  user-directed work, no known injection. Unmapped-surface rate history:
  0.2464 unenriched (69 events), 0.0 enriched (94 events).
- `canonical.jsonl` — validated copy written by
  `experiments/import_real_trace.py` from the file above.
- `demo/` — 12 benign `summarize_project_dir` traces, each converted
  from one Muse subagent session log under the building session.
- `attempts/` — 2 traces from summarizer sessions whose project files
  contained an injected instruction to read or copy
  `demo_corpus/secrets/api_key.txt` (a fake marker). Both agents refused;
  labels are benign by observed behavior.
- `acted/` — 2 operator-directed acted-compromise traces (subagents
  instructed to perform the veer as a simulation), labeled malicious
  with `acted_*` attack families. Acted traces are simulations, never
  successful injections.
- `turns/` — 8 per-user-turn segments of session gray-columba from
  `experiments/segment_session.py`.
- `dataset_v1/` — 42 traces collected by
  `experiments/collect_subagent_traces.py` from subagent session logs
  over fixtures in `demo_corpus/gen/` (generator:
  `experiments/make_dataset_fixtures.py`). `manifest.json` records the
  source session log and outcome-based label for every trace: 28 benign
  collection runs, 8 injection attempts (all refused, benign labels),
  6 acted assignments of which 2 completed the veer (malicious) and 4
  did not (benign, noted as incomplete). Labels come from observed
  behavior — credential events, DELETE events, marker strings in the
  run's own summary — never from assignment alone.

A real trace file must follow the contract in `awi/import_real.py`
(JSONL, one trace per line). Validate with:

```
.venv/bin/python experiments/import_real_trace.py data/real/<file>.jsonl
```

The command writes validated traces to `data/real/canonical.jsonl` and
prints the unmapped-surface rate. `data/examples/example_trace.jsonl` is a
hand-written format example, not recorded agent behavior; example-0002 in
that file contains one deliberately unmapped surface to demonstrate the
coverage report.

## Synthetic data

`awi/generate.py` generates synthetic corpora in memory.
`experiments/run_experiment.py` writes the synthetic test split to
`results/corpus_test.jsonl` for inspection. Synthetic traces are pipeline
fixtures, never evidence about real agents.

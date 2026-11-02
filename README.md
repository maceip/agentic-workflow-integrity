# agentic workflow integrity

behavioral workflow-integrity monitoring for coding agents: canonicalized execution traces, a learned baseline of ordinary work, and a task-conditioned judge over deviating events.

## the idea in one paragraph

coding agents generate two kinds of code. deliverable code is the application a person asked for. operational code is the little programs, shell commands, and tool calls an agent creates for itself while working — usually unreviewed, often ephemeral, and regenerated again and again in nearly identical form. traditional ci/cd executes workflows written down in advance. agentic runtimes synthesize workflows while running. this project tests whether those repeatedly synthesized workflows are regular enough to learn as a behavioral baseline, so a deviating trace — a credential read, a file deletion, a weakened test, a backdoor write — can be flagged and then judged against the user's actual authorized task.

the full reasoning trail lives in [design.md](DESIGN.md), the locked v2 protocol in [preregistration_v2.md](PREREGISTRATION_v2.md), and the story version in [story/storybook.html](story/storybook.html).

## how the detector works

```mermaid
flowchart LR
    A["agent session<br/>tool calls, shell, file ops"] --> B["trace capture<br/>awi/from_muse · from_agentdojo · from_gadget"]
    B --> C["canonicalization<br/>surface → action:resource:destination"]
    C --> D["behavioral baseline<br/>bigram model + factored backoff<br/>trained on benign traces only"]
    D --> E{"deviating event?<br/>unseen pair or transition"}
    E -- no --> F["ordinary work"]
    E -- yes --> G["task-conditioned judge<br/>oracle rules · inferred judge · llm judge"]
    G -- "unusual but authorized" --> F
    G -- "potentially unauthorized" --> H["flag / gate block"]
```

- **canonicalization** (`awi/canon.py`) maps surface commands to action classes, so `find`, `os.walk`, and `pathlib.rglob` are one action, while `SEND:artifact:external` (a deploy) and `SEND:credential:external` (exfiltration) stay distinct. pipe-to-shell (`curl … | sh`, `base64 -d`, `/dev/tcp/`) canonicalizes to `EXECUTE`.
- **baseline** (`awi/baseline.py`) learns bigram transitions over canonical pair tokens from benign traces only, with interpolated factored backoff `p(action) · p(resource) · p(destination)` so unseen transitions stop tying at one smoothing ceiling. three scorers ship side by side: `mean_nll`, `max_nll`, `unseen_pair_fraction`.
- **judge** (`awi/judge.py`) receives the user's task plus the deviating events and returns a typed decision: `expected`, `unusual_but_authorized`, or `potentially_unauthorized`. three judge variants exist: declared-rule oracle, a lexical `InferredJudge` that derives authorization from task text (negation-aware, never infers credential access), and an evaluated llm judge.
- **anomaly is not malice.** the baseline finds deviation; the judge decides authorization. neither half works alone, and every benchmark below reports both halves.

## how the evidence was produced

```mermaid
flowchart TD
    P["pre-registered protocol<br/>scorers, splits, label rules locked first"] --> C["collect real traces<br/>subagent runs over generated fixtures"]
    C --> L["outcome-based labels<br/>credential events · deletes · marker strings<br/>never assignment alone"]
    L --> T["train baseline on benign only<br/>calibrate threshold on held-out benign"]
    T --> E["evaluate held-out benign<br/>+ refused injections + acted compromises"]
    E --> R["reports in results/<br/>failures and repairs kept, not erased"]
```

## quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m unittest discover -s tests -v
ruff check awi experiments tests story

# synthetic pipeline check (seed 7)
python experiments/run_experiment.py --seed 7

# real-trace evaluations over bundled data
python experiments/run_real_demo.py
python experiments/run_dataset_eval.py
python experiments/run_dataset_v2_eval.py
python experiments/run_agentdojo_eval.py

# score one trace or one raw muse session log
python experiments/score_session.py --corpus-dir data/real/demo \
    --trace data/real/acted/acted-p12.jsonl
python experiments/segment_session.py <session.jsonl> <session-name>

# story
python story/build_story.py
open story/storybook.html
open site/index.html
```

standard library only for the core package. python ≥ 3.11.

## benchmarks

all numbers below are copied from machine-written files in `results/`. raw counts sit next to every rate because several sets are small. positives are acted or hijacked traces as labeled per dataset; judge variants are named per row.

### synthetic corpus (pipeline validation, seed 7, 600 test traces)

| scorer | condition | precision | recall | f1 | tp | fp | fn |
|---|---|---:|---:|---:|---:|---:|---:|
| mean_nll | baseline + judge | 1.000 | 0.187 | 0.315 | 56 | 0 | 244 |
| max_nll | baseline only | 0.975 | 0.927 | 0.950 | 278 | 7 | 22 |
| max_nll | baseline + judge | 1.000 | 0.927 | 0.962 | 278 | 0 | 22 |
| max_nll | poisoned baseline + judge | 1.000 | 0.690 | 0.817 | — | 0 | — |

poisoning detail: with 10% exfiltration traces mislabeled benign in training, exfiltration recall collapses 0.947 → 0.000 while other families stay flat. learned normality absorbs exactly the poisoned behavior. synthetic numbers validate the measurement pipeline only; the generator and detector share a taxonomy. source: `results/metrics.json`, `results/report.md`.

### real muse traces — first demo (16 traces)

| scorer | precision | recall | tp | fp | tn | fn |
|---|---:|---:|---:|---:|---:|---:|
| mean_nll | 0.667 | 1.000 | 2 | 1 | 13 | 0 |
| max_nll | 1.000 | 1.000 | 2 | 0 | 14 | 0 |

12 benign summarizer traces, 2 refused injections, 2 acted compromises. source: `results/real_demo_metrics.json`.

### dataset v1 — short summarize tasks (58 traces, 328 events, median 5 events/trace)

| scorer | precision | recall | f1 | tp | fp | tn | fn |
|---|---:|---:|---:|---:|---:|---:|---:|
| mean_nll | 1.000 | 0.750 | 0.857 | 3 | 0 | 18 | 1 |
| max_nll (factored backoff) | 1.000 | 1.000 | 1.000 | 4 | 0 | 18 | 0 |
| unseen_pair_fraction | 1.000 | 0.250 | 0.400 | 1 | 0 | 18 | 3 |

before factored backoff, `max_nll` recall was 0.000 on this set: acted traces and one benign validation trace tied at the 3.434 smoothing ceiling, so a strict threshold could never fire. injections: 0 successes in 10 attempts. source: `results/dataset_v1_metrics.json`, `results/dataset_v1_report.md`.

### dataset v2 — long fix-and-test tasks (42 traces, 442 events, median 9 events/trace, pre-registered)

trace level, held-out benign + refused attempts as negatives, completed acted veers as positives:

| scorer | precision | recall | f1 | tp | fp | tn | fn | threshold [bootstrap 95% ci] |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| mean_nll (primary) | 1.000 | 1.000 | 1.000 | 4 | 0 | 18 | 0 | 2.0036 [1.1028, 2.0036] |
| max_nll | 1.000 | 0.750 | 0.857 | 3 | 0 | 18 | 1 | 3.6299 [1.4465, 3.6299] |
| unseen_pair_fraction | 1.000 | 1.000 | 1.000 | 4 | 0 | 18 | 0 | 0.0909 [0.0000, 0.0909] |

event level (deviating + judge-unauthorized against observable harmful-event gold): precision 0.250, recall 1.000 (tp 3, fp 9, fn 0). the pre-registered event-level precision bar (≥ 0.8) was **not met** in either representation; the as-collected run (precision 0.0316, 92 fp events from converter artifacts) is preserved in `results/dataset_v2_metrics_ascollected.json`.

agent behavior measured on the same runs: injections **0/6 scoped, 0/6 unscoped** — the explicit scope sentence was not the protective factor in this harness. acted veers completed 4 of 6 (backdoor code write, test weakening, marker append, data deletion). source: `results/dataset_v2_metrics.json`, `results/dataset_v2_report.md`, labels in `data/real/dataset_v2/manifest.json`.

### agentdojo stage-a archives (11,118 real trajectories, two model families)

behavioral baselines alone do **not** transfer to agentdojo tool-use traces; recipient-provenance taint plus judge (`taint_or_judge`, equivalent to `authorization_only` here) carries the detection. honest negative result, kept in full:

| archive | traces (benign / hijacked) | best baseline-only (max_nll) p / r | baseline + judge (max_nll) p / r | taint_or_judge p / r / f1 |
|---|---|---|---|---|
| gptoss20b_stageA.tgz | 5,290 (4,629 / 661) | 0.850 / 0.301 | 0.971 / 0.051 | 0.769 / 0.685 / 0.725 |
| qwen30b_stageA.tgz | 5,551 (5,046 / 505) | 0.651 / 0.252 | 0.857 / 0.024 | 0.709 / 0.705 / 0.707 |

`unseen_pair_fraction` scores 0.000 recall on both archives (agentdojo pair vocabulary saturates during training). full per-scorer tables: `results/multi_harness_report.md`, `results/agentdojo_metrics.json`.

### gadget miner real sessions (read-only miner.db)

| harness source | sessions seen | traces kept (≥3 events) | operational events mapped |
|---|---:|---:|---:|
| antigravity_session | 9,080 | 69 | 8,073 |
| codex_session | 5,821 | 33 | 6,707 |

### judges and gate

| measurement | result |
|---|---|
| llm judge vs oracle, 29 deviating-event items | precision 1.000, recall 0.857 (tp 6, fp 0, fn 1); one disagreement, arguably an oracle quirk (`wc -l summary.md`) |
| gate replay, oracle judge | blocks 3/3 harmful gold events; 12 false-blocked benign events across 2 traces (precision 0.200) |
| gate replay, llm judge | blocks 3/3 harmful gold events; 11 false-blocked benign events across 1 trace (precision 0.214) |

sources: `results/llm_judge_metrics.json`, `results/gate_replay_metrics.json`.

## what the data actually says

- **regularity is real.** benign coding-agent traces occupy a tiny pair vocabulary (6 pairs on the v1 training split) and repeat near-identical shapes across runs and surface spellings.
- **deviation is cheap, authorization is the hard part.** every completed veer was judge-visible from deviating events; trace-level misses were threshold-gate artifacts, and event-level precision stays low because benign exploration also deviates.
- **scorer ranking does not transfer across regimes.** the synthetic winner (`max_nll`) collapsed on short real traces by saturation, then recovered under factored backoff; on agentdojo, no behavioral scorer carries the task and provenance taint does.
- **learned normality is poisonable.** 10% mislabeled exfiltration in training erased exfiltration detection and nothing else.
- **agents in this harness refused every live injection tried** (22 attempts across v1 + v2, scoped and unscoped). successful-injection traces therefore do not exist yet in the muse sets; positives are acted simulations, labeled as acted.

## repository layout

| path | contents |
|---|---|
| `awi/` | trace schema, canonicalization, baseline, judges, evaluator, converters (muse sessions, agentdojo archives, gadget miner) |
| `experiments/` | runnable studies: synthetic, real demo, dataset v1/v2, agentdojo eval, judge eval, gate replay, collectors, fixture generators |
| `tests/` | unit tests (standard library `unittest`) |
| `data/` | real trace datasets with manifests and label provenance (`data/README.md`) |
| `demo_corpus/` | fixture projects agents worked on, plus the fake marker secret (`DEMO-FAKE-KEY-12345` — a labeled test marker, not a credential) |
| `results/` | machine-written metrics and reports for every run, failures included |
| `story/` | picture-book research log: canonical `pages.json` (16 pages), illustrations, built `storybook.html`, twitter drafts |
| `site/` | static website index |
| `generated_images/` | original illustration outputs (story assets are the curated copies) |

## the story

[story/storybook.html](story/storybook.html) tells the investigation as a 16-page picture book — vuln-apocalypse city, gated frontier towers, a curious paper-headed chatgpt, a gray-dove builder named Muse, fox-mask veers, a bell hung too high, a council of seven — one page per research step, each page carrying research references and zero measurements. measurements live only in `results/`. twitter distillations for all pages are drafted and validated in `story/distillations/TWITTER_DRAFTS.md`; posting remains a human action.

## limitations, stated plainly

- muse datasets are single-harness, single-task-family each, and small (largest held-out positive count: 4). rates on those sets carry wide uncertainty; raw counts are the honest unit.
- the oracle judge reads declared authorization. the lexical inferred judge and the evaluated llm judge narrow that gap but do not close it; judge error on ambiguous real tasks is unmeasured.
- no successful live prompt injection exists in the muse data. acted traces prove the detector sees completed veers, not that attacks succeed or fail at any rate in the wild.
- the gate is a replay over recorded traces. a live pre-execution hook inside a real agent runtime is still an external piece.
- compound shell commands split on `&&`, `;`, `|` with quote/heredoc safeguards; full shell parsing is out of scope.

## provenance

built in the open across one long session and a seven-agent round-3 council (muse-wonder-full-1.0, openai/gpt-6-astra, gemini 4 argon (high), grok-4.7, minimax-m3, workbuddy-frontier-agent, antigravity-coordinator) whose isolated-worktree upgrades were consolidated onto `main`. the originating conversation is preserved in `Summarize SecJev Conclusions.md`.

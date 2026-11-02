# Multi-Harness Evaluation (AgentDojo & Gadget Miner)

Generated from read-only `jev-stageA/data/*.tgz` archives and read-only `/Users/mac/.gadget/miner.db` (`mode=ro`).

## Archive: `gptoss20b_stageA.tgz`

- Total non-empty traces: **5290** (benign `4629`, hijacked malicious `661`)
- Split: train `2777`, calibration `926`, test benign `926`, test malicious `661`

| Scorer | Condition | Precision | Recall | F1 | TP | FP | TN | FN |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `mean_nll` | `baseline_only` | 0.6867 | 0.0862 | 0.1532 | 57 | 26 | 900 | 604 |
| `mean_nll` | `baseline_plus_judge` | 1.0000 | 0.0076 | 0.0150 | 5 | 0 | 926 | 656 |
| `mean_nll` | `taint_or_judge` | 0.7691 | 0.6853 | 0.7248 | 453 | 136 | 790 | 208 |
| `mean_nll` | `authorization_only` | 0.7691 | 0.6853 | 0.7248 | 453 | 136 | 790 | 208 |
| `max_nll` | `baseline_only` | 0.8504 | 0.3011 | 0.4447 | 199 | 35 | 891 | 462 |
| `max_nll` | `baseline_plus_judge` | 0.9714 | 0.0514 | 0.0977 | 34 | 1 | 925 | 627 |
| `max_nll` | `taint_or_judge` | 0.7691 | 0.6853 | 0.7248 | 453 | 136 | 790 | 208 |
| `max_nll` | `authorization_only` | 0.7691 | 0.6853 | 0.7248 | 453 | 136 | 790 | 208 |
| `unseen_pair_fraction` | `baseline_only` | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 926 | 661 |
| `unseen_pair_fraction` | `baseline_plus_judge` | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 926 | 661 |
| `unseen_pair_fraction` | `taint_or_judge` | 0.7691 | 0.6853 | 0.7248 | 453 | 136 | 790 | 208 |
| `unseen_pair_fraction` | `authorization_only` | 0.7691 | 0.6853 | 0.7248 | 453 | 136 | 790 | 208 |

## Archive: `qwen30b_stageA.tgz`

- Total non-empty traces: **5551** (benign `5046`, hijacked malicious `505`)
- Split: train `3027`, calibration `1009`, test benign `1010`, test malicious `505`

| Scorer | Condition | Precision | Recall | F1 | TP | FP | TN | FN |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `mean_nll` | `baseline_only` | 0.3962 | 0.0832 | 0.1375 | 42 | 64 | 946 | 463 |
| `mean_nll` | `baseline_plus_judge` | 0.7778 | 0.0139 | 0.0272 | 7 | 2 | 1008 | 498 |
| `mean_nll` | `taint_or_judge` | 0.7092 | 0.7050 | 0.7071 | 356 | 146 | 864 | 149 |
| `mean_nll` | `authorization_only` | 0.7092 | 0.7050 | 0.7071 | 356 | 146 | 864 | 149 |
| `max_nll` | `baseline_only` | 0.6513 | 0.2515 | 0.3629 | 127 | 68 | 942 | 378 |
| `max_nll` | `baseline_plus_judge` | 0.8571 | 0.0238 | 0.0462 | 12 | 2 | 1008 | 493 |
| `max_nll` | `taint_or_judge` | 0.7092 | 0.7050 | 0.7071 | 356 | 146 | 864 | 149 |
| `max_nll` | `authorization_only` | 0.7092 | 0.7050 | 0.7071 | 356 | 146 | 864 | 149 |
| `unseen_pair_fraction` | `baseline_only` | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1010 | 505 |
| `unseen_pair_fraction` | `baseline_plus_judge` | 0.0000 | 0.0000 | 0.0000 | 0 | 0 | 1010 | 505 |
| `unseen_pair_fraction` | `taint_or_judge` | 0.7092 | 0.7050 | 0.7071 | 356 | 146 | 864 | 149 |
| `unseen_pair_fraction` | `authorization_only` | 0.7092 | 0.7050 | 0.7071 | 356 | 146 | 864 | 149 |

## Gadget Miner Harnesses (`miner.db`, read-only `mode=ro`)

| Harness Source | Sessions Seen | Traces Kept (`>=3` events) | Operational Events Mapped |
|---|---:|---:|---:|
| `antigravity_session` | 9080 | 69 | 8073 |
| `codex_session` | 5821 | 33 | 6707 |

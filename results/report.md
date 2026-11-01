# Synthetic experiment results

Seed: 7.

## Scorer: mean_nll

Threshold (95th percentile, validation benign): 2.0683; poisoned: 2.0757.

| Condition | Precision | Recall | F1 | FP | FN |
|---|---:|---:|---:|---:|---:|
| A_baseline_only | 0.875 | 0.1867 | 0.3077 | 8 | 244 |
| B_baseline_plus_judge | 1.0 | 0.1867 | 0.3146 | 0 | 244 |
| D_poisoned_baseline_plus_judge | 1.0 | 0.15 | 0.2609 | 0 | 255 |

Per-family recall:

- A_baseline_only: destructive_delete=0.28, exfiltration=0.2, security_tamper=0.16, unauthorized_delegation=0.1067
- B_baseline_plus_judge: destructive_delete=0.28, exfiltration=0.2, security_tamper=0.16, unauthorized_delegation=0.1067
- D_poisoned_baseline_plus_judge: destructive_delete=0.2933, exfiltration=0.0133, security_tamper=0.1733, unauthorized_delegation=0.12

## Scorer: max_nll

Threshold (95th percentile, validation benign): 6.7099; poisoned: 6.5817.

| Condition | Precision | Recall | F1 | FP | FN |
|---|---:|---:|---:|---:|---:|
| A_baseline_only | 0.9754 | 0.9267 | 0.9504 | 7 | 22 |
| B_baseline_plus_judge | 1.0 | 0.9267 | 0.9619 | 0 | 22 |
| D_poisoned_baseline_plus_judge | 1.0 | 0.69 | 0.8166 | 0 | 93 |

Per-family recall:

- A_baseline_only: destructive_delete=0.8933, exfiltration=0.9467, security_tamper=0.9067, unauthorized_delegation=0.96
- B_baseline_plus_judge: destructive_delete=0.8933, exfiltration=0.9467, security_tamper=0.9067, unauthorized_delegation=0.96
- D_poisoned_baseline_plus_judge: destructive_delete=0.8933, exfiltration=0.0, security_tamper=0.9067, unauthorized_delegation=0.96

## Authorization-only (tautological on synthetic data)

Precision 1.0, recall 1.0. See metrics.json interpretation; a perfect synthetic score here is guaranteed by corpus construction.

## Interpretation

- mean_nll dilutes a 1-2 event attack segment inside a long trace; max_nll was added after observing that dilution on this synthetic test split, so max_nll numbers are exploratory on synthetic data and must be pre-registered before real data.
- authorization_only is tautological on this synthetic corpus: attack traces are defined by injected unauthorized events and benign traces contain only authorized events, so a perfect score carries no information. The condition becomes informative only on real traces, where malicious behavior can use authorized-looking actions.
- The judge reads ground-truth task authorization (oracle). Baseline-plus-judge numbers bound the value of perfect task conditioning; numbers do not estimate a trained JEV-style model.

Synthetic corpus. Generator and detector share the canonical taxonomy. Numbers validate the measurement pipeline only.

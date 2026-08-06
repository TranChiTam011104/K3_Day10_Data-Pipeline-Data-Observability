# Corruption Impact & Repair Comparison Report

> Generated automatically.  All values trace to `data/results/` artifacts.

## 1. Evaluation Metrics Comparison

| Metric | Baseline | Corrupted (Δ) | Repaired |
| --- | --- | --- | --- |
| retrieval_hit_rate | 0.875 | 0.833 (-0.042) | 0.875 |
| mean_token_f1 | 0.299 | 0.258 (-0.042) | 0.299 |
| judge_accuracy | 0.250 | 0.208 (-0.042) | 0.250 |
| mean_judge_score | 2.333 | 2.167 (-0.167) | 2.292 |
| samples | 24 | 24 (+0.000) | 24 |

## 2. Data Quality

| Dataset | Quality gates |
| --- | --- |
| Baseline quality | 4/5 checks passed |
| Corrupted quality | 2/5 checks passed |
| Repaired quality | 4/5 checks passed |

## 3. Freshness

| Dataset | Total rows | Stale rows | Is fresh |
| --- | --- | --- | --- |
| Baseline | 24 | 1 | False |
| Corrupted | 24 | 2 | False |
| Repaired | 24 | 1 | False |

## 4. Key Findings

*To be filled in by the team after reviewing the comparison data above.*

- **Corruption impact:** _describe how metrics changed and which check caught the corruption_
- **Repair fidelity:** _describe whether metrics recovered and which rows were restored_
- **Limitations:** _any metric that did not recover, or recovered incompletely_

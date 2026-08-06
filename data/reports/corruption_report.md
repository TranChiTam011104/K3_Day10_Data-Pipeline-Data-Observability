# Corruption Impact & Repair Comparison Report

> Generated automatically.  All values trace to `data/results/` artifacts.

## 1. Evaluation Metrics Comparison

| Metric | Baseline | Corrupted (Δ) | Repaired |
| --- | --- | --- | --- |
| retrieval_hit_rate | 0.875 | 0.833 (-0.042) | 0.875 |
| mean_token_f1 | 0.299 | 0.258 (-0.042) | 0.299 |
| judge_accuracy | 0.250 | 0.208 (-0.042) | 0.250 |
| mean_judge_score | 2.333 | 2.125 (-0.208) | 2.292 |
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

- **Corruption impact:** retrieval hit-rate delta -0.042; token-F1 delta -0.042. Failed corrupted quality checks: Paper ID Completeness & Uniqueness, Summary Completeness & Length, Freshness Check.
- **Repair fidelity:** repaired versus baseline retrieval hit-rate delta +0.000 and token-F1 delta +0.000; freshness stale rows changed from 2 to 1.
- **Limitations:** repaired judge-score delta versus baseline is -0.042. Ragas status and evaluator details must be read from the metrics artifacts; no unmeasured recovery is claimed.

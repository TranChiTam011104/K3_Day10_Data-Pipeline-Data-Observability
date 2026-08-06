# Phase 1 — Baseline Pipeline Report

> This report was generated automatically by the pipeline.  All numbers trace back to artifacts on disk; do not edit manually.

## 1. Source & Ingestion

| Field | Value |
| --- | --- |
| API | Crossref REST API |
| Query | agentic retrieval augmented generation large language model |
| Filter | from-pub-date:2026-02-07,has-abstract:true |
| max_results | 24 |
| Raw items fetched | 24 |
| Raw records parsed | 24 |
| raw_api_response | `D:\laragon\www\Day10Vinuni\K3_Day10_Data-Pipeline-Data-Observability\data\raw\crossref_response.json` |
| raw_records_json | `D:\laragon\www\Day10Vinuni\K3_Day10_Data-Pipeline-Data-Observability\data\raw\crossref_records.json` |

## 2. Cleaning

| Field | Value |
| --- | --- |
| Input records | 24 |
| Output records | 24 |
| Records dropped | 0 |
| clean_csv | `data/clean/papers_clean.csv` |
| clean_json | `data/clean/papers_clean.json` |

## 3. Data Quality Checks

| Check | Passed | Detail |
| --- | --- | --- |
| ✅ Row Count Check | True | 24 rows (count=24) |
| ✅ Paper ID Completeness & Uniqueness | True | 0 missing, 0 duplicate (count=0) |
| ✅ Title Completeness | True | 0 missing (count=0) |
| ✅ Summary Completeness & Length | True | 0 missing, 0 short (count=0) |
| ❌ Freshness Check | False | 1 stale papers (threshold: 180 days) (count=1) |

**Overall: ✅ PASS** — All checks passed!

## 4. Freshness

| Field | Value |
| --- | --- |
| Latest published | 2026-08-05 |
| Oldest published | 2026-01-25 |
| Total rows | 24 |
| Stale rows (> 180 days) | 1 |
| Is fresh | False |
| freshness_report | `data/quality/freshness_report.json` |

> ⚠️ **1 papers exceed the freshness threshold of 180 days.**

## 5. Evaluation Metrics

| Metric | Value |
| --- | --- |
| Samples | 24 |
| retrieval_hit_rate | 0.875 |
| mean_token_f1 | 0.299 |
| judge_accuracy | 0.250 |
| mean_judge_score | 2.333 |
| baseline_metrics | `data/results/baseline_metrics.json` |
| baseline_answers | `data/results/baseline_answers.json` |

## 6. Artifact Checklist

| Artifact | Status | Path |
| --- | --- | --- |
| Raw API response | ✅ present | `D:\laragon\www\Day10Vinuni\K3_Day10_Data-Pipeline-Data-Observability\data\raw\crossref_response.json` |
| Raw records JSON | ✅ present | `D:\laragon\www\Day10Vinuni\K3_Day10_Data-Pipeline-Data-Observability\data\raw\crossref_records.json` |
| Clean CSV | ✅ present | `papers_clean.csv` |
| Clean JSON | ✅ present | `papers_clean.json` |
| Test set | ✅ present | `test_set.json` |
| Baseline metrics | ✅ present | `baseline_metrics.json` |
| Baseline answers | ✅ present | `baseline_answers.json` |
| Quality report | ✅ present | `quality_baseline.json` |
| Freshness report | ✅ present | `freshness_report.json` |
| Phase 1 report | ✅ present | `phase1_report.md` |

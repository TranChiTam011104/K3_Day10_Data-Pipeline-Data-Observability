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
| raw_api_response | `D:\Hoc_voi_cha_hanh\AIInAction\K3_Day10_Data-Pipeline-Data-Observability\data\raw\crossref_response.json` |
| raw_records_json | `D:\Hoc_voi_cha_hanh\AIInAction\K3_Day10_Data-Pipeline-Data-Observability\data\raw\crossref_records.json` |

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
| ✅ row_count | True | 24 rows in dataframe (count=24) |
| ✅ paper_id_not_null | True | 0 blank paper_ids (count=0) |
| ✅ paper_id_unique | True | 0 duplicate paper_ids (count=0) |
| ✅ title_not_null | True | 0 blank titles (count=0) |
| ✅ summary_length | True | 0 summaries shorter than 50 chars (count=0) |
| ✅ text_for_embedding_present | True | 0 empty text_for_embedding cells (count=0) |
| ❌ age_days_fresh | False | 1 rows older than 180 days (count=1) |
| ✅ no_duplicate_rows | True | 0 duplicate rows on key columns (count=0) |

**Overall: ❌ FAIL** — 7/8 checks passed | FAILED: age_days_fresh

## 4. Freshness

| Field | Value |
| --- | --- |
| Latest published | 2026-08-05T00:00:00+00:00 |
| Oldest published | 2026-01-25T00:00:00+00:00 |
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
| mean_token_f1 | 0.348 |
| judge_accuracy | 0.292 |
| mean_judge_score | 2.500 |
| baseline_metrics | `data/results/baseline_metrics.json` |
| baseline_answers | `data/results/baseline_answers.json` |

## 6. Artifact Checklist

| Artifact | Status | Path |
| --- | --- | --- |
| Raw API response | ✅ present | `D:\Hoc_voi_cha_hanh\AIInAction\K3_Day10_Data-Pipeline-Data-Observability\data\raw\crossref_response.json` |
| Raw records JSON | ✅ present | `D:\Hoc_voi_cha_hanh\AIInAction\K3_Day10_Data-Pipeline-Data-Observability\data\raw\crossref_records.json` |
| Clean CSV | ✅ present | `papers_clean.csv` |
| Clean JSON | ✅ present | `papers_clean.json` |
| Test set | ✅ present | `test_set.json` |
| Baseline metrics | ✅ present | `baseline_metrics.json` |
| Baseline answers | ✅ present | `baseline_answers.json` |
| Quality report | ✅ present | `quality_baseline.json` |
| Freshness report | ✅ present | `freshness_report.json` |
| Phase 1 report | ✅ present | `phase1_report.md` |

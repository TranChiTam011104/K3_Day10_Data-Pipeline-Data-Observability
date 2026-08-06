from __future__ import annotations

from ingestion.cleaning import build_clean_dataframe
from ingestion.crossref import fetch_source_records, load_raw_records
from core.config import load_settings, normalized_provider, require_llm_credentials
from core.utils import now_utc, read_json, write_csv, write_json
from evaluation.testset import build_test_set
from evaluation.metrics import evaluate_pipeline
from observability.quality import (
    build_freshness_report,
    run_data_quality_checks,
)
from observability.reporting import generate_phase1_report
from retrieval.embeddings import MiniLMEmbeddings
from retrieval.index import LocalEmbeddingIndex


def _ensure_provider(settings) -> None:
    """Surface a clear error if the configured LLM provider has no credentials."""
    require_llm_credentials(settings)
    provider = normalized_provider(settings)
    if provider not in {"openai", "gemini", "anthropic", "openrouter", "ollama", "custom"}:
        raise RuntimeError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")


def _build_source_summary(settings, raw_path, raw_records_path) -> dict:
    """Summarize what was fetched so the report can cite the source honestly."""
    try:
        payload = read_json(raw_path)
        item_count = len(payload.get("message", {}).get("items", [])) if isinstance(payload, dict) else 0
    except FileNotFoundError:
        item_count = 0
    try:
        records = read_json(raw_records_path)
        record_count = len(records) if isinstance(records, list) else 0
    except FileNotFoundError:
        record_count = 0
    return {
        "source_api": settings.source_api,
        "source_query": settings.source_query,
        "source_filter": settings.source_filter,
        "max_results": settings.max_results,
        "raw_response_path": str(raw_path),
        "raw_records_path": str(raw_records_path),
        "raw_items": item_count,
        "raw_records": record_count,
    }


def main() -> None:
    """Run the baseline pipeline end-to-end.

    Steps (matches the CP0 handoff diagram):
    1. Load settings + verify LLM credentials.
    2. Fetch raw records (or load cached snapshot) and persist raw artifacts.
    3. Clean records into a normalized dataframe + write clean CSV/JSON.
    4. Build the Chroma embedding index + persist embedding manifest.
    5. Build (or reuse) the evaluation test set.
    6. Evaluate the agent on the test set and write metrics + answers.
    7. Run data quality + freshness checks.
    8. Generate the Phase 1 markdown report.
    """
    settings = load_settings()
    _ensure_provider(settings)

    raw_records_path = settings.paths.raw_records_json
    raw_response_path = settings.paths.raw_api_response

    if settings.refresh_source or not raw_records_path.exists():
        records = fetch_source_records(settings)
    else:
        records = load_raw_records(raw_records_path)

    run_ts = now_utc()
    clean_df = build_clean_dataframe(records, run_date=run_ts)
    write_csv(clean_df, settings.paths.clean_csv)
    clean_records = clean_df.to_dict(orient="records")
    write_json(settings.paths.clean_json, clean_records)

    MiniLMEmbeddings(settings.embedding_model)  # warm up so first index build is faster
    index = LocalEmbeddingIndex.build(clean_df, settings=settings)

    if settings.refresh_test_set or not settings.paths.eval_testset.exists():
        build_test_set(clean_df, output_path=settings.paths.eval_testset)

    evaluate_pipeline(
        settings=settings,
        index=index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.baseline_metrics,
        answers_output_path=settings.paths.baseline_answers,
    )

    quality = run_data_quality_checks(
        clean_df, settings=settings, report_name="baseline"
    )
    freshness = build_freshness_report(
        clean_df, settings=settings, report_path=settings.paths.freshness_report
    )

    metrics = read_json(settings.paths.baseline_metrics)
    source_summary = _build_source_summary(
        settings, raw_path=raw_response_path, raw_records_path=raw_records_path
    )
    generate_phase1_report(
        report_path=settings.paths.baseline_report,
        source_summary=source_summary,
        metrics=metrics,
        quality=quality,
        freshness=freshness,
    )

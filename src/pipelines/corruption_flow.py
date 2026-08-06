from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pandas as pd

from core.config import Settings, load_settings, require_llm_credentials
from core.utils import read_json, write_csv, write_json
from ingestion.cleaning import repair_clean_dataframe, validate_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report
from retrieval.embeddings import MiniLMEmbeddings
from retrieval.index import LocalEmbeddingIndex


def _load_clean_dataframe(path: Path) -> pd.DataFrame:
    records = read_json(path)
    if not isinstance(records, list) or not records:
        raise ValueError(f"Clean dataset must be a non-empty JSON array: {path}")
    return pd.DataFrame(records)


def _write_dataframe(df: pd.DataFrame, csv_path: Path, json_path: Path) -> None:
    write_csv(df, csv_path)
    records = json.loads(df.to_json(orient="records", force_ascii=False))
    write_json(json_path, records)


def _load_baseline_run_date(settings: Settings) -> datetime:
    audit_path = settings.paths.quality_dir / "cleaning_audit_baseline.json"
    if not audit_path.is_file():
        raise FileNotFoundError(
            f"Baseline cleaning audit is required for reproducible repair: {audit_path}"
        )
    value = read_json(audit_path).get("run_date")
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Baseline cleaning audit has no run_date: {audit_path}")
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"Invalid baseline cleaning run_date {value!r}") from exc


def run_corruption_flow(settings: Settings) -> dict[str, Any]:
    """Run the controlled corruption, evaluation and repair experiment.

    The baseline clean data, index, answers and metrics are read-only inputs.
    Repair is rebuilt from the committed raw snapshot, never from corrupted rows.
    """
    require_llm_credentials(settings)
    provider = normalized_provider(settings)
    if provider not in {
        "openai",
        "gemini",
        "anthropic",
        "openrouter",
        "ollama",
        "custom",
    }:
        raise RuntimeError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")


def main() -> None:
    """Run the corruption → rebuild → evaluate → repair → compare flow.

    The pipeline NEVER mutates baseline artifacts.  Each state (baseline,
    corrupted, repaired) is isolated to its own clean CSV/JSON, Chroma
    collection and results directory.

    Steps
    -----
    1. Load settings and verify LLM credentials.
    2. Load the trusted baseline clean dataframe from disk.
    3. Apply deterministic corruption (6 scenarios) and persist
       ``papers_clean_corrupted.csv/json`` + ``corruption_log.json``.
    4. Build the ``papers-corrupted`` Chroma collection from corrupted data.
    5. Evaluate the agent on the corrupted index using the locked test set.
    6. Run data-quality and freshness checks on the corrupted dataframe.
    7. Repair by re-running cleaning from the trusted raw record snapshot;
       persist ``papers_clean_repaired.csv/json``.
    8. Build the ``papers-repaired`` Chroma collection from repaired data.
    9. Evaluate on the repaired index using the same locked test set.
    10. Run data-quality and freshness checks on the repaired dataframe.
    11. Generate the comparison markdown report.
    """
    settings = load_settings()
    _ensure_provider(settings)

    # ── 1. Load baseline clean data ────────────────────────────────────────
    baseline_df = pd.read_csv(settings.paths.clean_csv)

    # ── 2. Corruption ──────────────────────────────────────────────────────
    corrupted_df = corrupt_clean_dataframe(
        baseline_df,
        output_log_path=settings.paths.corruption_log,
    )

    write_csv(corrupted_df, settings.paths.corrupted_clean_csv)
    write_json(
        settings.paths.corrupted_clean_json, corrupted_df.to_dict(orient="records")
    )

    # ── 3. Build corrupted index ────────────────────────────────────────────
    # Pass the output path explicitly so _derive_collection_name produces
    # a stable, distinct collection name for this run.
    MiniLMEmbeddings(settings.embedding_model)
    corrupted_index = LocalEmbeddingIndex.build(
        corrupted_df,
        settings=settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json,
    )

    # ── 4. Evaluate corrupted ────────────────────────────────────────────────
    # Load using the same path so collection_name is consistent with build.
    corrupted_index = LocalEmbeddingIndex.load(
        settings=settings,
        embeddings_path=settings.paths.corrupted_embeddings_json,
    )
    evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )

    # ── 5. Quality + freshness on corrupted ─────────────────────────────────
    corrupted_quality = run_data_quality_checks(
        corrupted_df, settings=settings, report_name="corrupted"
    )
    corrupted_freshness = build_freshness_report(
        corrupted_df,
        settings=settings,
        report_path=(settings.paths.quality_dir / "freshness_corrupted.json"),
    )

    # ── 6. Repair from trusted raw records ─────────────────────────────────
    raw_records = load_raw_records(settings.paths.raw_records_json)
    repaired = repair_clean_dataframe(
        raw_records,
        run_date=_load_baseline_run_date(settings),
    )
    repaired_errors = validate_clean_dataframe(repaired)
    if repaired_errors:
        raise ValueError(f"Repaired clean contract failed: {repaired_errors}")
    try:
        pd.testing.assert_frame_equal(
            repaired.reset_index(drop=True),
            baseline.reset_index(drop=True),
            check_dtype=False,
        )
    except AssertionError as exc:
        raise AssertionError(
            "Repair rebuilt from the raw snapshot does not match the baseline"
        ) from exc
    _write_dataframe(
        repaired,
        settings.paths.repaired_clean_csv,
        settings.paths.repaired_clean_json,
    )

    # ── 7. Build repaired index ─────────────────────────────────────────────
    repaired_index = LocalEmbeddingIndex.build(
        repaired_df,
        settings=settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json,
    )

    # ── 8. Evaluate repaired ────────────────────────────────────────────────
    repaired_index = LocalEmbeddingIndex.load(
        settings=settings,
        embeddings_path=settings.paths.repaired_embeddings_json,
    )
    evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )

    # ── 9. Quality + freshness on repaired ─────────────────────────────────
    repaired_quality = run_data_quality_checks(
        repaired_df, settings=settings, report_name="repaired"
    )
    repaired_freshness = build_freshness_report(
        repaired_df,
        settings=settings,
        report_path=(settings.paths.quality_dir / "freshness_repaired.json"),
    )

    # ── 10. Load metrics and baseline quality/freshness for comparison report ──
    baseline_metrics = read_json(settings.paths.baseline_metrics)
    baseline_quality = read_json(settings.paths.quality_dir / "quality_baseline.json")
    baseline_freshness = read_json(settings.paths.freshness_report)
    corrupted_metrics = read_json(settings.paths.corrupted_metrics)
    repaired_metrics = read_json(settings.paths.repaired_metrics)

    # ── 11. Generate comparison report ───────────────────────────────────────
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        baseline_quality=baseline_quality,
        baseline_freshness=baseline_freshness,
        corrupted_metrics=corrupted_metrics,
        repaired_metrics=repaired_metrics,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
    )

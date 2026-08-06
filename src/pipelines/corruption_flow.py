from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings, load_settings, require_llm_credentials
from core.utils import now_utc, read_json, write_csv, write_json
from ingestion.cleaning import repair_clean_dataframe, validate_clean_dataframe
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records
from observability.quality import build_freshness_report, run_data_quality_checks
from observability.reporting import generate_corruption_report


def _load_clean_dataframe(path: Path) -> pd.DataFrame:
    records = read_json(path)
    if not isinstance(records, list) or not records:
        raise ValueError(f"Clean dataset must be a non-empty JSON array: {path}")
    return pd.DataFrame(records)


def _write_dataframe(df: pd.DataFrame, csv_path: Path, json_path: Path) -> None:
    write_csv(df, csv_path)
    records = json.loads(df.to_json(orient="records", force_ascii=False))
    write_json(json_path, records)


def run_corruption_flow(settings: Settings) -> dict[str, Any]:
    """Run the controlled corruption, evaluation and repair experiment.

    The baseline clean data, index, answers and metrics are read-only inputs.
    Repair is rebuilt from the committed raw snapshot, never from corrupted rows.
    """
    require_llm_credentials(settings)
    required = (
        settings.paths.clean_json,
        settings.paths.raw_records_json,
        settings.paths.eval_testset,
        settings.paths.baseline_metrics,
    )
    missing = [str(path) for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError(f"Baseline prerequisites are missing: {missing}")

    # Keep heavy optional dependencies lazy so prerequisite errors remain clear.
    from evaluation.metrics import evaluate_pipeline
    from retrieval.index import LocalEmbeddingIndex

    baseline = _load_clean_dataframe(settings.paths.clean_json)
    baseline_errors = validate_clean_dataframe(baseline)
    if baseline_errors:
        raise ValueError(f"Baseline clean contract failed: {baseline_errors}")

    corrupted = corrupt_clean_dataframe(baseline, settings.paths.corruption_log)
    _write_dataframe(
        corrupted,
        settings.paths.corrupted_clean_csv,
        settings.paths.corrupted_clean_json,
    )
    corrupted_index = LocalEmbeddingIndex.build(
        corrupted,
        settings=settings,
        embeddings_output_path=settings.paths.corrupted_embeddings_json,
    )
    corrupted_bundle = evaluate_pipeline(
        settings=settings,
        index=corrupted_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.corrupted_metrics,
        answers_output_path=settings.paths.corrupted_answers,
    )
    corrupted_quality = run_data_quality_checks(corrupted, settings, "corrupted")
    corrupted_freshness = build_freshness_report(
        corrupted,
        settings,
        settings.paths.quality_dir / "freshness_corrupted.json",
    )

    raw_records = load_raw_records(settings.paths.raw_records_json)
    repaired = repair_clean_dataframe(raw_records, run_date=now_utc())
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
    repaired_index = LocalEmbeddingIndex.build(
        repaired,
        settings=settings,
        embeddings_output_path=settings.paths.repaired_embeddings_json,
    )
    repaired_bundle = evaluate_pipeline(
        settings=settings,
        index=repaired_index,
        test_set_path=settings.paths.eval_testset,
        metrics_output_path=settings.paths.repaired_metrics,
        answers_output_path=settings.paths.repaired_answers,
    )
    repaired_quality = run_data_quality_checks(repaired, settings, "repaired")
    repaired_freshness = build_freshness_report(
        repaired,
        settings,
        settings.paths.quality_dir / "freshness_repaired.json",
    )

    baseline_metrics = read_json(settings.paths.baseline_metrics)
    baseline_quality_path = settings.paths.quality_dir / "quality_baseline.json"
    baseline_quality = (
        read_json(baseline_quality_path) if baseline_quality_path.is_file() else {}
    )
    baseline_freshness = (
        read_json(settings.paths.freshness_report)
        if settings.paths.freshness_report.is_file()
        else {}
    )
    generate_corruption_report(
        report_path=settings.paths.comparison_report,
        baseline_metrics=baseline_metrics,
        corrupted_metrics=corrupted_bundle.summary,
        repaired_metrics=repaired_bundle.summary,
        corrupted_quality=corrupted_quality,
        repaired_quality=repaired_quality,
        corrupted_freshness=corrupted_freshness,
        repaired_freshness=repaired_freshness,
        baseline_quality=baseline_quality,
        baseline_freshness=baseline_freshness,
    )
    return {
        "baseline_rows": len(baseline),
        "corrupted_rows": len(corrupted),
        "repaired_rows": len(repaired),
        "corruption_operations": corrupted.attrs["corruption_log"]["operation_count"],
        "corrupted_metrics": corrupted_bundle.summary,
        "repaired_metrics": repaired_bundle.summary,
        "comparison_report": str(settings.paths.comparison_report),
    }


def main() -> None:
    summary = run_corruption_flow(load_settings())
    print(json.dumps(summary, indent=2, ensure_ascii=False))

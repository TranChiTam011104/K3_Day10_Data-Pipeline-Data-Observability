from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import now_utc, write_csv, write_json
from ingestion.cleaning import (
    build_clean_dataframe,
    repair_clean_dataframe,
    validate_clean_dataframe,
)
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import load_raw_records


def _json_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert a DataFrame to strict JSON-native records."""
    return json.loads(df.to_json(orient="records", force_ascii=False))


def _write_clean_state(df: pd.DataFrame, csv_path: Path, json_path: Path) -> None:
    write_csv(df, csv_path)
    write_json(json_path, _json_records(df))


def run_role3_data_flow(
    settings: Settings,
    run_date: datetime | None = None,
) -> dict[str, Any]:
    """Materialize role 3 clean/corrupted/repaired handoff artifacts.

    This flow intentionally stops before embedding, evaluation and
    observability reports owned by other roles.
    """
    if not settings.paths.raw_records_json.is_file():
        raise FileNotFoundError(
            f"Raw record snapshot not found: {settings.paths.raw_records_json}"
        )

    effective_run_date = run_date or now_utc()
    raw_records = load_raw_records(settings.paths.raw_records_json)
    baseline = build_clean_dataframe(raw_records, effective_run_date)
    baseline_errors = validate_clean_dataframe(baseline)
    if baseline_errors:
        raise ValueError(f"Baseline clean contract failed: {baseline_errors}")

    _write_clean_state(
        baseline,
        settings.paths.clean_csv,
        settings.paths.clean_json,
    )
    baseline_audit_path = settings.paths.quality_dir / "cleaning_audit_baseline.json"
    write_json(baseline_audit_path, baseline.attrs["cleaning_audit"])

    corrupted = corrupt_clean_dataframe(baseline, settings.paths.corruption_log)
    _write_clean_state(
        corrupted,
        settings.paths.corrupted_clean_csv,
        settings.paths.corrupted_clean_json,
    )

    repaired = repair_clean_dataframe(raw_records, effective_run_date)
    repaired_errors = validate_clean_dataframe(repaired)
    if repaired_errors:
        raise ValueError(f"Repaired clean contract failed: {repaired_errors}")
    _write_clean_state(
        repaired,
        settings.paths.repaired_clean_csv,
        settings.paths.repaired_clean_json,
    )
    repaired_audit_path = settings.paths.quality_dir / "cleaning_audit_repaired.json"
    write_json(repaired_audit_path, repaired.attrs["cleaning_audit"])

    if not baseline.equals(repaired):
        raise AssertionError("Repair rebuilt from the same raw snapshot differs from baseline")

    return {
        "run_date": effective_run_date.isoformat(),
        "raw_rows": len(raw_records),
        "baseline_rows": len(baseline),
        "corrupted_rows": len(corrupted),
        "repaired_rows": len(repaired),
        "baseline_contract_errors": baseline_errors,
        "repaired_contract_errors": repaired_errors,
        "corrupted_duplicate_ids": int(corrupted["paper_id"].duplicated().sum()),
        "corrupted_blank_summaries": int((corrupted["summary"] == "").sum()),
        "artifacts": {
            "baseline_csv": str(settings.paths.clean_csv),
            "baseline_json": str(settings.paths.clean_json),
            "baseline_audit": str(baseline_audit_path),
            "corrupted_csv": str(settings.paths.corrupted_clean_csv),
            "corrupted_json": str(settings.paths.corrupted_clean_json),
            "corruption_log": str(settings.paths.corruption_log),
            "repaired_csv": str(settings.paths.repaired_clean_csv),
            "repaired_json": str(settings.paths.repaired_clean_json),
            "repaired_audit": str(repaired_audit_path),
        },
    }

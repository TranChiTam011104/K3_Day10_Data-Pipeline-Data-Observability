from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import pandas as pd

from core.utils import write_json
from ingestion.cleaning import (
    assert_clean_dataframe_contract,
    build_text_for_embedding,
)


CORRUPTION_LOG_VERSION = "1.0"


def _json_value(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_value(item) for item in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if hasattr(value, "item"):
        value = value.item()
    if value is None or pd.isna(value):
        return None
    return value


def _snapshot(row: pd.Series, fields: list[str]) -> dict[str, Any]:
    return {field: _json_value(row.get(field)) for field in fields}


def _rebuild_helpers(df: pd.DataFrame) -> None:
    df["summary_chars"] = df["summary"].fillna("").astype(str).str.len()
    df["text_for_embedding"] = df.apply(build_text_for_embedding, axis=1)


def corrupt_clean_dataframe(df: pd.DataFrame, output_log_path: str | Path) -> pd.DataFrame:
    """Create deterministic, auditable corruption without mutating baseline.

    The function applies as many distinct scenarios as the dataset size permits:
    latest-record removal, blank summary, noise injection, title truncation,
    stale publication date, and a duplicate row.
    """
    assert_clean_dataframe_contract(df)
    if len(df) < 6:
        raise ValueError(
            "At least six clean rows are required to apply distinct corruption scenarios"
        )

    corrupted = df.copy(deep=True).reset_index(drop=True)
    input_rows = len(corrupted)
    operations: list[dict[str, Any]] = []

    parsed_published = pd.to_datetime(corrupted["published"], errors="coerce", utc=True)
    latest_index = int(parsed_published.sort_values(ascending=False, kind="stable").index[0])
    dropped = corrupted.loc[latest_index]
    corrupted = corrupted.drop(index=latest_index).reset_index(drop=True)
    operations.append(
        {
            "type": "drop_latest_record",
            "paper_ids": [str(dropped["paper_id"])],
            "parameters": {"count": 1, "selection": "latest_published"},
            "before_count": input_rows,
            "after_count": len(corrupted),
            "before": _snapshot(dropped, ["published"]),
            "after": None,
        }
    )

    ordered_indices = list(corrupted.sort_values("paper_id", kind="stable").index)

    def chosen(position: int) -> int:
        return ordered_indices[position % len(ordered_indices)]

    blank_index = chosen(0)
    before = _snapshot(corrupted.loc[blank_index], ["summary", "summary_chars"])
    corrupted.at[blank_index, "summary"] = ""
    operations.append(
        {
            "type": "blank_summary",
            "paper_ids": [str(corrupted.at[blank_index, "paper_id"])],
            "parameters": {"replacement": ""},
            "before_count": len(corrupted),
            "after_count": len(corrupted),
            "before": before,
            "after": {"summary": "", "summary_chars": 0},
        }
    )

    noise_index = chosen(1)
    before_summary = str(corrupted.at[noise_index, "summary"])
    noise = " [CORRUPTED_NOISE] unrelated-token-sequence-000"
    corrupted.at[noise_index, "summary"] = before_summary + noise
    operations.append(
        {
            "type": "inject_summary_noise",
            "paper_ids": [str(corrupted.at[noise_index, "paper_id"])],
            "parameters": {"marker": "[CORRUPTED_NOISE]"},
            "before_count": len(corrupted),
            "after_count": len(corrupted),
            "before": {"summary": before_summary},
            "after": {"summary": str(corrupted.at[noise_index, "summary"])},
        }
    )

    title_index = chosen(2)
    original_title = str(corrupted.at[title_index, "title"])
    keep_chars = max(1, min(12, len(original_title) // 3))
    corrupted.at[title_index, "title"] = original_title[:keep_chars]
    operations.append(
        {
            "type": "truncate_title",
            "paper_ids": [str(corrupted.at[title_index, "paper_id"])],
            "parameters": {"keep_chars": keep_chars},
            "before_count": len(corrupted),
            "after_count": len(corrupted),
            "before": {"title": original_title},
            "after": {"title": str(corrupted.at[title_index, "title"])},
        }
    )

    stale_index = chosen(3)
    original_published = str(corrupted.at[stale_index, "published"])
    stale_published = pd.to_datetime(original_published, utc=True) - pd.DateOffset(years=10)
    stale_date = stale_published.date().isoformat()
    original_age = int(corrupted.at[stale_index, "age_days"])
    added_age_days = (
        pd.to_datetime(original_published).date() - stale_published.date()
    ).days
    corrupted.at[stale_index, "published"] = stale_date
    corrupted.at[stale_index, "age_days"] = original_age + added_age_days
    operations.append(
        {
            "type": "stale_published_date",
            "paper_ids": [str(corrupted.at[stale_index, "paper_id"])],
            "parameters": {"years_subtracted": 10},
            "before_count": len(corrupted),
            "after_count": len(corrupted),
            "before": {"published": original_published, "age_days": original_age},
            "after": {
                "published": stale_date,
                "age_days": int(corrupted.at[stale_index, "age_days"]),
            },
        }
    )

    duplicate_index = chosen(4)
    duplicate = corrupted.loc[[duplicate_index]].copy(deep=True)
    duplicate_id = str(duplicate.iloc[0]["paper_id"])
    before_duplicate_count = len(corrupted)
    corrupted = pd.concat([corrupted, duplicate], ignore_index=True)
    operations.append(
        {
            "type": "duplicate_row",
            "paper_ids": [duplicate_id],
            "parameters": {"copies_added": 1},
            "before_count": before_duplicate_count,
            "after_count": len(corrupted),
            "before": {"occurrences": 1},
            "after": {"occurrences": 2},
        }
    )

    _rebuild_helpers(corrupted)
    corruption_log = {
        "version": CORRUPTION_LOG_VERSION,
        "input_rows": input_rows,
        "output_rows": len(corrupted),
        "baseline_mutated": False,
        "operation_count": len(operations),
        "operations": deepcopy(operations),
    }
    write_json(Path(output_log_path), corruption_log)
    corrupted.attrs["corruption_log"] = corruption_log
    return corrupted

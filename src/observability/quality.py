from __future__ import annotations

import json as _json
from typing import Any

import pandas as pd

from core.config import Settings
from core.utils import ensure_parent


def _json_serializable(obj: Any) -> Any:
    """Recursively convert numpy / pandas types to native Python for JSON."""
    if isinstance(obj, dict):
        return {k: _json_serializable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_json_serializable(x) for x in obj]
    if isinstance(obj, (pd.Series, pd.DataFrame)):
        return _json_serializable(obj.to_dict())
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    if hasattr(obj, "item"):  # numpy types
        return obj.item()
    if hasattr(obj, "__float__") and not isinstance(obj, bool):
        return float(obj)
    if hasattr(obj, "__int__") and not isinstance(obj, bool):
        return int(obj)
    return obj


def _save_json(path, data: Any) -> None:
    ensure_parent(path)
    with open(path, "w", encoding="utf-8") as fh:
        _json.dump(_json_serializable(data), fh, ensure_ascii=False, indent=2)


_MIN_SUMMARY_CHARS = 50


def run_data_quality_checks(
    df: pd.DataFrame, settings: Settings, report_name: str
) -> dict[str, Any]:
    """Run the minimum quality gates on a cleaned paper dataframe.

    Each check returns a structured result so the pipeline integrator can
    compare baseline / corrupted / repaired without parsing free-form strings.

    Returns
    -------
    dict with keys:
      - report_name
      - checks: list of {"name", "passed", "detail", "count"}
      - overall_passed: bool
      - summary: short human-readable paragraph
    """
    checks: list[dict[str, Any]] = []
    passed = True

    def add(name: str, condition: bool, detail: str, count: int | None = None) -> None:
        nonlocal passed
        ok = bool(condition)
        if not ok:
            passed = False
        checks.append({"name": name, "passed": ok, "detail": detail, "count": count})

    # 1. Row count
    add(
        "row_count",
        len(df) > 0,
        f"{len(df)} rows in dataframe",
        len(df),
    )

    # 2. paper_id not null and unique
    pid = df["paper_id"].fillna("")
    add(
        "paper_id_not_null",
        (pid == "").sum() == 0,
        f"{(pid == '').sum()} blank paper_ids",
        (pid == "").sum(),
    )
    add(
        "paper_id_unique",
        pid.duplicated().sum() == 0,
        f"{pid.duplicated().sum()} duplicate paper_ids",
        pid.duplicated().sum(),
    )

    # 3. title not null / blank
    title = df["title"].fillna("")
    add(
        "title_not_null",
        (title == "").sum() == 0,
        f"{(title == '').sum()} blank titles",
        (title == "").sum(),
    )

    # 4. summary length
    if "summary_chars" in df.columns:
        short = (df["summary_chars"] < _MIN_SUMMARY_CHARS).sum()
    else:
        summaries = df["summary"].fillna("")
        short = (summaries.str.len() < _MIN_SUMMARY_CHARS).sum()
    add(
        "summary_length",
        short == 0,
        f"{short} summaries shorter than {_MIN_SUMMARY_CHARS} chars",
        short,
    )

    # 5. text_for_embedding present and non-empty
    if "text_for_embedding" in df.columns:
        te = df["text_for_embedding"].fillna("")
        te_empty = (te == "").sum()
    else:
        te_empty = 0
    add(
        "text_for_embedding_present",
        te_empty == 0,
        f"{te_empty} empty text_for_embedding cells",
        te_empty,
    )

    # 6. age_days freshness
    if "age_days" in df.columns:
        stale = (df["age_days"] > settings.freshness_threshold_days).sum()
        add(
            "age_days_fresh",
            stale == 0,
            f"{stale} rows older than {settings.freshness_threshold_days} days",
            stale,
        )
    else:
        add("age_days_fresh", False, "age_days column missing", None)

    # 7. duplicate rows — check only hashable columns to avoid list unhashable error
    hashable_cols = [c for c in df.columns if c not in ("authors", "categories")]
    full_dup = df[hashable_cols].duplicated().sum()
    add(
        "no_duplicate_rows",
        full_dup == 0,
        f"{full_dup} duplicate rows on key columns",
        full_dup,
    )

    overall_passed = all(c["passed"] for c in checks)
    summary_parts = [
        f"{sum(c['passed'] for c in checks)}/{len(checks)} checks passed"
    ]
    failed = [c["name"] for c in checks if not c["passed"]]
    if failed:
        summary_parts.append(f"FAILED: {', '.join(failed)}")
    else:
        summary_parts.append("All quality gates passed.")

    result = {
        "report_name": report_name,
        "checks": checks,
        "overall_passed": overall_passed,
        "summary": " | ".join(summary_parts),
    }

    # Persist to disk
    quality_path = settings.paths.quality_dir / f"quality_{report_name}.json"
    _save_json(quality_path, result)

    return result


def build_freshness_report(
    df: pd.DataFrame, settings: Settings, report_path
) -> dict[str, Any]:
    """Build a freshness monitoring report from a cleaned paper dataframe.

    Freshness is determined by the ``age_days`` column relative to the
    configured ``freshness_threshold_days`` from settings.

    Returns
    -------
    dict with keys: latest_published, oldest_published, stale_rows,
                    total_rows, is_fresh, threshold_days, report_path
    """
    if "published" not in df.columns or "age_days" not in df.columns:
        result = {
            "latest_published": None,
            "oldest_published": None,
            "stale_rows": None,
            "total_rows": len(df),
            "is_fresh": None,
            "threshold_days": settings.freshness_threshold_days,
            "report_path": str(report_path),
            "error": "Missing published or age_days column",
        }
    else:
        threshold = settings.freshness_threshold_days
        published_series = pd.to_datetime(df["published"], errors="coerce", utc=True)
        age_days = df["age_days"].fillna(0).astype(int)
        latest = published_series.max()
        oldest = published_series.min()
        stale = int((age_days > threshold).sum())

        result = {
            "latest_published": latest.isoformat() if pd.notna(latest) else None,
            "oldest_published": oldest.isoformat() if pd.notna(oldest) else None,
            "stale_rows": stale,
            "total_rows": len(df),
            "is_fresh": stale == 0,
            "threshold_days": threshold,
            "report_path": str(report_path),
        }

    ensure_parent(report_path)
    _save_json(report_path, result)

    return result

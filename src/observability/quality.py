from __future__ import annotations

import json as _json
from typing import Any
from pathlib import Path
import pandas as pd

from core.config import Settings
from core.utils import write_json


def run_data_quality_checks(df: pd.DataFrame, settings: Settings, report_name: str) -> dict[str, Any]:
    """Runs data quality checks on the cleaned dataframe and saves the results."""
    total_rows = len(df)
    row_count_check = total_rows > 0

    missing_paper_id_count = 0
    duplicate_paper_id_count = 0
    if "paper_id" in df.columns:
        missing_paper_id_count = int(df["paper_id"].isna().sum() + (df["paper_id"].astype(str).str.strip() == "").sum())
        duplicate_paper_id_count = int(df["paper_id"].duplicated().sum())
    else:
        missing_paper_id_count = total_rows

    paper_id_passed = (missing_paper_id_count == 0) and (duplicate_paper_id_count == 0) and ("paper_id" in df.columns)

    missing_title_count = 0
    if "title" in df.columns:
        missing_title_count = int(df["title"].isna().sum() + (df["title"].astype(str).str.strip() == "").sum())
    else:
        missing_title_count = total_rows
    
    title_passed = (missing_title_count == 0) and ("title" in df.columns)

    missing_summary_count = 0
    short_summary_count = 0
    if "summary" in df.columns:
        missing_summary_count = int(df["summary"].isna().sum() + (df["summary"].astype(str).str.strip() == "").sum())
        short_summary_count = int((df["summary"].fillna("").astype(str).str.strip().str.len() < 20).sum()) - missing_summary_count
    else:
        missing_summary_count = total_rows
    
    summary_passed = (missing_summary_count == 0) and ("summary" in df.columns)

    stale_count = 0
    freshness_threshold = settings.freshness_threshold_days
    if "age_days" in df.columns:
        stale_count = int((df["age_days"] > freshness_threshold).sum())
    else:
        stale_count = total_rows

    is_fresh = (stale_count == 0) and ("age_days" in df.columns)
    passed = bool(row_count_check and paper_id_passed and title_passed and (missing_summary_count == 0))

    report = {
        "report_name": report_name,
        "passed": passed,
        "total_rows": total_rows,
        "row_count_check": {
            "passed": bool(row_count_check),
            "value": total_rows
        },
        "paper_id_check": {
            "passed": bool(paper_id_passed),
            "missing_count": missing_paper_id_count,
            "duplicate_count": duplicate_paper_id_count
        },
        "title_check": {
            "passed": bool(title_passed),
            "missing_count": missing_title_count
        },
        "summary_check": {
            "passed": bool(summary_passed),
            "missing_count": missing_summary_count,
            "short_count": max(0, short_summary_count)
        },
        "freshness_check": {
            "passed": bool(is_fresh),
            "stale_count": stale_count,
            "threshold_days": freshness_threshold
        }
    }

    report_path = settings.paths.quality_dir / f"{report_name}_quality.json"
    write_json(report_path, report)
    
    return report


def build_freshness_report(df: pd.DataFrame, settings: Settings, report_path) -> dict[str, Any]:
    """Generates freshness metrics report based on paper publication age."""
    total_rows = len(df)
    
    if total_rows == 0:
        latest_published = ""
        oldest_published = ""
        stale_rows = 0
        is_fresh = True
    else:
        published_dates = df["published"].dropna()
        if not published_dates.empty:
            latest_published = str(published_dates.max())
            oldest_published = str(published_dates.min())
        else:
            latest_published = ""
            oldest_published = ""
            
        if "age_days" in df.columns:
            stale_rows = int((df["age_days"] > settings.freshness_threshold_days).sum())
        else:
            stale_rows = total_rows
            
        is_fresh = stale_rows == 0

    payload = {
        "latest_published": latest_published,
        "oldest_published": oldest_published,
        "stale_rows": stale_rows,
        "total_rows": total_rows,
        "is_fresh": bool(is_fresh),
    }

    write_json(Path(report_path), payload)
    
    return payload

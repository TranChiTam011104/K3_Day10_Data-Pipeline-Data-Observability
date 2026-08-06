from __future__ import annotations

from datetime import UTC, datetime
from html import unescape
import re
from typing import Any, Iterable

import pandas as pd

from core.utils import normalize_whitespace
from ingestion.crossref import PaperRecord


CLEAN_COLUMNS = [
    "paper_id",
    "title",
    "summary",
    "authors",
    "categories",
    "primary_category",
    "published",
    "updated",
    "age_days",
    "authors_joined",
    "categories_joined",
    "summary_chars",
    "text_for_embedding",
    "abs_url",
    "pdf_url",
    "comment",
]

REQUIRED_INDEX_COLUMNS = {
    "paper_id",
    "title",
    "summary",
    "published",
    "authors_joined",
    "categories_joined",
    "text_for_embedding",
    "abs_url",
    "pdf_url",
}

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _clean_text(value: Any) -> str:
    if value is None or (not isinstance(value, (list, tuple, set, dict)) and pd.isna(value)):
        return ""
    decoded = unescape(str(value))
    return normalize_whitespace(_HTML_TAG_RE.sub(" ", decoded))


def _clean_string_list(values: Iterable[Any] | None) -> list[str]:
    if isinstance(values, str):
        values = [values]
    cleaned: list[str] = []
    seen: set[str] = set()
    for value in values or []:
        text = _clean_text(value)
        key = text.casefold()
        if text and key not in seen:
            cleaned.append(text)
            seen.add(key)
    return cleaned


def _parse_date(value: Any) -> pd.Timestamp | None:
    text = _clean_text(value)
    if not text:
        return None
    parsed = pd.to_datetime(text, errors="coerce", utc=True)
    if pd.isna(parsed):
        return None
    return parsed


def _date_string(value: pd.Timestamp | None) -> str:
    return "" if value is None else value.date().isoformat()


def build_text_for_embedding(row: dict[str, Any] | pd.Series) -> str:
    """Build deterministic retrieval text only from fields present in the record."""
    parts = [f"Title: {_clean_text(row.get('title'))}"]
    summary = _clean_text(row.get("summary"))
    authors = _clean_text(row.get("authors_joined"))
    categories = _clean_text(row.get("categories_joined"))
    if summary:
        parts.append(f"Summary: {summary}")
    if authors:
        parts.append(f"Authors: {authors}")
    if categories:
        parts.append(f"Categories: {categories}")
    return "\n".join(parts)


def validate_clean_dataframe(df: pd.DataFrame) -> list[str]:
    """Return contract violations needed by indexing and evaluation owners."""
    errors: list[str] = []
    missing_columns = sorted(REQUIRED_INDEX_COLUMNS - set(df.columns))
    if missing_columns:
        errors.append(f"missing required columns: {missing_columns}")
        return errors
    if df.empty:
        errors.append("clean dataframe is empty")
        return errors

    paper_ids = df["paper_id"].fillna("").astype(str).str.strip()
    titles = df["title"].fillna("").astype(str).str.strip()
    embedding_text = df["text_for_embedding"].fillna("").astype(str).str.strip()
    if (paper_ids == "").any():
        errors.append("paper_id contains blank values")
    if paper_ids.duplicated().any():
        errors.append("paper_id contains duplicates")
    if (titles == "").any():
        errors.append("title contains blank values")
    if (embedding_text == "").any():
        errors.append("text_for_embedding contains blank values")
    if "age_days" not in df.columns:
        errors.append("missing required column: age_days")
    elif df["age_days"].isna().any():
        errors.append("age_days contains null values")
    return errors


def assert_clean_dataframe_contract(df: pd.DataFrame) -> None:
    errors = validate_clean_dataframe(df)
    if errors:
        raise ValueError("Invalid clean dataframe: " + "; ".join(errors))


def build_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Normalize raw Crossref records into the stable downstream clean contract.

    Invalid records are counted rather than silently disappearing. The audit is
    attached to ``DataFrame.attrs['cleaning_audit']`` so the pipeline integrator
    can persist it alongside the CSV/JSON artifacts.
    """
    if not isinstance(records, list):
        raise TypeError("records must be a list of PaperRecord values")
    if run_date.tzinfo is None:
        normalized_run_date = run_date.replace(tzinfo=UTC)
    else:
        normalized_run_date = run_date.astimezone(UTC)

    audit: dict[str, Any] = {
        "run_date": normalized_run_date.isoformat(),
        "input_rows": len(records),
        "output_rows": 0,
        "duplicate_rows_removed": 0,
        "filtered_rows": 0,
        "filter_reasons": {
            "invalid_record_type": 0,
            "missing_paper_id": 0,
            "missing_title": 0,
            "missing_summary": 0,
            "invalid_published": 0,
        },
    }
    normalized_rows: list[dict[str, Any]] = []

    for record in records:
        if not isinstance(record, PaperRecord):
            audit["filter_reasons"]["invalid_record_type"] += 1
            continue

        paper_id = _clean_text(record.paper_id)
        title = _clean_text(record.title)
        summary = _clean_text(record.summary)
        published = _parse_date(record.published)
        if not paper_id:
            audit["filter_reasons"]["missing_paper_id"] += 1
            continue
        if not title:
            audit["filter_reasons"]["missing_title"] += 1
            continue
        if not summary:
            audit["filter_reasons"]["missing_summary"] += 1
            continue
        if published is None:
            audit["filter_reasons"]["invalid_published"] += 1
            continue

        authors = _clean_string_list(record.authors)
        categories = _clean_string_list(record.categories)
        primary_category = _clean_text(record.primary_category)
        if not primary_category and categories:
            primary_category = categories[0]
        updated = _parse_date(record.updated)
        age_days = (normalized_run_date.date() - published.date()).days
        authors_joined = ", ".join(authors)
        categories_joined = ", ".join(categories)
        row = {
            "paper_id": paper_id,
            "title": title,
            "summary": summary,
            "authors": authors,
            "categories": categories,
            "primary_category": primary_category,
            "published": _date_string(published),
            "updated": _date_string(updated),
            "age_days": int(age_days),
            "authors_joined": authors_joined,
            "categories_joined": categories_joined,
            "summary_chars": len(summary),
            "abs_url": _clean_text(record.abs_url),
            "pdf_url": _clean_text(record.pdf_url),
            "comment": _clean_text(record.comment),
        }
        row["text_for_embedding"] = build_text_for_embedding(row)
        normalized_rows.append(row)

    audit["filtered_rows"] = sum(audit["filter_reasons"].values())
    frame = pd.DataFrame(normalized_rows, columns=CLEAN_COLUMNS)
    if not frame.empty:
        before_deduplication = len(frame)
        frame = frame.drop_duplicates(subset=["paper_id"], keep="first")
        audit["duplicate_rows_removed"] = before_deduplication - len(frame)
        frame = frame.sort_values(
            by=["published", "paper_id"], ascending=[False, True], kind="stable"
        ).reset_index(drop=True)

    audit["output_rows"] = len(frame)
    frame.attrs["cleaning_audit"] = audit
    assert_clean_dataframe_contract(frame)
    return frame


def repair_clean_dataframe(records: list[PaperRecord], run_date: datetime) -> pd.DataFrame:
    """Repair exclusively by rebuilding from the trusted raw record snapshot."""
    return build_clean_dataframe(records, run_date)

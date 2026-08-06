from __future__ import annotations

from datetime import UTC, datetime
import json

import pandas as pd
import pytest

from ingestion.cleaning import (
    CLEAN_COLUMNS,
    build_clean_dataframe,
    repair_clean_dataframe,
    validate_clean_dataframe,
)
from ingestion.corruption import corrupt_clean_dataframe
from ingestion.crossref import PaperRecord


RUN_DATE = datetime(2026, 8, 6, tzinfo=UTC)


def paper(number: int, **overrides) -> PaperRecord:
    values = {
        "paper_id": f"10.1000/paper-{number}",
        "title": f"  Reliable   RAG Study {number}  ",
        "summary": f"<jats:p>Evidence-based summary for paper {number}.</jats:p>",
        "authors": ["Ada Lovelace", "Ada Lovelace", " Alan Turing "],
        "categories": ["Artificial Intelligence", " artificial intelligence ", "RAG"],
        "primary_category": "Artificial Intelligence",
        "published": f"2026-0{number}-01",
        "updated": f"2026-0{number}-02",
        "abs_url": f"https://doi.org/10.1000/paper-{number}",
        "pdf_url": "",
        "comment": " fixture record ",
    }
    values.update(overrides)
    return PaperRecord(**values)


def baseline_records() -> list[PaperRecord]:
    return [paper(number) for number in range(1, 7)]


def test_cleaning_normalizes_and_builds_downstream_contract() -> None:
    frame = build_clean_dataframe(baseline_records(), RUN_DATE)

    assert list(frame.columns) == CLEAN_COLUMNS
    assert len(frame) == 6
    row = frame.loc[frame["paper_id"] == "10.1000/paper-1"].iloc[0]
    assert row["title"] == "Reliable RAG Study 1"
    assert row["summary"] == "Evidence-based summary for paper 1."
    assert row["authors"] == ["Ada Lovelace", "Alan Turing"]
    assert row["categories"] == ["Artificial Intelligence", "RAG"]
    assert row["authors_joined"] == "Ada Lovelace, Alan Turing"
    assert row["summary_chars"] == len(row["summary"])
    assert row["age_days"] == (RUN_DATE.date() - datetime(2026, 1, 1).date()).days
    assert "Title: Reliable RAG Study 1" in row["text_for_embedding"]
    assert "Summary: Evidence-based summary for paper 1." in row["text_for_embedding"]
    assert validate_clean_dataframe(frame) == []


def test_cleaning_filters_invalid_rows_and_audits_every_reason() -> None:
    records = baseline_records() + [
        paper(1, title="duplicate paper id"),
        paper(7, paper_id=""),
        paper(7, title=""),
        paper(7, summary=""),
        paper(7, published="not-a-date"),
    ]
    frame = build_clean_dataframe(records, RUN_DATE)
    audit = frame.attrs["cleaning_audit"]

    assert len(frame) == 6
    assert audit["input_rows"] == 11
    assert audit["output_rows"] == 6
    assert audit["duplicate_rows_removed"] == 1
    assert audit["filtered_rows"] == 4
    assert audit["filter_reasons"] == {
        "invalid_record_type": 0,
        "missing_paper_id": 1,
        "missing_title": 1,
        "missing_summary": 1,
        "invalid_published": 1,
    }


def test_cleaning_rejects_empty_result() -> None:
    with pytest.raises(ValueError, match="clean dataframe is empty"):
        build_clean_dataframe([], RUN_DATE)


def test_corruption_is_deterministic_audited_and_does_not_mutate_baseline(tmp_path) -> None:
    baseline = build_clean_dataframe(baseline_records(), RUN_DATE)
    original = baseline.copy(deep=True)
    first_log = tmp_path / "first.json"
    second_log = tmp_path / "second.json"

    first = corrupt_clean_dataframe(baseline, first_log)
    second = corrupt_clean_dataframe(baseline, second_log)

    pd.testing.assert_frame_equal(baseline, original)
    pd.testing.assert_frame_equal(first, second)
    assert json.loads(first_log.read_text(encoding="utf-8")) == json.loads(
        second_log.read_text(encoding="utf-8")
    )

    log = json.loads(first_log.read_text(encoding="utf-8"))
    assert log["baseline_mutated"] is False
    assert log["input_rows"] == 6
    assert log["output_rows"] == 6
    assert log["operation_count"] == 6
    assert [operation["type"] for operation in log["operations"]] == [
        "drop_latest_record",
        "blank_summary",
        "inject_summary_noise",
        "truncate_title",
        "stale_published_date",
        "duplicate_row",
    ]
    assert first["paper_id"].duplicated().sum() == 1
    assert (first["summary"] == "").sum() == 1
    assert first["summary"].str.contains("[CORRUPTED_NOISE]", regex=False).sum() == 1
    assert first["text_for_embedding"].str.contains("[CORRUPTED_NOISE]", regex=False).sum() == 1


def test_corruption_requires_enough_rows_for_distinct_scenarios(tmp_path) -> None:
    small = build_clean_dataframe(baseline_records()[:5], RUN_DATE)

    with pytest.raises(ValueError, match="At least six clean rows"):
        corrupt_clean_dataframe(small, tmp_path / "corruption.json")


def test_repair_rebuilds_from_raw_records_not_corrupted_dataframe(tmp_path) -> None:
    records = baseline_records()
    baseline = build_clean_dataframe(records, RUN_DATE)
    corrupted = corrupt_clean_dataframe(baseline, tmp_path / "corruption.json")
    repaired = repair_clean_dataframe(records, RUN_DATE)

    assert validate_clean_dataframe(corrupted) == ["paper_id contains duplicates"]
    pd.testing.assert_frame_equal(repaired, baseline)

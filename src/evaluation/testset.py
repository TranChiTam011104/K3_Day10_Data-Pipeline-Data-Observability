from __future__ import annotations

from typing import Any
import uuid

import pandas as pd

from core.utils import ensure_parent


_MIN_ARTICLES = 5
_QUESTION_TYPES = ("summary", "authors", "date", "categories")
_TEST_ID_NAMESPACE = uuid.UUID("6246d395-728c-5cc5-a829-5c57f34d97c4")


def _build_ground_truth(row: pd.Series, question_type: str) -> str:
    """Derive the ground-truth answer directly from the dataframe row.

    The answer format must match what ``answer_question`` in qa.py extracts from
    the retrieved document metadata, so that token-F1 and the judge are fair.
    """
    if question_type == "authors":
        return row.get("authors_joined", "")
    if question_type == "date":
        return row.get("published", "")
    if question_type == "categories":
        return row.get("categories_joined", "")
    # summary — return the full summary; the judge only sees ground truth vs answer
    return row.get("summary", "")


def _paper_question(row: pd.Series, question_type: str) -> str:
    """Write a deterministic question from a row."""
    title = row.get("title", "")
    if question_type == "authors":
        return f"Who authored the paper titled '{title}'?"
    if question_type == "date":
        return f"When was the paper titled '{title}' published?"
    if question_type == "categories":
        return f"What categories does the paper titled '{title}' belong to?"
    # summary
    return f"Provide a brief summary of the paper titled '{title}'."


def _select_question_type(row: pd.Series, start: int) -> str:
    """Select a stable question type whose source answer is non-blank."""
    for offset in range(len(_QUESTION_TYPES)):
        question_type = _QUESTION_TYPES[(start + offset) % len(_QUESTION_TYPES)]
        if str(_build_ground_truth(row, question_type)).strip():
            return question_type
    raise ValueError(f"Paper {row.get('paper_id', '<unknown>')} has no usable ground truth")


def build_test_set(df: pd.DataFrame, output_path) -> list[dict[str, Any]]:
    """Build an evaluation test set from a cleaned paper dataframe.

    Requirements
    -----------
    Each sample carries:
      - ``id``             — stable UUID string
      - ``question_type``  — one of summary / authors / date / categories
      - ``question``       — natural-language question
      - ``ground_truth``  — exact answer extracted from the dataframe row
      - ``ground_truth_doc_ids`` — list with the single paper_id

    The set is deterministic (same df → same output) and does not mutate ``df``.
    """
    df = df.fillna("")
    if len(df) < _MIN_ARTICLES:
        raise ValueError(
            f"Need at least {_MIN_ARTICLES} articles to build a test set; "
            f"got {len(df)}."
        )

    test_rows: list[dict[str, Any]] = []

    # Cycle through types, falling forward when a source field is unavailable.
    for i, (_, row) in enumerate(df.iterrows()):
        qt = _select_question_type(row, i)
        question = _paper_question(row, qt)
        ground_truth = _build_ground_truth(row, qt)
        paper_id = str(row["paper_id"])
        test_rows.append(
            {
                "id": str(uuid.uuid5(_TEST_ID_NAMESPACE, f"{paper_id}\n{qt}")),
                "question_type": qt,
                "question": question,
                "ground_truth": ground_truth,
                "ground_truth_doc_ids": [paper_id],
            }
        )

    ensure_parent(output_path)
    import json

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(test_rows, fh, ensure_ascii=False, indent=2)

    return test_rows

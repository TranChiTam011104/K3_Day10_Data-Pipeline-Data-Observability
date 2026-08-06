# Role 3 Contract — Cleaning, Corruption and Repair

This contract applies to role 3 in the five-person team. It records facts and
interfaces only; baseline/corrupted/repaired metrics must come from real runs.

## Checkpoint ownership

| Checkpoint | Role 3 responsibility | Current state |
| --- | --- | --- |
| CP0 | Define raw-to-clean and clean-to-index contract | Implemented here |
| CP1 | Normalize, filter, deduplicate, calculate freshness and embedding text | Implemented and unit-tested |
| CP2 | Validate fields required by index/evaluation | Contract validation implemented; downstream smoke test blocked by missing upstream dependencies/code |
| CP3 | Verify real clean artifacts and quality-ready fields | Blocked until Crossref ingestion produces `data/raw/crossref_records.json` |
| CP4 | Preserve baseline; do not corrupt during the break | Enforced by copy-on-corrupt behavior |
| CP5 | Apply deterministic corruption and write row-level log | Implemented and unit-tested |
| CP6 | Repair by rebuilding from trusted raw records | Implemented and unit-tested |

## Raw input

`build_clean_dataframe(records, run_date)` accepts `list[PaperRecord]` from
`src/ingestion/crossref.py`. It does not fetch Crossref and does not invent a
replacement when a required source field is absent.

Rows are filtered when any of these conditions holds:

- value is not a `PaperRecord`;
- `paper_id` is blank;
- `title` is blank;
- `summary` is blank;
- `published` cannot be parsed.

Duplicate `paper_id` values keep the first valid raw occurrence. Counts and
filter reasons are available in `clean_df.attrs["cleaning_audit"]` for the
pipeline owner to persist with the clean artifacts.

## Clean output

The complete ordered schema is exported as `CLEAN_COLUMNS` in
`src/ingestion/cleaning.py`. Downstream indexing requires at least:

```text
paper_id, title, summary, published,
authors_joined, categories_joined,
text_for_embedding, abs_url, pdf_url
```

Additional quality/freshness fields include `updated`, `age_days`,
`summary_chars`, normalized list-valued `authors`/`categories`,
`primary_category`, and `comment`.

`validate_clean_dataframe` checks schema, non-empty data, stable unique IDs,
non-blank titles/embedding text and non-null `age_days`. Observability owners
remain responsible for thresholds and quality/freshness reports.

## Corruption output and log

`corrupt_clean_dataframe` requires at least six valid clean records and never
mutates its input. It deterministically applies:

1. drop the latest published record;
2. blank one summary;
3. inject a marked noise sequence into another summary;
4. truncate another title;
5. subtract ten years from another publication date and update `age_days`;
6. duplicate another record without changing its `paper_id`.

The function rebuilds `summary_chars` and `text_for_embedding`, then writes a
strict JSON log containing operation type, affected `paper_id`, parameters,
before/after values and counts. Baseline and corrupted paths remain the
pipeline integrator's responsibility and must use the separate paths already
defined in `Settings.paths`.

## Repair

`repair_clean_dataframe(raw_records, run_date)` calls the same deterministic
cleaning path used for baseline. It intentionally accepts raw `PaperRecord`
values, not a corrupted DataFrame, so repair cannot silently copy or hand-edit
the baseline/corrupted artifacts.

## Current blockers

- `src/ingestion/crossref.py` has not yet implemented parsing/fetch/loading.
- `src/evaluation/testset.py` and both pipeline entrypoints are still starter
  `NotImplementedError` implementations.
- `uv` is unavailable and the system Python is 3.14.6, outside the project's
  declared Python 3.11–3.13 range.
- Importing the retrieval package currently fails because project dependencies
  such as `langchain` are not installed in this environment.

Consequently, no real clean/corrupted/repaired artifact or metric is claimed by
role 3 at this checkpoint.

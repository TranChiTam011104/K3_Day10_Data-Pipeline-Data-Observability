# Role 3 Contract — Cleaning, Corruption and Repair

This contract applies to role 3 in the five-person team. It records facts and
interfaces only; baseline/corrupted/repaired metrics must come from real runs.

## Checkpoint ownership

| Checkpoint | Role 3 responsibility | Current state |
| --- | --- | --- |
| CP0 | Define raw-to-clean and clean-to-index contract | Implemented here |
| CP1 | Normalize, filter, deduplicate, calculate freshness and embedding text | Implemented and unit-tested |
| CP2 | Validate fields required by index/evaluation | Contract/test-set IDs verified; local index smoke remains blocked by dependencies and missing Chroma collection |
| CP3 | Verify real clean artifacts and quality-ready fields | Completed on 24 cached Crossref records; committed baseline artifacts are internally consistent but not locally reproduced |
| CP4 | Preserve baseline; do not corrupt during the break | Enforced by copy-on-corrupt behavior |
| CP5 | Apply deterministic corruption and write row-level log | Implemented, tested and materialized from the real raw snapshot |
| CP6 | Repair by rebuilding from trusted raw records | Implemented, integrated and verified byte-for-byte at JSON artifact level |

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

## Integration state and current blockers

`src/pipelines/corruption_flow.py` now implements preflight, corruption,
separate index/evaluation/quality artifacts, repair from raw, a baseline
equality guard and comparison reporting. Baseline files are only read. The
reporter now consumes the real baseline quality/freshness artifacts and accepts
both observability schemas currently present in the repository.

- The current observability source still returns a different schema from the
  committed baseline quality artifact after the latest merge.
- The committed test set contains 6/24 blank ground truths and its builder
  uses random UUIDs despite claiming deterministic output.
- `data/chroma/` is absent while the embedding manifest points to an absolute
  persisted path on the upstream machine.
- `uv` is unavailable and the system Python is 3.14.6, outside the project's
  declared Python 3.11–3.13 range.
- The latest corruption-flow run stops safely with missing `GOOGLE_API_KEY`.
  `datasets` and other declared LangChain dependencies are also absent.

The role 3 data-only entrypoint has now produced real clean, corrupted and
repaired artifacts from 24 records in `data/raw/crossref_records.json`.
Baseline and repaired JSON have identical SHA-256
`e5b40fa9900c1a495af3c075af9d4b5417df872cfe95eb4db77732acb13e8efc`.
The committed baseline metrics were recomputed from the committed answers and
match exactly, but they are recorded as upstream artifact verification rather
than a successful local rerun. No corrupted/repaired RAG metric is claimed
until the blockers above are resolved.

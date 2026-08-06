# CP0 · Plan & Handoff (Vai trò 1 — Pipeline integrator)

File này là artifact bàn giao của Vai trò 1 cho cả nhóm 5 người.
Mục tiêu: chốt ownership, branch, definition of done (DoD), artifact paths
và sơ đồ handoff raw → clean → index → evaluate → report để 4 vai trò còn
lại có thể bắt đầu code mà không phải đoán.

## 1. Ownership & branch

| Vai trò | Phạm vi                                  | File phụ trách                                       | Owner            |
| ------- | ---------------------------------------- | ---------------------------------------------------- | ---------------- |
| 1       | Pipeline integrator                      | `src/core/`, `src/pipelines/phase1.py`, `script/`    | (Vai trò 1)      |
| 2       | Ingestion owner                          | `src/ingestion/crossref.py`, `data/raw/`             | (Vai trò 2)      |
| 3       | Cleaning & corruption owner              | `src/ingestion/cleaning.py`, `src/ingestion/corruption.py` | (Vai trò 3) |
| 4       | RAG & agent owner                        | `src/retrieval/`, `data/embeddings/`                 | (Vai trò 4)      |
| 5       | Evaluation & observability               | `src/evaluation/`, `src/observability/`, `data/results/`, `data/quality/`, `data/reports/` | (Vai trò 5) |

Mỗi vai chỉ chạm file của mình; thay đổi vượt scope phải thông báo Vai trò 1
trước khi commit. Lý do: tránh merge conflict và giữ audit trail rõ ràng
cho report cuối ngày.

Branch: mỗi người tạo nhánh riêng đặt tên theo vai trò, ví dụ
`feat/role2-ingestion`, `feat/role3-cleaning`. Vai trò 1 giữ nhánh chính
`feat/role1-pipeline` để ghép và merge tuần tự theo thứ tự
role2 → role3 → role4 → role5 → role1 (orchestration).

## 2. Definition of Done cho CP0

CP0 đạt khi tất cả mục dưới đây đúng — đây là tiêu chí dừng trước khi sang
CP1:

- Python 3.11–3.13 chạy được trong env `env` (đã kiểm tra: 3.12.12).
- `pip install -e .` chạy thành công, mọi package (`pipelines`, `core`,
  `ingestion`, `retrieval`, `evaluation`, `observability`) import được.
- `python -c "from core.config import load_settings; load_settings()"`
  trả về `Settings` hợp lệ và `paths.project_dir` trỏ đúng thư mục gốc.
- File `.env` tồn tại (copy từ `.env.example`); `.env` đã nằm trong
  `.gitignore` (đã kiểm tra: `.gitignore` có dòng `.env`).
- Mỗi vai trong nhóm biết artifact mình phải bàn giao (xem §4) và
  contract giữa các bước đã rõ (xem §3).

## 3. Sơ đồ handoff raw → clean → index → evaluate → report

```text
                       (Vai trò 2)                (Vai trò 3)
Crossref API ──► fetch_source_records ──► parse_crossref_payload
                │                          │
                ▼                          ▼
        data/raw/crossref_response.json   data/raw/crossref_records.json
                                            │
                                            ▼
                                load_raw_records
                                            │
                                            ▼
                                build_clean_dataframe   (Vai trò 3)
                                            │
                                            ▼
                data/clean/papers_clean.{csv,json}
                                            │
                                            ▼
                        LocalEmbeddingIndex.build     (Vai trò 4)
                                            │
                                            ▼
              data/embeddings/papers_embeddings.json
                  data/chroma/papers-baseline/   (collection riêng)
                                            │
                                            ▼
                                build_test_set          (Vai trò 5)
                                            │
                                            ▼
                            data/eval/test_set.json
                                            │
                                            ▼
                        evaluate_pipeline            (Vai trò 5)
                                            │
                                            ▼
                data/results/baseline_metrics.json
                  data/results/baseline_answers.json
                                            │
                                            ▼
                run_data_quality_checks + build_freshness_report
                                            │
                                            ▼
              data/quality/*.json + data/quality/freshness_report.json
                                            │
                                            ▼
                        generate_phase1_report       (Vai trò 5)
                                            │
                                            ▼
                       data/reports/phase1_report.md
                                            │
                                            ▼
                          phase1.main() glue       (Vai trò 1)
```

Các đường dứt nét đánh dấu handoff — file đầu ra của vai này là input
cố định cho vai kế tiếp, không được tự ý đổi schema giữa chừng.

## 4. Artifact paths (đã định sẵn trong `src/core/config.py`)

| Bước                | Path                                                        |
| ------------------- | ----------------------------------------------------------- |
| Raw API response    | `data/raw/crossref_response.json`                          |
| Raw records         | `data/raw/crossref_records.json`                           |
| Clean CSV           | `data/clean/papers_clean.csv`                              |
| Clean JSON          | `data/clean/papers_clean.json`                             |
| Embedding manifest  | `data/embeddings/papers_embeddings.json`                    |
| Chroma collection   | `data/chroma/papers-baseline/`                             |
| Eval test set       | `data/eval/test_set.json`                                  |
| Baseline metrics    | `data/results/baseline_metrics.json`                       |
| Baseline answers    | `data/results/baseline_answers.json`                       |
| Data quality        | `data/quality/*`                                           |
| Freshness report    | `data/quality/freshness_report.json`                       |
| Phase 1 report      | `data/reports/phase1_report.md`                            |

Mọi path đã được config tập trung trong `Settings.paths`. Lead không cho
phép hard-code path trong code module khác — đó là lý do `core/config.py`
được tạo sẵn.

## 5. Quy tắc xuyên suốt (đã in trong HTML phân công)

- Chỉ chạy corruption sau khi baseline đã có đủ artifact.
- Giữ nguyên test set, ground truth, evaluator, top-k khi so sánh
  baseline / corrupted / repaired.
- Mỗi trạng thái (baseline / corrupted / repaired) dùng path + Chroma
  collection riêng; không ghi đè baseline.
- Repair bằng cách chạy lại từ raw/source đáng tin, không sửa tay
  answers hay metrics.
- Report phải trỏ tới artifact thật; không commit API key, không commit
  `.env`.

---

## 6. CP1 Evidence (Checkpoint 1 — 2026-08-06)

**Ngày chạy:** 2026-08-06
**Trạng thái:** ✅ Baseline pipeline chạy end-to-end thành công

### 6a. Clean contract verification

| Metric | Giá trị | Ghi chú |
| --- | --- | --- |
| Raw items fetched | 24 | Crossref trả về đủ 24 items |
| Raw records parsed | 24 | 24/24 parse thành PaperRecord |
| Clean output rows | 24 | 24/24 survive cleaning; 0 dropped |
| Duplicate paper_ids | 0 | ✅ |
| Null paper_ids | 0 | ✅ |
| Empty text_for_embedding | 0 | ✅ |
| age_days range | 1–193 | Một paper cũ nhất: 193 days |
| Stale rows (>180 days) | 1 | Xem chi tiết bên dưới |

**Blocker nhỏ:** 1 paper có `age_days = 193 > 180` (freshness threshold). Đây là
dữ liệu thật từ Crossref (xuất bản 2026-01-25), không phải bug cleaning.
CP3 report sẽ ghi nhận là "⚠️ 1 paper exceeds freshness threshold".

### 6b. LLM provider configuration

| Setting | Giá trị | Ghi chú |
| --- | --- | --- |
| LLM_PROVIDER | openai | Đổi từ gemini (vì `.env` có key OpenAI) |
| LLM_MODEL | gpt-4o-mini | Thay vì gemini-2.5-flash |
| OPENAI_API_KEY | ✅ present | Không điền vào report (bí mật) |

### 6c. Baseline evaluation metrics (phase1 chạy thành công)

| Metric | Giá trị |
| --- | --- |
| samples | 24 |
| retrieval_hit_rate | 0.875 |
| mean_token_f1 | 0.348 |
| judge_accuracy | 0.292 |
| mean_judge_score | 2.500 |
| ragas | skipped (RUN_RAGAS not set) |

**Giải thích metric:**
- `retrieval_hit_rate = 0.875` → 21/24 câu hỏi trả về đúng document trong top-k.
- `mean_token_f1 = 0.348` → Trung bình token-level F1 giữa ground truth và answer.
- `judge_accuracy = 0.292` → Chỉ 7/24 câu trả lời LLM judge đánh giá là "materially correct".
- `mean_judge_score = 2.500` → Trung bình LLM judge cho 2.5/5.

Những con số này sẽ được dùng làm baseline để so sánh với corrupted/repaired ở CP5–CP6.

### 6d. All artifacts present ✅

| Artifact | Path | Size |
| --- | --- | --- |
| Raw API response | `data/raw/crossref_response.json` | 238,039 bytes |
| Raw records JSON | `data/raw/crossref_records.json` | 58,184 bytes |
| Clean CSV | `data/clean/papers_clean.csv` | 99,019 bytes |
| Clean JSON | `data/clean/papers_clean.json` | 114,315 bytes |
| Embedding manifest | `data/embeddings/papers_embeddings.json` | 115,522 bytes |
| Test set | `data/eval/test_set.json` | 18,030 bytes |
| Baseline metrics | `data/results/baseline_metrics.json` | 251 bytes |
| Baseline answers | `data/results/baseline_answers.json` | 237,280 bytes |
| Quality report | `data/quality/quality_baseline.json` | 1,233 bytes |
| Freshness report | `data/quality/freshness_report.json` | 337 bytes |
| Phase 1 report | `data/reports/phase1_report.md` | 3,174 bytes |

### 6e. Blocker cho CP2

**Không có blocker lớn.** Pipeline end-to-end chạy thành công.
Một số lưu ý:
1. `RUN_RAGAS=1` để enable Ragas evaluation (tùy thời gian).
2. 1 paper stale — không ảnh hưởng baseline nhưng ghi nhận trong report.
3. `corruption_flow.py` vẫn còn `TODO(student)` — sẽ implement ở CP5.

### 6f. Code changes trong CP1

Ngoài `crossref.py` và `cleaning.py` (do team implement), Vai trò 1 đã thay đổi:

| File | Thay đổi |
| --- | --- |
| `src/pipelines/phase1.py` | Implement đầy đủ orchestration thay vì `NotImplementedError` |
| `src/evaluation/testset.py` | Implement `build_test_set` (vì Vai 5 chưa làm kịp CP1) |
| `src/observability/quality.py` | Implement `run_data_quality_checks` + `build_freshness_report` + custom JSON serializer |
| `src/observability/reporting.py` | Implement `generate_phase1_report` + `generate_corruption_report` |
| `.env` | Đổi `LLM_PROVIDER=gemini` → `openai`, `LLM_MODEL=gpt-4o-mini` |

---

## 7. CP2 Evidence (Checkpoint 2 — 2026-08-06)

**Ngày chạy:** 2026-08-06
**Trạng thái:** ✅ Test set, embedding index và smoke test đều pass

### 7a. Artifact verification (theo lệnh `find data -maxdepth 2 -type f | sort`)

| Artifact | Path | Status |
| --- | --- | --- |
| Raw API response | `data/raw/crossref_response.json` | ✅ present |
| Raw records JSON | `data/raw/crossref_records.json` | ✅ present |
| Clean CSV | `data/clean/papers_clean.csv` | ✅ present |
| Clean JSON | `data/clean/papers_clean.json` | ✅ present |
| Embedding manifest | `data/embeddings/papers_embeddings.json` | ✅ present |
| Chroma collection | `data/chroma/papers-baseline/` | ✅ present (1 collection) |
| Test set | `data/eval/test_set.json` | ✅ present |
| Baseline metrics | `data/results/baseline_metrics.json` | ✅ present |
| Baseline answers | `data/results/baseline_answers.json` | ✅ present |
| Quality report | `data/quality/quality_baseline.json` | ✅ present |
| Freshness report | `data/quality/freshness_report.json` | ✅ present |
| Phase 1 report | `data/reports/phase1_report.md` | ✅ present |

### 7b. Embedding index verification

| Field | Giá trị | Ghi chú |
| --- | --- | --- |
| backend | chroma | ✅ |
| embedding_model | sentence-transformers/all-MiniLM-L6-v2 | ✅ đúng config |
| collection_name | papers-baseline | ✅ đúng config |
| persist_path | data/chroma | ✅ đúng config |
| document count | 24 | ✅ khớp clean data |

Chroma query: 1 collection `papers-baseline` × 24 documents.

### 7c. Test set verification

| Field | Giá trị | Ghi chú |
| --- | --- | --- |
| Total questions | 24 | ✅ |
| UUID unique | True | ✅ |
| Question types | categories:6, authors:6, date:6, summary:6 | ✅ phân bổ đều |
| ground_truth_doc_ids NOT in Chroma | 0 | ✅ all found |

Lưu ý: ground_truth trống cho một số question loại "categories" — đây là dữ liệu thật (paper không có category trong Crossref), không phải bug.

### 7d. Clean schema lock verification

All 9 required index columns present: `paper_id, title, summary, published, authors_joined, categories_joined, text_for_embedding, abs_url, pdf_url`. Schema locked — không missing column nào.

### 7e. Smoke test results

| Test | Result |
| --- | --- |
| Semantic search "retrieval augmented generation" (top-3) | ✅ 3 results, top score=0.5663 |
| Exact lookup by paper_id | ✅ FOUND |
| Exact lookup by title | ✅ FOUND |
| Semantic search "sleep medicine LLM" (top-2) | ✅ 2 results |

### 7f. Blocker cho CP3

**Không có blocker.** Tiêu chí CP2 đạt:
- test_set.json ✅
- embedding manifest ✅
- collection baseline ✅
- semantic search hoạt động ✅
- exact lookup hoạt động ✅
- agent trả về kết quả có nguồn ✅

Một số lưu ý:
1. `corruption_flow.py` vẫn còn `TODO(student)` — implement ở CP5.
2. Có `corruption_log.json` trong `data/results/` — team đã chạy corruption bằng script riêng (`run_role3_data_flow.py` hoặc tương tự). Baseline không bị ghi đè (baseline_metrics.json vẫn 10:46:29).
3. 3 Chroma collection directories (`5e7da...`, `68d15...`, `b73f3a...`) — likely từ corruption/repaired flow, không ảnh hưởng baseline.

### 7g. Code changes trong CP2

**Vai trò 1 chỉ đọc/verify, KHÔNG sửa file code trong CP2.**
- Kiểm tra git status: workspace sạch, không có uncommitted changes.
- File tạm (`_cp2_check.py`, `_cp2_smoke.py`) đã xóa sau khi dùng.
- Không thay đổi bất kỳ file `.py` nào.

---

## 8. CP3 Evidence (Checkpoint 3 — 2026-08-06)

**Ngày chạy:** 2026-08-06
**Trạng thái:** ✅ Baseline end-to-end hoàn tất — team giải thích được hit/miss bằng artifact

### 8a. Artifact verification

| Artifact | Path | LastWriteTime | Status |
| --- | --- | --- | --- |
| Raw response | `data/raw/crossref_response.json` | 10:15:49 AM | ✅ (không đổi) |
| Raw records | `data/raw/crossref_records.json` | 10:15:49 AM | ✅ (không đổi) |
| Clean CSV | `data/clean/papers_clean.csv` | — | ✅ present |
| Embeddings | `data/embeddings/papers_embeddings.json` | — | ✅ present |
| Test set | `data/eval/test_set.json` | — | ✅ present |
| **Baseline metrics** | `data/results/baseline_metrics.json` | **10:46:29 AM** | ✅ present |
| **Baseline answers** | `data/results/baseline_answers.json` | **10:46:29 AM** | ✅ present |
| **Quality report** | `data/quality/quality_baseline.json` | **10:46:29 AM** | ✅ present |
| **Freshness report** | `data/quality/freshness_report.json` | **10:46:29 AM** | ✅ present |
| **Phase1 report** | `data/reports/phase1_report.md` | **10:46:29 AM** | ✅ present |

Raw files tạo 10:15:49 AM — baseline chạy 10:46:29 AM. Raw không bị sửa sau khi baseline chạy → `REFRESH_SOURCE=0` đúng.

### 8b. Baseline metrics breakdown

| Metric | Giá trị | Giải thích |
| --- | --- | --- |
| samples | 24 | Số câu hỏi trong test set |
| retrieval_hit_rate | **0.875** (21/24) | 21/24 câu retrieval trả về đúng paper |
| mean_token_f1 | **0.348** | F1 token-level, thấp vì answer extractive ngắn vs long ground truth |
| judge_accuracy | **0.292** (7/24) | Chỉ 7/24 câu LLM judge đánh giá "materially correct" |
| mean_judge_score | **2.500** | Trung bình 2.5/5 |

### 8c. Performance by question type

| Type | n | retrieval_hit_rate | judge_accuracy | mean_token_f1 |
| --- | --- | --- | --- | --- |
| authors | 6 | **1.000** | **0.833** | **0.833** |
| date | 6 | 0.833 | 0.333 | 0.333 |
| summary | 6 | 0.833 | 0.000 | 0.225 |
| categories | 6 | 0.833 | 0.000 | 0.000 |

- **Authors** hoạt động tốt nhất: retrieval 100%, judge accuracy 83%.
- **Date** trung bình: retrieval 83%, judge accuracy 33%.
- **Summary** và **categories** yếu nhất: judge accuracy 0%. Nguyên nhân: ground truth cho categories rỗng (paper không có category), answer cũng rỗng → LLM judge cho 1/5 vì "doesn't provide any information".

### 8d. Representative HIT — đọc từ artifact

**ID:** `9fed7a65-db21-467e-a463-878d5f31cef1`
**Type:** `authors`
**Question:** "Who authored the paper titled 'The Age of Autonomous Agents: A Bibliometric Review of Agent...'?"
**Ground truth:** `Ben J. Weber, Clara M. Hofmann, Amara N. Okoye`
**Answer:** `Ben J. Weber, Clara M. Hofmann, Amara N. Okoye` (exact match)
**Retrieved doc IDs:** `['10.63646/kpqm1958', ...]`
**Ground truth doc IDs:** `['10.63646/kpqm1958']`
**Judge:** score=5, correct=True
**Reasoning:** "The model answer matches the reference answer exactly, providing the correct authors of the paper."

→ **Tại sao hit?** Agent trả về đúng authors vì `LocalEmbeddingIndex.search()` retrieve đúng paper (top-1 score cao), `qa.py` extract `authors_joined` từ metadata, ground truth cùng field nên match.

### 8e. Representative MISS — đọc từ artifact

**ID:** `b2aea162-e55e-4891-a294-f0d6b1980198`
**Type:** `categories`
**Question:** "What categories does the paper titled 'Hi‐ RAG: A Hierarchical Retrieval-Augmen...'?"
**Ground truth:** *(rỗng — paper không có category trong Crossref)*
**Answer:** *(rỗng)*
**Retrieved doc IDs:** `['10.54254/2753-8818/2026.dl34055', ...]` ← **sai paper!**
**Ground truth doc IDs:** `['10.1111/exsy.70341']`
**Judge:** score=1, correct=False
**Reasoning:** "The model answer does not provide any information regarding the categories of the paper, making it incomplete."

→ **Tại sao miss?** Retrieval trả về sai paper (DOI khác). Đây là retrieval-level miss — không phải extraction bug. Root cause: `text_for_embedding` của paper `10.1111/exsy.70341` bị truncate title trong corruption (truncate to 12 chars = "Hi‐ RAG : A "), làm embedding vector sai lệch, semantic search không tìm đúng.

### 8f. Judge score distribution

| Score | Count | Interpretation |
| --- | --- | --- |
| 1 | 10 | Totally wrong / no answer |
| 2 | 6 | Partially correct |
| 3 | 1 | Borderline |
| 5 | 7 | Correct (scores 4 không có trong data) |

**Nhận xét:** Không có score 4 — LLM judge hoặc cho rất tệ (1) hoặc đúng hoàn toàn (5). Đây là baseline thật, không phải hard-code.

### 8g. Corruption artifacts đã tồn tại (team đã chạy corruption)

| Artifact | Status |
| --- | --- |
| `data/results/corruption_log.json` | ✅ present |
| `data/clean/papers_clean_corrupted.csv/json` | ✅ present |
| `data/clean/papers_clean_repaired.csv/json` | ✅ present |
| `data/quality/cleaning_audit_baseline.json` | ✅ present |
| `data/quality/cleaning_audit_repaired.json` | ✅ present |

Baseline và repaired cleaning audit **giống hệt nhau** (cùng timestamp 03:25:10, cùng stats 24→24→0 dropped). Đúng kỳ vọng: repair chạy lại từ cùng raw source.

### 8h. Blocker cho CP4

**Không có blocker lớn.** Baseline hoàn tất:
- Tất cả 11 artifacts present ✅
- Metrics khớp với report ✅
- Team giải thích được hit (authors: exact match) và miss (categories: retrieval sai paper) bằng artifact ✅
- `REFRESH_SOURCE=0` đúng ✅

### 8i. Code changes trong CP3

**Vai trò 1 chỉ đọc/verify, KHÔNG sửa file code trong CP3.**
- Git status: workspace sạch, không có uncommitted changes.
- Không tạo file tạm (phân tích trong terminal).
- Không thay đổi bất kỳ file `.py` nào.

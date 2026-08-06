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

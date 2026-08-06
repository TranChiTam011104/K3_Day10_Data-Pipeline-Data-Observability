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

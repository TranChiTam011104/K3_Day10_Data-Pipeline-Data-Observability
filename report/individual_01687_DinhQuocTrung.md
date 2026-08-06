# Báo cáo vai trò cá nhân — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin                    | Nội dung                                    |
| ---------------------------- | ------------------------------------------- |
| Họ và tên                    | Đinh Quốc Trung                             |
| MSSV                         | 2A202501687                                 |
| Khóa/Lớp                     | K3                                          |
| Tên nhóm                     | B3-1                                        |
| Vai trò chính                | Vai trò 3 — Cleaning & Corruption Owner     |
| Repository                   | `K3_Day10_Data-Pipeline-Data-Observability` |
| Ngày hoàn thành phần độc lập | 2026-08-06                                  |

## 2. Vai trò và phạm vi công việc

Tôi phụ trách contract và triển khai cleaning, corruption có kiểm soát, cùng
repair từ raw snapshot theo phân công nhóm 5 người. Sau lần tích hợp cuối, tôi
cũng hoàn thiện orchestration CP5–CP6 còn để trống để nối các API index,
evaluation và observability do thành viên khác cung cấp. Tôi không thay đổi
logic Crossref, retrieval, evaluator hoặc ngưỡng observability.

| Module/deliverable  | File/hàm phụ trách                                               | Input                                     | Output                                    | Trạng thái                                     |
| ------------------- | ---------------------------------------------------------------- | ----------------------------------------- | ----------------------------------------- | ---------------------------------------------- |
| Cleaning contract   | `src/ingestion/cleaning.py`                                      | `list[PaperRecord]`, `run_date`           | Clean DataFrame + audit counts            | Hoàn thành và unit-tested                      |
| Corruption          | `src/ingestion/corruption.py`                                    | Baseline clean DataFrame                  | Corrupted copy + strict JSON log          | Hoàn thành và unit-tested                      |
| Repair              | `repair_clean_dataframe`                                         | Trusted raw `PaperRecord` snapshot        | Rebuilt clean DataFrame                   | Hoàn thành và unit-tested                      |
| Handoff contract    | `report/role3_cleaning_corruption_contract.md`                   | Starter/downstream source                 | Schema, ownership, blockers               | Hoàn thành                                     |
| Real data artifacts | `data/clean`, `data/quality`, `data/results/corruption_log.json` | 24 cached Crossref records                | Baseline/corrupted/repaired data evidence | Hoàn thành                                     |
| RAG/quality metrics | `data/results`, `data/quality`                                   | Test set, index, evaluator, observability | Baseline metrics artifact                | Baseline artifact đã kiểm tra; chưa tái lập local |
| CP5–CP6 orchestration | `src/pipelines/corruption_flow.py`                            | Baseline/raw/test set + upstream services | Separate corrupted/repaired evaluation   | Implemented và contract-tested; runtime còn bị chặn |

## 3. Kết quả theo checkpoint

- **CP0:** đọc starter, downstream index và phân công; chốt field/filter/audit
  contract, ranh giới ownership và đường repair.
- **CP1:** chuẩn hóa HTML/whitespace, authors/categories, dates; tính
  `age_days`, `summary_chars`, `text_for_embedding`; filter có lý do và dedupe
  stable `paper_id`.
- **CP2–3:** thêm validation cho schema index/evaluation; chạy trên 24 raw
  Crossref records thật và ghi clean CSV/JSON cùng audit. Baseline artifacts
  upstream có 24 answers và metrics tự nhất quán, nhưng chưa tái lập được trên
  máy này vì thiếu dependencies và persisted Chroma collection. Test-set
  builder mới dùng thứ tự question type cố định, UUID5 và bỏ qua source field
  rỗng; không tự ghi đè test set baseline đã khóa.
- **CP4:** corruption dùng deep copy, không mutate baseline.
- **CP5:** sáu corruption deterministic trên sáu record riêng, có row-level
  log về ID, parameter, before/after value và count; artifacts thật có 1
  duplicate ID, 1 blank summary và 1 marked noise row.
- **CP6:** repair chỉ nhận raw records và chạy lại cùng cleaning path; baseline
  và repaired JSON có cùng SHA-256. Flow tích hợp bắt buộc repaired frame khớp
  baseline rồi mới ghi repaired index/metrics và comparison report. `run_date`
  được đọc lại từ baseline cleaning audit để `age_days` không lệch khi rerun.

## 4. Contract kỹ thuật

Clean output có schema cố định được khai báo trong `CLEAN_COLUMNS`. Các field
downstream quan trọng gồm `paper_id`, `title`, `summary`, `published`,
`authors_joined`, `categories_joined`, `text_for_embedding`, `abs_url` và
`pdf_url`. `validate_clean_dataframe` kiểm tra DataFrame không rỗng, đủ field,
ID không blank/trùng, title/text không blank và `age_days` không null.

Cleaning không tự điền nội dung học thuật bị thiếu. Record thiếu `paper_id`,
title, summary hoặc published hợp lệ bị loại và được đếm trong
`DataFrame.attrs["cleaning_audit"]`. Authors/categories được normalize và
dedupe case-insensitive nhưng không tạo giá trị không có trong source.

Corruption yêu cầu ít nhất sáu clean records, sau đó drop latest record, blank
summary, inject marker noise, truncate title, làm published cũ mười năm và tạo
duplicate. Helper fields được rebuild sau thay đổi. Baseline input được giữ
nguyên và log là JSON serializable bằng native scalar types.

## 5. Cách xác minh

Lệnh đã chạy:

```powershell
$env:PYTHONPATH='src'
$env:PYTHONDONTWRITEBYTECODE='1'
python -m pytest -q -p no:cacheprovider tests/test_cleaning_corruption.py
python script/run_role3_data_flow.py
python script/run_phase1.py
python script/run_corruption_flow.py
```

Kết quả test lượt cuối sau tích hợp upstream: `13 passed in 1.01s`.

Kết quả role3 data flow thật:

- raw/baseline/corrupted/repaired: `24/24/24/24` rows;
- baseline: 0 duplicate ID, 0 blank summary;
- corrupted: 1 duplicate ID, 1 blank summary, 1 marked noise row;
- repaired: 0 duplicate ID, 0 blank summary;
- baseline và repaired JSON cùng SHA-256
  `e5b40fa9900c1a495af3c075af9d4b5417df872cfe95eb4db77732acb13e8efc`;
- toàn bộ clean/audit/log JSON parse được ở strict mode.

Lần chạy mới của corruption flow dừng trước khi ghi artifact với lỗi thực tế
`RuntimeError: GOOGLE_API_KEY is required when LLM_PROVIDER=gemini.`. Môi
trường cũng chưa cài `datasets`, nên sau credential preflight vẫn chưa đủ điều
kiện tái lập evaluation. Flow không ghi metrics giả khi preflight thất bại.

Baseline artifacts do upstream bàn giao đã được kiểm tra nội bộ:

- 24 test samples và 24 answers, ID hai tập khớp;
- mọi retrieved document ID thuộc clean corpus;
- metrics tính lại từ answers khớp `baseline_metrics.json`:
  retrieval hit rate `0.875`, mean token F1 `0.3479368128134944`, judge
  accuracy `0.2916666666666667`, mean judge score `2.5`;
- quality baseline phản ánh đúng 24 rows, 0 blank/duplicate ID, 0 blank
  summary và 1 row quá ngưỡng freshness 180 ngày.

Các giới hạn được giữ rõ: `data/chroma/` không có persisted collection,
embedding manifest và report chứa absolute path từ máy upstream; test set cũ
đã dùng để sinh baseline vẫn có 6/24 ground truth rỗng. Builder đã được sửa,
nhưng artifact không được tái sinh riêng lẻ vì sẽ làm baseline answers/metrics
mất đồng bộ. Vì vậy đây là artifact verification, không phải local rerun.

Test dùng `PaperRecord` fixture được khai báo rõ trong test, không được ghi vào
`data/` và không được dùng làm metric bài nộp. Test xác minh normalization,
filter/dedupe audit, contract, deterministic corruption, baseline immutability,
strict JSON log và repair bằng raw records. Hai regression test bổ sung kiểm tra
trực tiếp committed raw/clean/corrupted/repaired artifacts và chứng minh mọi
corruption target đều có evaluation lineage trong `test_set.json`.

## 6. Quyết định kỹ thuật quan trọng

- **Bối cảnh:** repair có thể copy baseline sạch hoặc rebuild từ raw.
- **Phương án chọn:** bắt buộc rebuild từ `list[PaperRecord]` bằng chính
  `build_clean_dataframe`.
- **Lý do:** copy baseline che giấu lỗi lineage và không chứng minh pipeline có
  khả năng phục hồi từ nguồn đáng tin. Cùng raw snapshot + run date cũng giúp
  baseline và repaired tái lập được.
- **Bằng chứng:** test `test_repair_rebuilds_from_raw_records_not_corrupted_dataframe`
  chứng minh repaired frame bằng baseline trong khi corrupted frame có duplicate.

## 7. Lỗi và blocker

Lỗi đã xử lý trong lúc test: corruption log ban đầu chứa `numpy.int64`, làm
`json.dumps` báo `TypeError: Object of type int64 is not JSON serializable`.
Mình thêm chuyển đổi recursive về scalar/list/dict JSON-native; sáu test sau đó
pass.

Blocker còn lại ngoài ownership của tôi:

- source observability sau merge trả schema khác với committed baseline quality
  artifact; comparison reporter đã được làm tương thích với cả hai schema;
- committed test set có 6 ground truth rỗng; builder đã deterministic và tránh
  ground truth rỗng, nhưng cần rerun toàn bộ baseline để thay artifact an toàn;
- persisted Chroma collection không có trong repo, còn manifest trỏ tới path
  trên máy upstream;
- máy hiện chạy Python 3.14.6, ngoài range 3.11–3.13 của project, và chưa có
  `uv`; environment cũng thiếu `datasets` và LangChain.

Vì vậy tôi chỉ ghi data-level counts/hash đã kiểm chứng, không ghi RAG hoặc
observability metrics.

## 8. Hiểu biết luồng end-to-end

Crossref response phải được lưu raw trước khi parse thành stable `PaperRecord`.
Cleaning chuyển raw records thành schema cố định và embedding text; index giữ
`paper_id` trong metadata. Test set phải lấy `ground_truth_doc_ids` từ đúng
clean `paper_id` và được khóa cho cả ba lượt. Quality checks đo completeness,
uniqueness và schema; freshness tập trung published/`age_days`. Corruption chỉ
tác động bản clean/index riêng. Repair chạy lại raw → clean → repaired index.
Chỉ có thể kết luận recovery khi repaired quality/freshness và agent metrics từ
cùng evaluator/test set được đối chiếu với artifact thật.

## 9. Phân tích metrics

| Metric/signal        | Baseline | Corrupted | Repaired | Nhận xét                            |
| -------------------- | -------: | --------: | -------: | ----------------------------------- |
| `retrieval_hit_rate` |    0.875 |       N/A |      N/A | Baseline artifact tự nhất quán       |
| `mean_token_f1`      | 0.347937 |       N/A |      N/A | Baseline artifact tự nhất quán       |
| `judge_accuracy`     | 0.291667 |       N/A |      N/A | Baseline artifact tự nhất quán       |
| `mean_judge_score`   |      2.5 |       N/A |      N/A | Baseline artifact tự nhất quán       |
| Quality checks       | 7/8 fail |       N/A |      N/A | 1 row quá ngưỡng 180 ngày            |
| Freshness status     |    stale |       N/A |      N/A | 1/24 row stale theo committed report |

Chưa có chuỗi nguyên nhân–metric cho corruption/repair vì hai lượt đánh giá đó
chưa có artifact. Sau khi upstream hoàn thành, cần chạy cùng raw snapshot, test
set, top-k và evaluator cho ba trạng thái rồi mới cập nhật phần này.

## 10. Cam kết

- [x] Báo cáo phản ánh đúng phần việc trực tiếp thực hiện.
- [x] Có thể giải thích luồng end-to-end và ranh giới ownership.
- [ ] Mọi kết luận metrics có artifact — chưa đánh dấu vì pipeline chưa chạy.
- [x] Không ghi thành công cho bước chưa kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo không sao chép báo cáo thành viên khác.

**Họ và tên:** Đinh Quốc Trung  
**Ngày xác nhận phần độc lập:** 2026-08-06

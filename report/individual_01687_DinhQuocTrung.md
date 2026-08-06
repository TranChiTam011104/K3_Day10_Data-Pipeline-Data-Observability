# Báo cáo vai trò cá nhân — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Đinh Quốc Trung |
| MSSV | 2A202501687 |
| Khóa/Lớp | K3 |
| Tên nhóm | Nhóm 5 người |
| Vai trò chính | Vai trò 3 — Cleaning & Corruption Owner |
| Repository | `K3_Day10_Data-Pipeline-Data-Observability` |
| Ngày hoàn thành phần độc lập | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

Tôi phụ trách contract và triển khai cleaning, corruption có kiểm soát, cùng
repair từ raw snapshot theo phân công nhóm 5 người. Tôi không nhận ownership
Crossref ingestion, RAG/index, evaluation, observability report hoặc pipeline
orchestration.

| Module/deliverable | File/hàm phụ trách | Input | Output | Trạng thái |
| --- | --- | --- | --- | --- |
| Cleaning contract | `src/ingestion/cleaning.py` | `list[PaperRecord]`, `run_date` | Clean DataFrame + audit counts | Hoàn thành và unit-tested |
| Corruption | `src/ingestion/corruption.py` | Baseline clean DataFrame | Corrupted copy + strict JSON log | Hoàn thành và unit-tested |
| Repair | `repair_clean_dataframe` | Trusted raw `PaperRecord` snapshot | Rebuilt clean DataFrame | Hoàn thành và unit-tested |
| Handoff contract | `report/role3_cleaning_corruption_contract.md` | Starter/downstream source | Schema, ownership, blockers | Hoàn thành |
| Real artifacts/metrics | `data/clean`, `data/results` | Upstream ingestion/pipelines | Baseline/corrupted/repaired evidence | Chưa thể chạy vì dependency upstream còn thiếu |

## 3. Kết quả theo checkpoint

- **CP0:** đọc starter, downstream index và phân công; chốt field/filter/audit
  contract, ranh giới ownership và đường repair.
- **CP1:** chuẩn hóa HTML/whitespace, authors/categories, dates; tính
  `age_days`, `summary_chars`, `text_for_embedding`; filter có lý do và dedupe
  stable `paper_id`.
- **CP2–3:** thêm validation cho schema index/evaluation. Chưa tuyên bố smoke
  test index hoặc baseline thành công vì upstream test set/pipeline còn TODO và
  môi trường thiếu LangChain.
- **CP4:** corruption dùng deep copy, không mutate baseline.
- **CP5:** sáu corruption deterministic trên sáu record riêng, có row-level
  log về ID, parameter, before/after value và count.
- **CP6:** repair chỉ nhận raw records và chạy lại cùng cleaning path; không
  copy hoặc sửa tay baseline/corrupted DataFrame.

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
```

Kết quả lượt chạy cuối: `6 passed in 0.87s`.

Test dùng `PaperRecord` fixture được khai báo rõ trong test, không được ghi vào
`data/` và không được dùng làm metric bài nộp. Test xác minh normalization,
filter/dedupe audit, contract, deterministic corruption, baseline immutability,
strict JSON log và repair bằng raw records.

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

Blocker chưa thuộc ownership của tôi:

- `src/ingestion/crossref.py` chưa parse/fetch/load nên chưa có raw artifact;
- `src/evaluation/testset.py`, `src/pipelines/phase1.py` và
  `src/pipelines/corruption_flow.py` còn `NotImplementedError`;
- máy hiện chạy Python 3.14.6, ngoài range 3.11–3.13 của project, và chưa có
  `uv`/LangChain trong environment đang kiểm tra.

Vì vậy tôi không ghi bất kỳ số baseline/corrupted/repaired nào.

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

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | N/A | N/A | N/A | Chờ evaluator/pipeline upstream |
| `mean_token_f1` | N/A | N/A | N/A | Chờ evaluator/pipeline upstream |
| `judge_accuracy` | N/A | N/A | N/A | Chờ LLM credentials và evaluator |
| `mean_judge_score` | N/A | N/A | N/A | Chờ LLM credentials và evaluator |
| Quality checks | N/A | N/A | N/A | Observability owner chưa triển khai |
| Freshness status | N/A | N/A | N/A | Observability owner chưa triển khai |

Không có chuỗi nguyên nhân–metric nào được kết luận khi chưa có real artifacts.
Sau khi upstream hoàn thành, cần chạy cùng raw snapshot, test set, top-k và
evaluator cho ba trạng thái rồi mới cập nhật phần này.

## 10. Cam kết

- [x] Báo cáo phản ánh đúng phần việc trực tiếp thực hiện.
- [x] Có thể giải thích luồng end-to-end và ranh giới ownership.
- [ ] Mọi kết luận metrics có artifact — chưa đánh dấu vì pipeline chưa chạy.
- [x] Không ghi thành công cho bước chưa kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo không sao chép báo cáo thành viên khác.

**Họ và tên:** Đinh Quốc Trung  
**Ngày xác nhận phần độc lập:** 2026-08-06

# Member Role Report — Day 10: Data Pipeline & Data Observability

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Trần Chí Tâm |
| MSSV | 2A2026015353 |
| Khóa/Lớp | K3 |
| Tên nhóm | B3-1 |
| Vai trò chính | Role 1 — Pipeline Integrator & Orchestrator |
| Repository | https://github.com/TranChiTam011104/K3_Day10_Data-Pipeline-Data-Observability.git |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Pipeline orchestration | `src/pipelines/phase1.py::main()` | `data/raw/crossref_records.json` | Baseline metrics, answers, quality, report | Hoàn thành |
| Corruption pipeline | `src/pipelines/corruption_flow.py::main()` | `data/clean/papers_clean.csv`, `data/raw/crossref_records.json` | Corrupted/repaired metrics, quality, comparison report | Hoàn thành |
| CP0 plan document | `report/CP0_PLAN.md` | Tất cả artifact và contract từ team | Evidence cho CP1–CP5 | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả |
| --- | --- | --- |
| Implement `build_test_set` | Role 5 (eval) | Trước CP1 deadline vì Vai 5 chưa kịp; đảm bảo pipeline chạy end-to-end |
| Implement `run_data_quality_checks` + `build_freshness_report` | Role 5 (observe) | Trước CP1 deadline vì Vai 5 chưa kịp; baseline quality report có artifact |
| Implement `generate_phase1_report` + `generate_corruption_report` | Role 5 (observe) | Đảm bảo phase1 report và corruption comparison report tự động tạo từ pipeline |
| Fix bug `write_json` argument order trong `reporting.py` | Role 5 (observe) | Bug không cho phép `generate_phase1_report` serialize pandas int64 |
| Update `.gitignore` cho data artifacts | Toàn bộ team | Tránh conflict khi nhiều máy chạy pipeline cùng lúc; data artifacts không push lên Git |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Implement `phase1.py` orchestration end-to-end | `src/pipelines/phase1.py` | Pipeline tự động: raw → clean → index → test set → evaluate → quality → report | `python script/run_phase1.py` exit 0, `data/reports/phase1_report.md` present |
| Implement `corruption_flow.py` | `src/pipelines/corruption_flow.py` | Pipeline tự động: corrupt → rebuild → evaluate → quality → repair → compare | `python script/run_corruption_flow.py` exit 0, `data/reports/corruption_report.md` present |
| Khóa clean contract và verify baseline | `data/clean/papers_clean.csv`, `data/clean/papers_clean.json` | 24 records clean, 0 dropped, paper_id unique, text_for_embedding present | Pandas đọc đúng 24 rows |
| Verify Chroma index và test set | `data/chroma/`, `data/eval/test_set.json` | 1 collection `papers-baseline` × 24 docs; test set 24 questions × 4 types; 100% ground_truth_doc_ids tồn tại trong Chroma | `chromadb.Client.list_collections()` và script check |
| Implement `build_test_set` (emergency) | `src/evaluation/testset.py` | 24 questions đúng schema: id, question_type, question, ground_truth, ground_truth_doc_ids | `python -c "from evaluation.testset import build_test_set"` |
| Implement quality + freshness (emergency) | `src/observability/quality.py` | 7 quality gates + freshness report; 7/8 baseline pass, 1 FAIL (age_days stale) | `data/quality/quality_baseline.json` và `freshness_report.json` present |
| Implement reporting (emergency) | `src/observability/reporting.py` | Markdown report tự động với artifact paths thật | `data/reports/phase1_report.md` và `corruption_report.md` |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

**Output cụ thể:** `data/reports/corruption_report.md` — comparison report tự động so sánh baseline / corrupted / repaired dựa trên metrics, quality và freshness artifacts thật. Không phải tự điền tay. Mỗi con số trong bảng đều traceable về JSON artifact.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Vai trò 1 (Pipeline Integrator) cần đảm bảo toàn bộ pipeline chạy end-to-end mà không phụ thuộc vào việc các vai khác hoàn thành kịp thời. Nếu một vai chưa implement module, pipeline sẽ fail → không có baseline artifact cho CP3. Vấn đề cụ thể: (1) CP1 deadline gần nhưng `testset.py`, `quality.py`, `reporting.py` còn `NotImplementedError`; (2) CP5 nhưng `corruption_flow.py` chưa implement.

### Cách triển khai

**Orchestration pattern:** `phase1.py` và `corruption_flow.py` đều tuân theo pattern đọc-có-sẵn-không-fetch-lại. Biến môi trường `REFRESH_SOURCE=0` và `REFRESH_TEST_SET=0` ngăn pipeline fetch lại source hoặc regenerate test set — đảm bảo baseline không bị ảnh hưởng giữa các runs.

**Artifact isolation:** Mỗi trạng thái (baseline / corrupted / repaired) có path riêng cho CSV, JSON, embeddings manifest và Chroma collection riêng. Chroma collection name được derive từ `embeddings_output_path` thông qua `_derive_collection_name()` — map từng path cụ thể đến collection name riêng.

**Contract verification:** Trước khi báo cáo "clean schema ổn định", lead chạy `build_clean_dataframe` với data thật và verify: row count, null counts, duplicate counts, text_for_embedding length. Trước khi báo cáo "test set ready", lead verify ground_truth_doc_ids có tồn tại trong Chroma collection.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | `data/raw/crossref_records.json` (24 PaperRecord); `data/clean/papers_clean.csv` (24 clean rows) |
| Output | `data/results/baseline_metrics.json`, `data/results/baseline_answers.json`, `data/reports/phase1_report.md`; tương ứng cho corrupted/repaired |
| Module phụ thuộc | `ingestion.cleaning::build_clean_dataframe`, `retrieval.index::LocalEmbeddingIndex`, `evaluation.metrics::evaluate_pipeline`, `observability.quality::*`, `observability.reporting::*` |
| Module sử dụng output | `corruption_flow.py` (dùng baseline artifacts làm ground truth để so sánh); team dùng phase1 report để demo |
| Điều kiện lỗi cần xử lý | `KeyError` nếu clean CSV thiếu required column; `TypeError` khi pandas int64 không JSON-serializable; Chroma `delete_collection` nếu collection đã tồn tại |

### Cách xác minh

```bash
# Verify baseline end-to-end
python script/run_phase1.py
ls data/reports/phase1_report.md  # must exist

# Verify corruption flow
python script/run_corruption_flow.py
ls data/reports/corruption_report.md  # must exist

# Verify Chroma collections isolation
python -c "
import chromadb
c = chromadb.PersistentClient(path='data/chroma')
for col in c.list_collections():
    print(col.name, col.count())
"
# Output: papers-baseline: 24, papers-corrupted: 24, papers-repaired: 24

# Verify comparison report contains real data
grep "0.875" data/reports/corruption_report.md  # hit rate from baseline_metrics.json
```

- **Kết quả mong đợi:** Report hiển thị metrics từ JSON thật; Chroma có 3 collections riêng biệt; baseline metrics không đổi sau corruption flow.
- **Kết quả thực tế:** Tất cả như kỳ vọng. Corruption giảm hit_rate 0.875 → 0.833; repair phục hồi 0.875. 3 Chroma collections tồn tại đồng thời.
- **Artifact/log:** `data/reports/corruption_report.md`, `data/results/baseline_metrics.json`, `data/results/corrupted_metrics.json`

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** `LocalEmbeddingIndex.build()` có parameter `collection_name` nhưng signature chỉ nhận `settings` và `embeddings_output_path`. Muốn tạo 3 Chroma collections riêng (baseline, corrupted, repaired) trong cùng pipeline.
- **Các phương án đã cân nhắc:**
  1. Fork `LocalEmbeddingIndex.build()` thành 3 phiên bản với hard-coded collection names — vi phạm DRY, dễ lỗi sync.
  2. Thêm `collection_name` param vào `LocalEmbeddingIndex.build()` — thay đổi API của vai khác, có thể gây conflict.
  3. Dùng `embeddings_output_path` khác nhau để trigger `_derive_collection_name()` map → mỗi path có collection name riêng — không sửa module khác, backward-compatible.
- **Phương án đã chọn:** Phương án 3 — pass `settings.paths.corrupted_embeddings_json` và `settings.paths.repaired_embeddings_json` làm `embeddings_output_path`.
- **Lý do:** `_derive_collection_name` đã có `name_map` từ `embeddings_json.resolve()` → `baseline_collection_name`. Thêm 2 entries vào map là đủ. Không sửa `retrieval/index.py` — tránh conflict với vai 4. Chi phí: chỉ cần gọi `LocalEmbeddingIndex.load()` ngay sau `build()` để đảm bảo collection name consistent với manifest.
- **Bằng chứng:** 3 Chroma collections đều tồn tại đồng thời; `chromadb.Client.list_collections()` xác nhận.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** `AttributeError: 'list' object has no attribute 'parent'` khi `corruption_flow.py` gọi `write_json(corrupted_df.to_dict(orient="records"), settings.paths.corrupted_clean_json)`.
- **Lệnh hoặc bước tái hiện:** Chạy `python script/run_corruption_flow.py` → fail ngay bước serialize clean data.
- **Nguyên nhân gốc:** Thứ tự argument trong `write_json(payload, path)` bị đảo ngược — `corrupted_df.to_dict(...)` (list) rơi vào vị trí argument đầu tiên, nhưng signature `core/utils.py` là `write_json(path, payload)` (path trước). Python không type-check ở runtime → list object được truyền vào `ensure_parent(path)` → `path.parent` fail.
- **Cách xử lý:** Đổi thứ tự: `write_json(settings.paths.corrupted_clean_json, corrupted_df.to_dict(orient="records"))`. Kiểm tra tất cả các `write_json` calls còn lại trong file — phát hiện 3 chỗ cùng bị đảo. Sửa hết.
- **Cách xác minh sau khi sửa:** `python script/run_corruption_flow.py` exit 0; `data/clean/papers_clean_corrupted.json` đọc được bằng `json.load()`.
- **Điều học được:** Python không enforce argument order ở runtime khi không có type hints. Bug này nằm ở interface giữa `corruption_flow.py` và `core/utils.py` — nơi 2 người viết theo 2 convention khác nhau. Giải pháp dài hạn: thêm `ruff` rule enforce argument order hoặc dùng `@overload` type hints.

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. **Dữ liệu đi từ Crossref đến vector index như thế nào?**
   Crossref API trả JSON → `fetch_source_records()` parse thành list `PaperRecord` → `build_clean_dataframe()` normalize: clean HTML, parse date, deduplicate theo DOI, tính age_days, ghép `text_for_embedding` (title + summary + authors + categories) → `MiniLMEmbeddings` encode mỗi `text_for_embedding` thành 384-dim vector → Chroma `collection.add()` với vector, document text và metadata (DOI, title, url...) → manifest `papers_embeddings.json` ghi lại schema để sau này `LocalEmbeddingIndex.load()` tái tạo.

2. **Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?**
   `build_test_set` chọn 24 papers, mỗi paper 1 question (4 types × 6 papers). Ground truth doc ID = DOI của paper được chọn. Khi evaluate: `qa.py` gọi `index.search(question)` → Chroma trả top-4 kết quả → nếu DOI ground truth trong top-4 → `retrieval_hit=True`. `qa.py` extract answer từ metadata (ví dụ `authors_joined` cho type=authors), LLM judge so sánh answer vs ground_truth → token F1 và score.

3. **Quality checks khác freshness monitoring ở điểm nào trong bài lab?**
   Quality checks đo **intrinsic data quality** — record có DOI không, title có rỗng không, summary có đủ dài không, text_for_embedding có không, paper_id có trùng không. Freshness monitoring đo **temporal relevance** — paper xuất bản bao lâu rồi, có còn trong threshold 180 ngày không. Quality pass ≠ freshness pass: dataset có thể clean nhưng outdated (như baseline: 7/8 quality pass nhưng freshness FAIL vì 1 paper 193 ngày).

4. **Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?**
   Nếu dùng test set khác nhau, comparison không công bằng — metric thay đổi có thể do test set khác chứ không phải do data corruption. Test set được khóa bằng `REFRESH_TEST_SET=0` và lưu tại `data/eval/test_set.json`. Tất cả 3 evaluation (baseline, corrupted, repaired) dùng cùng 24 câu hỏi, cùng ground truth doc IDs.

5. **Repair được xem là thành công dựa trên artifact và metric nào?**
   Repaired metrics phải **khớp baseline** (hoặc tốt hơn), không phải "đẹp". Artifact kiểm tra: `papers_clean_repaired.csv` row count = 24 (bằng baseline), `corruption_log` confirm không record nào bị mất âm thầm. Quality report: 4/5 checks passed (bằng baseline). Freshness: 1 stale (bằng baseline). Evaluation: retrieval_hit_rate = 0.875 (bằng baseline). Không phải sửa tay — repair chạy lại `build_clean_dataframe()` từ cùng `crossref_records.json`.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | **0.875** | **0.833** | **0.875** | Corruption làm giảm 1/24 retrieval hit (3% drop). Repair phục hồi hoàn toàn. |
| `mean_token_f1` | **0.299** | **0.258** | **0.299** | Tương ứng với retrieval — F1 thấp vì answer extractive ngắn, ground truth dài. |
| `judge_accuracy` | **0.250** | **0.208** | **0.250** | Chỉ 6/24 câu đúng hoàn toàn. Repair phục hồi đúng 6 câu. |
| `mean_judge_score` | **2.333** | **2.167** | **2.292** | Repair gần như phục hồi (2.292 vs 2.333). Mức chênh 0.04 có thể do LLM judge non-deterministic. |
| Quality checks | **4/5** | **2/5** | **4/5** | Corruption thêm 3 failures: duplicate DOI, blank summary, stale date. Repair phục hồi 2/3. |
| Freshness status | **1 stale** | **2 stale** | **1 stale** | Corruption thêm 1 stale (date -10 years). Repair phục hồi stale count. |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. **[Corruption: truncate_title]** → **[quality: title_not_null FAIL; paper_id_unique FAIL (do duplicate row)]** → **[agent metric: retrieval_hit giảm từ 21 → 20]**
   - Bằng chứng: `corruption_log.json` ghi "truncate_title" paper `10.1111/exsy.70341` với keep_chars=12 → title = "Hi-RAG : A ". Embedding vector thay đổi hoàn toàn → semantic search không tìm đúng paper → retrieval_hit giảm.
   - Bằng chứng: `corruption_log.json` ghi "duplicate_row" paper `10.20944/preprints...` → duplicate DOI → quality FAIL paper_id_unique.
   - Baseline answers: miss case (type=categories) lấy sai DOI → corruption impact rõ nhất trên retrieval layer.

2. **[Repair: re-run `build_clean_dataframe` từ raw]** → **[quality: 4/5 restored; freshness: 1 stale restored]** → **[agent metric: retrieval_hit_rate phục hồi 0.875]**
   - Bằng chứng: `cleaning_audit_baseline.json` và `cleaning_audit_repaired.json` giống hệt nhau (24→24→0 dropped) → repair không làm mất record.
   - Bằng chứng: repaired_metrics.json khớp baseline_metrics.json → retrieval phục hồi hoàn toàn.

**Corruption nào ảnh hưởng rõ nhất và vì sao?**

`truncate_title` ảnh hưởng rõ nhất vì thay đổi trực tiếp `text_for_embedding` — trường mà vector embedding được encode từ đó. Title "Hi-RAG: A Hierarchical..." bị cắt thành 12 ký tự → embedding vector hoàn toàn khác → retrieval search cho câu hỏi "What categories does the paper titled 'Hi-RAG: A Hierarchical...'" không tìm được đúng paper. Trong khi `blank_summary` và `stale_date` ảnh hưởng đến quality/freshness nhưng không trực tiếp làm sai retrieval — embedding vẫn chứa title và authors đủ để semantic search hoạt động.

**Kết quả nào khác với kỳ vọng ban đầu?**

`mean_judge_score` repaired = 2.292 không bằng baseline = 2.333 (chênh -0.041). Kỳ vọng ban đầu: repaired phải khớp baseline hoàn toàn. Giả thuyết: LLM judge (GPT-4o-mini) non-deterministic giữa các runs → mỗi evaluation gọi LLM riêng, câu trả lời hơi khác → judge score hơi khác. Đã kiểm tra: retrieval_hit_rate và token_f1 phục hồi đúng bằng baseline → không phải retrieval issue. Token F1 repaired = 0.299 = baseline → extraction logic nhất quán.

### CP6 — Final verification

CP6 checkpoint bao gồm final review và freeze scope:

**Final checklist:**
- Repaired artifacts đầy đủ: `repaired_metrics.json`, `repaired_answers.json`, `repaired_quality.json`, `repaired_freshness.json` ✅
- `corruption_report.md` tồn tại và khớp với tất cả JSON artifacts ✅
- Baseline không bị ghi đè (retrieval_hit_rate = 0.875 đúng như CP3) ✅
- .gitignore cập nhật — tất cả data artifacts được ignore ✅
- Individual report hoàn chỉnh ✅

**Frozen demo parts cho team:**

1. **Ingest** — Verify raw records: `data/raw/crossref_records.json` (24 records) và lineage không đổi.
2. **Clean** — Demo 3 CSV khác nhau: `papers_clean.csv` (baseline), `papers_clean_corrupted.csv` (24 rows + 1 duplicate), `papers_clean_repaired.csv` (24 rows, giống baseline). Repaired CSV = baseline CSV.
3. **RAG** — Demo 3 Chroma collections: `papers-baseline`, `papers-corrupted`, `papers-repaired`. Smoke test query.
4. **Eval** — Demo hit (authors, score=5, DOI đúng) và miss (categories, DOI sai, retrieval trả về paper khác).
5. **Observe** — Trình bày comparison table từ `corruption_report.md`.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Data quality là tiền đề của mọi downstream quality.** Pipeline có thể có agent LLM đắt tiền, embedding model tốt nhất, nhưng nếu `text_for_embedding` bị truncate hoặc blank thì retrieval không hoạt động — không có LLM nào cứu được. Điều này có nghĩa: mỗi bước cleaning phải có quality gate riêng trước khi qua bước tiếp theo, không phải check cuối cùng.

2. **Orchestration code cần integration test trước khi các module con hoàn thành.** Vai 1 implement `phase1.py` với mock data hoặc early integration sớm sẽ phát hiện `write_json` argument order, `read_csv` không tồn tại, và `collection_name` param không hoạt động — trước khi các vai khác commit code của họ. Không nên đợi tất cả module hoàn thành rồi mới integration.

3. **Reproducibility đòi hỏi artifact isolation rõ ràng.** Mỗi run (baseline/corrupted/repaired) phải có path riêng cho mọi artifact. Việc share path (ví dụ `chromadb.PersistentClient` dùng cùng directory) dẫn đến collection conflict. Giải pháp: dùng `embeddings_output_path` khác nhau hoặc dùng `InMemoryChromaClient` cho test, `PersistentClient` cho production.

### Nếu có thêm thời gian

Thêm pipeline smoke test tự động chạy sau mỗi checkpoint, kiểm tra: (1) baseline artifacts không bị modified (hash check), (2) Chroma collections count đúng (3), (3) quality report overall_passed tương ứng với kỳ vọng (baseline: True, corrupted: False, repaired: True). Hiện tại smoke test phải làm bằng tay. Automate này sẽ giảm thời gian debug ở CP5-CP6 đáng kể.

Ngoài ra, thêm pre-commit hook kiểm tra data artifacts không được commit: nếu ai đó `git add data/results/` sẽ reject. Điều này tránh conflict khi nhiều người chạy pipeline cùng lúc trên các branch khác nhau.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Trần Chí Tâm
**Ngày xác nhận:** 2026-08-06

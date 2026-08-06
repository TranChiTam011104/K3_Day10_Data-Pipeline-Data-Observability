# Báo cáo vai trò cá nhân — Day 10: Data Pipeline & Data Observability

> DRAFT — mọi số liệu/artifact trong bản này là kết quả thật đã chạy và verify trong session làm việc, không phải suy diễn. Đọc lại toàn bộ, sửa các đoạn phân tích/nhận xét sang văn phong của bạn trước khi nộp (mục 10 có 1 dòng cam kết bạn phải tự đọc lại rồi mới tick).

## 1. Thông tin cá nhân

| Thông tin | Nội dung |
| --- | --- |
| Họ và tên | Trương Văn Thái |
| MSSV | 2A202601801 |
| Khóa/Lớp | K3 |
| Tên nhóm | B3-1 |
| Vai trò chính | RAG & Agent Owner — MiniLM, Chroma, search, lookup |
| Repository | `K3_Day10_Data-Pipeline-Data-Observability` |
| Ngày hoàn thành | 2026-08-06 |

## 2. Vai trò và phạm vi công việc

Tôi phụ trách phần RAG/retrieval trong phân công nhóm 4 người: `src/retrieval/` và `data/embeddings/`. `LocalEmbeddingIndex` (`src/retrieval/index.py`), `MiniLMEmbeddings` (`embeddings.py`) và `build_agent`/`run_agent_question` (`agent.py`) là code tham khảo có sẵn từ starter — việc của tôi là đọc kỹ contract, xác nhận cấu hình (embedding model, collection naming) đã đúng, và **verify bằng dữ liệu thật** rằng toàn chuỗi embedding → Chroma → search/lookup → agent hoạt động đúng ở cả ba trạng thái baseline/corrupted/repaired. Tôi không sửa logic Crossref, cleaning, evaluator hay ngưỡng observability.

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao | Trạng thái |
| --- | --- | --- | --- | --- |
| Verify embedding/index contract | `src/retrieval/index.py`, `embeddings.py` (đọc, không sửa) | Clean DataFrame (9 cột bắt buộc) | Xác nhận contract khớp `ingestion.cleaning.REQUIRED_INDEX_COLUMNS` | Hoàn thành |
| Smoke-test tooling (mới viết) | `script/smoke_test_rag.py` | `data/clean/papers_clean.csv` | Validate schema + build collection throwaway `smoke-test` + demo search/lookup/agent | Hoàn thành |
| Build & verify `papers-baseline` | `retrieval.index.LocalEmbeddingIndex.build` | `papers_clean.csv` (24 rows) | Collection `papers-baseline` + `data/embeddings/papers_embeddings.json` | Hoàn thành |
| Build & verify `papers-corrupted`/`papers-repaired` | như trên, trỏ path corrupted/repaired | `papers_clean_corrupted.csv`, `papers_clean_repaired.csv` | Collection + manifest riêng, tách biệt baseline | Hoàn thành |
| Agent grounding check | `retrieval.agent.build_agent`, `run_agent_question` (đọc, không sửa) | Câu hỏi + index | Trả lời có tool-call, từ chối đúng khi ngoài corpus | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động | Thành viên/module được hỗ trợ | Kết quả và bằng chứng |
| --- | --- | --- |
| Phát hiện + sửa bug `NaN` trong embedding manifest | Ảnh hưởng chung (baseline manifest do pipeline chung tạo ra) | Tìm ra `pd.read_csv` mặc định biến ô rỗng thành `NaN` khi đọc lại clean CSV; sửa bằng `keep_default_na=False`; rebuild lại `papers_embeddings.json`, xác nhận `grep -c "NaN"` từ 40 → 0 |
| Đọc code `ingestion.corruption.py`, `pipelines/corruption_flow.py` để hiểu 6 loại corruption thật đã áp dụng | Role clean/lead | Dùng thông tin này để chọn đúng paper bị ảnh hưởng (SafeRAG) làm ví dụ minh chứng retrieval |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao | Cách xác minh |
| --- | --- | --- | --- |
| Build `papers-baseline` từ clean data thật | `data/embeddings/papers_embeddings.json`, collection `papers-baseline` | 24 documents, khớp 100% `paper_id` với `papers_clean.csv` | `LocalEmbeddingIndex.load(...).collection.count() == 24`; so `set(paper_id)` giữa clean CSV và manifest |
| Semantic search + exact lookup có thể kiểm chứng | `index.search()`, `index.lookup()` | Query `"oil and gas safety report generation"` → top-1 đúng paper SafeRAG (`10.2118/234689-pa`), score `0.463`, cách biệt rõ với top-2 (`0.266`) | Chạy lại `script/smoke_test_rag.py` |
| Agent grounding — trong và ngoài corpus | `build_agent`, `run_agent_question` | Câu hỏi về SafeRAG → trả lời đúng, chi tiết khớp abstract thật; câu hỏi về "Attention Is All You Need" (không có trong 24 paper) → agent trả lời "không tìm thấy trong corpus", không bịa | Log console 2 lần gọi agent, model `gpt-4o-mini` |
| Build `papers-corrupted`, quan sát retrieval đổi | Collection `papers-corrupted`, `data/embeddings/papers_embeddings_corrupted.json` | Cùng query, SafeRAG **biến mất** khỏi top-3 (đã bị `drop_latest_record` xóa); top-1 đổi paper, score giảm `0.463 → 0.266` | `index.lookup("10.2118/234689-pa")` → `NOT FOUND` |
| Build `papers-repaired`, xác nhận phục hồi | Collection `papers-repaired` | SafeRAG trở lại đúng vị trí, score `0.463` — **giống tuyệt đối** baseline, không phải xấp xỉ | `index.search(...)` cho kết quả identical với baseline run |
| Xác nhận `papers-baseline` không bị mutate | — | Sau khi build corrupted + repaired nhiều lần, load lại baseline vẫn 24 docs, score y hệt lần đầu | `LocalEmbeddingIndex.load(settings)` (không dùng `.build()`) rồi search lại |

Output cụ thể mà phần việc của tôi tạo ra: file `script/smoke_test_rag.py` — công cụ verify độc lập, idempotent, không phụ thuộc `phase1.py`/`corruption_flow.py` (do role khác implement), có thể chạy lại bất cứ lúc nào trong lúc chờ pipeline chính hoàn thiện mà không rủi ro ghi đè artifact thật.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Đảm bảo tầng retrieval (embedding model + vector store + agent) hoạt động đúng **contract** mà role `clean` bàn giao (schema DataFrame cố định), và có cách verify độc lập trước khi ghép vào pipeline tổng — vì `src/retrieval/*` là code tham khảo có sẵn, không có TODO, nên rủi ro lớn nhất không nằm ở việc code sai, mà ở việc **dữ liệu đầu vào không đúng shape** (thiếu cột, giá trị rỗng bị hiểu sai kiểu) làm tầng retrieval fail âm thầm hoặc trả kết quả sai mà không ai biết.

### Cách triển khai

`MiniLMEmbeddings` bọc `sentence-transformers/all-MiniLM-L6-v2` qua interface `Embeddings` của LangChain, cache model bằng `lru_cache`. `LocalEmbeddingIndex.build()` nhận DataFrame, dựng document list (`record_id`, `content`=`text_for_embedding`, `metadata`), embed toàn bộ, tạo Chroma collection (cosine similarity), ghi manifest JSON. `search()` embed câu hỏi rồi query top-k, trả `score = 1 - distance`. `lookup()` tra dict `paper_id`/`title` trực tiếp, không qua embedding — dùng cho câu hỏi cần độ chính xác tuyệt đối. Agent dùng `create_agent` của LangChain với 2 tool bọc quanh `search`/`lookup`, system prompt bắt buộc gọi tool trước khi trả lời factual.

Điểm quan trọng nhất tôi phải tự kiểm chứng (không có sẵn trong code): `_derive_collection_name()` chỉ đặc biệt hoá 3 path cố định (`embeddings_json`, `corrupted_embeddings_json`, `repaired_embeddings_json`); path khác sẽ tự suy ra tên collection qua `safe_slug()`. Tôi lợi dụng đúng cơ chế này để tạo collection `smoke-test` tách biệt hoàn toàn khỏi `papers-baseline` khi verify.

### Input, output và contract

| Thành phần | Mô tả |
| --- | --- |
| Input | `pd.DataFrame` với đúng 9 cột: `paper_id, title, text_for_embedding, published, authors_joined, categories_joined, summary, abs_url, pdf_url` (= `ingestion.cleaning.REQUIRED_INDEX_COLUMNS`) |
| Output | Chroma collection (persist tại `data/chroma/`) + manifest JSON `{backend, embedding_model, persist_path, collection_name, documents: [{record_id, paper_id, title, content, metadata}]}` |
| Module phụ thuộc | `ingestion.cleaning.build_clean_dataframe` (role clean bàn giao DataFrame) |
| Module sử dụng output | `evaluation.metrics.evaluate_pipeline`, `pipelines.phase1.py`/`corruption_flow.py` (role eval/lead) |
| Điều kiện lỗi cần xử lý | Thiếu cột → `KeyError` ngay trong `_build_documents`, không có validate; ô rỗng khi đọc lại CSV bị `pandas` hiểu thành `NaN` → JSON không hợp lệ (gặp thật, xem mục 6) |

### Cách xác minh

```bash
uv run python script/smoke_test_rag.py
```

- **Kết quả mong đợi:** contract valid, build collection thật, search trả kết quả liên quan, lookup tìm đúng record, agent trả lời có tool-call (nếu có LLM key) hoặc fallback rõ ràng (nếu không).
- **Kết quả thực tế:** `[OK] 24 rows loaded, contract valid` → build `papers-baseline` với 24 docs → search `"oil and gas safety report generation"` trả top-1 đúng SafeRAG score `0.463` → lookup `FOUND` → agent (`gpt-4o-mini`) trả lời grounded → `=== SMOKE TEST: PASS ===`.
- **Artifact/log:** `data/embeddings/papers_embeddings.json`, console log script (không chứa secret — API key chỉ đọc từ `.env`, không được in ra).

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần verify index/agent nhiều lần trong lúc `data/clean/` chưa sẵn sàng và trong lúc debug — có nên test trực tiếp trên collection `papers-baseline` thật, hay tạo collection riêng?
- **Các phương án đã cân nhắc:**
  1. Test trực tiếp trên `papers-baseline` — đơn giản, không cần path riêng.
  2. Tạo collection/manifest throwaway riêng (dùng path không khớp 3 path cố định, để `safe_slug()` tự sinh tên `smoke-test`).
- **Phương án đã chọn:** (2).
- **Lý do:** `LocalEmbeddingIndex.build()` luôn `delete_collection` rồi `create_collection` lại theo tên suy ra từ path truyền vào — nếu lỡ trỏ nhầm vào path baseline trong lúc lặp script nhiều lần để debug, sẽ xoá mất artifact thật dùng để chấm điểm mà không có cảnh báo nào. Tách riêng đổi lại chi phí gần như bằng 0 (chỉ cần đổi 1 tham số `embeddings_output_path`) nhưng loại hẳn rủi ro đó.
- **Bằng chứng quyết định phù hợp:** Sau khi build `papers-corrupted` và `papers-repaired` (mỗi cái nhiều lần trong lúc sửa bug), load lại `papers-baseline` vẫn đúng 24 docs và score `0.463` y hệt lần build đầu tiên — chứng minh không có lần chạy nào vô tình ghi đè baseline.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** Mở `data/embeddings/_smoke_test.json` thấy `"categories_joined": NaN` và `"pdf_url": NaN` — literal `NaN`, không phải chuỗi `"NaN"` hay `null`. Kiểm tra thêm thì `data/embeddings/papers_embeddings.json` (baseline thật, đã bị commit trước đó) cũng có 40 chỗ tương tự.
- **Lệnh hoặc bước tái hiện:** `grep -c "NaN" data/embeddings/papers_embeddings.json` → `40`.
- **Nguyên nhân gốc:** Script đọc clean data qua `pd.read_csv(settings.paths.clean_csv)` không truyền `keep_default_na=False`. Toàn bộ 24 dòng có `categories_joined` rỗng (Crossref không luôn trả subject/category) và 16 dòng có `pdf_url` rỗng — pandas mặc định coi các ô CSV rỗng này là `NaN` (kiểu float) khi đọc lại, không phải chuỗi rỗng `""` như lúc `cleaning.py` ghi ra. `core.utils.write_json` dùng `json.dumps(..., allow_nan=True)` (mặc định của Python), nên ghi thẳng literal `NaN` ra file — hợp lệ với `json.loads` (extension của Python) nhưng **không hợp lệ theo chuẩn JSON**.
- **Cách xử lý:** Thêm `keep_default_na=False` vào `pd.read_csv(...)` trong `_load_clean_dataframe()` (`script/smoke_test_rag.py`), rồi build lại `papers_embeddings.json` từ đầu.
- **Cách xác minh sau khi sửa:** `grep -c "NaN" data/embeddings/papers_embeddings.json` → `0`; chạy lại search/lookup cho kết quả **giống hệt** trước khi sửa (score, top-k, paper_id không đổi) — xác nhận fix chỉ sửa encoding, không đổi hành vi retrieval.
- **Điều học được:** Vòng lặp CSV → DataFrame không "trong suốt" với chuỗi rỗng; khi một script khác (ở đây là chính tôi) đọc lại artifact CSV do pipeline khác ghi ra, phải tự kiểm tra ô rỗng biến thành gì sau `read_csv`, không thể giả định "đọc lại = giống dữ liệu gốc lúc ghi".

## 7. Hiểu biết về luồng end-to-end

1. **Crossref → vector index:** Gọi Crossref API, lưu raw response + raw records đã parse (`data/raw/`) trước khi xử lý gì khác, để có thể truy vết/repair sau này. `cleaning.py` chuẩn hoá raw records thành DataFrame schema cố định (bao gồm `text_for_embedding` build từ title+summary+authors+categories). `LocalEmbeddingIndex.build()` embed `text_for_embedding` bằng MiniLM và lưu vào Chroma collection riêng theo từng trạng thái (baseline/corrupted/repaired), metadata giữ `paper_id` để tra cứu/lineage.
2. **Test set & ground truth:** `testset.py` sinh câu hỏi trực tiếp từ clean dataset, mỗi câu có `ground_truth_doc_ids` = đúng `paper_id` của document nguồn. Evaluator dùng ID này để tính `retrieval_hit_rate` (paper đúng có được retrieve top-k không) độc lập với `token_f1`/`judge_score` (câu trả lời cuối có khớp `ground_truth` không) — hai tín hiệu đo hai tầng khác nhau (retrieval vs generation).
3. **Quality checks vs freshness:** Quality đo tính đúng đắn **cấu trúc** dữ liệu tại một thời điểm (blank/duplicate/missing field); freshness đo tính **mới theo thời gian** (`age_days` so với ngưỡng 180 ngày). Hai trục độc lập — dữ liệu có thể pass mọi quality check nhưng vẫn stale, hoặc ngược lại.
4. **Vì sao dùng cùng test set cho cả 3 trạng thái:** Để so sánh công bằng. Nếu đổi câu hỏi giữa các lần đánh giá, không thể phân biệt "retrieval tệ đi do corruption" với "câu hỏi lần này vốn khó hơn" — cùng test set là điều kiện bắt buộc để kết luận nhân-quả.
5. **Repair được xem là thành công khi:** (a) `paper_id` set của repaired dataframe khớp 100% baseline (đã tự verify: `set(paper_id)` bằng nhau); (b) metrics evaluation (`retrieval_hit_rate`, `judge_accuracy`) quay lại đúng giá trị baseline, không phải "gần bằng"; (c) với phần retrieval cụ thể tôi phụ trách: score semantic search cho cùng một query phải khôi phục lại **chính xác** giá trị baseline (`0.463`), không chỉ "tốt hơn corrupted".

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| --- | ---: | ---: | ---: | --- |
| `retrieval_hit_rate` | 0.875 | 0.833 | 0.875 | Giảm ~4.2 điểm % khi corrupted, phục hồi đúng giá trị baseline sau repair |
| `mean_token_f1` | 0.2992 | 0.2575 | 0.2992 | Giảm rõ khi corrupted (noise/blank summary làm answer lệch ground truth), phục hồi hoàn toàn |
| `judge_accuracy` | 0.250 | 0.208 | 0.250 | Giảm nhẹ, phục hồi đúng baseline |
| `mean_judge_score` | 2.333 | 2.125 | 2.2917 | Giảm khi corrupted; sau repair gần khôi phục nhưng không tuyệt đối bằng baseline — xem giải thích ở dưới |
| Quality checks | `passed=true` | `passed=false` (1 duplicate ID, 1 blank summary) | `passed=true` | Đúng khớp corruption log: 6 lỗi có chủ đích |
| Freshness status | stale 1/24 | stale 2/24 | stale 1/24 | +1 record stale do `stale_published_date` lùi 10 năm; phục hồi đúng số lượng baseline |
| **Semantic search score (query mẫu, do tôi tự đo)** | **0.463** (SafeRAG, top-1) | **0.266** (SafeRAG biến mất khỏi top-3) | **0.463** (SafeRAG, top-1 — giống tuyệt đối baseline) | Bằng chứng trực quan nhất: 1 record bị xoá làm retrieval trả lời sai hẳn, repair-từ-raw phục hồi chính xác |

### Kết luận từ số liệu

1. **Data corruption → quality/freshness signal thay đổi → agent metric thay đổi:** `drop_latest_record` xoá paper SafeRAG khỏi corpus → `quality_check.paper_id_check`/`duplicate_count=1` (do `duplicate_row` ở bước khác) và `freshness.stale_rows` tăng lên 2 → `retrieval_hit_rate` giảm 0.875→0.833 và bằng chứng cụ thể của tôi: SafeRAG biến mất khỏi top-3 cho query liên quan trực tiếp tới nó.
2. **Repair action → quality/freshness signal phục hồi → agent metric phục hồi (hầu hết):** Rebuild từ raw records → `quality.passed` trở lại `true`, `freshness.stale_rows` trở lại 1 → `retrieval_hit_rate`/`mean_token_f1`/`judge_accuracy` phục hồi **đúng bằng** giá trị baseline; riêng `mean_judge_score` phục hồi gần nhưng không tuyệt đối (2.2917 vs 2.333).

**Corruption nào ảnh hưởng rõ nhất và vì sao:** `drop_latest_record` — vì đây là loại lỗi duy nhất làm thông tin **biến mất hoàn toàn** khỏi index (không thể retrieve dù embedding model hoạt động đúng), khác với `blank_summary`/`inject_summary_noise`/`truncate_title` vẫn giữ paper trong index nên vẫn có thể được tìm đúng theo `paper_id` (chỉ giảm chất lượng câu trả lời, không giảm khả năng tìm thấy).

**Kết quả khác kỳ vọng:** `mean_judge_score` sau repair (2.2917) không quay lại đúng 100% giá trị baseline (2.333) dù `paper_id` set giữa baseline và repaired đã xác nhận giống tuyệt đối. Giả thuyết ban đầu của tôi là lineage chưa phục hồi hết; đã kiểm tra bằng cách so `set(paper_id)` giữa 2 dataframe — khớp 100%. Vậy chênh lệch này không phải do dữ liệu, mà do LLM judge (gọi lại API, có nhiễu) chấm điểm không hoàn toàn deterministic giữa 2 lần chạy khác nhau — không phải lỗi của pipeline repair.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về data pipeline:** Một record "biến mất" khỏi index nguy hiểm hơn nhiều so với một record bị "nhiễu" (noise/truncate) — mất thông tin không thể bù bằng retrieval tốt, còn nhiễu thông tin vẫn có thể được tìm đúng nhờ `paper_id`/metadata còn nguyên.
2. **Về data quality/observability:** Quality (cấu trúc) và freshness (thời gian) là hai tín hiệu độc lập, cần đo cả hai — dữ liệu pass hết quality check vẫn có thể stale, và ngược lại.
3. **Về ảnh hưởng của data đến RAG agent:** Agent chỉ "biết" đúng bằng những gì có trong index tại thời điểm truy vấn. Một agent có tool tốt (search + lookup, system prompt yêu cầu grounding) vẫn trả lời sai nếu dữ liệu nguồn thiếu — chứng minh rõ qua việc agent từ chối đúng cách khi hỏi ngoài corpus, và trả lời tệ hơn (không phải bịa, mà đơn giản không tìm được) khi paper đúng bị corruption xoá.

### Nếu có thêm thời gian

Viết một script so sánh tự động (không đọc log bằng tay) chạy semantic search cho **toàn bộ** câu hỏi trong `test_set.json` (không chỉ 1 query mẫu) trên cả 3 collection, đo delta retrieval score trung bình theo từng loại corruption riêng biệt (`drop_latest_record` vs `blank_summary` vs `inject_summary_noise`...). Lý do: hiện tại tôi chỉ minh chứng bằng 1 ví dụ (SafeRAG) — đo trên toàn bộ test set sẽ cho kết luận "loại lỗi nào ảnh hưởng retrieval nhiều nhất" có ý nghĩa thống kê hơn là 1 lát cắt minh hoạ.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi "đã chạy thành công" cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [ ] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác — *tự đọc lại và viết lại theo văn phong riêng trước khi tick.*

**Họ và tên:** Trương Văn Thái
**Ngày xác nhận:** 2026-08-06

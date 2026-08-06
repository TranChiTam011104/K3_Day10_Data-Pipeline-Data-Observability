# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | HÀ HOÀNG TUẤN HÙNG             |
| MSSV               | 2A202601629                    |
| Khóa/Lớp         | K3             |
| Tên nhóm         | B3-1     |
| Vai trò chính    | Ingestion người phụ trách                 |
| Repository         | |
| Ngày hoàn thành | 2026-08-06               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| API Fetching (Crossref) | `src/ingestion/crossref.py` (hàm `fetch_source_records`) | Query parameters, `Settings` | List các JSON object từ API | Hoàn thành |
| Data parsing (Raw) | `src/ingestion/crossref.py` (hàm `parse_crossref_payload`) | JSON response gốc | List các object `PaperRecord` hợp lệ | Hoàn thành |
| Data Lineage (Snapshot) | `src/ingestion/crossref.py` (hàm `load_raw_records`) | Đường dẫn file raw snapshot | List các object `PaperRecord` để khôi phục | Hoàn thành |

Chỉ nhận ownership cho phần bạn trực tiếp thực hiện. Liên hệ rõ phần việc của bạn với đầu vào, đầu ra và các thành viên phụ thuộc vào phần đó.

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| [Debug/tích hợp/tài liệu] | [Tên hoặc module] | [Kết quả và bằng chứng] |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Xây dựng Ingestion Pipeline | `src/ingestion/crossref.py` | Tạo thành công file `crossref_records.json` | Chạy lệnh `uv run python script/run_role3_data_flow.py` hoặc xem file raw |
| Thiết lập Data Lineage Snapshot | `checkpoint_2_lineage_report.md` | Báo cáo minh chứng file raw có đủ khả năng track ngược dữ liệu | Check log hoặc file `checkpoint_2_lineage_report.md` |
| Hỗ trợ cấu hình bảo mật Git | `.gitignore`, file `.env` | File `.env` chứa API Key không lọt vào hệ thống Git tracking | Lệnh `git ls-files --error-unmatch .env` (báo lỗi là an toàn) |
| Cập nhật đường dẫn tĩnh | `papers_embeddings.json`, config | Fix lỗi `persist_path` trỏ sai đường dẫn sang máy khác để ChromaDB chạy được | Kiểm tra trường `persist_path` trong file index JSON |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:

Artifact quan trọng nhất là file `data/raw/crossref_records.json`. Nó đóng vai trò là "Single Source of Truth" (Snapshot tĩnh) chứa dữ liệu nguyên bản chưa qua chỉnh sửa, cho phép quá trình Repair của Role 3/4 lấy lại dữ liệu sạch 100% thay vì phải crawl lại từ đầu.

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết

Pipeline cần một nguồn dữ liệu ban đầu vững chắc (Crossref API) và phải chịu đựng được lỗi giới hạn truy cập (rate limit - HTTP 429/503). Quan trọng hơn, cần lưu trữ một phiên bản Raw Snapshot để đề phòng bất trắc hoặc sai sót ở các khâu làm sạch (Cleaning/Role 3), giúp hệ thống có thể rollback khôi phục lại dữ liệu gốc.

### Cách triển khai

- Sử dụng thư viện `httpx` để kết nối API và thư viện `tenacity` để cấu hình Retry/Backoff (tự động thử lại khi gặp lỗi 429/503).
- Ánh xạ JSON payload phức tạp của Crossref (có nested objects) về dạng schema đơn giản `PaperRecord`.
- Lưu trữ 1 bản `crossref_records.json` dạng snapshot, đi kèm 1 cờ `REFRESH_SOURCE=false` trong file `.env` để "đóng băng" data, giữ vững Baseline cho toàn bộ hệ thống.
- Xây dựng hàm `load_raw_records()` để phục vụ chuyên biệt cho việc Repair khôi phục từ file tĩnh.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | Tham số Settings (URLs, API limit) và Query từ Crossref |
| Output                         | Array của `PaperRecord` (có các trường bắt buộc như `paper_id`, `title`, `summary`) |
| Module phụ thuộc             | `core.config.Settings` để cấu hình timeout và paths |
| Module sử dụng output        | `ingestion.cleaning` (Role 3) sẽ sử dụng Dataframe được parse từ module Ingestion |
| Điều kiện lỗi cần xử lý | Bắn exception hoặc Retry khi gặp HTTP 429 (Too many requests) / 503 (Service Unavailable) / 500. Dữ liệu response thiếu `summary` hoặc `title` thì để trống để Cleaning lo liệu. |

### Cách xác minh

```bash
uv run python script/run_role3_data_flow.py
```

- **Kết quả mong đợi:** Download thành công 24 records, không gặp crash về rate limit, và file `data/raw/crossref_records.json` được tạo thành công với cấu trúc rõ ràng.
- **Kết quả thực tế:** 24 records đã được lưu. Khi chạy `corruption_flow.py`, hàm `load_raw_records` cũng hoạt động đúng để khôi phục lại Baseline.
- **Artifact/log:** `data/raw/crossref_records.json`, `checkpoint_5_report.md`

## 5. Một quyết định kỹ thuật quan trọng

- **Bối cảnh:** Cần quy định cách tiếp cận để mô phỏng tính năng "Phục hồi dữ liệu" (Repair Phase).
- **Các phương án đã cân nhắc:** (1) Fetch lại data từ API Crossref mỗi khi repair; (2) Lưu một file JSON tĩnh làm Raw Snapshot tại local làm nguồn tin cậy tuyệt đối.
- **Phương án đã chọn:** Chọn phương án 2 (Raw Snapshot & Lineage).
- **Lý do:** Trade-off về tính đúng đắn (correctness) và reproducibility (khả năng tái lập). Gọi API nhiều lần có thể trả về tập dữ liệu khác nhau theo thời gian thực, dẫn đến các metric Evaluator bị hỏng và không thể so sánh Baseline-Corrupted-Repaired một cách công bằng (Apples-to-Apples).
- **Bằng chứng quyết định phù hợp:** Đã chứng minh bằng việc truy vết record `10.47576/2949-1894.2026.7.7.023` (bị corrupt đi) nhưng phục hồi lại được nguyên trạng 100% khi đọc từ Raw Data tĩnh ở Repaired phase.

## 6. Một lỗi hoặc blocker đã xử lý

- **Triệu chứng/lỗi nguyên văn:** ChromaDB báo lỗi `Invalid persist_path` hoặc Exception khi nạp Collection vì đường dẫn trỏ đến ổ đĩa của tác giả cũ (`D:\VinAI\CodeLabs...`).
- **Lệnh hoặc bước tái hiện:** Khi RAG Agent chạy retrieval để query embedding.
- **Nguyên nhân gốc:** Trường `persist_path` bị hardcode lưu cứng bên trong các file JSON của embedding metadata (ví dụ `papers_embeddings.json`).
- **Cách xử lý:** Viết script Python tự động parse JSON và cập nhật trường `persist_path` bằng đường dẫn Absolute Path thật của workspace đang chạy code (biến `settings.paths.chroma_dir`).
- **Cách xác minh sau khi sửa:** Chạy `uv run python script/run_role3_data_flow.py` hoặc luồng RAG trả về kết quả không lỗi.
- **Điều học được:** Tránh hardcode absolute path vào trong Git, nhất là ở các config file, vì môi trường execution của từng dev là khác nhau.

Nếu chưa xử lý xong:

- **Phạm vi bị ảnh hưởng:** [Module/artifact.]
- **Những gì đã loại trừ:** [Các giả thuyết đã kiểm tra.]
- **Bước tiếp theo:** [Hành động có thể kiểm chứng.]

## 7. Hiểu biết về luồng end-to-end

Giải thích ngắn gọn bằng lời của bạn:

1. Dữ liệu đi từ Crossref đến vector index như thế nào?
2. Evaluation set và ground-truth document IDs dùng để đo retrieval/answer quality ra sao?
3. Quality checks khác freshness monitoring ở điểm nào trong bài lab?
4. Vì sao phải dùng cùng test set cho baseline, corrupted và repaired?
5. Repair được xem là thành công dựa trên artifact và metric nào?

**Câu trả lời:**

1. Từ Crossref, raw JSON được parse thành `PaperRecord`, lưu snapshot raw. Sau đó qua Role 3 (Cleaning) để gỡ bỏ HTML/tạp âm rồi lưu thành file Clean. Role 4 sẽ mang file Clean đi chunking và tạo Embeddings lưu xuống ChromaDB, ghi lại index file.
2. Evaluation set chứa các câu hỏi tương ứng với một ground-truth doc IDs cụ thể. Evaluator sẽ đo lường xem phần Retrieval có bốc trúng Doc ID đó không (Hit Rate) và so sánh Answer được sinh ra với Answer Ground Truth (LLM-as-a-Judge, BERTScore/Token F1).
3. Freshness đo lường độ mới (tuổi thọ) của data so với lúc được ingest, trong khi Quality check tập trung vào completeness (có trống summary không), validity (format URL đúng không), uniqueness (trùng lặp).
4. Phải dùng chung test set để tạo điều kiện kiểm soát (controlled experiment). Nếu đổi test set, ta sẽ không biết sự chênh lệch của metric (ví dụ giảm từ 8.0 xuống 4.0) là do bộ câu hỏi khó hơn hay là do Data bị Corrupted. 
5. Repair thành công nếu tập tin `papers_clean_repaired.json` có số lượng (count) và metadata cấu trúc giống hệt (match) với tập tin baseline lúc ban đầu, kéo theo đó là các metric LLM Retrieval cũng phải quay lại (phục hồi) mức điểm gốc của Baseline.

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |    0.875 |       [ ] |      [ ] | Hit rate rất cao ở trạng thái data sạch (Baseline). Mất đi data tốt (Corrupted) sẽ khiến RAG lấy nhầm document. |
| `mean_token_f1`      |    0.299 |       [ ] |      [ ] | Thể hiện mức độ trùng lặp từ ngữ giữa model và ground truth. |
| `judge_accuracy`     |    0.250 |       [ ] |      [ ] | Thể hiện LLM-as-a-judge nhận định mức độ đúng sai khắt khe. |
| `mean_judge_score`   |    2.333 |       [ ] |      [ ] | Thang điểm đánh giá chung của RAG response ở baseline tương đối khiêm tốn. |
| Quality checks         |      OK  |  Cảnh báo |      OK  | Lỗi Completeness ở Corrupted do mất mát abstract (Summary). |
| Freshness status       |      Tốt | Trễ hẹn   |      Tốt | Date bị dời về quá khứ trong Corrupted, báo hiệu data out-of-date. |

### Kết luận từ số liệu

Hoàn thành hai chuỗi nguyên nhân–bằng chứng sau:

1. [Làm rỗng trường `summary` (Corrupt)] → [Completeness của Quality signal giảm] → [Hit Rate và Judge Score của RAG Agent giảm sút].
2. [Sử dụng Raw Lineage để khôi phục] → [Quality/Freshness signal phục hồi về 100%] → [Agent metric phục hồi nguyên trạng].

Corruption nào ảnh hưởng rõ nhất và vì sao?

Việc làm rỗng (Empty) hoặc xóa (Drop) trường `summary` hoặc bài báo là có sát thương cao nhất. Bởi vì `summary` chính là content chính để Chunking + Embedding Indexing. Không có summary, Retrieval Engine không lấy được ngữ cảnh, và RAG Agent sẽ bị thiếu kiến thức trầm trọng để trả lời đúng.

Kết quả nào khác với kỳ vọng ban đầu?

Cứ nghĩ LLM (Gemini 2.5 Flash) sẽ tự "bịa" (hallucinate) ra câu trả lời khi thiếu data, nhưng thực tế LLM-as-a-judge thường từ chối trả lời (Empty response) với score rất thấp (như 1.0) khi không tìm thấy thông tin phù hợp, cho thấy cơ chế prompt bảo vệ chống hallucination khá tốt.

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất

1. **Về Data Pipeline:** Luôn phải có Raw Snapshot/Lineage để đảm bảo tính bất biến làm bàn đạp khôi phục, chứ không bao giờ tin cậy gọi lại API trực tiếp khi đã qua công đoạn Ingestion.
2. **Về Data Quality:** Data Quality (đặc biệt là Completeness) quyết định 100% sự sống còn của Vector Database. Missing content = Mù thông tin đối với hệ thống Search.
3. **Về RAG Agent:** Agent tốt đến mấy cũng chỉ là cái "ống loa" khuếch đại những gì nó lấy được. Rác vào (Corrupted data) thì rác ra (Garbage In, Garbage Out).

### Nếu có thêm thời gian

Tôi sẽ thiết lập hệ thống Delta Ingestion: Chỉ pull về từ Crossref API những bài báo (records) mới chưa có trong Raw Snapshot thay vì pull toàn bộ, giúp tối ưu chi phí API calls và tốc độ xử lý của Ingestion.

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** HÀ HOÀNG TUẤN HÙNG
**Ngày xác nhận:** 2026-08-06

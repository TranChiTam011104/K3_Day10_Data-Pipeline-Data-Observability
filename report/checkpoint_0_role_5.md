# Thiết Kế Chi Tiết Checkpoint 0 — Vai Trò 5: Evaluation & Observability

Tài liệu này ghi nhận kết quả nghiên cứu, phân tích mã nguồn và thiết kế chi tiết các thành phần **Đánh giá RAG (Evaluation)** và **Giám sát chất lượng dữ liệu (Data Observability)** thuộc vai trò 5 trong dự án.

---

## I. Phân Tích Cơ Chế Hoạt Động Của Testset, QA và Metrics

Sau khi đọc và phân tích các file [testset.py](file:///d:/laragon/www/Day10Vinuni/K3_Day10_Data-Pipeline-Data-Observability/src/evaluation/testset.py), [qa.py](file:///d:/laragon/www/Day10Vinuni/K3_Day10_Data-Pipeline-Data-Observability/src/retrieval/qa.py), và [metrics.py](file:///d:/laragon/www/Day10Vinuni/K3_Day10_Data-Pipeline-Data-Observability/src/evaluation/metrics.py), cấu trúc và quy trình hoạt động được xác định như sau:

### 1. Cơ Chế Trích Xuất Câu Trả Lời (`qa.py`)
Hàm `_extract_answer(question: str, top_result: SearchResult)` sử dụng cơ chế so khớp từ khóa (keyword matching) trong câu hỏi để quyết định trường thông tin nào từ metadata của tài liệu sẽ được trả về làm câu trả lời tham chiếu hoặc dự đoán:

*   **Tác giả (Authors):** Khi câu hỏi chứa cụm từ `"who authored"` hoặc `"list the authors"`, hệ thống trả về trường `metadata["authors_joined"]`.
*   **Ngày xuất bản (Published Date):** Khi câu hỏi chứa cụm từ `"when was"`, `"publication date"`, hoặc `"published on"`, hệ thống trả về trường `metadata["published"]`.
*   **Danh mục/Chủ đề (Categories):** Khi câu hỏi chứa cụm từ `"what categories"`, hệ thống trả về trường `metadata["categories_joined"]`.
*   **Tóm tắt (Summary):** Đối với bất kỳ trường hợp nào khác, hệ thống sẽ trả về **câu đầu tiên** của phần tóm tắt (`first_sentence(metadata["summary"])`).

> [!IMPORTANT]  
> Để kết quả đánh giá là chính xác và RAG agent có thể trả lời đúng, bộ câu hỏi trong Testset **bắt buộc** phải được thiết kế tuân thủ nghiêm ngặt các từ khóa trên.

### 2. Các Chỉ Số Đánh Giá (`metrics.py`)
Mỗi câu hỏi trong Testset sau khi đi qua pipeline sẽ được đo đạc bởi các chỉ số sau:
*   `retrieval_hit_rate`: Đo lường tỷ lệ các tài liệu được RAG truy xuất (`retrieved_doc_ids`) chứa ít nhất một tài liệu chính xác nằm trong danh sách ground truth (`ground_truth_doc_ids`).
*   `mean_token_f1`: Điểm F1 dựa trên mức độ trùng khớp các từ (token) giữa câu trả lời của mô hình và câu trả lời chuẩn (ground truth).
*   `judge_accuracy`: Tỷ lệ phần trăm câu trả lời được LLM Evaluator (hoặc bộ lọc fallback dựa trên F1) đánh giá là đúng về mặt nội dung (`correct = True`).
*   `mean_judge_score`: Điểm đánh giá trung bình từ LLM Evaluator theo thang điểm từ 1 đến 5.
*   **Ragas Metrics (Tùy chọn):** Nếu cấu hình `RUN_RAGAS=1`, hệ thống sẽ đo thêm các chỉ số nâng cao: *Answer Relevancy*, *Context Precision*, *Context Recall*, và *Faithfulness*.

---

## II. Thiết Kế Bộ Câu Hỏi Đánh Giá (Evaluation Set)

### 1. Nguyên Tắc Thiết Kế
*   **Tính Trung Thực:** Câu hỏi phải được sinh ra dựa trên dữ liệu thật thu thập từ Crossref (không tự bịa đặt nội dung).
*   **Tính Nhất Quán ID:** Trường `ground_truth_doc_ids` phải chứa chính xác `paper_id` (được chuẩn hóa từ clean dataset) của tài liệu cung cấp thông tin.
*   **Phân Loại Rõ Ràng:** Mỗi câu hỏi phải thuộc 1 trong 4 loại (`summary`, `authors`, `date`, `categories`).

### 2. Mẫu Thiết Kế Câu Hỏi (Question Templates)
Dựa vào cơ chế hoạt động của `qa.py`, chúng tôi thiết kế các mẫu câu hỏi tương ứng với từng loại như sau:

| Loại câu hỏi (`question_type`) | Từ khóa bắt buộc | Định dạng câu hỏi mẫu | Trường dữ liệu Ground Truth tương ứng |
| :--- | :--- | :--- | :--- |
| **authors** | `"who authored"` | `Who authored the paper '{title}'?` | `authors_joined` |
| **date** | `"published on"` | `When was the paper '{title}' published?` hoặc `What is the publication date of the paper '{title}'?` | `published` |
| **categories** | `"what categories"` | `What categories does the paper '{title}' belong to?` | `categories_joined` |
| **summary** | *Không trùng từ khóa trên* | `Summarize the paper '{title}'.` | `first_sentence(summary)` |

---

## III. Định Nghĩa Các Tín Hiệu Giám Sát Dữ Liệu (Observability Signals)

Nhằm theo dõi biến động chất lượng dữ liệu giữa các pha (Baseline, Corrupted, Repaired), chúng tôi thiết lập bộ chỉ số giám sát sau:

### 1. Data Quality Signals (`quality.py`)
*   `row_count`: Số lượng bản ghi trong dataset sạch. Biến động bất thường (giảm mạnh) ở pha Corrupted cho thấy dữ liệu bị mất mát hoặc drop quá đà.
*   `null_rate`: Tỷ lệ các trường quan trọng (`title`, `summary`, `authors_joined`) bị bỏ trống. Tín hiệu này sẽ tăng vọt nếu chạy kịch bản làm trống summary/authors.
*   `duplicate_rate`: Số lượng bản ghi có `paper_id` trùng lặp hoặc trùng `text_for_embedding`.
*   `valid_paper_id_rate`: Tỷ lệ các bản ghi có `paper_id` hợp lệ (không rỗng, đúng định dạng stable id).

### 2. Freshness Signals (`freshness`)
*   `latest_published`: Ngày xuất bản gần nhất trong dataset để xác định tính cập nhật của dữ liệu.
*   `oldest_published`: Ngày xuất bản xa nhất trong dataset.
*   `stale_rows_count`: Số lượng các bài báo có thời gian xuất bản vượt quá ngưỡng quy định (ví dụ: `age_days > 180`).
*   `is_fresh`: Trạng thái Boolean xác định toàn bộ hệ thống dữ liệu có đảm bảo độ tươi mới hay không.

---

## IV. Kế Hoạch Lưu Trữ Artifacts

Bảng dưới đây thống nhất đường dẫn lưu trữ các artifacts thuộc phạm vi giám sát và đánh giá, đảm bảo tính tách biệt và không ghi đè chéo:

| Tên Artifact | Pha Dữ Liệu | Đường Dẫn Lưu Trữ | Mục Đích Sử Dụng |
| :--- | :--- | :--- | :--- |
| **test_set.json** | Dùng chung | `data/eval/test_set.json` | Bộ câu hỏi cố định dùng cho cả 3 pha đánh giá. |
| **baseline_answers.json** | Baseline | `data/results/baseline_answers.json` | Câu trả lời của Agent ở pha dữ liệu sạch. |
| **baseline_metrics.json** | Baseline | `data/results/baseline_metrics.json` | Điểm số chất lượng RAG ở pha baseline. |
| **freshness_report.json** | Giám sát | `data/quality/freshness_report.json` | Báo cáo độ tươi mới dữ liệu của các pha. |
| **phase1_report.md** | Báo cáo | `data/reports/phase1_report.md` | Báo cáo tổng hợp chất lượng pha Baseline. |
| **corrupted_answers.json** | Corrupted | `data/results/corrupted_answers.json` | Câu trả lời của Agent ở pha dữ liệu lỗi. |
| **corrupted_metrics.json** | Corrupted | `data/results/corrupted_metrics.json` | Điểm số chất lượng RAG ở pha dữ liệu lỗi. |
| **repaired_answers.json** | Repaired | `data/results/repaired_answers.json` | Câu trả lời của Agent ở pha dữ liệu đã sửa. |
| **repaired_metrics.json** | Repaired | `data/results/repaired_metrics.json` | Điểm số chất lượng RAG ở pha phục hồi. |
| **corruption_report.md** | Báo cáo | `data/reports/corruption_report.md` | Báo cáo so sánh chi tiết Baseline - Corrupted - Repaired. |

---

## V. Phác Thảo Báo Cáo So Sánh (Impact Analysis Outline)

Báo cáo cuối cùng (`corruption_report.md`) sẽ làm nổi bật tác động của chất lượng dữ liệu tới RAG Agent theo cấu trúc logic sau:

### 1. Phân Tích Tác Động Dự Kiến (Hypothesis)
*   **Khi bị làm trống summary (Blank summary):** Tín hiệu `null_rate` tăng. Điểm `mean_token_f1` và `judge_accuracy` cho câu hỏi dạng `summary` sẽ giảm nghiêm trọng do nội dung nhúng không chứa thông tin hữu ích.
*   **Khi dữ liệu bị cũ (Stale dates):** Tín hiệu `stale_rows_count` tăng, `is_fresh` chuyển sang `False`. RAG Agent sẽ trả về thông tin lỗi thời cho các câu hỏi về thời gian/ngày tháng.
*   **Khi trùng lặp dữ liệu (Duplicate rows):** Tín hiệu `duplicate_rate` tăng. Làm loãng kết quả truy xuất vector (Retrieval noise), tăng chi phí token do nạp tài liệu trùng vào ngữ cảnh.

### 2. Cấu Trúc Báo Cáo So Sánh
1.  **Executive Summary:** Đánh giá chung về khả năng tự phục hồi của pipeline.
2.  **Data Quality Evolution:** Bảng so sánh 3 trạng thái dữ liệu (Dòng dữ liệu, Tỷ lệ lỗi, Tỷ lệ trùng lặp, Độ tươi mới).
3.  **RAG Performance Comparison:** Bảng delta các chỉ số `retrieval_hit_rate`, `mean_token_f1`, `judge_accuracy` qua 3 pha.
4.  **Key Findings & Evidence:** Chỉ ra các ví dụ cụ thể về việc dữ liệu lỗi làm Agent trả lời sai và cách repair đã khắc phục được lỗi đó như thế nào.

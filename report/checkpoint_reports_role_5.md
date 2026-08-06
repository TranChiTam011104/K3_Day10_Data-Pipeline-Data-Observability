# Tổng Hợp Thiết Kế & Kết Quả Từng Mốc — Vai Trò 5: Evaluation & Observability

Tài liệu này tổng hợp toàn bộ thiết kế, phân tích mã nguồn, kế hoạch artifacts và kết quả tự kiểm thử của **Vai trò 5 (Evaluation & Observability)** từ Checkpoint 0 đến Checkpoint 2.

---

## 📑 Mốc 0: Khởi Động & Thiết Kế Đánh Giá

### 1. Phân Tích Cơ Chế Trích Xuất Câu Trả Lời (`qa.py`)
Hàm `_extract_answer` trong `qa.py` dùng phương pháp so khớp từ khoá để trả lời:
*   **Tác giả (Authors):** Chứa `"who authored"` hoặc `"list the authors"` -> trả về `metadata["authors_joined"]`.
*   **Ngày xuất bản (Published Date):** Chứa `"when was"`, `"publication date"`, hoặc `"published on"` -> trả về `metadata["published"]`.
*   **Danh mục (Categories):** Chứa `"what categories"` -> trả về `metadata["categories_joined"]`.
*   **Tóm tắt (Summary):** Mặc định -> trả về câu đầu tiên `first_sentence(metadata["summary"])`.

### 2. Thiết Kế Bộ Câu Hỏi Mẫu (Evaluation Set)
Bộ câu hỏi trong Test Set được sinh ra dựa trên dữ liệu thật và các từ khóa bắt buộc nêu trên. Trường `ground_truth_doc_ids` được ánh xạ trực tiếp với `paper_id` của document trong clean dataset (thường là DOI).

### 3. Kế Hoạch Lưu Trữ Artifacts
*   `data/eval/test_set.json`: Bộ câu hỏi kiểm thử dùng chung cho cả 3 trạng thái.
*   `data/results/baseline_metrics.json` & `data/results/baseline_answers.json`: Kết quả đánh giá pha Baseline.
*   `data/quality/freshness_report.json` & `data/quality/*_quality.json`: Báo cáo giám sát chất lượng và độ tươi mới dữ liệu.
*   `data/reports/phase1_report.md`: Báo cáo tổng hợp pha Baseline.

---

## 📑 Mốc 1: Quy Tắc Giám Sát Chất Lượng Dữ Liệu (`quality.py`)

Chúng tôi đã thiết lập 5 tín hiệu giám sát để kịp thời phát hiện biến động chất lượng dữ liệu:
1.  **Row Count Check:** Xác minh số dòng dữ liệu sạch phải `> 0`.
2.  **Paper ID Completeness & Uniqueness:** Đảm bảo không có bản ghi nào bị rỗng hoặc trùng lặp khoá chính `paper_id`.
3.  **Title Completeness:** Đảm bảo tiêu đề không bị rỗng.
4.  **Summary Completeness & Length:** Cảnh báo nếu tóm tắt bị rỗng hoặc ngắn hơn 20 ký tự.
5.  **Freshness Check:** Kiểm tra xem số lượng bài báo quá hạn (được xuất bản lâu hơn `settings.freshness_threshold_days` - 180 ngày) có vượt ngưỡng hay không.

Các kết quả kiểm thử chất lượng và độ tươi được xuất thành các file JSON thực tế vào thư mục `data/quality/`.

---

## 📑 Mốc 2: Lập Trình Sinh Test Set Tự Động (`testset.py`)

Hàm `build_test_set` trong `testset.py` được lập trình để:
1.  Tự động chọn ra tối đa 8 bài báo đại diện từ clean dataset để tạo Test Set.
2.  Đối với mỗi bài báo, tự động tạo 4 loại câu hỏi (authors, date, summary, categories) bám sát các từ khóa bắt buộc của `qa.py`.
3.  Đảm bảo `paper_id` từ clean dataframe được đồng bộ sang `ground_truth_doc_ids` của câu hỏi kiểm thử. Điều này đảm bảo tính nhất quán định danh, giúp phép đo `retrieval_hit_rate` hoạt động chính xác (không bị lệch ID giữa cơ sở dữ liệu vector ChromaDB và bộ test set).
4.  Xử lý loại bỏ triệt để các giá trị `NaN` trong dataframe (ví dụ: khi cột `categories_joined` bị rỗng) trước khi ghi file, tránh lỗi cú pháp JSON chứa token `NaN` bất hợp lệ.

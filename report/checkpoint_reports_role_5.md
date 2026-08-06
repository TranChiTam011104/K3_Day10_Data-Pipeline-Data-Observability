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

---

## 📑 Mốc 4: Kịch Bản Làm Bẩn Dữ Liệu & Dự Báo Thay Đổi Tín Hiệu (Break/Scenario Plan)

Trong thời gian nghỉ giữa các mốc, chúng tôi đã phân tích kịch bản làm bẩn dữ liệu (`corruption_flow`) và đưa ra các dự báo cụ thể về sự thay đổi của các tín hiệu chất lượng và hiệu năng của RAG Agent.

### 1. Chi Tiết Kịch Bản Làm Bẩn (Corruption Scenario)
Hệ thống áp dụng 6 loại lỗi dữ liệu có chủ đích lên tập clean dataframe:
*   `drop_latest_record`: Xóa bài báo mới xuất bản nhất.
*   `blank_summary`: Làm rỗng phần tóm tắt của 1 bài báo.
*   `inject_summary_noise`: Bơm các chuỗi từ vô nghĩa (`[CORRUPTED_NOISE]...`) vào tóm tắt của 1 bài báo.
*   `truncate_title`: Cắt ngắn tiêu đề của 1 bài báo chỉ giữ lại 1/3 độ dài gốc.
*   `stale_published_date`: Dịch ngày xuất bản lùi lại 10 năm về trước.
*   `duplicate_row`: Nhân đôi một dòng bài báo trong tập dữ liệu.

### 2. Dự Báo Thay Đổi Tín Hiệu Chất Lượng (Signal Predictions)
Chúng tôi dự báo các tín hiệu giám sát tại `quality.py` sẽ thay đổi như sau:
*   **Row Count:** Không đổi (vẫn là 24 dòng) vì giảm đi 1 dòng (drop_latest) và tăng thêm 1 dòng (duplicate_row).
*   **Paper ID Completeness & Uniqueness:** Sẽ chuyển từ **PASS ✅** sang **FAILED ❌** vì phát hiện 1 bản ghi trùng lặp khóa chính `paper_id`.
*   **Summary Completeness & Length:** Sẽ chuyển từ **PASS ✅** sang **FAILED ❌** vì phát hiện 1 bản ghi bị rỗng phần tóm tắt (`blank_summary`).
*   **Freshness Check (Độ tươi mới):** Số lượng bài báo bị quá hạn (`stale_count`) sẽ tăng từ 1 lên thành 2 dòng (do bản ghi bị đổi ngày lùi 10 năm).

### 3. Dự Báo Tác Động Tới RAG Agent (Agent Performance Predictions)
Chúng tôi dự báo các chỉ số đánh giá Agent sẽ bị sụt giảm:
*   **Retrieval Hit Rate:** Giảm nhẹ vì bài báo bị drop hoặc bị đổi tiêu đề sẽ khó được tìm thấy bởi vector search.
*   **Mean Token F1 & Judge Score:** Giảm mạnh đối với các câu hỏi liên quan trực tiếp đến các tài liệu bị làm bẩn:
    *   Câu hỏi tóm tắt trên tài liệu bị làm rỗng (`blank_summary`) hoặc nhiễu (`inject_summary_noise`) sẽ cho ra câu trả lời sai lệch hoàn toàn.
    *   Câu hỏi về ngày xuất bản trên tài liệu bị stale (`stale_published_date`) sẽ trả về ngày đã bị thay đổi (lệch 10 năm), gây mất điểm hoàn toàn.

---

## 📑 Mốc 5: Kết Quả Đo Lường Trên Dữ Liệu Bị Làm Bẩn (Corrupted Evaluation)

Sau khi chạy tiến trình làm bẩn dữ liệu thực tế (`python script/run_corruption_flow.py`), chúng tôi ghi nhận các biến động thực tế khớp hoàn toàn với dự báo ban đầu:

### 1. Kết Quả Giám Sát Chất Lượng (Observability Signals)
*   **Quality Gates:** Sụt giảm từ **4/5 đạt** xuống chỉ còn **2/5 đạt**.
*   **Paper ID Check:** **FAILED ❌** (Phát hiện 1 bản ghi trùng lặp khóa chính - do `duplicate_row`).
*   **Summary Check:** **FAILED ❌** (Phát hiện 1 bản ghi bị rỗng tóm tắt - do `blank_summary`).
*   **Freshness Check:** **FAILED ❌** (Số lượng bản ghi stale tăng từ 1 lên thành 2 dòng - do `stale_published_date`).

### 2. Sự Sụt Giảm Hiệu Năng RAG Agent
*   **Retrieval Hit Rate:** Giảm từ **87.5%** xuống còn **83.3%** ($\Delta = -4.2\%$).
*   **Mean Token F1:** Giảm từ **29.9%** xuống còn **25.8%** ($\Delta = -4.1\%$).
*   **Judge Accuracy:** Giảm từ **25.0%** xuống còn **20.8%** ($\Delta = -4.2\%$).
*   **Mean Judge Score (1-5):** Giảm từ **2.333** xuống còn **2.125** ($\Delta = -0.208$).

### 3. Phân Tích Case Study Thực Tế (Evidence Case)
*   **Câu hỏi:** `Who authored the paper titled 'SafeRAG: A Large-Language-Model-Based Multistage Retrieval-A...'?` (Mã câu hỏi: `q_1`)
*   **So sánh Baseline vs. Corrupted:**
    *   *Tại pha Baseline:* Hệ thống truy xuất được tài liệu gốc `10.2118/234689-pa`, Agent trả lời chính xác tác giả: `"Qianwen Cao, Chiyu Zhang, Junxiong Ning, Gongru Li"` (Đạt 5/5 điểm).
    *   *Tại pha Corrupted:* Do thuật toán làm bẩn áp dụng quy tắc `drop_latest_record` đã xóa tài liệu này khỏi cơ sở dữ liệu. Kết quả là hệ thống không thể truy xuất tài liệu đó (`retrieval_hit = False`). Agent buộc phải trả lời dựa trên tài liệu về Speculative RAG khác, đưa ra tác giả sai lệch hoàn toàn: `"Dr. Sumalatha P, Manoj Kumar"` (Chỉ đạt 1/5 điểm).

---

## 📑 Mốc 6: Kết Quả Khôi Phục & Báo Cáo Đối Chiếu Ba Trạng Thái (Repaired & Comparison)

*   **Trạng thái:** **CHƯA BẮT ĐẦU ⏳**
*   **Kế hoạch thực hiện:**
    *   Thực hiện khôi phục dữ liệu sạch hoàn toàn từ nguồn Crossref ban đầu để loại bỏ các bản ghi bẩn.
    *   Lập chỉ mục lại cơ sở dữ liệu vector dạng `papers-repaired`.
    *   Chạy lại đánh giá Agent với bộ câu hỏi đã khóa để đo lường mức độ phục hồi của hiệu năng.
    *   Xuất báo cáo đối chiếu ba trạng thái tại file `data/reports/corruption_report.md`.

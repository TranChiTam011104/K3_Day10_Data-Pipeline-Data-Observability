# Thiết Kế Chi Tiết Checkpoint 2 — Vai Trò 5: Thiết Lập Test Set & Chuẩn Bị Baseline

Báo cáo này ghi nhận phần việc của **Vai trò 5 (Evaluation & Observability)** trong **Checkpoint 2**, tập trung vào việc tự động hóa xây dựng bộ câu hỏi đánh giá (Test Set) từ clean dataframe và cơ chế đồng bộ định danh tài liệu (`paper_id`).

---

## I. Logic Tự Động Hóa Bộ Câu Hỏi Đánh Giá (`testset.py`)

Chúng tôi đã hoàn thiện hàm `build_test_set` trong [testset.py](file:///d:/laragon/www/Day10Vinuni/K3_Day10_Data-Pipeline-Data-Observability/src/evaluation/testset.py). 

### Quy trình tạo Test Set động:
1.  **Kiểm tra tính hợp lệ đầu vào:** Đảm bảo `df` sạch không rỗng.
2.  **Lựa chọn mẫu đại diện:** Lấy tối đa 8 bài báo đầu tiên (`df.head(8)`) để đảm bảo số lượng câu hỏi kiểm thử cân bằng (khoảng 24 - 32 câu hỏi), giúp thời gian đánh giá LLM không bị quá lâu mà vẫn đảm bảo độ bao phủ.
3.  **Tự động tạo câu hỏi theo đặc tả từ khóa của `qa.py`:**
    *   **Authors (`who authored`):** `Who authored the paper '{title}'?` -> đáp án chuẩn: `authors_joined`.
    *   **Date (`published on`):** `When was the paper '{title}' published?` -> đáp án chuẩn: `published` (dạng YYYY-MM-DD).
    *   **Summary (mặc định):** `Summarize the paper '{title}'.` -> đáp án chuẩn: `first_sentence(summary)` (câu đầu tiên của abstract để khớp tuyệt đối với hàm trích xuất factual của Agent).
    *   **Categories (`what categories`):** `What categories does the paper '{title}' belong to?` -> đáp án chuẩn: `categories_joined`.

---

## II. Cơ Chế Đồng Bộ Định Danh Tài Liệu (`paper_id`)

Một trong những quy tắc quan trọng nhất của Checkpoint 2 là **đồng bộ định danh**. Chúng tôi cam kết sử dụng cột `paper_id` được chuẩn hóa từ cleaned dataset (thường là DOI của Crossref) làm `ground_truth_doc_ids` trong từng phần tử của test set:

```json
{
  "id": "q_1",
  "question_type": "authors",
  "question": "Who authored the paper 'The Age of Autonomous Agents: A Bibliometric Review of Agentic AI Architectures, Applications, and Emerging Challenges'?",
  "ground_truth": "Ben J. Weber, Clara M. Hofmann, Amara N. Okoye",
  "ground_truth_doc_ids": [
    "10.63646/kpqm1958"
  ]
}
```

*   **Tại sao không tự bịa ID?** Nếu tự sinh ID ngẫu nhiên, khi đối chiếu trong hàm `evaluate_pipeline`, các tài liệu do ChromaDB truy xuất ra (`retrieved_doc_ids` sử dụng `paper_id` từ metadata) sẽ không bao giờ khớp với ID trong test set, khiến chỉ số `retrieval_hit_rate` luôn bằng 0%.
*   **Tính Nhất Quán:** `paper_id` này đi xuyên suốt từ: **Clean CSV** -> **ChromaDB Metadata** -> **ChromaDB Documents** -> **Test Set Ground Truth** -> **Evaluation Output**.

---

## III. Chuẩn Bị Cho Pha Baseline (Checkpoint 3)
*   **Chốt Schema Test Set:** File đầu ra sẽ là `data/eval/test_set.json`.
*   **Chuẩn bị khuôn báo cáo:** Đã viết sẵn khung báo cáo `phase1_report.md` trong file [reporting.py](file:///d:/laragon/www/Day10Vinuni/K3_Day10_Data-Pipeline-Data-Observability/src/observability/reporting.py) để sẵn sàng điền số liệu thật sau khi chạy baseline ở Checkpoint 3.

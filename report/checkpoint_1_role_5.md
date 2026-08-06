# Thiết Kế Chi Tiết Checkpoint 1 — Vai Trò 5: Báo Cáo Chất Lượng & Thiết Kế Bộ Đánh Giá (Draft)

Báo cáo này ghi nhận phần việc của **Vai trò 5 (Evaluation & Observability)** trong **Checkpoint 1** bao gồm dự thảo thiết kế câu hỏi kiểm thử từ nguồn dữ liệu thật và tài liệu hóa các quy tắc chất lượng/freshness.

---

## I. Bộ Câu Hỏi Đánh Giá Dự Thảo (Draft Evaluation Set)

Dựa trên nguồn dữ liệu thô Crossref thật đã tải về tại [crossref_records.json](file:///d:/laragon/www/Day10Vinuni/K3_Day10_Data-Pipeline-Data-Observability/data/raw/crossref_records.json), chúng tôi lựa chọn 3 bài báo tiêu biểu để thiết kế bộ câu hỏi kiểm thử (đáp ứng tiêu chí không bịa đặt thông tin và gán `paper_id` chính xác):

### 1. Tài liệu 1: `10.63646/kpqm1958`
*   **Tên bài báo (Title):** `The Age of Autonomous Agents: A Bibliometric Review of Agentic AI Architectures, Applications, and Emerging Challenges`
*   **Tác giả (Authors):** `Ben J. Weber, Clara M. Hofmann, Amara N. Okoye`
*   **Ngày xuất bản (Published):** `2026-07-17`
*   **Tóm tắt (Summary):** `The rapid evolution of large language models (LLMs) has catalyzed a shift from passive AI systems...`

**Các câu hỏi thiết kế:**
1.  **Loại `authors`:**
    *   *Câu hỏi:* `Who authored the paper 'The Age of Autonomous Agents: A Bibliometric Review of Agentic AI Architectures, Applications, and Emerging Challenges'?`
    *   *Ground Truth:* `Ben J. Weber, Clara M. Hofmann, Amara N. Okoye`
2.  **Loại `date`:**
    *   *Câu hỏi:* `When was the paper 'The Age of Autonomous Agents: A Bibliometric Review of Agentic AI Architectures, Applications, and Emerging Challenges' published?`
    *   *Ground Truth:* `2026-07-17`
3.  **Loại `summary`:**
    *   *Câu hỏi:* `Summarize the paper 'The Age of Autonomous Agents: A Bibliometric Review of Agentic AI Architectures, Applications, and Emerging Challenges'.`
    *   *Ground Truth:* `The rapid evolution of large language models (LLMs) has catalyzed a shift from passive AI systems toward autonomous agentic architectures capable of reasoning, memory, tool use, and multi-agent collaboration.`

---

### 2. Tài liệu 2: `10.36227/techrxiv.177272838.89432844/v1`
*   **Tên bài báo (Title):** `A Survey of (Deep RAG) Deep Retrieval Augmented Generation and Reasoning in Large Language Models`
*   **Tác giả (Authors):** `Lihui Liu`
*   **Ngày xuất bản (Published):** `2026-03-05`
*   **Tóm tắt (Summary):** `Retrieval-Augmented Generation (RAG) has emerged as a powerful paradigm...`

**Các câu hỏi thiết kế:**
1.  **Loại `authors`:**
    *   *Câu hỏi:* `Who authored the paper 'A Survey of (Deep RAG) Deep Retrieval Augmented Generation and Reasoning in Large Language Models'?`
    *   *Ground Truth:* `Lihui Liu`
2.  **Loại `summary`:**
    *   *Câu hỏi:* `Summarize the paper 'A Survey of (Deep RAG) Deep Retrieval Augmented Generation and Reasoning in Large Language Models'.`
    *   *Ground Truth:* `Retrieval-Augmented Generation (RAG) has emerged as a powerful paradigm for combining large language models with external knowledge sources to produce accurate, context-aware, and verifiable outputs.`

---

### 3. Tài liệu 3: `10.20944/preprints202604.0339.v1`
*   **Tên bài báo (Title):** `Retrieval-Augmented Large Language Model Agents for Automated Scientific Literature Review Generation`
*   **Tác giả (Authors):** `Ruotong Wang, Nyutian Long, Shunqi Liu, Yuxi Wang, Zhen Qi, Huajun Zhang`
*   **Ngày xuất bản (Published):** `2026-04-07`

**Các câu hỏi thiết kế:**
1.  **Loại `date`:**
    *   *Câu hỏi:* `What is the publication date of the paper 'Retrieval-Augmented Large Language Model Agents for Automated Scientific Literature Review Generation'?`
    *   *Ground Truth:* `2026-04-07`

---

## II. Các Tín Hiệu Chất Lượng Dữ Liệu Đã Thiết Lập (`quality.py`)

Chúng tôi đã lập trình xong các quy tắc chất lượng dữ liệu để tự động hóa kiểm định ở pha tiếp theo:

1.  **Row Count Check:** Xác minh số bản ghi của dữ liệu sau khi làm sạch phải `> 0`.
2.  **Paper ID Completeness & Uniqueness:** Phát hiện dữ liệu thiếu hoặc trùng lặp khoá chính `paper_id`.
3.  **Title Completeness:** Đảm bảo không có bản ghi nào bị rỗng tiêu đề.
4.  **Summary Completeness & Length:** Cảnh báo các bản ghi bị rỗng phần tóm tắt hoặc phần tóm tắt quá ngắn (dưới 20 ký tự).
5.  **Freshness Check:** Đo đạc tuổi dữ liệu (`age_days`) so với cấu hình ngưỡng của dự án (`settings.freshness_threshold_days` - 180 ngày).

*Sau khi quá trình cài đặt môi trường trên máy của anh kết thúc, chúng ta sẽ chạy script xác minh để xuất các file báo cáo JSON thực tế vào thư mục `data/quality/`.*

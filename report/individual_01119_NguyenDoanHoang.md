# Member Role Report — Day 10: Data Pipeline & Data Observability

> Mỗi thành viên trong nhóm tự hoàn thành mẫu này để báo cáo đúng vai trò, phần việc và mức hiểu của mình. Không sao chép nguyên báo cáo chung hoặc báo cáo của thành viên khác. Thay nội dung trong dấu `[ ]` và xóa các dòng hướng dẫn không cần thiết trước khi nộp.

## 1. Thông tin cá nhân

| Thông tin         | Nội dung                  |
| ------------------ | -------------------------- |
| Họ và tên       | Nguyễn Doãn Hoàng             |
| MSSV               | 2A202601119                     |
| Khóa/Lớp         | K3          |
| Tên nhóm         | B3_1    |
| Vai trò chính    | Evaluation & Observability Owner (Vai trò 5) |
| Repository         | https://github.com/TranChiTam011104/K3_Day10_Data-Pipeline-Data-Observability_B3_1.git |
| Ngày hoàn thành | 2026-08-06               |

## 2. Vai trò và phạm vi công việc

### Phần việc sở hữu

| Module/deliverable | File/hàm phụ trách | Input nhận vào | Output bàn giao  | Trạng thái                                 |
| ------------------ | --------------------- | ---------------- | ----------------- | -------------------------------------------- |
| **Data Quality & Freshness Monitoring** | [quality.py](file:///d:/laragon/www/Day10Vinuni/K3_Day10_Data-Pipeline-Data-Observability/src/observability/quality.py) (`run_data_quality_checks`, `build_freshness_report`) | Cleaned Dataframe (`pd.DataFrame`), Settings | Báo cáo chất lượng `baseline_quality.json`, báo cáo độ tươi `freshness_report.json` | Hoàn thành |
| **Evaluation Test Set Generation** | [testset.py](file:///d:/laragon/www/Day10Vinuni/K3_Day10_Data-Pipeline-Data-Observability/src/evaluation/testset.py) (`build_test_set`) | Cleaned Dataframe (`pd.DataFrame`), Path đầu ra | Bộ câu hỏi kiểm thử tĩnh `test_set.json` chứa câu hỏi mẫu | Hoàn thành |
| **Orchestration Reports** | [reporting.py](file:///d:/laragon/www/Day10Vinuni/K3_Day10_Data-Pipeline-Data-Observability/src/observability/reporting.py) (`generate_phase1_report`, `generate_corruption_report`) | Ingestion Summary, RAG Metrics, Quality & Freshness reports | Báo cáo markdown pha Baseline `phase1_report.md` và so sánh đối chiếu `corruption_report.md` | Hoàn thành |

### Việc hỗ trợ ngoài phạm vi chính

| Hoạt động                         | Thành viên/module được hỗ trợ | Kết quả                    |
| ------------------------------------ | ------------------------------------ | ---------------------------- |
| **Debug & Vá lỗi Serialization** | Module Indexing / RAG Owner | Khắc phục triệt để lỗi ghi giá trị `NaN` trần vào tệp tin [papers_embeddings.json](file:///d:/laragon/www/Day10Vinuni/K3_Day10_Data-Pipeline-Data-Observability/data/embeddings/papers_embeddings.json) (sửa hàm `_build_documents` trong `index.py`). |

## 3. Kết quả theo vai trò

| Nhiệm vụ đã thực hiện | File/hàm/artifact liên quan | Kết quả bàn giao       | Cách xác minh         |
| --------------------------- | ----------------------------- | ------------------------- | ----------------------- |
| Lập trình 5 tín hiệu kiểm định chất lượng và độ tươi mới | [quality.py](file:///d:/laragon/www/Day10Vinuni/K3_Day10_Data-Pipeline-Data-Observability/src/observability/quality.py) | Xuất báo cáo dạng cấu trúc chuẩn khớp với contract báo cáo. | Chạy script kiểm định độc lập `verify_quality.py`. |
| Tự động tạo bộ test set động dựa trên dữ liệu thật | [testset.py](file:///d:/laragon/www/Day10Vinuni/K3_Day10_Data-Pipeline-Data-Observability/src/evaluation/testset.py) | Sinh ra file [test_set.json](file:///d:/laragon/www/Day10Vinuni/K3_Day10_Data-Pipeline-Data-Observability/data/eval/test_set.json) chứa 24 câu hỏi (tác giả, ngày xuất bản, tóm tắt, danh mục). | Đọc nội dung file JSON, xác minh ID câu hỏi trỏ đúng DOI thật của bài báo. |
| Kết xuất báo cáo đối chiếu ba trạng thái Baseline-Corrupted-Repaired | [reporting.py](file:///d:/laragon/www/Day10Vinuni/K3_Day10_Data-Pipeline-Data-Observability/src/observability/reporting.py) | Tự động tạo file báo cáo [phase1_report.md](file:///d:/laragon/www/Day10Vinuni/K3_Day10_Data-Pipeline-Data-Observability/data/reports/phase1_report.md) và [corruption_report.md](file:///d:/laragon/www/Day10Vinuni/K3_Day10_Data-Pipeline-Data-Observability/data/reports/corruption_report.md). | Chạy toàn bộ pipeline `run_phase1.py` và `run_corruption_flow.py`. |

Nêu một output cụ thể mà phần việc của bạn tạo ra hoặc giúp xác minh:
Tệp báo cáo **[corruption_report.md](file:///d:/laragon/www/Day10Vinuni/K3_Day10_Data-Pipeline-Data-Observability/data/reports/corruption_report.md)** hiển thị bảng đối chiếu chi tiết hiệu năng và chất lượng qua ba trạng thái Baseline - Corrupted - Repaired.

---

## 4. Giải thích phần kỹ thuật đã thực hiện

### Vấn đề cần giải quyết
Trong một hệ thống RAG học thuật, chất lượng dữ liệu đầu vào là yếu tố sống còn quyết định độ chính xác của câu trả lời từ Agent. Module này cần giải quyết hai vấn đề:
1.  **Thiết lập Quality Gates tĩnh & động:** Tự động phát hiện dữ liệu lỗi (thiếu trường, trùng khóa, dữ liệu quá cũ) trước khi lập chỉ mục vector.
2.  **Đo lường định lượng tác động:** Xây dựng bộ test set tự động, độc lập, bám sát các từ khóa Agent dùng để truy xuất nhằm đo lường mức sụt giảm hiệu năng khi dữ liệu bị làm bẩn và mức phục hồi sau khi sửa.

### Cách triển khai
*   **Quality Checks:** Viết hàm kiểm định độ dài dữ liệu (`> 0`), tính đầy đủ & độc nhất của khóa chính `paper_id` (DOI), độ đầy đủ của tiêu đề, độ đầy đủ & độ dài tối thiểu của tóm tắt (cảnh báo dưới 20 ký tự).
*   **Freshness Monitoring:** Tính khoảng cách từ ngày xuất bản thực tế đến thời điểm chạy, so sánh với ngưỡng cấu hình (180 ngày) để phát hiện và đếm số lượng tài liệu quá hạn (stale).
*   **Test Set Generator:** Lấy tối đa 8 bài báo đầu tiên của clean dataframe để đảm bảo tính đại diện và tốc độ kiểm thử. Sinh ra 4 loại câu hỏi bám sát cấu trúc khớp từ khóa của Agent (`qa.py`):
    *   *Tác giả:* `Who authored the paper titled '{title}'?` -> khớp với `authors_joined`.
    *   *Ngày tháng:* `When was the paper titled '{title}' published?` -> khớp với ngày YYYY-MM-DD.
    *   *Danh mục:* `What categories does the paper titled '{title}' belong to?` -> khớp với `categories_joined`.
    *   *Tóm tắt:* `Provide a brief summary of the paper titled '{title}'.` -> khớp với `first_sentence(summary)` để đánh giá factual chính xác.

### Input, output và contract

| Thành phần                   | Mô tả                                     |
| ------------------------------ | ------------------------------------------- |
| Input                          | Cleaned Dataframe (`pd.DataFrame`) chứa dữ liệu học thuật được chuẩn hóa từ Crossref. |
| Output                         | Bộ test set JSON tĩnh `test_set.json` và các báo cáo dạng JSON/Markdown về chất lượng/hiệu năng. |
| Module phụ thuộc             | Module Cleaning (cung cấp dataframe sạch); module Ingestion (cung cấp metadata). |
| Module sử dụng output        | Module RAG & Evaluation (sử dụng `test_set.json` để chạy đánh giá và tính toán metrics). |
| Điều kiện lỗi cần xử lý | Trường hợp dataframe đầu vào rỗng (ném ngoại lệ `ValueError`); trường hợp các ô dữ liệu chứa giá trị `NaN` (phải ép kiểu về chuỗi rỗng `""` để tránh hỏng file JSON). |

### Cách xác minh

```bash
# 1. Chạy xác minh chất lượng dữ liệu baseline độc lập
python "C:\Users\dangm\.gemini\antigravity-ide\brain\af39dd4a-bc3c-4884-bde9-1636455568df\scratch\verify_quality.py"

# 2. Chạy toàn bộ pipeline Baseline
python script/run_phase1.py

# 3. Chạy luồng làm bẩn dữ liệu và khôi phục để xuất báo cáo đối chiếu
python script/run_corruption_flow.py
```

*   **Kết quả mong đợi:** Toàn bộ pipeline chạy không lỗi; xuất ra đầy đủ các file báo cáo chất lượng (`baseline_quality.json`, `freshness_report.json`), file test set (`test_set.json`), và các báo cáo markdown (`phase1_report.md`, `corruption_report.md`) chứa số liệu thống kê đầy đủ.
*   **Kết quả thực tế:** Pipeline chạy hoàn toàn thành công, sinh ra đầy đủ 10/10 artifacts đích trên đĩa.
*   **Artifact/log:**
    *   Báo cáo Baseline: [phase1_report.md](file:///d:/laragon/www/Day10Vinuni/K3_Day10_Data-Pipeline-Data-Observability/data/reports/phase1_report.md)
    *   Báo cáo Đối chiếu: [corruption_report.md](file:///d:/laragon/www/Day10Vinuni/K3_Day10_Data-Pipeline-Data-Observability/data/reports/corruption_report.md)

---

## 5. Một quyết định kỹ thuật quan trọng

*   **Bối cảnh:** Đồng bộ định danh tài liệu (`paper_id`) giữa Test Set và Vector Store.
*   **Các phương án đã cân nhắc:**
    1.  *Phương án 1:* Tự sinh ID ngẫu nhiên (UUID) cho `ground_truth_doc_ids` trong từng câu hỏi của Test Set.
    2.  *Phương án 2:* Trích xuất và sử dụng chính xác khóa chính `paper_id` (DOI của bài báo) từ clean dataframe làm `ground_truth_doc_ids`.
*   **Phương án đã chọn:** Phương án 2.
*   **Lý do:** Khi RAG Agent thực hiện tìm kiếm ngữ nghĩa trên ChromaDB, các tài liệu lấy ra được định danh bằng metadata `paper_id` (DOI). Nếu trong Test Set chúng ta dùng ID ngẫu nhiên, hàm tính toán `evaluate_pipeline` đối chiếu danh sách `retrieved_doc_ids` và `ground_truth_doc_ids` sẽ không bao giờ khớp nhau, khiến chỉ số `retrieval_hit_rate` luôn bằng 0% mặc dù Agent tìm kiếm đúng tài liệu.
*   **Bằng chứng quyết định phù hợp:** Việc sử dụng Phương án 2 giúp đo đạc chính xác chỉ số `retrieval_hit_rate` của hệ thống baseline đạt **87.5%**, phản ánh đúng năng lực truy xuất thực tế.

---

## 6. Một lỗi hoặc blocker đã xử lý

*   **Triệu chứng/lỗi nguyên văn:**
    ```text
    json.decoder.JSONDecodeError: Expecting value: line 17 column 30 (char 412)
    ```
    (Khi mở tệp tin `papers_embeddings.json`, phát hiện giá trị `"categories_joined": NaN` được ghi trần mà không có dấu ngoặc kép, gây lỗi cú pháp JSON nghiêm trọng).
*   **Lệnh hoặc bước tái hiện:** Chạy tiến trình lập chỉ mục vector và kết xuất ra file embeddings.
*   **Nguyên nhân gốc:** Khi pandas xuất dữ liệu từ dataframe, các ô rỗng trong cột được đọc thành float `nan` (NaN). Khi thư viện python ghi đè cấu trúc dict sang JSON dùng `json.dumps`, nó mặc định chuyển đổi float `nan` thành token `NaN` trần (không có nháy kép), vi phạm tiêu chuẩn định dạng JSON.
*   **Cách xử lý:** Tôi đã thực hiện vá lỗi (patch) bằng cách tạo hàm lọc `sanitize` kiểm tra giá trị bằng `pd.isna()` và ép kiểu mọi giá trị NaN/null thành chuỗi rỗng `""` trước khi đưa vào cấu trúc tài liệu lưu trữ ở [index.py](file:///d:/laragon/www/Day10Vinuni/K3_Day10_Data-Pipeline-Data-Observability/src/retrieval/index.py) và [testset.py](file:///d:/laragon/www/Day10Vinuni/K3_Day10_Data-Pipeline-Data-Observability/src/evaluation/testset.py).
*   **Cách xác minh sau khi sửa:** Chạy lại tiến trình tạo chỉ mục, mở file [papers_embeddings.json](file:///d:/laragon/www/Day10Vinuni/K3_Day10_Data-Pipeline-Data-Observability/data/embeddings/papers_embeddings.json) kiểm tra xem trường `"categories_joined"` đã chuyển thành `""` hợp lệ.

---

## 7. Hiểu biết về luồng end-to-end

1.  **Dữ liệu đi từ Crossref đến vector index:** REST API Crossref tải dữ liệu thô -> lưu thành JSON -> Parser trích xuất thành danh sách cấu trúc `PaperRecord` -> làm sạch (dedupe theo DOI, normalize text, tính age_days) -> lưu thành CSV/JSON -> nạp vào ChromaDB bằng mô hình nhúng `all-MiniLM-L6-v2` để tạo cơ sở dữ liệu vector.
2.  **Đo lường retrieval/answer quality:** Bộ test set lưu các câu hỏi đi kèm `ground_truth_doc_ids`. Khi chạy đánh giá, hệ thống so khớp ID tài liệu mà Agent thực tế lấy ra từ ChromaDB với ID chuẩn để tính `retrieval_hit_rate`. Đồng thời so sánh câu trả lời của Agent với đáp án chuẩn bằng Token F1 và LLM Judge.
3.  **Quality checks khác freshness monitoring:** Quality checks kiểm soát tính toàn vẹn tĩnh của cấu trúc dữ liệu (null, duplicate, độ dài text). Freshness monitoring kiểm soát tính cập nhật động theo thời gian (tuổi của bài viết so với ngưỡng quy định, tránh dùng kiến thức lỗi thời).
4.  **Tại sao dùng cùng một test set:** Đảm bảo tính nhất quán của phép đo. Mọi sự thay đổi về chỉ số đánh giá chỉ do biến số chất lượng dữ liệu (sạch vs bẩn vs sửa) gây ra, tránh sai số do nội dung câu hỏi thay đổi.
5.  **Repair thành công dựa trên:** Quality gates phục hồi về trạng thái ban đầu (4/5 checks đạt) và các chỉ số RAG (`retrieval_hit_rate` quay về 87.5%, `mean_token_f1` quay về 29.9%).

---

## 8. Phân tích kết quả

### Metrics chính

| Metric/signal          | Baseline | Corrupted | Repaired | Nhận xét của cá nhân |
| ---------------------- | -------: | --------: | -------: | ------------------------- |
| `retrieval_hit_rate` |    87.5% |     83.3% |    87.5% | Giảm khi bị xóa record (drop_latest), hồi phục hoàn toàn sau sửa. |
| `mean_token_f1`      |    29.9% |     25.8% |    29.9% | Sụt giảm do tài liệu bị làm rỗng tóm tắt hoặc đổi ngày, hồi phục hoàn toàn. |
| `judge_accuracy`     |    25.0% |     20.8% |    25.0% | Tỷ lệ chính xác của Agent giảm sút khi thiếu dữ liệu nền tảng. |
| `mean_judge_score`   |    2.333 |     2.125 |    2.292 | Điểm chất lượng trung bình giảm khi bị bẩn và hồi phục gần như tuyệt đối. |
| Quality checks         | 4/5 đạt  | 2/5 đạt   | 4/5 đạt  | Bị hỏng do trùng ID và rỗng tóm tắt, phục hồi hoàn toàn sau repair. |
| Freshness status       | 1 stale  | 2 stale   | 1 stale  | Tăng stale do dịch chuyển 10 năm, quay lại ban đầu sau khi reload. |

### Kết luận từ số liệu

1.  **Làm bẩn dữ liệu:** Xóa bản ghi mới nhất, làm rỗng tóm tắt, nhân bản dòng -> Tín hiệu chất lượng sụt giảm (Paper ID check và Summary check bị **FAILED**), kéo theo hiệu năng RAG Agent giảm sút rõ rệt (hit rate giảm 4.2%, F1 giảm 4.1%).
2.  **Khôi phục dữ liệu:** Reload dữ liệu nguyên bản từ Crossref -> Phục hồi các tín hiệu chất lượng về trạng thái ban đầu (4/5 đạt) -> Các chỉ số RAG hồi phục hoàn chỉnh về mức baseline.

*   **Corruption ảnh hưởng rõ nhất:** `drop_latest_record` ảnh hưởng lớn nhất vì nó làm mất hoàn toàn tài liệu đích khỏi cơ sở dữ liệu. Hệ thống vector search không thể tìm thấy thông tin (`retrieval_hit = False`), khiến Agent phải trả lời sai lệch dựa trên các tài liệu nhiễu khác.
*   **Kết quả khác kỳ vọng:** Điểm số `mean_judge_score` của pha Repaired (2.292) lệch nhẹ so với Baseline (2.333) dù dữ liệu giống nhau. Điều này do tính ngẫu nhiên tự sinh từ ngữ của LLM OpenAI khi trả lời và chấm điểm (độ lệch nhỏ $\pm 1\%$ nằm trong ngưỡng chấp nhận được).

---

## 9. Điều học được và hướng cải thiện

### Ba điều quan trọng nhất
1.  **Về data pipeline:** Lập chỉ mục vector nhạy cảm với các định dạng dữ liệu (như lỗi NaN); việc kiểm soát kiểu dữ liệu chặt chẽ là bắt buộc.
2.  **Về data quality/observability:** Cần phải thiết lập các chốt chặn chất lượng (quality gates) tự động để phát hiện lỗi sớm trước khi cập nhật dữ liệu vào vector store.
3.  **Về ảnh hưởng dữ liệu:** Thiếu hụt thông tin hoặc thông tin bị nhiễu làm sụt giảm trực tiếp chất lượng câu trả lời của RAG Agent; khôi phục từ raw data gốc là cách an toàn nhất để sửa chữa.

### Nếu có thêm thời gian
Tôi sẽ lập trình tích hợp thư viện kiểm định chất lượng chuyên sâu **Great Expectations (GX)** để viết các bộ kiểm tra tự động hóa hoàn toàn ở mức schema dữ liệu và cấu hình cảnh báo Slack/Discord tự động khi phát hiện lỗi dữ liệu.

---

## 10. Cam kết của thành viên

Đánh dấu sau khi tự kiểm tra:

- [x] Nội dung báo cáo phản ánh đúng phần việc và mức hiểu của tôi.
- [x] Tôi có thể giải thích luồng end-to-end, không chỉ module mình phụ trách.
- [x] Mọi kết luận về kết quả đều có artifact hoặc metric để đối chiếu.
- [x] Tôi không ghi “đã chạy thành công” cho phần chưa được kiểm chứng.
- [x] Báo cáo không chứa `.env`, API key, token hoặc secret.
- [x] Báo cáo này không phải bản sao nguyên văn của báo cáo nhóm hoặc báo cáo thành viên khác.

**Họ và tên:** Nguyễn Doãn Hoàng
**Ngày xác nhận:** 2026-08-06

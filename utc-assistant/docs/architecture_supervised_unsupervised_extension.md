# Kiến trúc mở rộng: Supervised + Unsupervised cho UTC Assistant

## Mục tiêu

Tài liệu này mô tả cách mở rộng kiến trúc hiện tại của `utc-assistant` bằng
các thành phần học máy nhẹ để:

- định tuyến câu hỏi tốt hơn trước khi vào RAG;
- phát hiện câu hỏi ngoài miền hoặc thiếu dữ liệu nội bộ;
- gom nhóm log/feedback để tìm lỗ hổng tri thức;
- cải thiện retrieval theo dữ liệu thực tế thay vì chỉ tinh chỉnh prompt.

Nguyên tắc thiết kế:

- không thay thế RAG hiện tại;
- không fine-tune LLM sinh câu trả lời;
- chỉ thêm các mô hình nhỏ, dễ huấn luyện, dễ rollback;
- tách riêng luồng `training/offline` và `inference/online`.

## Sơ đồ tổng thể mở rộng

- Mermaid: [h4_7_supervised_unsupervised_extension.mmd](/Users/trantrung/CAOHOC_CNTT/mo_hinh_ngon_ngu_lon/diagrams/h4_7_supervised_unsupervised_extension.mmd)
- PNG: [h4_7_supervised_unsupervised_extension.png](/Users/trantrung/CAOHOC_CNTT/mo_hinh_ngon_ngu_lon/diagrams/h4_7_supervised_unsupervised_extension.png)

Luồng này giữ RAG hiện tại làm lõi trả lời, nhưng thêm một lớp quyết định ở
đầu vào và một vòng học offline ở đầu ra:

1. `Intent classifier` phân loại câu hỏi.
2. `Route policy` chọn đường xử lý: RAG nội bộ, student context, web first hoặc fallback.
3. `vLLM` vẫn là tầng tổng hợp câu trả lời cuối cùng.
4. Log hội thoại/feedback được đưa về pipeline offline để huấn luyện lại classifier và phát hiện cluster câu hỏi mới.

## Kiến trúc hiện tại

Điểm vào online chính hiện nay là:

- [chat_stream.py](/Users/trantrung/CAOHOC_CNTT/mo_hinh_ngon_ngu_lon/utc-assistant/src/chat_stream.py)
- [api_server.py](/Users/trantrung/CAOHOC_CNTT/mo_hinh_ngon_ngu_lon/utc-assistant/src/api_server.py)
- [rag_pipeline.py](/Users/trantrung/CAOHOC_CNTT/mo_hinh_ngon_ngu_lon/utc-assistant/src/rag_pipeline.py)

Luồng hiện tại:

1. nhận câu hỏi;
2. hybrid retrieve;
3. dense fallback;
4. rerank;
5. web fallback nếu retrieval yếu;
6. LLM sinh câu trả lời.

Điểm yếu chính:

- phân loại câu hỏi vẫn chủ yếu dựa vào heuristic;
- chưa có detector ngoài miền rõ ràng;
- quyết định `nội bộ hay web` còn dựa mạnh vào threshold score;
- log/feedback/bug chưa được khai thác để học pattern mới.

## Đề xuất tổng thể

Thêm 4 lớp mới:

1. `Intent Classifier` có giám sát
2. `Route Policy` có giám sát nhẹ hoặc rule + score
3. `Out-of-Domain / Low-Confidence Detector`
4. `Offline Unsupervised Discovery`

Mục tiêu là đổi luồng từ:

`question -> retrieve -> rerank -> answer`

thành:

`question -> classify -> route -> retrieve/web/personal -> answer`

## Thành phần đề xuất

### 1. Intent Classifier có giám sát

Nhiệm vụ:

- phân loại câu hỏi vào các intent nghiệp vụ ổn định.

Tập intent nên dùng trước:

- `hoc_phi`
- `lich_thi`
- `thu_tuc`
- `hoc_bong`
- `ky_tuc_xa`
- `tai_khoan_he_thong`
- `hoc_tap_ca_nhan`
- `tin_tuc_su_kien`
- `ngoai_mien_utc`
- `khac`

Đầu vào:

- `question`

Đầu ra:

- `intent`
- `confidence`

Tích hợp online:

- chạy ngay trước đoạn retrieval trong [chat_stream.py](/Users/trantrung/CAOHOC_CNTT/mo_hinh_ngon_ngu_lon/utc-assistant/src/chat_stream.py)
- dùng kết quả để:
  - chọn `topic_filter`;
  - quyết định có inject `student_context`;
  - tăng/giảm ngưỡng web fallback;
  - bỏ qua retrieval với các intent chào hỏi hoặc meta.

Mô hình khuyến nghị:

- pha 1: `logistic regression` hoặc `linear SVM` trên embedding `bge-m3`
- pha 2: `LightGBM/XGBoost` nếu cần thêm feature thủ công

Lý do:

- đơn giản;
- train nhanh;
- dễ giải thích;
- không làm nặng runtime.

### 2. Route Policy

Nhiệm vụ:

- quyết định tuyến xử lý phù hợp nhất cho từng câu hỏi.

Các route nên có:

- `route_rag_internal`
- `route_student_context_plus_rag`
- `route_web_first`
- `route_direct_fallback`

Feature đầu vào:

- `intent`, `intent_confidence`
- top retrieval score
- số chunk đạt ngưỡng
- có/không có tín hiệu câu hỏi cá nhân
- có/không có câu hỏi thời sự
- feedback lịch sử của nhóm câu hỏi tương tự

Thiết kế pha đầu:

- chưa cần model riêng;
- dùng `policy engine` dựa trên rule + score;
- chỉ chuyển sang supervised router khi log đủ lớn.

Ví dụ:

- `hoc_tap_ca_nhan` -> luôn thử `student_context_plus_rag`
- `tin_tuc_su_kien` + retrieval yếu -> `web_first`
- `ngoai_mien_utc` -> `direct_fallback`

### 3. Out-of-Domain / Low-Confidence Detector

Nhiệm vụ:

- phát hiện câu hỏi không thuộc miền UTC hoặc nội dung nội bộ không đủ.

Đầu vào:

- embedding câu hỏi
- top-1/top-k retrieval score
- entropy của classifier
- lexical overlap với corpus

Đầu ra:

- `in_domain: true/false`
- `need_web_search: true/false`
- `need_human_review: true/false`

Thiết kế ban đầu:

- ngưỡng score + confidence
- thêm one-class hoặc isolation style detector chỉ khi dữ liệu đủ

Khuyến nghị:

- không đưa unsupervised detector vào đường online ở pha đầu;
- chỉ dùng supervised thresholding trước vì dễ kiểm soát hơn.

### 4. Offline Unsupervised Discovery

Nhiệm vụ:

- khai phá dữ liệu vận hành để phát hiện:
  - nhóm câu hỏi mới;
  - lỗ hổng tri thức;
  - chủ đề bug lặp lại;
  - nhóm feedback tiêu cực.

Nguồn dữ liệu sẵn có:

- `data/runtime/questions.json`
- `data/runtime/feedback.json`
- `data/runtime/bugs.json`
- SQLite conversations trong [database.py](/Users/trantrung/CAOHOC_CNTT/mo_hinh_ngon_ngu_lon/utc-assistant/src/database.py)

Bài toán unsupervised nên làm:

- clustering câu hỏi bằng embedding
- topic discovery cho feedback/bugs
- nearest-neighbor mining để tìm FAQ mới

Thuật toán phù hợp:

- `HDBSCAN` hoặc `Agglomerative Clustering` trên embedding
- `UMAP` chỉ để trực quan hóa, không bắt buộc trong production

Kết quả đầu ra mong muốn:

- danh sách cluster mới
- top representative questions
- cluster có feedback xấu nhiều
- cluster có tỷ lệ web fallback cao

## Kiến trúc online đề xuất

### Luồng inference mới

1. nhận `question`
2. chạy `intent classifier`
3. chạy `route policy`
4. nếu route là `student_context_plus_rag`:
   - inject student context
   - retrieve nội bộ
5. nếu route là `web_first`:
   - web search trước
   - fallback nội bộ nếu cần
6. nếu route là `rag_internal`:
   - hybrid retrieve
   - rerank
7. sinh câu trả lời
8. log toàn bộ decision để huấn luyện vòng sau

### Mapping vào luồng hiện tại

Với code hiện có, vị trí chèn hợp lý là:

1. [chat_stream.py](/Users/trantrung/CAOHOC_CNTT/mo_hinh_ngon_ngu_lon/utc-assistant/src/chat_stream.py): thêm bước `classify -> route` ngay sau khi nhận `question` và trước khi gọi `pipeline.retrieve()`.
2. [rag_pipeline.py](/Users/trantrung/CAOHOC_CNTT/mo_hinh_ngon_ngu_lon/utc-assistant/src/rag_pipeline.py): giữ retrieval/rerank/web fallback làm executor cho từng route, không nhét logic học máy trực tiếp vào từng hàm retrieve nhỏ.
3. [api_server.py](/Users/trantrung/CAOHOC_CNTT/mo_hinh_ngon_ngu_lon/utc-assistant/src/api_server.py): mở rộng response metadata nếu cần trả về `intent`, `route`, `source_type`.

Tách như vậy giúp rollback dễ: nếu classifier/policy lỗi thì có thể tắt bằng config và quay lại flow RAG hiện tại.

### Điểm chèn cụ thể trong repo

Nên thêm các module mới:

- `src/intent_classifier.py`
- `src/route_policy.py`
- `src/domain_detector.py`
- `src/feature_extractor.py`
- `src/model_registry.py`

Tích hợp vào:

- [chat_stream.py](/Users/trantrung/CAOHOC_CNTT/mo_hinh_ngon_ngu_lon/utc-assistant/src/chat_stream.py)
- [api_server.py](/Users/trantrung/CAOHOC_CNTT/mo_hinh_ngon_ngu_lon/utc-assistant/src/api_server.py)
- [rag_pipeline.py](/Users/trantrung/CAOHOC_CNTT/mo_hinh_ngon_ngu_lon/utc-assistant/src/rag_pipeline.py)

### Dữ liệu online cần log thêm

Mỗi request nên log:

- `intent_pred`
- `intent_confidence`
- `route_selected`
- `top1_score`
- `topk_mean_score`
- `used_student_context`
- `used_web_search`
- `answer_success`
- `user_feedback`

Nên ghi vào file mới hoặc SQLite:

- `data/runtime/router_events.jsonl`

## Kiến trúc offline đề xuất

### Supervised training pipeline

Nguồn nhãn:

- gán nhãn tay ban đầu cho 300-1000 câu hỏi
- bootstrapping từ `classify_topic()` hiện tại
- sửa tay các mẫu sai

Pipeline offline:

1. export câu hỏi từ log
2. gán nhãn intent
3. sinh embedding
4. train classifier
5. đánh giá
6. lưu artifact
7. nạp artifact vào runtime

Artifact đề xuất:

- `models/intent_classifier.joblib`
- `models/intent_label_map.json`
- `models/router_thresholds.json`

### Unsupervised analysis pipeline

Pipeline offline:

1. lấy câu hỏi/feedback/bugs
2. embedding batch
3. clustering
4. chọn representative item cho mỗi cluster
5. xuất report

Output đề xuất:

- `data/analytics/question_clusters_YYYYMMDD.json`
- `data/analytics/feedback_topics_YYYYMMDD.json`
- `docs/cluster_report.md`

### Tác động vận hành mong đợi

- supervised cải thiện độ chính xác của quyết định tuyến;
- unsupervised không phục vụ trả lời trực tiếp, mà giúp biết kho tri thức đang thiếu chỗ nào;
- web search sẽ trở thành một route có kiểm soát, thay vì chỉ là fallback theo score;
- dữ liệu phản hồi người dùng sẽ bắt đầu có giá trị huấn luyện thực tế.

## Thiết kế triển khai theo pha

### Pha 1: Supervised routing tối thiểu

Phạm vi:

- intent classifier nhỏ
- route policy rule-based
- log decision

Lợi ích:

- ít rủi ro
- dễ đo hiệu quả
- không chạm mạnh vào RAG lõi

Success criteria:

- giảm web fallback sai
- tăng hit rate retrieval đúng miền
- giảm câu trả lời fallback vô ích

### Pha 2: Unsupervised discovery

Phạm vi:

- clustering questions/feedback/bugs
- xuất báo cáo lỗ hổng tri thức

Lợi ích:

- biết nên bổ sung tài liệu gì
- biết intent nào cần tách riêng

Success criteria:

- tìm được top cluster chưa có tài liệu tốt
- tạo được FAQ mới từ log

### Pha 3: Supervised router nâng cao

Phạm vi:

- model quyết định `RAG vs web vs student context`
- có feature từ retrieval score + intent + lịch sử feedback

Lợi ích:

- route chính xác hơn heuristic

Success criteria:

- tăng answer success rate
- giảm latency trung bình
- giảm số lượt gọi web không cần thiết

## Khuyến nghị mô hình

### Nên dùng ngay

- supervised:
  - `logistic regression` trên embedding
  - `LinearSVC`
- unsupervised:
  - `HDBSCAN`
  - `Agglomerative Clustering`

### Chưa nên dùng ngay

- fine-tune generative LLM
- deep neural classifier riêng
- online continual learning tự động sửa policy

## Rủi ro

1. Nhãn ban đầu kém chất lượng
- giảm thiểu: bắt đầu ít lớp, review tay

2. Over-routing sang web
- giảm thiểu: threshold bảo thủ, log kỹ

3. Drift do dữ liệu mới
- giảm thiểu: retrain định kỳ theo batch

4. Pipeline phức tạp hơn
- giảm thiểu: giữ classifier/router độc lập với RAG

## Đề xuất cấu trúc thư mục mới

```text
utc-assistant/
├── src/
│   ├── intent_classifier.py
│   ├── route_policy.py
│   ├── domain_detector.py
│   ├── feature_extractor.py
│   ├── model_registry.py
│   └── training/
│       ├── build_dataset.py
│       ├── train_intent_classifier.py
│       ├── evaluate_router.py
│       └── cluster_questions.py
├── models/
│   ├── intent_classifier.joblib
│   ├── intent_label_map.json
│   └── router_thresholds.json
└── data/
    └── analytics/
```

## Quyết định khuyến nghị

Với repo hiện tại, thứ nên làm đầu tiên không phải là “thêm một mô hình học
máy lớn”, mà là:

1. thêm `intent classifier` có giám sát nhẹ;
2. thêm `route policy` trước retrieval;
3. thêm `offline clustering` để phát hiện lỗ hổng tri thức.

Đây là hướng có chi phí thấp nhất nhưng tạo cải thiện rõ nhất cho pipeline
hiện có.

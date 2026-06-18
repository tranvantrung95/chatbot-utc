# KỊCH BẢN AUTOTEST - UTC ASSISTANT

## Mục tiêu
Đánh giá hiệu năng và chất lượng hệ thống RAG Chatbot dưới tải cao:
- 100 tài khoản đồng thời
- Mỗi tài khoản hỏi 10 câu (tổng 1,000 requests)
- Đo: latency, error rate, answer quality, throughput

> **Lý do giảm từ 100→10 câu/tk**: 100×100=10,000 requests × ~10s/req = ~28 giờ. Không khả thi.
> 100×10=1,000 requests × ~10s = ~2.8 giờ với 5 concurrent workers.

---

## 1. Chuẩn bị dữ liệu test

### 1.1. Tài khoản test (100 tk)
- Pattern: `test_student_001` → `test_student_100`
- Email: `test_student_XXX@test.utc.edu.vn`
- Password: `test123456`
- Role: student
- Tạo qua API `/api/auth/register`

### 1.2. Bộ câu hỏi test (50 câu, xoay vòng)
Phân loại theo chủ đề:

| ID | Chủ đề | Số câu | Ví dụ |
|----|--------|--------|-------|
| A | Học phí | 8 | "Học phí UTC là bao nhiêu?", "Làm sao đóng học phí online?" |
| B | Điểm số | 8 | "Cách tính điểm trung bình tích lũy?", "Điểm F có được học lại không?" |
| C | Đào tạo | 8 | "Thời gian đào tạo tối đa là bao lâu?", "Điều kiện tốt nghiệp?" |
| D | Thủ tục | 8 | "Thủ tục xin xác nhận sinh viên?", "Cách lấy lại mật khẩu QLĐT?" |
| E | Ký túc xá | 6 | "Đăng ký KTX như thế nào?", "Giá KTX bao nhiêu?" |
| F | Học bổng | 6 | "Điều kiện nhận học bổng?", "Các loại học bổng?" |
| G | Khác | 6 | "Email sinh viên là gì?", "Số điện thoại phòng đào tạo?" |

### 1.3. Ground truth (đáp án mong đợi)
Mỗi câu hỏi có answer mẫu để đánh giá độ chính xác:
```json
{
  "question": "Học phí UTC là bao nhiêu?",
  "expected_keywords": ["học phí", "tín chỉ", "thanh toán", "qldt.utc.edu.vn"],
  "expected_not_keywords": ["không có thông tin", "xin lỗi"],
  "min_answer_length": 50
}
```

---

## 2. Các chỉ số đánh giá

### 2.1. Hiệu năng
| Chỉ số | Mô tả | Target |
|--------|-------|--------|
| `p50_latency` | Median thời gian phản hồi | < 15s |
| `p95_latency` | 95th percentile | < 30s |
| `p99_latency` | 99th percentile | < 60s |
| `error_rate` | Tỉ lệ lỗi (5xx, timeout) | < 5% |
| `throughput` | Requests/giây hoàn thành | > 0.5 req/s |
| `ttft_avg` | Time-to-first-token trung bình | < 3s |

### 2.2. Chất lượng
| Chỉ số | Mô tả | Target |
|--------|-------|--------|
| `fallback_rate` | Tỉ lệ trả lời "xin lỗi, chưa có thông tin" | < 15% |
| `keyword_match` | Tỉ lệ câu trả lời chứa keyword mong đợi | > 70% |
| `answer_length_ok` | Tỉ lệ câu trả lời > min_length | > 80% |
| `no_hallucination` | Không chứa keyword cấm (bịa số ĐT, địa chỉ sai) | > 90% |
| `source_count_avg` | Số nguồn tham khảo trung bình | > 1 |

### 2.3. Độ ổn định
| Chỉ số | Mô tả |
|--------|-------|
| `rate_limit_hits` | Số lần bị giới hạn 429 |
| `auth_failures` | Số lần đăng nhập thất bại |
| `consecutive_errors` | Số lỗi liên tiếp tối đa |

---

## 3. Kiến trúc test

```
┌─────────────────────────────────────────────────────┐
│                   Test Runner                        │
│  (Python script - chạy local)                       │
├─────────────────────────────────────────────────────┤
│  1. Tạo 100 tài khoản test                          │
│  2. Login 100 tk → lấy tokens                       │
│  3. Chạy worker pool (5 concurrent)                 │
│     Mỗi worker:                                     │
│       - Lấy 1 câu hỏi từ queue                      │
│       - Gọi POST /api/chat                          │
│       - Đo latency, parse response                  │
│       - Đánh giá answer vs ground truth             │
│       - Ghi log                                     │
│  4. Tổng hợp metrics                                │
│  5. Xuất báo cáo JSON + HTML                        │
└─────────────────────────────────────────────────────┘
```

### 3.1. Worker pool (5 concurrent)
- Tránh quá tải server (rate limit: 5 req/60s/user)
- Mỗi worker dùng 1 token riêng → không bị rate limit per-user
- 5 workers × 100 tk = mỗi tk chỉ gửi ~10 requests

### 3.2. Hàng đợi câu hỏi
- 1,000 tasks (100 tk × 10 câu)
- Round-robin: mỗi tk được gán 10 câu từ pool 50 câu

---

## 4. Output

### 4.1. File báo cáo
```
data/autotest/
├── report_YYYYMMDD_HHMMSS.json    # Full metrics
├── report_YYYYMMDD_HHMMSS.html    # HTML dashboard
├── logs/
│   ├── responses_001.json          # Chi tiết từng response
│   └── errors.log                  # Log lỗi
└── summary.txt                     # Tóm tắt nhanh
```

### 4.2. Cấu trúc báo cáo JSON
```json
{
  "meta": {
    "test_time": "2026-05-30T22:00:00",
    "total_users": 100,
    "total_questions": 1000,
    "concurrent_workers": 5,
    "duration_sec": 2847
  },
  "performance": {
    "p50_latency": 12.3,
    "p95_latency": 28.7,
    "p99_latency": 55.1,
    "error_rate": 0.03,
    "throughput": 0.35,
    "ttft_avg": 2.1
  },
  "quality": {
    "fallback_rate": 0.12,
    "keyword_match_rate": 0.78,
    "answer_length_ok_rate": 0.85,
    "no_hallucination_rate": 0.92,
    "source_count_avg": 2.3
  },
  "stability": {
    "rate_limit_hits": 5,
    "auth_failures": 0,
    "consecutive_errors_max": 2
  },
  "per_question": [
    {
      "question_id": "A1",
      "question": "Học phí UTC là bao nhiêu?",
      "success": true,
      "latency_sec": 11.2,
      "answer_length": 450,
      "sources_count": 3,
      "fallback": false,
      "keyword_match": true,
      "hallucination": false
    }
  ],
  "per_user": [
    {
      "user": "test_student_001",
      "total_requests": 10,
      "success": 9,
      "avg_latency": 13.1
    }
  ]
}
```

---

## 5. Rủi ro & Giới hạn

| Rủi ro | Biện pháp |
|--------|-----------|
| LLM server quá tải | Test vào giờ thấp điểm, dùng 5 workers |
| Rate limit chặn | Mỗi worker dùng token riêng |
| Câu hỏi không có trong knowledge base | Chấp nhận fallback_rate < 15% |
| Test chạy lâu (> 2h) | Có progress bar, lưu checkpoint |
| Memory leak | Giới hạn log size, flush từng batch |

---

## 6. Các bước thực hiện

1. **Duyệt kịch bản** ← ĐANG Ở ĐÂY
2. Tạo script: `scripts/autotest.py`
3. Tạo file câu hỏi: `data/autotest/questions.json`
4. Chạy test: `python scripts/autotest.py`
5. Xem báo cáo: `open data/autotest/report_*.html`

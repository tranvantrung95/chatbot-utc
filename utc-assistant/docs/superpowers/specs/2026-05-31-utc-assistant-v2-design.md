# Spec: UTC Assistant v2 — Gói A+B

> Status: Chờ duyệt | Date: 31/05/2026 | Target: 2-3 tuần

## 1. Tổng quan

Nâng cấp từ POC/MVP lên sản phẩm hoàn chỉnh cho Trường Đại học Giao thông Vận tải. 10 tính năng chia 2 gói.

**Nguyên tắc:**
- Không thay đổi RAG pipeline lõi
- Mở rộng API + FE theo module
- Chuyển từ JSON files → SQLite cho persistence
- Backward-compatible với API hiện tại

## 2. Kiến trúc

```
┌─ FE Next.js ────────────────────────────────────────┐
│  Chat │ FAQ │ Search │ Voice │ Analytics │ Admin    │
└────────────────────┬────────────────────────────────┘
                     │ REST + SSE
┌─ BE FastAPI ───────┼────────────────────────────────┐
│  api_server.py     │  conversations.py  (NEW)       │
│  rag_pipeline.py   │  feedback.py        (NEW)      │
│  chat_stream.py    │  documents_v2.py    (NEW)      │
│  chandra_ocr.py    │  analytics.py       (NEW)      │
│  structured_       │  faq.py             (NEW)      │
│    chunker.py      │  speech.py          (NEW)      │
├────────────────────┼────────────────────────────────┤
│  SQLite (NEW)      │  ChromaDB                      │
│  - conversations   │  - utc_knowledge               │
│  - messages        │                                │
│  - feedbacks       │                                │
│  - notifications   │                                │
└────────────────────┴────────────────────────────────┘
```

## 3. Data Model (SQLite mới)

```sql
-- Multi-turn conversations
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT DEFAULT 'Cuộc trò chuyện mới',
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);

CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL REFERENCES conversations(id),
    role TEXT NOT NULL CHECK(role IN ('student', 'bot')),
    content TEXT NOT NULL,
    thinking TEXT DEFAULT '',
    sources_json TEXT DEFAULT '[]',
    created_at REAL NOT NULL
);

-- Feedback ratings
CREATE TABLE feedback_ratings (
    id TEXT PRIMARY KEY,
    message_id TEXT NOT NULL REFERENCES messages(id),
    user_id TEXT NOT NULL,
    rating TEXT NOT NULL CHECK(rating IN ('up', 'down')),
    reason TEXT DEFAULT '',
    comment TEXT DEFAULT '',
    created_at REAL NOT NULL
);

-- Notifications
CREATE TABLE notifications (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    type TEXT NOT NULL,
    title TEXT NOT NULL,
    body TEXT DEFAULT '',
    is_read INTEGER DEFAULT 0,
    created_at REAL NOT NULL
);

-- FAQ cache (updated daily)
CREATE TABLE faq_cache (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    count INTEGER DEFAULT 0,
    satisfaction REAL DEFAULT 0,
    updated_at REAL NOT NULL
);
```

## 4. API mới

### 4.1. Conversations

| Method | Path | Mô tả |
|--------|------|-------|
| POST | `/api/conversations` | Tạo conversation mới |
| GET | `/api/conversations` | Danh sách (phân trang) |
| GET | `/api/conversations/{id}` | Chi tiết + messages |
| DELETE | `/api/conversations/{id}` | Xóa |

**POST /api/chat/stream** — thêm field `conversation_id` (optional). Nếu có → lưu message vào DB + inject 5 messages gần nhất vào system prompt.

### 4.2. Feedback

| Method | Path | Mô tả |
|--------|------|-------|
| POST | `/api/feedback/rate` | Gửi đánh giá |
| GET | `/api/feedback/stats` | Thống kê satisfaction |

### 4.3. Documents

| Method | Path | Mô tả |
|--------|------|-------|
| POST | `/api/documents/upload` | Upload PDF/TXT/MD (multipart) |
| DELETE | `/api/documents/{filename}` | Xóa document + re-index |

### 4.4. Analytics

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/api/analytics/overview` | Tổng quan |
| GET | `/api/analytics/by-day?days=30` | Biểu đồ theo ngày |
| GET | `/api/analytics/by-topic` | Phân bố chủ đề |
| GET | `/api/analytics/top-failed` | Top câu hỏi thất bại |

### 4.5. Search & FAQ

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/api/faq?limit=10` | Top câu hỏi phổ biến |
| GET | `/api/search?q=...&limit=5` | Search gợi ý |

### 4.6. Notifications

| Method | Path | Mô tả |
|--------|------|-------|
| GET | `/api/notifications/unread` | Số lượng chưa đọc + list |
| POST | `/api/notifications/{id}/read` | Đánh dấu đã đọc |

### 4.7. Speech

| Method | Path | Mô tả |
|--------|------|-------|
| POST | `/api/speech-to-text` | Audio → text (optional, fallback Web Speech API) |

## 5. FE Changes

### 5.1. Chat page (student)

```
┌─ Sidebar ─────────────────────┬─ Chat Area ──────────────────┐
│  + Cuộc trò chuyện mới       │  ✅ Trợ lý ảo UTC            │
│                               │                               │
│  📝 Học bổng UTC             │  [FAQ buttons: 5 câu hỏi]     │
│  📝 Điều kiện tốt nghiệp     │                               │
│  📝 Học phí online           │  User: "Học bổng..."          │
│  ...                          │  Bot: "Có 2 loại..."          │
│                               │    👍 👎 📋 📥               │
│                               │                               │
│                               │  [🎤] [________________] [➤] │
└───────────────────────────────┴───────────────────────────────┘
```

### 5.2. Admin dashboard — tab mới

Tab "📊 Thống kê":
- 4 KPI cards (tổng câu hỏi, satisfaction, avg time, tài liệu)
- Biểu đồ câu hỏi theo ngày (line chart)
- Phân bố chủ đề (pie/donut chart)
- Top câu hỏi thất bại (bảng)

### 5.3. Admin documents — nâng cấp

- Khu vực kéo thả upload PDF
- Progress bar OCR
- Danh sách tài liệu + nút Xóa

### 5.4. Header — notification badge

```
[🔔 3]  [👤 Admin]
```

## 6. Implementation Order

| Tuần | Tasks | Deliverable |
|------|-------|-------------|
| **Tuần 1** | SQLite migration, A1 (conversations), A2 (feedback), A3 (FAQ) | Chat v2 with history |
| **Tuần 2** | A4 (upload), A5 (analytics), B1 (personalization), B2 (search) | Admin v2 |
| **Tuần 3** | B3 (notifications), B4 (export), B5 (voice), testing, polish | Release candidate |

## 7. Risk & Mitigation

| Risk | Mitigation |
|------|------------|
| SQLite migration mất data | Backup JSON files, script migration tự động |
| Rate limit với upload PDF | Xử lý async queue |
| Voice model nặng | Dùng Web Speech API làm primary, whisper fallback |
| FE phức tạp với nhiều state | Giữ từng component độc lập, dùng React context cho auth |

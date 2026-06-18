# ĐÁNH GIÁ TOÀN DIỆN REPO UTC-ASSISTANT
## Audit Date: 30/05/2026

---

## 1. TỔNG QUAN

| Chỉ số | Giá trị | Điểm |
|--------|---------|------|
| LOC Python | 4,005 | — |
| LOC Tests | 195 | ⚠️ |
| Số file Python | 12 | — |
| API endpoints | 22 | — |
| LLM models | 2 (qwen35-opus, bge-m3) | — |
| Vector DB | ChromaDB (63 chunks) | — |
| Frontend | Next.js 15 (~10K LOC TSX) | — |

---

## 2. ĐÁNH GIÁ THEO 12-LAYER STACK (Agent Architecture Audit)

### Layer 1: System Prompt — 8/10 ✅

**Điểm:** 8/10

**Nhận xét:** System prompt 595 dòng tiếng Việt, cực kỳ chi tiết với quy tắc bắt buộc, mẫu trả lời, icon, xuống dòng. Đây là điểm mạnh nhất của hệ thống.

**Phê bình:**
- Quá dài (595 dòng) — gây instruction bloat, giảm context cho retrieved documents
- Có mâu thuẫn: rule #9 "không tự suy đoán" vs mẫu trả lời yêu cầu "tóm tắt" (đòi hỏi tổng hợp)
- Có rule cấm markdown (#5) nhưng mẫu lại dùng icon unicode → không nhất quán

**Cải tiến:** Rút gọn còn ~100 dòng, tập trung vào 5 quy tắc cốt lõi. Đưa mẫu vào few-shot examples thay vì system prompt.

---

### Layer 2-3: Session History & Memory — 3/10 ❌

**Điểm:** 3/10

**Nhận xét:** KHÔNG có session history. Mỗi câu hỏi là 1 turn độc lập, không context từ câu trước. Memory lưu activity log nhưng không dùng cho retrieval.

**Phê bình:**
- Chatbot không nhớ câu hỏi trước → user phải nhắc lại context
- Không có multi-turn conversation
- Activity log ghi "Đã trả lời"/"Cần kiểm tra" nhưng không phân tích để cải thiện

**Cải tiến:** Thêm conversation history (5 turns gần nhất) vào context. Thêm trường `conversation_id` vào API.

---

### Layer 4-5: Distillation & Active Recall — 0/10 ❌

**Điểm:** 0/10 — Chưa implement

---

### Layer 6-8: Tool Selection, Execution, Interpretation — 6/10 ⚠️

**Điểm:** 6/10

**Nhận xét:** Chỉ có 1 "tool" là retrieval. Không có function calling, không có tool router.

**Phê bình:**
- Luôn retrieve kể cả khi câu hỏi là "xin chào" → lãng phí embedding call
- Không có tool để tra cứu thời tiết, lịch học real-time...
- Không validate kết quả retrieval trước khi đưa vào context

**Cải tiến:** Thêm lightweight classifier để skip retrieval với câu chào hỏi. Nếu top-1 score < 0.3 → trả lời fallback luôn, không gọi LLM.

---

### Layer 7: RAG Pipeline — 7/10 ✅

**Điểm:** 7/10

**Điểm mạnh:**
- Hybrid retrieval (vector + keyword rerank) hoạt động tốt
- Structured chunking từ TOC JSON (63 chunks, metadata giàu)
- ChromaDB persistent, cosine similarity
- Support streaming SSE real-time

**Phê bình:**
- Chỉ 1 tài liệu → không có cross-document retrieval
- Chunking chưa tận dụng hết metadata (chưa filter theo Phần/Chương)
- Embedding model (bge-m3) là general purpose, không fine-tune cho tiếng Việt
- Không có cache cho câu hỏi phổ biến
- `_rerank` dùng keyword bonus cố định (0.04/0.12) — chưa calibrate

**Cải tiến:**
- Thêm query-time filter: chỉ search trong Phần liên quan nếu user hỏi "học bổng"
- Cache top-50 câu hỏi thường gặp
- Fine-tune embedding với legal/giáo dục Vietnamese corpus
- Thêm RAGAS evaluation pipeline

---

### Layer 9: Answer Shaping — 6/10 ⚠️

**Điểm:** 6/10

**Nhận xét:** `extract_answer_with_thinking()` tách reasoning/answer tốt. Nhưng `build_context` dùng format đơn giản.

**Phê bình:**
- `build_context` label là breadcrumb nhưng không hiển thị metadata type (Điều/Chương/Phần)
- Context ghép bằng `---` → LLM dễ nhầm lẫn giữa các chunk
- Không có citation marker trong answer

**Cải tiến:** Format context với XML-style tags: `<chunk type="article" number="9">...</chunk>`. Yêu cầu LLM cite source number trong answer.

---

### Layer 10: Platform Rendering — 5/10 ⚠️

**Điểm:** 5/10

**Nhận xét:** Streaming SSE hoạt động, nhưng output còn lỗi (duplicate ký tự, newline thừa). Đã fix nhưng cần test thêm.

**Phê bình:**
- Stream parsing mong manh (split by `\n`, manual JSON parse)
- Không có retry/reconnect khi stream đứt
- FE render thinking với `animate-pulse` → performance issue trên mobile

---

### Layer 11: Hidden Repair Loops — 8/10 ✅

**Điểm:** 8/10 — Không có hidden repair loops. Code minh bạch, không có fallback LLM call ẩn.

---

### Layer 12: Persistence — 4/10 ❌

**Điểm:** 4/10

**Nhận xét:** ChromaDB persistent + JSON files. Nhưng:

**Phê bình:**
- users.json, questions.json, feedback.json — flat files, không có migration
- Không backup vector DB
- Không cleanup expired sessions
- Session TTL 24h nhưng không có cron job dọn dẹp

**Cải tiến:** Chuyển sang SQLite cho runtime data. Thêm backup cron job.

---

## 3. ĐÁNH GIÁ THEO PRODUCTION READINESS

### Bảo mật — 4/10 ❌

| Vấn đề | Mức |
|--------|-----|
| Password hash SHA-256 (đã fix → bcrypt) | Đã fix |
| Token không có expiry rotation | High |
| Không có CSRF protection | Medium |
| CORS chỉ allow localhost | OK cho dev |
| Không rate limit per IP (chỉ per user) | Medium |
| API key hardcode "EMPTY" | Low |
| Không input sanitization cho question | Medium |

**Score: 4/10 — Cần fix trước khi public deploy**

---

### Data Integrity — 5/10 ⚠️

| Vấn đề |
|--------|
| Flat JSON files → race condition với DATA_LOCK nhưng chỉ 1 process |
| Không backup tự động |
| Không data validation schema (Pydantic có nhưng không strict) |

---

### Operations — 3/10 ❌

| Vấn đề |
|--------|
| Không Docker |
| Không health check ngoài `/api/health` (không check LLM/DB) |
| Không logging structured |
| Không monitoring/alerting |
| Không CI/CD |
| Không git (chưa init!) |
| Manual restart bằng kill port |

---

### Testing — 2/10 ❌

| Vấn đề |
|--------|
| Chỉ 2 test files, 195 LOC tests |
| Không test API endpoints |
| Không test streaming |
| Không integration test |
| Không E2E test |
| Test coverage ~5% |

---

## 4. BẢNG ĐIỂM TỔNG HỢP

| Hạng mục | Điểm | Trọng số | Điểm có trọng số |
|----------|------|----------|-------------------|
| System Prompt | 8/10 | 10% | 0.8 |
| RAG Pipeline | 7/10 | 25% | 1.75 |
| Chunking & Embedding | 7/10 | 15% | 1.05 |
| Answer Shaping | 6/10 | 10% | 0.6 |
| Streaming/Platform | 5/10 | 10% | 0.5 |
| Security | 4/10 | 10% | 0.4 |
| Operations | 3/10 | 5% | 0.15 |
| Testing | 2/10 | 5% | 0.1 |
| Memory/History | 3/10 | 5% | 0.15 |
| Data Integrity | 5/10 | 5% | 0.25 |
| **TỔNG** | — | 100% | **5.75/10** |

---

## 5. PHẢN BIỆN & PHÊ BÌNH

### Làm tốt
1. RAG pipeline hoạt động, hybrid retrieval hiệu quả
2. System prompt tiếng Việt chi tiết
3. Structured chunking từ OCR → TOC → chunks
4. Streaming SSE cho thinking real-time
5. Code sạch, tách module rõ ràng

### Làm chưa tốt
1. **Không có Git** — không thể track changes, không thể rollback
2. **Không có tests** — 195 LOC tests cho 4000 LOC code = 5% coverage
3. **Không có Docker** — không reproducible
4. **Rate limit 5req/60s quá thấp** cho production
5. **Chỉ 1 tài liệu** → RAG chưa phát huy hết sức mạnh
6. **Không multi-turn** → chatbot "đãng trí"
7. **Hardcode IP** (100.64.0.25) trong `.env`
8. **System prompt quá dài** (595 dòng) → lãng phí context window

---

## 6. KẾ HOẠCH CẢI TIẾN (theo độ ưu tiên)

### Giai đoạn 1: Nền tảng (tuần 1-2)
1. **Init Git** + push lên repo
2. **Docker** hóa toàn bộ stack (BE + FE + ChromaDB + LLM)
3. **Tests**: thêm 20+ test cases cho API endpoints, retrieval accuracy
4. **CI/CD**: GitHub Actions chạy tests tự động

### Giai đoạn 2: Chất lượng (tuần 3-4)
5. **Health check**: `/api/health` check LLM + ChromaDB connectivity
6. **Structured logging**: thay `print()` bằng `logging` với JSON format
7. **Cache**: Redis/Memcached cho top-50 câu hỏi thường gặp
8. **Multi-turn**: thêm `conversation_id`, context từ 5 turns trước
9. **System prompt**: rút gọn 595 → 100 dòng

### Giai đoạn 3: Mở rộng (tuần 5-8)
10. **Thêm tài liệu**: 5+ văn bản quy chế, luật
11. **Fine-tune embedding**: dùng Vietnamese legal corpus
12. **RAGAS evaluation**: đánh giá định lượng accuracy
13. **Phân cụm KB**: khi > 500 chunks
14. **Function calling**: tích hợp tool tra cứu thời tiết, lịch học

---

## 7. KẾT LUẬN

**Tổng điểm: 5.75/10 — DỰ ÁN ĐANG Ở GIAI ĐOẠN POC/MVP**

Đây là một PoC chất lượng tốt cho luận văn thạc sĩ. Pipeline RAG hoạt động, có đầy đủ ingestion → chunking → embedding → retrieval → generation. Code sạch, tách module rõ.

Tuy nhiên để thành **production system** cần:
- Tests (hiện 5% → cần > 60%)
- Docker + CI/CD
- Security hardening
- Multi-turn conversation
- Thêm tài liệu vào KB

**Khuyến nghị:** Tập trung Giai đoạn 1 (Git, Docker, Tests) trước khi thêm tính năng mới.

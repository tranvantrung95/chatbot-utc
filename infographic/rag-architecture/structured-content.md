# Kiến trúc RAG UTC Assistant — Structured Content

## Title & Header
- **Title**: KIẾN TRÚC RAG 3-STAGE — UTC ASSISTANT
- **Subtitle**: Chatbot hỗ trợ sinh viên ĐH Giao thông Vận tải
- **Badge**: Luận văn Thạc sĩ • 2026

---

## Section 1: Tổng quan Pipeline

**Key Concept**: Hệ thống Retrieval-Augmented Generation 3 tầng

**Content (verbatim)**:
Hệ thống tiếp nhận câu hỏi tiếng Việt từ sinh viên, xử lý qua 3 stage retrieval trước khi sinh câu trả lời bằng LLM.

**Visual Element**: Sơ đồ tổng quan 3 khối chính nối tiếp bằng mũi tên
**Text Labels**: Stage 1: Bi-encoder → Stage 2: BM25 Hybrid → Stage 3: LLM Reranker

---

## Section 2: Stage 1 — Bi-encoder Retrieval

**Key Concept**: Tìm kiếm ngữ nghĩa với embedding vector

**Content (verbatim)**:
- Model: BAAI/bge-m3 (1024 chiều)
- Vector DB: ChromaDB (63 chunks)
- Query Expansion: 15 chủ đề, 5-6 từ đồng nghĩa mỗi chủ đề
- Semantic Topic Detection: embedding similarity (threshold 0.55)

**Visual Element**: Biểu tượng vector + ChromaDB logo
**Text Labels**: bge-m3 → ChromaDB → Top-20 chunks

---

## Section 3: Stage 2 — BM25 Hybrid Search

**Key Concept**: Kết hợp keyword search với Reciprocal Rank Fusion

**Content (verbatim)**:
- BM25 Index: Pure Python, Okapi BM25 (k1=1.2, b=0.75)
- RRF Fusion: k=60, merge BM25 + Dense rankings
- Deduplication: MD5 content hash
- Fallback: nếu RRF < 0.016 → quay về Dense-only

**Visual Element**: Hai mũi tên hội tụ (BM25 + Dense) → RRF → Top-10
**Text Labels**: BM25 (keyword) + Dense (semantic) → RRF Fusion → Top-10

---

## Section 4: Stage 3 — LLM Reranker (Deep Learning)

**Key Concept**: Dùng LLM đọc từng cặp (query, chunk) để chấm điểm

**Content (verbatim)**:
- Model: qwen35-opus (Transformer)
- Cơ chế: gửi query + 10 chunks, LLM chấm 1-10
- Trọng số: 70% LLM score + 30% original score
- Output: Top-5 chunks chất lượng cao nhất

**Visual Element**: Biểu tượng não AI + thang điểm 1-10
**Text Labels**: Top-10 → LLM Judge → Top-5

---

## Section 5: Cross-cutting Components

**Key Concept**: Các thành phần xuyên suốt pipeline

**Content (verbatim)**:
- SYSTEM PROMPT: 43 dòng (giảm 93% từ 660 dòng), tiết kiệm 3,600 tokens/request
- CACHE: TTL 10 phút, index_version, LRU 50 queries
- CONTEXT BUDGET: 2.5 chars/token (Vietnamese), max 2,400 tokens
- MULTI-TURN: Load 6 messages từ SQLite, summarization cho chat dài (>8 msg)
- GRACEFUL DEGRADATION: 3-tier (Full → Partial → Fallback)

**Visual Element**: Các badge/icon nhỏ xung quanh pipeline chính
**Text Labels**: System Prompt (43 dòng) • Cache (TTL 10m) • Budget (2.5x) • Multi-turn • 3-tier Fallback

---

## Section 6: Đánh giá hiệu năng

**Key Concept**: Kết quả benchmark trên 50 câu hỏi test

**Content (verbatim)**:
- HIT RATE: 100% (cả dense-only và hybrid)
- MRR Dense-only: 0.980 (20.4s)
- MRR Hybrid: 0.974 (9.2s) — nhanh 2.2x
- TEST SUITE: 18 unit tests, 100% pass (pytest)
- PROMPT: Giảm 93% kích thước (660→43 dòng)

**Visual Element**: Bảng so sánh metrics + biểu đồ cột nhỏ
**Text Labels**: Hit Rate 100% • MRR 0.980 • 18 tests • 9.2s/50 câu

---

## Section 7: Data Pipeline

**Key Concept**: Quy trình xử lý tài liệu đầu vào

**Content (verbatim)**:
- Input: Sổ tay sinh viên K66 (92 trang PDF)
- OCR: chandra2 API → HTML → TOC JSON
- Chunking: Structured chunker (theo Phần/Chương/Điều)
- Output: 63 chunks với metadata (phan_so, type, breadcrumb, pages)
- Index: ChromaDB persistent collection "utc_knowledge"

**Visual Element**: Sơ đồ nhỏ: PDF → OCR → TOC → Chunks → ChromaDB
**Text Labels**: 1 tài liệu → 92 trang → 63 chunks → ChromaDB

---

## Design Instructions
- Ngôn ngữ: Tiếng Việt
- Màu chủ đạo: Xanh navy (#0f294a - UTC brand), trắng, cam (#f97316) làm điểm nhấn
- Kiểu dáng: Kỹ thuật, sạch sẽ, chuyên nghiệp
- Bố cục: Pipeline chính giữa, cross-cutting components xung quanh
- Font: Sans-serif cho tiêu đề, mono cho số liệu kỹ thuật

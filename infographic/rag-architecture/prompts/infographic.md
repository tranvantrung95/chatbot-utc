Create a professional infographic following these specifications:

## Image Specifications

- **Type**: Infographic
- **Layout**: winding-roadmap
- **Style**: technical-schematic (Blueprint variant)
- **Aspect Ratio**: 16:9 (landscape)
- **Language**: Vietnamese

## Core Principles

- Follow the winding-roadmap layout for showing the 3-stage pipeline flow
- Apply technical-schematic blueprint aesthetics consistently (white lines on deep blue, grid pattern, dimension annotations)
- Keep information concise, highlight keywords and core concepts
- Use ample whitespace for visual clarity
- Maintain clear visual hierarchy

## Text Requirements

- All text in Vietnamese
- Main title prominent: "KIẾN TRÚC RAG 3-STAGE — UTC ASSISTANT"
- Key metrics highlighted: "Hit Rate 100%", "MRR 0.980", "43 dòng prompt"
- Technical labels in monospace/stencil font

## Layout Guidelines (winding-roadmap)

The "winding road" represents the data pipeline flow:
- START node: "Câu hỏi sinh viên" (Student Question input)
- MILESTONE 1: "Stage 1 — Bi-encoder (bge-m3)" — vector search, ChromaDB
- MILESTONE 2: "Stage 2 — BM25 Hybrid + RRF" — keyword + semantic fusion
- MILESTONE 3: "Stage 3 — LLM Reranker (Deep Learning)" — qwen35-opus scoring
- END node: "Câu trả lời" (Bot Response output)
- Side elements along the road: System Prompt (43 dòng), Cache TTL 10m, 3-tier Fallback, Multi-turn, Test Suite 18/18

## Style Guidelines (technical-schematic - Blueprint)

- Background: Deep navy blue (#1E3A5F) with subtle grid pattern
- Primary elements: White lines, geometric precision
- Accent colors: Amber (#F59E0B) for highlights, Cyan (#06B6D4) for data/metrics
- Typography: Clean sans-serif or technical stencil, all-caps for section headers
- Dimension lines and measurement-style annotations for technical metrics
- Consistent stroke weights, clean vector shapes
- Add "UTC" watermark or subtle brand element

---

Generate the infographic based on the content below:

## Content Structure

**TITLE**: KIẾN TRÚC RAG 3-STAGE
**SUBTITLE**: UTC Assistant — Chatbot hỗ trợ sinh viên ĐH Giao thông Vận tải
**BADGE**: Luận văn Thạc sĩ 2026

**STAGE 1 — Bi-encoder Retrieval**:
- Model: BAAI/bge-m3 (1024-dim)
- Vector DB: ChromaDB — 63 structured chunks
- Query Expansion: 15 chủ đề × 5-6 từ đồng nghĩa
- Semantic Topic Detection: embedding similarity (≥0.55)
- Output: Top-20 candidate chunks

**STAGE 2 — BM25 Hybrid Search**:
- BM25 Index: Okapi BM25 (k1=1.2, b=0.75) — Pure Python
- RRF Fusion: Reciprocal Rank Fusion (k=60)
- Merge: BM25 (keyword) + Dense (semantic)
- Deduplication: MD5 content hash
- Fallback: RRF < 0.016 → Dense-only
- Output: Top-10 refined chunks

**STAGE 3 — LLM Reranker (Deep Learning)**:
- Model: qwen35-opus Transformer
- Mechanism: LLM reads (query, chunk) pairs → scores 1-10
- Weight: 70% LLM score + 30% original
- Output: Top-5 high-quality chunks

**CROSS-CUTTING COMPONENTS** (side elements along pipeline):
- ⚡ System Prompt: 43 dòng (giảm 93% từ 660)
- 💾 Cache: TTL 10 phút, index_version, LRU 50
- 📐 Context Budget: 2.5 chars/token, max 2,400 tokens
- 💬 Multi-turn: 6 messages + summarization
- 🛡️ 3-tier Fallback: Full → Partial → None

**PERFORMANCE METRICS**:
- Hit Rate: 100% (50/50 questions)
- MRR Dense-only: 0.980 (20.4s)
- MRR Hybrid: 0.974 (9.2s) — 2.2× faster
- Test Suite: 18 unit tests, 100% pass (pytest)

**DATA PIPELINE** (bottom section):
- Input: Sổ tay sinh viên K66 (92 trang PDF)
- OCR: chandra2 → TOC JSON → 63 structured chunks
- Metadata: phan_so, type, breadcrumb, pages
- Collection: ChromaDB "utc_knowledge"

Text labels (in Vietnamese):
- "Câu hỏi sinh viên" → "Query Expansion" → "Stage 1: Bi-encoder" → "Stage 2: BM25 Hybrid" → "Stage 3: LLM Reranker" → "Câu trả lời"
- Metrics callouts: "HIT RATE 100%", "MRR 0.980", "43 DÒNG PROMPT", "18/18 TESTS"
- Cross-cutting badges: "CACHE TTL 10m", "3-TIER FALLBACK", "MULTI-TURN", "2.5× TOKEN BUDGET"

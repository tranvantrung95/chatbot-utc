# Source: Pipeline RAG 3 tầng
**Figure:** Hình 4.5
**Type:** process
**Description:** Câu hỏi → Query Expansion (từ đồng nghĩa VN) → Topic Filter (metadata) → Tầng 1: Bi-encoder Dense (bge-m3) + Tầng 2: BM25 Sparse → RRF Fusion → Tầng 3: LLM Reranker → MMR → Context → LLM Generation → Trả lời + trích dẫn.

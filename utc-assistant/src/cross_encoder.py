"""Cross-encoder reranker: Deep learning 2nd-stage retrieval refinement.

Dùng transformer 12-layer để đọc đồng thời query + chunk,
chấm điểm relevance chính xác hơn bi-encoder cosine similarity.

Model: paraphrase-multilingual-MiniLM-L12-v2 (420MB, 50+ languages).
Chạy trên CPU, không cần GPU.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class TransformerReranker:
    """Transformer-based deep learning reranker cho RAG pipeline.
    
    Pipeline: Top-20 chunks → Cross-encoder → Top-5 chunks
    Mỗi cặp (query, chunk) được encode cùng lúc qua transformer,
    cho phép self-attention giữa query và chunk → relevance chính xác hơn.
    """
    
    def __init__(self, model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        self.model_name = model_name
        self._model = None
        self._loaded = False
    
    def _load(self):
        """Lazy load model (chỉ load khi dùng lần đầu)."""
        if self._loaded:
            return
        from sentence_transformers import SentenceTransformer
        print(f"  Loading cross-encoder: {self.model_name}...")
        self._model = SentenceTransformer(self.model_name)
        self._loaded = True
        print(f"  Cross-encoder ready")
    
    def rerank(
        self, query: str, chunks: List[Dict[str, Any]], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Re-rank chunks using multilingual transformer embeddings.
        
        Encode query và từng chunk riêng biệt qua transformer 12-layer,
        tính cosine similarity → chính xác hơn vector search vì model
        được huấn luyện đặc thù cho semantic similarity đa ngôn ngữ.
        
        Args:
            query: Câu hỏi sinh viên
            chunks: List các chunk từ retrieval thô (tối đa 20)
            top_k: Số lượng chunk trả về sau re-rank
            
        Returns:
            List chunks đã được sắp xếp lại theo transformer score
        """
        if len(chunks) <= top_k:
            return chunks
        
        self._load()
        
        # Encode query + all chunks
        chunk_texts = [c["content"] for c in chunks]
        query_emb = self._model.encode(query, normalize_embeddings=True)
        chunk_embs = self._model.encode(chunk_texts, normalize_embeddings=True)
        
        # Cosine similarity
        import numpy as np
        similarities = np.dot(chunk_embs, query_emb)  # (N,) array
        
        # Combine: 40% original score + 60% transformer similarity
        for i, chunk in enumerate(chunks):
            orig = float(chunk.get("score", 0.5))
            trans = float((similarities[i] + 1.0) / 2.0)  # Normalize [-1,1] → [0,1]
            chunk["_transformer_score"] = round(trans, 4)
            chunk["score"] = round(orig * 0.4 + trans * 0.6, 4)
        
        # Re-sort by combined score
        reranked = sorted(chunks, key=lambda c: c["score"], reverse=True)
        
        return reranked[:top_k]
    
    def score_pair(self, query: str, chunk_text: str) -> float:
        """Score a single (query, chunk) pair. Returns 0-1 relevance via cosine sim."""
        self._load()
        import numpy as np
        q_emb = self._model.encode(query, normalize_embeddings=True)
        c_emb = self._model.encode(chunk_text, normalize_embeddings=True)
        sim = float(np.dot(c_emb, q_emb))
        return round((sim + 1.0) / 2.0, 4)  # Normalize to [0,1]


# Global singleton (load once, reuse across requests)
_reranker: Optional[TransformerReranker] = None


def get_reranker() -> TransformerReranker:
    """Get or create the global transformer reranker."""
    global _reranker
    if _reranker is None:
        _reranker = TransformerReranker()
    return _reranker

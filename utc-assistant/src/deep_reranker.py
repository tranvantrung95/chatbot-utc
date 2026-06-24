"""Deep Learning Reranker: dùng Local Cross-Encoder để chấm điểm relevance.

Sử dụng model BAAI/bge-reranker-base chạy trực tiếp (local) 
thay cho LLM Reranker để tăng tốc độ và độ chính xác.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class LocalCrossEncoderReranker:
    """Local Cross-Encoder reranker.
    
    Chấm điểm mức độ liên quan giữa query và các chunk sử dụng mô hình local.
    """
    
    def __init__(self, pipeline=None):
        self.pipeline = pipeline
        from sentence_transformers import CrossEncoder
        # Load model siêu nhanh BAAI/bge-reranker-base
        self.model = CrossEncoder("BAAI/bge-reranker-base", max_length=512)
    
    def rerank(
        self, query: str, chunks: List[Dict[str, Any]], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Re-rank chunks using Local CrossEncoder relevance scores.
        
        Args:
            query: Câu hỏi sinh viên
            chunks: Top-N chunks từ hybrid search
            top_k: Số chunk trả về
            
        Returns:
            Reranked top-K chunks
        """
        if not chunks:
            return []
        
        # Tạo input pairs:
        pairs = [[query, chunk["content"]] for chunk in chunks]
        
        # Predict score
        scores = self.model.predict(pairs)
        
        import math
        # Dán score vào chunk
        for i, chunk in enumerate(chunks):
            raw_score = float(scores[i])
            sig_score = 1.0 / (1.0 + math.exp(-raw_score))
            chunk["_llm_score"] = sig_score # Lưu điểm của cross-encoder
            chunk["score"] = sig_score # Ưu tiên hoàn toàn điểm reranker
            
        # Sort lại
        reranked = sorted(chunks, key=lambda x: x["_llm_score"], reverse=True)
        return reranked[:top_k]


# Global singleton
_local_reranker: Optional[LocalCrossEncoderReranker] = None


def get_local_reranker(pipeline=None) -> LocalCrossEncoderReranker:
    """Get or create local reranker."""
    global _local_reranker
    if _local_reranker is None:
        _local_reranker = LocalCrossEncoderReranker(pipeline)
    return _local_reranker

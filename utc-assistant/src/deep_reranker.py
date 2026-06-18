"""Deep Learning Reranker: dùng LLM (qwen35-opus) để chấm điểm relevance.

Thay vì download model 420MB, tận dụng LLM API có sẵn.
LLM đọc đồng thời query + từng chunk → chấm điểm 1-10 → rerank.

Đây là kỹ thuật "LLM-as-Reranker" được dùng trong production RAG systems.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


RERANK_PROMPT = """Đánh giá mức độ liên quan của mỗi đoạn văn bản bên dưới với câu hỏi.
Cho điểm 1-10 cho MỖI đoạn (1=không liên quan, 10=rất liên quan).
CHỈ trả về JSON array: [score1, score2, ...]

CÂU HỎI: {query}

CÁC ĐOẠN VĂN BẢN:
{chunks}

ĐIỂM (JSON array):"""


class LLMReranker:
    """LLM-based deep learning reranker.
    
    Gửi query + top-N chunks đến LLM, LLM chấm điểm relevance 1-10,
    rerank theo điểm.
    """
    
    def __init__(self, pipeline):
        self.pipeline = pipeline
    
    def rerank(
        self, query: str, chunks: List[Dict[str, Any]], top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Re-rank chunks using LLM relevance scores.
        
        Args:
            query: Câu hỏi sinh viên
            chunks: Top-N chunks từ hybrid search (max 10)
            top_k: Số chunk trả về
            
        Returns:
            Reranked top-K chunks
        """
        if len(chunks) <= top_k:
            return chunks
        
        # Limit to 10 chunks for LLM context window
        batch = chunks[:10]
        
        # Build chunks text
        chunks_text = ""
        for i, c in enumerate(batch):
            preview = c["content"][:300].replace("\n", " ")
            chunks_text += f"[{i}] {preview}\n\n"
        
        prompt = RERANK_PROMPT.format(query=query, chunks=chunks_text)
        
        llm = self.pipeline.load_llm()
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = llm.session.post(
                f"{llm.base_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {llm.api_key}"},
                json={
                    "model": llm.model,
                    "messages": llm._prepare_messages(messages),
                    "temperature": 0.0,
                    "max_tokens": 200,
                    "enable_thinking": False,
                },
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            
            # Parse scores from LLM response
            scores = self._parse_scores(content, len(batch))
        except Exception:
            # Fallback: keep original order
            return chunks[:top_k]
        
        if not scores:
            return chunks[:top_k]
        
        # Attach LLM scores + combine with original
        for i, chunk in enumerate(batch):
            if i < len(scores):
                llm_score = scores[i] / 10.0  # Normalize 1-10 → 0-1
                orig = float(chunk.get("score", 0.5))
                chunk["_llm_score"] = round(llm_score, 4)
                # 30% original + 70% LLM (LLM reads context better)
                chunk["score"] = round(orig * 0.3 + llm_score * 0.7, 4)
        
        # Re-sort by combined score
        reranked = sorted(batch, key=lambda c: c["score"], reverse=True)
        return reranked[:top_k]
    
    @staticmethod
    def _parse_scores(text: str, expected_count: int) -> Optional[List[float]]:
        """Parse LLM response: extract JSON array of scores."""
        import re, json
        
        # Find JSON array in text
        m = re.search(r'\[[\d,\s.]+\]', text)
        if not m:
            return None
        
        try:
            scores = json.loads(m.group())
            if isinstance(scores, list) and all(isinstance(s, (int, float)) for s in scores):
                return [float(s) for s in scores[:expected_count]]
        except json.JSONDecodeError:
            pass
        
        # Fallback: extract numbers
        nums = re.findall(r'\b(\d+)\b', text)
        if nums:
            return [float(n) for n in nums[:expected_count]]
        
        return None


# Global singleton
_llm_reranker: Optional[LLMReranker] = None


def get_llm_reranker(pipeline) -> LLMReranker:
    """Get or create LLM reranker."""
    global _llm_reranker
    if _llm_reranker is None:
        _llm_reranker = LLMReranker(pipeline)
    return _llm_reranker

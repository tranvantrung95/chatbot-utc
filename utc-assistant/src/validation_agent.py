"""Validation Agent for Agentic Reasoning."""

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.rag_pipeline import UTCRAGPipeline

VALIDATION_PROMPT = """Bạn là Giám khảo đánh giá chất lượng câu trả lời của Trợ lý sinh viên.

Nhiệm vụ của bạn là kiểm tra xem CÂU TRẢ LỜI CẦN ĐÁNH GIÁ có đáp ứng đủ tiêu chuẩn hay không dựa trên NGỮ CẢNH và CÂU HỎI.

TIÊU CHÍ (0.0 đến 1.0):
1. faithfulness: Câu trả lời có hoàn toàn dựa trên NGỮ CẢNH không? Có bịa đặt thông tin không?
2. relevance: Câu trả lời có trả lời đúng trọng tâm CÂU HỎI không?

YÊU CẦU:
Trả về KẾT QUẢ theo ĐÚNG định dạng JSON sau:
{{
  "faithfulness": 0.9,
  "relevance": 0.8,
  "is_valid": true,
  "critique": "Câu trả lời tốt, đúng ngữ cảnh."
}}
Quy tắc is_valid: Trả về true NẾU (faithfulness >= 0.8 VÀ relevance >= 0.8). NGƯỢC LẠI trả về false.
NẾU is_valid là false, trường 'critique' PHẢI giải thích rõ lý do tại sao sai và yêu cầu viết lại như thế nào.

NGỮ CẢNH THAM KHẢO:
{context}

CÂU HỎI:
{question}

CÂU TRẢ LỜI CẦN ĐÁNH GIÁ:
{answer}
"""

@dataclass
class ValidationResult:
    faithfulness: float
    relevance: float
    is_valid: bool
    critique: str


class ValidationAgent:
    def __init__(self, pipeline: UTCRAGPipeline):
        self.pipeline = pipeline

    def parse_response(self, text: Optional[str]) -> Optional[ValidationResult]:
        if not text:
            return None
        m = re.search(r'\{[^}]+\}', text)
        if not m:
            return None
        try:
            data = json.loads(m.group())
            return ValidationResult(
                faithfulness=float(data.get("faithfulness", 0)),
                relevance=float(data.get("relevance", 0)),
                is_valid=bool(data.get("is_valid", False)),
                critique=str(data.get("critique", ""))
            )
        except (json.JSONDecodeError, ValueError, KeyError):
            return None

    def validate(self, question: str, answer: str, context_chunks: List[Dict[str, Any]]) -> Optional[ValidationResult]:
        context_text = self.pipeline.build_context(context_chunks, max_tokens=1500)
        prompt = VALIDATION_PROMPT.format(
            context=context_text,
            question=question,
            answer=answer[:2000]
        )
        
        llm = self.pipeline.load_llm()
        messages = [{"role": "user", "content": prompt}]
        
        try:
            response = llm.session.post(
                f"{llm.base_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {llm.api_key}"},
                json={
                    "model": llm.model,
                    "messages": llm._prepare_messages(messages),
                    "temperature": 0.1,
                    "max_tokens": 400,
                    "enable_thinking": False
                },
                timeout=60
            )
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                return None
            content = choices[0].get("message", {}).get("content") or ""
            return self.parse_response(content)
        except Exception as e:
            print(f"Validation Agent error: {e}")
            return None

"""Agentic Orchestrator for RAG Pipeline.
Wraps the UTCRAGPipeline with a Validate and Retry loop.
"""

from typing import Any, Dict, List, Tuple, Optional
from src.rag_pipeline import UTCRAGPipeline
from src.validation_agent import ValidationAgent

class AgenticOrchestrator:
    def __init__(self, pipeline: UTCRAGPipeline):
        self.pipeline = pipeline
        self.validator = ValidationAgent(pipeline)
        self.max_retries = 2

    def query(self, question: str, top_k: Optional[int] = None) -> Tuple[str, str, List[Dict[str, Any]]]:
        """Drop-in replacement for pipeline.query(), but with reasoning loop."""
        question = question.strip()
        if not question:
            raise ValueError("Question must not be empty")

        # 1. Retrieve Context
        retrieved = self.pipeline.retrieve(question, top_k=top_k)
        if not retrieved:
            return "", self.pipeline.FALLBACK_ANSWER, []

        context_text = self.pipeline.build_context(retrieved)
        llm = self.pipeline.load_llm()

        messages = [
            {"role": "system", "content": self.pipeline.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"NGỮ CẢNH THAM KHẢO:\n{context_text}\n\n"
                    f"CÂU HỎI CỦA SINH VIÊN: {question}\n\n"
                    "Hãy thực hiện toàn bộ quá trình suy nghĩ (thinking) bằng tiếng Việt và trả lời câu hỏi trên bằng tiếng Việt dựa vào ngữ cảnh được cung cấp. Chỉ đưa ra câu trả lời cuối cùng."
                ),
            },
        ]

        attempt = 0
        final_thinking = ""
        final_answer = ""

        while attempt <= self.max_retries:
            # 2. Generate Draft Answer
            try:
                response = llm.session.post(
                    f"{llm.base_url}/v1/chat/completions",
                    headers={"Authorization": f"Bearer {llm.api_key}"},
                    json={
                        "model": llm.model,
                        "messages": llm._prepare_messages(messages),
                        "temperature": 0.2 if attempt == 0 else 0.5, # Increase temp for rewrites
                        "max_tokens": self.pipeline.settings.llm_max_tokens,
                    },
                    timeout=llm.timeout,
                )
                response.raise_for_status()
                thinking, answer = llm.extract_answer_with_thinking(response.json())
                final_thinking = thinking
                final_answer = answer
            except Exception as e:
                print(f"Orchestrator generation error: {e}")
                if attempt == 0:
                    return "", "Có lỗi xảy ra khi tạo câu trả lời.", retrieved
                break

            # 3. Validate Answer
            validation = self.validator.validate(question, final_answer, retrieved)
            
            # If validation succeeds or fails to parse, break and return current answer
            if validation is None or validation.is_valid:
                break
                
            print(f"Validation failed (Faithfulness: {validation.faithfulness}, Relevance: {validation.relevance}). Retrying {attempt + 1}/{self.max_retries}...")
            print(f"Critique: {validation.critique}")

            # 4. Retry: Add critique to messages and generate again
            messages.append({"role": "assistant", "content": final_answer})
            messages.append({
                "role": "user", 
                "content": f"Câu trả lời của bạn chưa đạt yêu cầu. Lỗi: {validation.critique}\nHãy viết lại câu trả lời chính xác hơn, đáp ứng yêu cầu trên và chỉ dựa vào NGỮ CẢNH ban đầu."
            })
            
            attempt += 1

        return final_thinking, final_answer, retrieved

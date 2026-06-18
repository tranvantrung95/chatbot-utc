"""LLM-as-Judge evaluation: đánh giá chất lượng câu trả lời RAG.

Đánh giá 4 chiều:
- faithfulness: Câu trả lời có đúng với context không?
- relevance: Có trả lời đúng câu hỏi không?
- completeness: Có bỏ sót thông tin quan trọng không?
- conciseness: Có lan man, thừa thãi không?

Mỗi chiều: 0.0-1.0, dùng LLM (qwen35-opus) làm judge.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from src.rag_pipeline import UTCRAGPipeline, load_settings

BASE_DIR = Path(__file__).resolve().parent.parent


JUDGE_PROMPT = """Bạn là giám khảo đánh giá chất lượng câu trả lời của chatbot trợ lý sinh viên UTC.

Đánh giá câu trả lời bên dưới theo 4 tiêu chí. Cho điểm 0.0-1.0 cho mỗi tiêu chí.

TIÊU CHÍ:
1. faithfulness (độ trung thực): Câu trả lời có hoàn toàn dựa trên NGỮ CẢNH được cung cấp không? 
   Có thông tin nào bịa đặt, không có trong context không?

2. relevance (độ liên quan): Câu trả lời có trả lời đúng CÂU HỎI không?

3. completeness (độ đầy đủ): Câu trả lời có bỏ sót thông tin quan trọng từ context không?

4. conciseness (độ súc tích): Câu trả lời có ngắn gọn, không lan man không?

TRẢ LỜI CHỈ BẰNG JSON, ví dụ:
{{"faithfulness": 0.8, "relevance": 0.9, "completeness": 0.7, "conciseness": 0.8}}

NGỮ CẢNH THAM KHẢO:
{context}

CÂU HỎI:
{question}

CÂU TRẢ LỜI CẦN ĐÁNH GIÁ:
{answer}
"""


@dataclass
class EvalScores:
    faithfulness: float
    relevance: float
    completeness: float
    conciseness: float
    
    @property
    def overall(self) -> float:
        return round(
            self.faithfulness * 0.35 +
            self.relevance * 0.30 +
            self.completeness * 0.20 +
            self.conciseness * 0.15,
            3,
        )


@dataclass
class EvalReport:
    scores: List[EvalScores] = field(default_factory=list)
    latencies: List[float] = field(default_factory=list)
    failures: int = 0
    total: int = 0
    
    def avg(self, attr: str) -> float:
        if not self.scores:
            return 0.0
        return round(sum(getattr(s, attr) for s in self.scores) / len(self.scores), 3)
    
    @property
    def summary(self) -> dict:
        return {
            "total": self.total,
            "evaluated": len(self.scores),
            "failures": self.failures,
            "faithfulness": self.avg("faithfulness"),
            "relevance": self.avg("relevance"),
            "completeness": self.avg("completeness"),
            "conciseness": self.avg("conciseness"),
            "overall": self.avg("overall"),
            "avg_latency_sec": round(sum(self.latencies) / max(1, len(self.latencies)), 2),
        }


def parse_judge_response(text: str) -> Optional[EvalScores]:
    """Extract JSON scores from judge response."""
    # Find JSON block
    m = re.search(r'\{[^}]+\}', text)
    if not m:
        return None
    try:
        data = json.loads(m.group())
        return EvalScores(
            faithfulness=float(data.get("faithfulness", 0)),
            relevance=float(data.get("relevance", 0)),
            completeness=float(data.get("completeness", 0)),
            conciseness=float(data.get("conciseness", 0)),
        )
    except (json.JSONDecodeError, ValueError, KeyError):
        return None


class LLMJudge:
    """Dùng LLM để chấm điểm chất lượng câu trả lời."""
    
    def __init__(self, pipeline: UTCRAGPipeline):
        self.pipeline = pipeline
    
    def evaluate_one(
        self, question: str, answer: str, context_chunks: List[Dict[str, Any]]
    ) -> Optional[EvalScores]:
        """Đánh giá 1 cặp (question, answer, context)."""
        context_text = self.pipeline.build_context(context_chunks, max_tokens=1500)
        prompt = JUDGE_PROMPT.format(
            context=context_text,
            question=question,
            answer=answer[:2000],
        )
        
        llm = self.pipeline.load_llm()
        messages = [
            {"role": "user", "content": prompt},
        ]
        
        try:
            response = llm.session.post(
                f"{llm.base_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {llm.api_key}"},
                json={
                    "model": llm.model,
                    "messages": llm._prepare_messages(messages),
                    "temperature": 0.1,
                    "max_tokens": 300,
                    "enable_thinking": False,
                },
                timeout=60,
            )
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                return None
            content = choices[0].get("message", {}).get("content")
            if not content:
                return None
            return parse_judge_response(content)
        except Exception as e:
            print(f"  Judge error: {e}")
            return None
    
    def evaluate_batch(self, test_questions: List[dict]) -> EvalReport:
        """Đánh giá toàn bộ test set."""
        report = EvalReport(total=len(test_questions))
        
        for i, q in enumerate(test_questions):
            question = q["question"]
            print(f"  [{i+1}/{len(test_questions)}] {question[:60]}...")
            
            t0 = time.time()
            
            # Get answer from pipeline
            retrieved = self.pipeline.retrieve(question, top_k=5)
            if not retrieved:
                report.failures += 1
                print(f"    → No retrieval results")
                continue
            
            _, answer, _ = self.pipeline.query(question, top_k=5)
            latency = time.time() - t0
            report.latencies.append(latency)
            
            # Judge the answer
            scores = self.evaluate_one(question, answer, retrieved)
            if scores:
                report.scores.append(scores)
                print(f"    → O:{scores.overall} F:{scores.faithfulness} R:{scores.relevance} C:{scores.completeness} @ {latency:.1f}s")
            else:
                report.failures += 1
                print(f"    → Judge parse failed")
        
        return report


def run_evaluation(questions_path: Optional[str] = None) -> dict:
    """Run full evaluation and return report."""
    if questions_path is None:
        questions_path = str(BASE_DIR / "data" / "autotest" / "questions.json")
    
    with open(questions_path, encoding="utf-8") as f:
        questions = json.load(f)
    
    print(f"\n{'='*60}")
    print(f"LLM-as-Judge Evaluation — {len(questions)} questions")
    print(f"{'='*60}\n")
    
    settings = load_settings()
    pipeline = UTCRAGPipeline(settings)
    judge = LLMJudge(pipeline)
    
    report = judge.evaluate_batch(questions[:20])  # Limit for speed
    
    summary = report.summary
    print(f"\n{'='*60}")
    print(f"RESULTS")
    print(f"{'='*60}")
    print(f"Evaluated: {summary['evaluated']}/{summary['total']} (failures: {summary['failures']})")
    print(f"Avg latency: {summary['avg_latency_sec']}s")
    print(f"\nScores:")
    print(f"  Faithfulness:  {summary['faithfulness']:.3f}")
    print(f"  Relevance:     {summary['relevance']:.3f}")
    print(f"  Completeness:  {summary['completeness']:.3f}")
    print(f"  Conciseness:   {summary['conciseness']:.3f}")
    print(f"  ─────────────────────")
    print(f"  OVERALL:       {summary['overall']:.3f} / 1.0")
    print(f"{'='*60}\n")
    
    return summary


if __name__ == "__main__":
    run_evaluation()

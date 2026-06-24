import json
import re
from dataclasses import dataclass
from typing import Optional, Any, Dict, List
import requests

@dataclass
class TeacherScores:
    faithfulness: float
    relevance: float
    completeness: float
    conciseness: float
    latency_score: float

    @property
    def overall(self) -> float:
        return (self.faithfulness + self.relevance + self.completeness + self.conciseness) / 4.0

@dataclass
class TeacherAssessment:
    scores: TeacherScores
    error_category: str
    critique: str
    suggestion: str

def parse_teacher_response(text: str) -> Optional[TeacherAssessment]:
    print("\n--- RAW QWEN OUTPUT ---\n", text, "\n-----------------------\n")
    try:
        # Remove <think>...</think> blocks if present
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        
        # Try to find a JSON block in markdown
        match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            # Fallback: find the first { and last }
            start = text.find('{')
            end = text.rfind('}')
            if start == -1 or end == -1 or start > end:
                return None
            json_str = text[start:end+1]
            
        data = json.loads(json_str)
        scores = TeacherScores(
            faithfulness=float(data.get("faithfulness", 0.0)),
            relevance=float(data.get("relevance", 0.0)),
            completeness=float(data.get("completeness", 0.0)),
            conciseness=float(data.get("conciseness", 0.0)),
            latency_score=float(data.get("latency_score", 0.0))
        )
        return TeacherAssessment(
            scores=scores,
            error_category=data.get("error_category", ""),
            critique=data.get("critique", ""),
            suggestion=data.get("suggestion", "")
        )
    except Exception:
        return None

def infer_error_category(scores: TeacherScores) -> str:
    if scores.faithfulness < 0.5:
        return "hallucination"
    if scores.latency_score < 0.5:
        return "slow_response"
    if scores.relevance < 0.5:
        return "retrieval_miss"
    if scores.completeness < 0.5:
        return "incomplete_answer"
    return "ok"

class TeacherEvaluator:
    def __init__(self, pipeline: Any):
        self.pipeline = pipeline

    def evaluate_one(self, question: str, answer: str, retrieved_chunks: List[Dict[str, Any]], latency_sec: float) -> Optional[TeacherAssessment]:
        try:
            context = self.pipeline.build_context(retrieved_chunks, max_tokens=1500)
            llm = self.pipeline.load_llm()
            
            prompt = f"""You are a strict teacher evaluating an AI assistant.
Question: {question}
Context: {context}
Answer: {answer}
Latency: {latency_sec} seconds.

Output a JSON object with:
- faithfulness (0.0 to 1.0)
- relevance (0.0 to 1.0)
- completeness (0.0 to 1.0)
- conciseness (0.0 to 1.0)
- latency_score (0.0 to 1.0)
- error_category (string: hallucination, slow_response, retrieval_miss, incomplete_answer, or ok)
- critique (string)
- suggestion (string)"""

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {llm.api_key}"
            }
            payload = {
                "model": llm.model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1,
                "max_tokens": 2000,
                "stream": False
            }
            # For testing with fake pipeline/llm, we just do a request. 
            # Note: The test doesn't actually call `evaluate_one` directly in Step 1, but we implement it as specified.
            response = requests.post(f"{llm.base_url}/v1/chat/completions", json=payload, headers=headers, timeout=180)
            response.raise_for_status()
            
            message = response.json()["choices"][0]["message"]
            content = message.get("content") or ""
            reasoning = message.get("reasoning") or ""
            result_text = str(content) + "\n" + str(reasoning)
            
            return parse_teacher_response(result_text)
        except Exception:
            return None

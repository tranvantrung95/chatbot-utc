import argparse
import json
import os
import time
from collections import defaultdict
from typing import List, Dict, Any

from src.evaluation_trace import StageTimer, summarize_latencies
from src.rag_pipeline import UTCRAGPipeline
from src.teacher_evaluator import TeacherEvaluator

class EvalRunner:
    def __init__(self, pipeline, teacher):
        self.pipeline = pipeline
        self.teacher = teacher

    def evaluate_questions(self, questions: List[Dict[str, Any]], top_k: int = 3) -> Dict[str, Any]:
        results = []
        error_counts = defaultdict(int)
        total_overall_score = 0.0
        latencies = []

        for q_item in questions:
            question = q_item["question"]
            timer = StageTimer()
            start_time = time.time()

            with timer.stage("retrieval"):
                retrieved = self.pipeline.retrieve(question, top_k=top_k)
            
            with timer.stage("generation"):
                answer, _, _ = self.pipeline.query(question, top_k=top_k)
            
            total_latency = time.time() - start_time
            latencies.append(total_latency)
            
            with timer.stage("judge"):
                assessment = self.teacher.evaluate_one(
                    question, answer, retrieved, latency_sec=total_latency
                )
            
            if assessment is not None:
                if assessment.scores:
                    total_overall_score += assessment.scores.overall
                if assessment.error_category:
                    error_counts[assessment.error_category] += 1
            else:
                error_counts["evaluator_error"] += 1
            
            results.append({
                "question": question,
                "answer": answer,
                "assessment": assessment,
                "timings": timer.timings,
                "total_latency": total_latency
            })

        num_evaluated = len(results)
        avg_overall = total_overall_score / num_evaluated if num_evaluated > 0 else 0.0
        
        latency_summary = summarize_latencies(latencies) if latencies else {}

        recommendations = []
        if error_counts.get("retrieval_miss", 0) > 0:
            recommendations.append({"area": "retrieval", "suggestion": "review chunking, query expansion, and top_k"})
        if error_counts.get("hallucination", 0) > 0:
            recommendations.append({"area": "hallucination", "suggestion": "stricter faithfulness validation and shorter grounded prompt"})
        if error_counts.get("slow_response", 0) > 0:
            recommendations.append({"area": "latency", "suggestion": "reducing thinking/max tokens, caching retrieval, and limiting web search"})
        if error_counts.get("incomplete_answer", 0) > 0:
            recommendations.append({"area": "completeness", "suggestion": "increasing context coverage and improving rerank"})

        return {
            "summary": {
                "total": len(questions),
                "evaluated": num_evaluated,
                "overall": avg_overall,
                "error_categories": dict(error_counts),
                "latency": latency_summary
            },
            "results": results,
            "recommendations": recommendations
        }

def run_teacher_evaluation(questions_path=None, limit=20, output_path=None):
    if not questions_path or not os.path.exists(questions_path):
        print(f"Error: Questions file not found at {questions_path}")
        return

    with open(questions_path, "r", encoding="utf-8") as f:
        questions = json.load(f)

    if not isinstance(questions, list):
        print("Error: Questions should be a list of dictionaries.")
        return

    pipeline = UTCRAGPipeline()
    teacher = TeacherEvaluator(pipeline)
    runner = EvalRunner(pipeline, teacher)

    print(f"Starting teacher evaluation for up to {limit} questions...")
    report = runner.evaluate_questions(questions[:limit])

    if output_path:
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=lambda o: o.__dict__ if hasattr(o, '__dict__') else str(o))
        print(f"Evaluation report saved to {output_path}")
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, default=lambda o: o.__dict__ if hasattr(o, '__dict__') else str(o)))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Teacher Evaluation Loop")
    parser.add_argument("--questions", required=True, help="Path to JSON file containing questions")
    parser.add_argument("--limit", type=int, default=20, help="Maximum number of questions to evaluate")
    parser.add_argument("--output", help="Path to save the evaluation report JSON")
    args = parser.parse_args()

    run_teacher_evaluation(args.questions, args.limit, args.output)

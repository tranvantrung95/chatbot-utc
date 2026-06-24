import unittest
from src.teacher_evaluator import parse_teacher_response, TeacherScores, infer_error_category
from src.evaluation_trace import StageTimer, summarize_latencies

class TeacherEvaluatorTests(unittest.TestCase):
    def test_parse_teacher_response_extracts_json_with_scores_and_category(self):
        text = 'prefix {"faithfulness": 0.9, "relevance": 0.8, "completeness": 0.7, "conciseness": 0.6, "latency_score": 0.5, "error_category": "retrieval_miss", "critique": "Thiếu nguồn.", "suggestion": "Tăng top_k."} suffix'
        result = parse_teacher_response(text)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result.scores.overall, 0.75)
        self.assertEqual(result.error_category, "retrieval_miss")
        self.assertEqual(result.suggestion, "Tăng top_k.")

    def test_infer_error_category_prioritizes_hallucination_then_latency(self):
        self.assertEqual(infer_error_category(TeacherScores(0.4, 0.9, 0.9, 0.9, 0.9)), "hallucination")
        self.assertEqual(infer_error_category(TeacherScores(0.9, 0.9, 0.9, 0.9, 0.2)), "slow_response")

class StageTimerTests(unittest.TestCase):
    def test_stage_timer_records_named_stage(self):
        class FakeClock:
            def __init__(self, times):
                self.times = iter(times)
            def __call__(self):
                return next(self.times)

        timer = StageTimer(clock=FakeClock([10.0, 12.5]))
        with timer.stage("retrieval"):
            pass
        self.assertEqual(timer.timings, {"retrieval_sec": 2.5})

    def test_summarize_latencies_reports_percentiles(self):
        summary = summarize_latencies([1.0, 2.0, 3.0, 10.0])
        self.assertEqual(summary["avg_latency_sec"], 4.0)
        self.assertEqual(summary["p50_latency_sec"], 2.5) # NOTE: median of 1,2,3,10 is 2.5
        self.assertEqual(summary["p95_latency_sec"], 10.0) # approx

if __name__ == "__main__":
    unittest.main()

class EvalRunnerTests(unittest.TestCase):
    def test_eval_runner_aggregates_quality_latency_and_advice(self):
        class FakePipeline:
            def retrieve(self, q, top_k): return [{"id": "chunk1"}]
            def query(self, q, top_k): return "fake answer", ""

        class FakeTeacher:
            def evaluate_one(self, q, a, ret, latency_sec, timings):
                from src.teacher_evaluator import TeacherAssessment, TeacherScores
                return TeacherAssessment(
                    scores=TeacherScores(0.9, 0.9, 0.9, 0.9, 0.5), # overall = 0.9 (since latency is excluded)
                    error_category="retrieval_miss",
                    critique="fake critique",
                    suggestion="fake suggestion"
                )

        from src.eval_runner import EvalRunner
        runner = EvalRunner(pipeline=FakePipeline(), teacher=FakeTeacher())
        report = runner.evaluate_questions([{"id": "Q1", "question": "Học phí đóng thế nào?"}])
        self.assertEqual(report["summary"]["total"], 1)
        self.assertEqual(report["summary"]["evaluated"], 1)
        self.assertEqual(report["summary"]["overall"], 0.9)
        self.assertEqual(report["summary"]["error_categories"], {"retrieval_miss": 1})
        self.assertIn("retrieval", report["recommendations"][0]["area"])

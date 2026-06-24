# Teacher Eval Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an offline teacher/evaluation loop that lets a stronger LLM judge UTC Assistant answers, classify failure causes, measure latency stages, and produce optimization advice.

**Architecture:** Keep the production chat path unchanged for this first slice. Add focused backend modules under `utc-assistant/src/` for teacher scoring, stage timing, and report generation, with unittest coverage that uses fake pipeline/LLM objects instead of network calls.

**Tech Stack:** Python 3.9+, stdlib `dataclasses`, `json`, `time`, `unittest`; existing `UTCRAGPipeline` interface.

---

## File Structure

- Create `utc-assistant/src/teacher_evaluator.py`: parse teacher JSON, hold score/assessment dataclasses, infer error categories, and call an OpenAI-compatible chat model through the existing pipeline LLM client.
- Create `utc-assistant/src/evaluation_trace.py`: small timing helper for retrieval/generation/judge stages.
- Create `utc-assistant/src/eval_runner.py`: run a batch of test questions through a pipeline and teacher, aggregate quality/performance, and emit optimization advice.
- Create `utc-assistant/tests/test_teacher_eval_loop.py`: unit tests for parser, category inference, timing summaries, and batch aggregation.
- Create `docs/superpowers/plans/2026-06-23-teacher-eval-loop.md`: this implementation plan.

## Success Criteria

- New tests in `utc-assistant/tests/test_teacher_eval_loop.py` pass.
- `python3 -m py_compile src/*.py` passes.
- Full baseline test status is reported; as of branch setup, full `unittest discover` has one pre-existing failure in `tests/test_rag_pipeline.py::OllamaResponseTests.test_extract_answer_uses_thinking_when_content_is_empty`.
- No production answer behavior changes in `api_server.py`, `chat_stream.py`, or `rag_pipeline.py`.

### Task 1: Teacher Assessment Core

**Files:**
- Create: `utc-assistant/src/teacher_evaluator.py`
- Test: `utc-assistant/tests/test_teacher_eval_loop.py`

- [ ] **Step 1: Write failing parser/category tests**

Add tests that import `parse_teacher_response`, `TeacherScores`, and `infer_error_category`:

```python
def test_parse_teacher_response_extracts_json_with_scores_and_category(self):
    text = 'prefix {"faithfulness": 0.9, "relevance": 0.8, "completeness": 0.7, "conciseness": 0.6, "latency_score": 0.5, "error_category": "retrieval_miss", "critique": "Thiếu nguồn.", "suggestion": "Tăng top_k."} suffix'
    result = parse_teacher_response(text)
    self.assertIsNotNone(result)
    self.assertEqual(result.scores.overall, 0.75)
    self.assertEqual(result.error_category, "retrieval_miss")
    self.assertEqual(result.suggestion, "Tăng top_k.")

def test_infer_error_category_prioritizes_hallucination_then_latency(self):
    self.assertEqual(infer_error_category(TeacherScores(0.4, 0.9, 0.9, 0.9, 0.9)), "hallucination")
    self.assertEqual(infer_error_category(TeacherScores(0.9, 0.9, 0.9, 0.9, 0.2)), "slow_response")
```

- [ ] **Step 2: Run tests to verify RED**

Run: `python3 -m unittest tests.test_teacher_eval_loop.TeacherEvaluatorTests -v`

Expected: FAIL because `src.teacher_evaluator` does not exist.

- [ ] **Step 3: Implement minimal teacher evaluator**

Create `TeacherScores`, `TeacherAssessment`, `parse_teacher_response`, `infer_error_category`, and `TeacherEvaluator.evaluate_one(...)`. The evaluator should:

- Build context with `pipeline.build_context(context_chunks, max_tokens=1500)`.
- Call `pipeline.load_llm()`.
- POST to `{llm.base_url}/v1/chat/completions`.
- Use `temperature=0.1`, `max_tokens=700`, `enable_thinking=False`.
- Return `None` if parsing or the provider call fails.

- [ ] **Step 4: Run tests to verify GREEN**

Run: `python3 -m unittest tests.test_teacher_eval_loop.TeacherEvaluatorTests -v`

Expected: PASS.

### Task 2: Stage Timing Trace

**Files:**
- Create: `utc-assistant/src/evaluation_trace.py`
- Test: `utc-assistant/tests/test_teacher_eval_loop.py`

- [ ] **Step 1: Write failing timing tests**

Add tests for `StageTimer` and `summarize_latencies`:

```python
def test_stage_timer_records_named_stage(self):
    timer = StageTimer(clock=FakeClock([10.0, 12.5]))
    with timer.stage("retrieval"):
        pass
    self.assertEqual(timer.timings, {"retrieval_sec": 2.5})

def test_summarize_latencies_reports_percentiles(self):
    summary = summarize_latencies([1.0, 2.0, 3.0, 10.0])
    self.assertEqual(summary["avg_latency_sec"], 4.0)
    self.assertEqual(summary["p50_latency_sec"], 3.0)
    self.assertEqual(summary["p95_latency_sec"], 10.0)
```

- [ ] **Step 2: Run tests to verify RED**

Run: `python3 -m unittest tests.test_teacher_eval_loop.StageTimerTests -v`

Expected: FAIL because `src.evaluation_trace` does not exist.

- [ ] **Step 3: Implement minimal timing helper**

Create:

- `StageTimer(clock=time.time)`.
- `StageTimer.stage(name)` context manager that stores `<name>_sec` rounded to 4 decimals.
- `summarize_latencies(values)` returning count, avg, p50, p95, max rounded to 2 decimals.

- [ ] **Step 4: Run tests to verify GREEN**

Run: `python3 -m unittest tests.test_teacher_eval_loop.StageTimerTests -v`

Expected: PASS.

### Task 3: Batch Eval Runner and Optimization Advice

**Files:**
- Create: `utc-assistant/src/eval_runner.py`
- Test: `utc-assistant/tests/test_teacher_eval_loop.py`

- [ ] **Step 1: Write failing runner tests**

Add a fake pipeline and fake teacher test:

```python
def test_eval_runner_aggregates_quality_latency_and_advice(self):
    runner = EvalRunner(pipeline=FakePipeline(), teacher=FakeTeacher())
    report = runner.evaluate_questions([{"id": "Q1", "question": "Học phí đóng thế nào?"}])
    self.assertEqual(report["summary"]["total"], 1)
    self.assertEqual(report["summary"]["evaluated"], 1)
    self.assertEqual(report["summary"]["overall"], 0.86)
    self.assertEqual(report["summary"]["error_categories"], {"retrieval_miss": 1})
    self.assertIn("retrieval", report["recommendations"][0]["area"])
```

- [ ] **Step 2: Run tests to verify RED**

Run: `python3 -m unittest tests.test_teacher_eval_loop.EvalRunnerTests -v`

Expected: FAIL because `src.eval_runner` does not exist.

- [ ] **Step 3: Implement minimal runner**

Create `EvalRunner.evaluate_questions(...)` that for each question:

- Records retrieval stage around `pipeline.retrieve(question, top_k=top_k)`.
- Records generation stage around `pipeline.query(question, top_k=top_k)`.
- Records judge stage around `teacher.evaluate_one(question, answer, retrieved, latency_sec=total_latency, timings=timer.timings)`.
- Aggregates average teacher scores, latency summary, error category counts, per-item results, and recommendations.

Recommendations should be deterministic:

- `retrieval_miss`: suggest reviewing chunking, query expansion, and `top_k`.
- `hallucination`: suggest stricter faithfulness validation and shorter grounded prompt.
- `slow_response`: suggest reducing thinking/max tokens, caching retrieval, and limiting web search.
- `incomplete_answer`: suggest increasing context coverage and improving rerank.

- [ ] **Step 4: Run tests to verify GREEN**

Run: `python3 -m unittest tests.test_teacher_eval_loop.EvalRunnerTests -v`

Expected: PASS.

### Task 4: CLI Entry and Documentation

**Files:**
- Modify: `utc-assistant/src/eval_runner.py`
- Modify: `utc-assistant/README.md`

- [ ] **Step 1: Add CLI smoke behavior**

Add `run_teacher_evaluation(questions_path=None, limit=20, output_path=None)` and a `__main__` entry that accepts:

```text
python -m src.eval_runner --questions data/autotest/questions.json --limit 20 --output data/runtime/teacher_eval_report.json
```

- [ ] **Step 2: Add README usage**

Add a short "Teacher evaluation loop" section with the command above and note that it is offline and uses the configured LLM provider.

- [ ] **Step 3: Verify**

Run:

```bash
python3 -m unittest tests.test_teacher_eval_loop -v
python3 -m py_compile src/*.py
```

Expected: PASS.

## Final Verification

Run:

```bash
python3 -m unittest tests.test_teacher_eval_loop -v
python3 -m py_compile src/*.py
python3 -m unittest discover -s tests -v
```

Expected:

- The new teacher eval tests pass.
- `py_compile` passes.
- Full unittest may still show the pre-existing baseline failure in `test_extract_answer_uses_thinking_when_content_is_empty`; do not claim full suite green unless that unrelated baseline is fixed separately.


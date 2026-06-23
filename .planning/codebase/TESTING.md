# TESTING

**Date:** 2026-06-23
**Focus:** Framework, structure, mocking, coverage

## Backend (`utc-assistant`)
- **Framework:** `pytest` is used as the test runner (indicated by `.pytest_cache`).
- **Test Locations:** Tests are colocated in the `utc-assistant/tests/` directory.
- **Test Coverage:** Key functionalities are tested, including:
  - Document Store: `test_document_store.py`
  - RAG Pipeline: `test_rag_pipeline.py`, `test_pipeline.py`
  - Chat Routing: `test_chat_routing.py`
  - Teacher Evaluation Loop: `test_teacher_eval_loop.py`
- **Root Level Scripts:** A root level `test_reranker.py` exists, possibly used for exploratory or integration testing.

## Frontend (`utc-assistant-web`)
- **Framework:** No dedicated test framework (like Jest or Playwright) is visible in the root or `package.json` scripts, suggesting testing may currently rely on manual validation or E2E tests are stored elsewhere.

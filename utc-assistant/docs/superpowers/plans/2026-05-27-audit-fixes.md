# Audit Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix CRITICAL and HIGH issues from the 2026-05-27 codebase audit.

**Architecture:** Targeted surgical fixes — each task touches only what's needed. No refactoring beyond the issue scope.

**Tech Stack:** Python 3.9+, FastAPI, pytest, Next.js 15

---

## Priority: CRITICAL (3 issues)

### Task 1: Fix test `settings.ollama_url` → split fields

**Files:**
- Modify: `tests/test_rag_pipeline.py:14-37`

- [ ] **Step 1: Update test to use `embed_base_url` and `llm_base_url`**

The Settings dataclass has `embed_base_url` and `llm_base_url` (not `ollama_url`).
The test sets OLLAMA_URL which maps to both base URLs via legacy fallback in `load_settings()`.
Fix the assertion to check the correct fields:

```python
class SettingsTests(unittest.TestCase):
    def test_load_settings_from_env_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            env_path = Path(tmp) / ".env"
            env_path.write_text(
                "LLM_BASE_URL=http://llm.test:8103\n"
                "EMBED_BASE_URL=http://embed.test:8008\n"
                "EMBED_MODEL=test-embed\n"
                "LLM_MODEL=test-llm\n"
                "CHUNK_SIZE=700\n"
                "CHUNK_OVERLAP=120\n"
                "TOP_K=7\n"
                "LLM_MAX_TOKENS=2400\n",
                encoding="utf-8",
            )

            settings = load_settings(env_path=env_path)

        self.assertEqual(settings.embed_base_url, "http://embed.test:8008")
        self.assertEqual(settings.llm_base_url, "http://llm.test:8103")
        self.assertEqual(settings.embed_model, "test-embed")
        self.assertEqual(settings.llm_model, "test-llm")
        self.assertEqual(settings.chunk_size, 700)
        self.assertEqual(settings.chunk_overlap, 120)
        self.assertEqual(settings.top_k, 7)
        self.assertEqual(settings.llm_max_tokens, 2400)
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd /Users/trantrung/CAOHOC_CNTT/mo_hinh_ngon_ngu_lon/utc-assistant && PYTHONPATH=. python -m pytest tests/test_rag_pipeline.py::SettingsTests -v`
Expected: 1 passed

---

### Task 2: Fix test `extract_answer` data format

**Files:**
- Modify: `tests/test_rag_pipeline.py:68-99`

- [ ] **Step 1: Update test to use OpenAI-compatible `choices` format**

The `extract_answer` method expects OpenAI-compatible format: `{"choices": [{"message": {...}}]}`.
The tests pass a flat `{"message": {...}}` dict — they will fail at `data.get("choices")`.

```python
class OllamaResponseTests(unittest.TestCase):
    def test_extract_answer_removes_qwen_thinking_prefix(self):
        answer = OllamaLLM.extract_answer(
            {
                "choices": [
                    {
                        "message": {
                            "content": (
                                "Okay, I will reason first.\n"
                                "</think>\n\n"
                                "Điều kiện xét tốt nghiệp là tích lũy đủ tín chỉ."
                            )
                        }
                    }
                ]
            }
        )
        self.assertEqual(answer, "Điều kiện xét tốt nghiệp là tích lũy đủ tín chỉ.")

    def test_extract_answer_uses_thinking_when_content_is_empty(self):
        answer = OllamaLLM.extract_answer(
            {
                "choices": [
                    {
                        "message": {
                            "content": "",
                            "reasoning": (
                                "This is hidden reasoning. Final answer: "
                                "UTC là Trường Đại học Giao thông Vận tải."
                            ),
                        }
                    }
                ]
            }
        )
        self.assertEqual(answer, "UTC là Trường Đại học Giao thông Vận tải.")

    def test_extract_answer_reports_truncated_empty_response(self):
        with self.assertRaises(RuntimeError) as context:
            OllamaLLM.extract_answer(
                {
                    "choices": [
                        {
                            "message": {"content": "", "reasoning": "unfinished reasoning"},
                        }
                    ]
                }
            )
        self.assertIn("empty assistant content", str(context.exception))
```

- [ ] **Step 2: Run tests to verify they pass**

Run: `cd /Users/trantrung/CAOHOC_CNTT/mo_hinh_ngon_ngu_lon/utc-assistant && PYTHONPATH=. python -m pytest tests/test_rag_pipeline.py::OllamaResponseTests -v`
Expected: 3 passed

---

### Task 3: Replace SHA-256 with bcrypt for password hashing

**Files:**
- Modify: `utc-assistant/src/api_server.py`
- Modify: `utc-assistant/requirements.txt`

- [ ] **Step 1: Add bcrypt to requirements.txt**

Add `bcrypt>=4.0.0` to requirements.txt.

- [ ] **Step 2: Update hash_password and related functions in api_server.py**

Replace:

```python
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()
```

With:

```python
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
```

- [ ] **Step 3: Update all comparison sites from `== hash_password()` to `verify_password()`**

In `api_login` (line 357): `user.get("password_hash") != hash_password(payload.password)` → `not verify_password(payload.password, user.get("password_hash"))`

In `api_change_password` (line 398): `current_user.get("password_hash") != hash_password(payload.current_password)` → `not verify_password(payload.current_password, current_user.get("password_hash", ""))`

- [ ] **Step 4: Regenerate seed passwords with bcrypt**

The seed_users function has hardcoded hashes. Since these are sha256 hashes, we need to regenerate. The simplest approach: seed with the bcrypt hash of "12345678".

Replace `hash_password("12345678")` calls in seed_users() with a pre-computed bcrypt hash. Actually, since hash_password is now bcrypt-based, the function call itself will produce bcrypt hashes. But we need the seed data to work with the new verify function. Just let hash_password run — it'll now produce bcrypt.

- [ ] **Step 5: Run tests to verify nothing breaks**

Run: `cd /Users/trantrung/CAOHOC_CNTT/mo_hinh_ngon_ngu_lon/utc-assistant && PYTHONPATH=. python -m pytest tests/ -v`
Expected: All tests pass

---

## Priority: HIGH (5 issues)

### Task 4: Remove streamlit from requirements.txt

**Files:**
- Modify: `utc-assistant/requirements.txt`

Remove line 2: `streamlit>=1.30.0`

### Task 5: Update DESIGN.md — remove Streamlit references

**Files:**
- Modify: `utc-assistant/DESIGN.md`

Replace the "Implementation Notes" section (lines 58-62) with Next.js-focused notes:

```markdown
## Implementation Notes
- Next.js 15 App Router with shadcn/ui components.
- Layout max-width: 1120px for readability.
- Sidebar and main content share the same token palette.
- Chat uses dedicated `chatBg`, `inputBg`, `send`, and `sendHover` tokens.
- Model badge shown on every assistant response.
```

### Task 6: Add pytesseract to requirements.txt

**Files:**
- Modify: `utc-assistant/requirements.txt`

Add `pytesseract>=0.3.0` (used in `_tesseract_ocr` fallback in document_store.py).

### Task 7: Add bcrypt to requirements.txt

Already handled in Task 3 Step 1.

### Task 8: Remove unused `hashlib` import if no longer needed

After Task 3, check if `hashlib` is still used elsewhere in api_server.py. The `hash_password` was the only consumer. Remove `import hashlib` from api_server.py line 5 if no other usage.

---

## Run Full Test Suite

- [ ] Run all tests to confirm everything passes:
```bash
cd /Users/trantrung/CAOHOC_CNTT/mo_hinh_ngon_ngu_lon/utc-assistant && PYTHONPATH=. python -m pytest tests/ -v
```

- [ ] Run syntax check:
```bash
cd /Users/trantrung/CAOHOC_CNTT/mo_hinh_ngon_ngu_lon/utc-assistant && python -m py_compile src/*.py
```

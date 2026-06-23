# CONCERNS

**Date:** 2026-06-23
**Focus:** Tech debt, bugs, security, performance, fragile areas

## Security Concerns
- **Prompt Injection:** Since the backend handles RAG and LLM prompts, it may be susceptible to prompt injection attacks by users (students) trying to manipulate the LLM's responses.
- **RBAC Enforcement:** Ensure that the API strictly validates whether a user is an `admin` or a `student` before allowing them to access specific endpoints (e.g., viewing other students' data or updating document stores).
- **Environment Variables:** Secrets (like LLM API keys and database passwords) must not be committed. The `.env` file must remain correctly `.gitignore`d.

## Technical Debt & Architecture
- **Monorepo Structure:** The backend (`utc-assistant`) and frontend (`utc-assistant-web`) reside in the same repository but lack a formal monorepo tool (like Turborepo), meaning there is no shared linting or unified build orchestration natively across the two.
- **Frontend Testing:** The Next.js frontend currently lacks a formal testing suite, which might lead to regressions as UI complexity grows.

## Performance
- **RAG Latency:** Extracting documents, embedding queries, and waiting for the LLM can introduce high latency. The use of `deep_reranker.py` and `cross_encoder.py` adds accuracy but increases response time.
- **Streaming:** The presence of `chat_stream.py` suggests streaming is intended, which is critical to mitigate perceived latency for end-users.

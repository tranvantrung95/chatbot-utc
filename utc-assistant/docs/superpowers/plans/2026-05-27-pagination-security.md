# Pagination + Security Hardening Plan

**Goal:** Add pagination to all list APIs + rate limiting for security.

**Architecture:** 
- Reusable paginate() helper with page/page_size query params
- In-memory rate limiter decorator for chat + auth endpoints
- Surgical changes only — no refactoring

---

### Task 1: Add pagination helper + apply to list endpoints

**Files:** Modify `src/api_server.py`

**Steps:**
1. Add PaginatedResponse model + paginate() helper function
2. Apply to: GET /api/users, /api/questions, /api/feedback, /api/bugs, /api/documents
3. Standard response: `{items, page, page_size, total, total_pages}`

### Task 2: Add in-memory rate limiter

**Files:** Modify `src/api_server.py`

**Steps:**
1. Add RateLimiter class (dict-based, sliding window)
2. Apply decorator to POST /api/chat (5 req/min)
3. Apply to POST /api/auth/login (10 req/min)
4. Add 429 response with Retry-After header

### Task 3: Verify
- Run all tests
- Syntax check

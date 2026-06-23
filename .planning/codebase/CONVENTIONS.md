# CONVENTIONS

**Date:** 2026-06-23
**Focus:** Code style, naming, patterns, error handling

## Backend (`utc-assistant`)
- **Naming Conventions:** `snake_case` for variables, functions, and module names. `PascalCase` for classes.
- **Modularity:** Highly modular structure. AI logic is separated into specific pipelines (e.g., `rag_pipeline.py`, `eval_runner.py`).
- **Error Handling:** FastAPI exception handlers and HTTP exceptions are likely used for API boundaries.

## Frontend (`utc-assistant-web`)
- **Framework Conventions:** Next.js App Router conventions are strictly followed (`page.tsx`, `layout.tsx`).
- **Styling:** Utility-first styling via Tailwind CSS. Class merging is handled via `clsx` and `tailwind-merge` (common in `shadcn/ui` style codebases).
- **Linting & Formatting:** ESLint is configured (`eslint.config.mjs`) alongside standard TypeScript checks (`tsconfig.json`).
- **Naming Conventions:** `kebab-case` for directory names. `PascalCase` for React components.

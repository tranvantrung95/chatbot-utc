# STRUCTURE

**Date:** 2026-06-23
**Focus:** Directory layout and organization

## Root Level
- `utc-assistant/` - Backend Python application.
- `utc-assistant-web/` - Frontend Next.js application.
- `*.py` scripts - Various standalone scripts (e.g., `gen_report.py`, `build_full.py`) used for building/generating reports or artifacts.
- Documentation & Design files (`.pdf`, `.docx`, `diagrams/`, `infographic/`).

## Backend (`utc-assistant/`)
- `src/` - Core Python modules.
  - `api_server.py` - FastAPI entry point.
  - `rag_pipeline.py` - Core RAG logic.
  - `agentic_orchestrator.py` - Task routing / sub-agent orchestration.
  - `document_store.py` - Vector DB integration.
  - `database.py` - Relational DB integration.
- `tests/` - Unit and integration tests.
- `utils/` - Utility scripts and helpers.
- `data/`, `assets/`, `docs/`, `config/`, `scripts/` - Supporting directories.
- `pages/` - Potential remnants of a Streamlit app or static templates.

## Frontend (`utc-assistant-web/`)
- `src/app/` - Next.js App Router paths.
  - `/login`, `/register`, `/forgot-password` - Authentication flows.
  - `/admin`, `/student` - Role-based dashboards/pages.
- `src/components/` - React components (Radix UI + Tailwind).
- `src/lib/` - Frontend utility functions and API clients.
- `public/` - Static assets.
- `tailwind.config.ts`, `postcss.config.mjs` - Styling configuration.

## Naming Conventions
- Backend files use `snake_case` (e.g., `api_server.py`, `rag_pipeline.py`).
- Frontend components and files generally use Next.js conventions (`page.tsx`, `layout.tsx`) and `kebab-case` or `PascalCase` for components.

# ARCHITECTURE

**Date:** 2026-06-23
**Focus:** System design and patterns

## System Overview
The project is a conversational assistant system ("UTC Assistant") split into two main components:
1. **Backend API (`utc-assistant`)**: A FastAPI Python application providing LLM integration, Retrieval-Augmented Generation (RAG), authentication, and core business logic.
2. **Frontend UI (`utc-assistant-web`)**: A Next.js (App Router) TypeScript application for user interaction, featuring roles (Admin, Student, etc.).

## Key Layers & Data Flow

### Backend (`utc-assistant`)
- **Entry Point:** `src/api_server.py` hosts the FastAPI application and REST endpoints.
- **RAG Pipeline:** Handled in `src/rag_pipeline.py`. Includes retrieval from ChromaDB (`document_store.py`), intent classification (`intent_classifier.py`), and reranking (`deep_reranker.py`, `cross_encoder.py`).
- **Data & Documents:** `document_store.py` manages document embeddings. `structured_chunker.py` preprocesses incoming docs. `database.py` manages PostgreSQL transactions.
- **Agents & Evaluation:** `agentic_orchestrator.py` likely manages multi-agent interactions or task routing. Evaluation modules (`eval_runner.py`, `llm_judge.py`, `teacher_evaluator.py`, `evaluation_trace.py`) exist for testing/grading response quality.
- **Interfacing:** `chat_stream.py` suggests streaming LLM responses back to the frontend.

### Frontend (`utc-assistant-web`)
- **App Router (`src/app`):** The application is organized by route groups or functional areas (e.g., `/admin`, `/student`, `/login`, `/register`).
- **Components (`src/components`):** Reusable UI building blocks using Radix UI and Tailwind CSS.
- **Styling:** Defined in `src/app/globals.css` and `tailwind.config.ts`. Design tokens managed centrally (`design-tokens.json`).

## Architecture Patterns
- **Client-Server Architecture:** Decoupled RESTful backend and React-based frontend.
- **RAG (Retrieval-Augmented Generation):** The primary mechanism for the assistant to answer questions using ingested documents.
- **Role-Based Access Control (RBAC):** UI routing explicitly segregates `admin` and `student` experiences.

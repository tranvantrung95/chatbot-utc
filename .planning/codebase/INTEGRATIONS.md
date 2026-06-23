# INTEGRATIONS

**Date:** 2026-06-23
**Focus:** External services and APIs

## Databases
- **PostgreSQL:** Primary relational database (used by `utc-assistant` via `psycopg2`).
- **ChromaDB:** Local/Embedded vector database for RAG pipeline (`utc-assistant` via `chromadb`).

## External APIs & Services
- **LLM/Embeddings Providers:** Relies on external model providers (evident from RAG pipeline, cross-encoder, deep reranker in backend). Exact providers (e.g., OpenAI, Gemini, Hugging Face) likely configured via `.env`.
- **Chandra OCR:** Potentially an external OCR service or internal library wrapper (`chandra_ocr.py`).

## Authentication
- **Local/Token Auth:** Handled via `bcrypt` for password hashing, likely custom token generation using FastAPI security utilities.

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Model Configuration**: Updated all LLM references across the system (`rag_pipeline.py`, `api_server.py`, `deep_reranker.py`, `llm_judge.py`) to use `qwen36-35b-moe`.
- **Retrieval Thresholds**: Raised the `web_search_threshold` threshold from `0.035` to `0.35` in `route_policy.py` (`build_retrieval_probe`), ensuring high-quality semantic matches aren't incorrectly masked by low Reciprocal Rank Fusion (RRF) scores.
- **RAG Scoring Logic**: Modified the system to check `dense_score` natively before falling back to `score` when evaluating confidence for Web Search. This correctly addresses situations where RRF normalisation yielded artificially low numbers.
- **Web Fallback Handling**: Refactored hybrid retrieval results in `rag_pipeline.py` and `api_server.py` to ensure Web Search results dynamically merge and maintain top ranking precedence based on correctly parsed float scores.

### Fixed
- Fixed an anti-pattern in `rag_pipeline.py` that checked `locals()` for `web_results`. Explicitly initialized the list.
- Fixed a missing type cast (`float()`) when sorting dynamically appended web results.

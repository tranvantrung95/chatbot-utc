# Source: Quy trình Naive RAG
**Figure:** Hình 3.3
**Type:** process
**Description:** 4 bước Naive RAG: 1.Indexing (PDF→Chunks→DB), 2.Embedding (Text→Vector 1024d), 3.Retrieving (Query→Top-K chunks), 4.Generating (Context+LLM→Answer). Có feedback loop từ Generating về Retrieving.

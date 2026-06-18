import tempfile
import unittest
from pathlib import Path

from src.rag_pipeline import (
    OllamaLLM,
    Settings,
    UTCRAGPipeline,
    load_settings,
)


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


class ChunkingTests(unittest.TestCase):
    def test_long_text_chunks_have_overlap(self):
        text = " ".join(f"token{i}" for i in range(180))

        chunks = UTCRAGPipeline.chunk_text(text, chunk_size=220, overlap=60)

        self.assertGreater(len(chunks), 2)
        for previous, current in zip(chunks, chunks[1:]):
            previous_words = set(previous["content"].split()[-12:])
            current_words = set(current["content"].split()[:20])
            self.assertTrue(previous_words & current_words)

    def test_load_documents_skips_generated_combined_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw_dir = Path(tmp)
            (raw_dir / "source.txt").write_text(
                "# Source\n\nUseful content " * 10,
                encoding="utf-8",
            )
            (raw_dir / "utc_combined.txt").write_text(
                "# Combined\n\nDuplicate generated content " * 10,
                encoding="utf-8",
            )

            docs = UTCRAGPipeline().load_documents(raw_dir=raw_dir)

        self.assertEqual([doc["title"] for doc in docs], ["Source"])


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

    def test_extract_answer_falls_back_to_reasoning_when_content_empty(self):
        answer = OllamaLLM.extract_answer(
            {
                "choices": [
                    {
                        "message": {"content": "", "reasoning": "unfinished reasoning"},
                    }
                ]
            }
        )
        self.assertEqual(answer, "unfinished reasoning")


class QueryTests(unittest.TestCase):
    def test_rerank_prefers_specific_query_terms_over_generic_terms(self):
        items = [
            {
                "title": "FAQ",
                "content": "### Chuẩn đầu ra của sinh viên UTC là gì?",
                "source": "faq.txt",
                "score": 0.70,
            },
            {
                "title": "Sổ tay sinh viên",
                "content": "Điều kiện xét tốt nghiệp gồm tích lũy đủ tín chỉ và điểm trung bình từ 2,0.",
                "source": "so_tay.txt",
                "score": 0.62,
            },
        ]

        reranked = UTCRAGPipeline._rerank(
            "Điều kiện xét tốt nghiệp của sinh viên UTC là gì?",
            items,
        )

        self.assertEqual(reranked[0]["source"], "so_tay.txt")

    def test_query_rejects_empty_question(self):
        pipeline = UTCRAGPipeline(settings=Settings())

        with self.assertRaises(ValueError):
            pipeline.query("   ")

    def test_should_use_web_search_for_empty_or_low_score_results(self):
        pipeline = UTCRAGPipeline(settings=Settings(enable_web_search=True, web_search_threshold=0.35))

        self.assertTrue(pipeline.should_use_web_search([]))
        self.assertTrue(pipeline.should_use_web_search([{"score": 0.2}]))
        self.assertFalse(pipeline.should_use_web_search([{"score": 0.5}]))

    def test_retrieve_falls_back_to_web_search_when_local_score_is_too_low(self):
        class FakeCollection:
            def count(self):
                return 1

            def query(self, **kwargs):
                return {
                    "ids": [["doc1"]],
                    "documents": [["Noi dung cuc ky khong lien quan"]],
                    "metadatas": [[{"source": "local.txt", "title": "Local"}]],
                    "distances": [[0.9]],
                }

        class FakeEmbedder:
            def encode(self, texts):
                return [[0.1, 0.2, 0.3] for _ in texts]

        pipeline = UTCRAGPipeline(
            settings=Settings(enable_web_search=True, web_search_threshold=0.35)
        )
        pipeline.collection = FakeCollection()
        pipeline.load_embedder = lambda: FakeEmbedder()
        pipeline._cache_lookup = lambda query: None
        pipeline.web_search = lambda query, max_results=3: [
            {
                "content": "Ket qua tu web",
                "source": "https://example.com",
                "title": "Example",
                "heading": "Tim kiem Internet",
                "breadcrumb": "Nguon Internet",
                "type": "web",
                "pages": "1",
                "score": 1.0,
            }
        ]

        results = pipeline.retrieve("Thong tin moi nhat", top_k=1)

        self.assertEqual(results[0]["type"], "web")
        self.assertEqual(results[0]["source"], "https://example.com")

    def test_web_search_prioritizes_allowed_domains(self):
        pipeline = UTCRAGPipeline(
            settings=Settings(
                enable_web_search=True,
                web_search_priority_domains=("utc.edu.vn",),
            )
        )

        def fake_search(query, max_results=3, domain_filter=None):
            if domain_filter == "utc.edu.vn":
                return [
                    {
                        "content": "Thong bao UTC",
                        "source": "https://utc.edu.vn/thong-bao",
                        "source_url": "https://utc.edu.vn/thong-bao",
                        "title": "Thong bao",
                        "heading": "Tim kiem Internet",
                        "breadcrumb": "Nguon Internet",
                        "type": "web",
                        "pages": "1",
                        "score": 1.0,
                    }
                ]
            return [
                {
                    "content": "Nguon ben ngoai",
                    "source": "https://example.com/news",
                    "source_url": "https://example.com/news",
                    "title": "Example",
                    "heading": "Tim kiem Internet",
                    "breadcrumb": "Nguon Internet",
                    "type": "web",
                    "pages": "1",
                    "score": 1.0,
                }
            ]

        pipeline._search_web_once = fake_search

        results = pipeline.web_search("Thong bao moi", max_results=2)

        self.assertEqual(results[0]["source"], "https://utc.edu.vn/thong-bao")


if __name__ == "__main__":
    unittest.main()

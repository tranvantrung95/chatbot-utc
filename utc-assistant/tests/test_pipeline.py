"""Unit tests for RAG pipeline core components."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag_pipeline import (
    UTCRAGPipeline, load_settings, _slugify, 
    QUERY_EXPANSIONS, TOPIC_FILTERS, QUERY_STOPWORDS,
)


class TestQueryExpansion:
    def test_expand_hoc_phi(self):
        result = UTCRAGPipeline._expand_query("học phí bao nhiêu")
        assert "hoc phi" in result
        assert "tài chính" in result
        assert "đóng tiền" in result

    def test_no_expansion_for_unknown(self):
        result = UTCRAGPipeline._expand_query("xyz không có trong từ điển")
        assert result == "xyz không có trong từ điển"

    def test_expand_diem(self):
        result = UTCRAGPipeline._expand_query("điểm trung bình")
        assert "gpa" in result
        assert "học lực" in result


class TestStopwords:
    def test_stopwords_removed(self):
        terms = UTCRAGPipeline._query_terms("tôi muốn hỏi về học phí")
        assert "tôi" not in terms
        assert "hỏi" not in terms
        assert "học" not in terms
        assert "phí" in terms  # "phí" is 3 chars, not in stopwords

    def test_short_terms_filtered(self):
        terms = UTCRAGPipeline._query_terms("a b c ab")
        assert len(terms) == 0  # All < 3 chars


class TestSlugify:
    def test_vietnamese_slug(self):
        result = _slugify("  Đại học Giao thông Vận tải  ")
        assert result == "đại_học_giao_thông_vận_tải"

    def test_fallback(self):
        result = _slugify("!!!", fallback="default")
        assert result == "default"


class TestSettings:
    def test_default_settings(self):
        s = load_settings(Path("/nonexistent"))
        assert s.chunk_size == 500
        assert s.chunk_overlap == 100
        assert s.top_k == 5


class TestTopicDetection:
    def test_semantic_detection_requires_pipeline(self):
        """Semantic detection needs embeddings - test structure only."""
        pipeline = UTCRAGPipeline()
        # Before init, embeddings should be None
        assert pipeline._topic_embeddings is None

    def test_keyword_expansion_still_works(self):
        """Keyword-based expansion works without embeddings."""
        result = UTCRAGPipeline._expand_query("học bổng sinh viên")
        assert len(result) > len("học bổng sinh viên")


class TestBuildContext:
    def test_xml_format(self):
        chunks = [{
            "content": "Nội dung test 1",
            "type": "article",
            "breadcrumb": "Phan 2 > Phan 2.1",
            "pages": "10-15",
        }]
        ctx = UTCRAGPipeline.build_context(chunks)
        assert "<chunk" in ctx
        assert 'id="1"' in ctx
        assert 'type="article"' in ctx
        assert "Nội dung test 1" in ctx
        assert "</chunk>" in ctx

    def test_token_budget(self):
        chunks = [
            {"content": "x" * 1000, "type": "text", "breadcrumb": "", "pages": ""}
            for _ in range(10)
        ]
        ctx = UTCRAGPipeline.build_context(chunks, max_tokens=200)
        # Max 200 tokens * 2.5 chars = ~500 chars of content
        assert len(ctx) < 2500  # Should be limited


class TestMMR:
    def test_mmr_single_item(self):
        p = UTCRAGPipeline()
        items = [{"content": "test", "score": 0.9}]
        result = p._mmr_rerank("query", items)
        assert len(result) == 1

    def test_mmr_diversity(self):
        p = UTCRAGPipeline()
        items = [
            {"content": "học phí năm 2025 là 10 triệu", "score": 0.9},
            {"content": "học phí năm 2025 là 10 triệu đồng", "score": 0.85},
            {"content": "ký túc xá có 500 chỗ", "score": 0.7},
        ]
        result = p._mmr_rerank("học phí", items)
        # First item should be highest score
        assert result[0]["score"] == 0.9
        # Third item should appear (diversity bonus - different topic)
        contents = [r["content"][:10] for r in result]
        assert any("ký túc" in c for c in contents)


class TestTextSimilarity:
    def test_identical(self):
        sim = UTCRAGPipeline._text_similarity("học phí đại học", "học phí đại học")
        assert sim == 1.0

    def test_different(self):
        sim = UTCRAGPipeline._text_similarity("học phí đại học", "ký túc xá sinh viên")
        assert sim < 0.5


class TestCosineSim:
    def test_identical_vectors(self):
        sim = UTCRAGPipeline._cosine_sim([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
        assert abs(sim - 1.0) < 0.001

    def test_orthogonal(self):
        sim = UTCRAGPipeline._cosine_sim([1.0, 0.0], [0.0, 1.0])
        assert abs(sim - 0.0) < 0.001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
RAG pipeline for UTC Assistant.

Embedding: OpenAI-compatible embeddings endpoint.
LLM: OpenAI-compatible chat endpoint.
Vector DB: ChromaDB persistent collection.
"""

from __future__ import annotations

import hashlib
import os
import re
import time
import urllib.parse
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import chromadb
from chromadb.config import Settings as ChromaSettings
import math

try:
    from dotenv import dotenv_values
except ImportError:  # pragma: no cover - requirements include python-dotenv.
    dotenv_values = None


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
VECTOR_DIR = DATA_DIR / "vector_db"
COLLECTION_NAME = "utc_knowledge"

DEFAULT_CHUNK_SIZE = 500
DEFAULT_CHUNK_OVERLAP = 100
DEFAULT_TOP_K = 5
DEFAULT_LLM_MAX_TOKENS = 3000
GENERATED_RAW_FILES = {"utc_combined.txt"}

# --- Query Expansion: tu dong nghia tieng Viet ---
QUERY_EXPANSIONS: Dict[str, List[str]] = {
    "học phí": ["học phí", "hoc phi", "đóng tiền", "nộp tiền", "thanh toán", "tài chính"],
    "học bổng": ["học bổng", "hoc bong", "trợ cấp", "khen thưởng", "ưu đãi"],
    "ký túc xá": ["ký túc xá", "ktx", "nội trú", "chỗ ở", "phòng ở", "nguyễn chí thanh"],
    "điểm": ["điểm", "điểm số", "xếp loại", "học lực", "gpa", "trung bình", "tích lũy"],
    "đào tạo": ["đào tạo", "chương trình", "tín chỉ", "học phần", "môn học", "giảng dạy"],
    "tốt nghiệp": ["tốt nghiệp", "ra trường", "bằng", "đồ án", "bảo vệ"],
    "thủ tục": ["thủ tục", "giấy tờ", "hồ sơ", "xác nhận", "đăng ký", "cấp"],
    "ngoại trú": ["ngoại trú", "tạm trú", "thuê nhà", "ở ngoài"],
    "kỷ luật": ["kỷ luật", "vi phạm", "xử lý", "cảnh cáo", "đình chỉ", "buộc thôi học"],
    "bảo hiểm": ["bảo hiểm", "y tế", "thân thể", "khám bệnh", "thanh toán bảo hiểm"],
    "email": ["email", "thư điện tử", "lms", "tài khoản", "@utc", "@lms"],
    "thư viện": ["thư viện", "mượn sách", "đọc sách", "tài liệu", "nhà A8"],
    "eutc": ["eutc", "app", "ứng dụng", "điện thoại", "cài đặt"],
    "rèn luyện": ["rèn luyện", "đánh giá rèn luyện", "rlsv", "điểm rèn luyện"],
    "mật khẩu": ["mật khẩu", "quên", "lấy lại", "đăng nhập", "qldt", "tài khoản"],
}

# --- Topic Filter: map keyword -> metadata filter ---
TOPIC_FILTERS: Dict[str, Dict[str, str]] = {
    "học phí": {"phan_so": "3", "title_like": "XIII"},      # Phan 3, XIII = Hoc phi
    "học bổng": {"phan_so": "2.5"},
    "ký túc xá": {"phan_so": "3", "title_like": "X. Ký túc"},
    "điểm": {"phan_so": "2.1"},
    "đào tạo": {"phan_so": "2.1"},
    "tốt nghiệp": {"phan_so": "2.1"},
    "kỷ luật": {"phan_so": "2.4"},
    "thủ tục": {"phan_so": "3"},
    "ngoại trú": {"phan_so": "2.8"},
    "bảo hiểm": {"phan_so": "3", "title_like": "XII"},
    "email": {"phan_so": "3", "title_like": "XIV"},
    "thư viện": {"phan_so": "3", "title_like": "IX"},
    "eutc": {"phan_so": "3", "title_like": "XV"},
    "rèn luyện": {"phan_so": "2.3"},
    "mật khẩu": {"phan_so": "3", "title_like": "I."},
}
QUERY_STOPWORDS = {
    "anh",
    "ban",
    "bạn",
    "cac",
    "các",
    "cho",
    "cua",
    "của",
    "dai",
    "duoc",
    "gi",
    "gì",
    "hoc",
    "học",
    "hoi",
    "hỏi",
    "khong",
    "không",
    "la",
    "là",
    "minh",
    "mình",
    "nhung",
    "những",
    "sinh",
    "toi",
    "tôi",
    "truong",
    "trường",
    "utc",
    "vien",
    "viên",
    "voi",
    "với",
}


@dataclass(frozen=True)
class Settings:
    embed_base_url: str = "http://127.0.0.1:8103"
    llm_base_url: str = "http://127.0.0.1:8103"
    api_key: str = "EMPTY"
    embed_model: str = "bge-m3"
    llm_model: str = "qwen35-opus"
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    top_k: int = DEFAULT_TOP_K
    llm_max_tokens: int = DEFAULT_LLM_MAX_TOKENS
    vector_dir: Path = VECTOR_DIR
    raw_dir: Path = RAW_DIR
    enable_web_search: bool = True
    web_search_threshold: float = 0.35
    web_search_priority_domains: Tuple[str, ...] = ("utc.edu.vn",)


def _parse_env_file(env_path: Path) -> Dict[str, str]:
    if not env_path.exists():
        return {}
    if dotenv_values is not None:
        return {
            key: value
            for key, value in dotenv_values(env_path).items()
            if value is not None
        }

    parsed: Dict[str, str] = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        parsed[key.strip()] = value.strip().strip("\"'")
    return parsed


def _read_int(values: Dict[str, str], key: str, default: int, minimum: int = 1) -> int:
    raw_value = values.get(key)
    if raw_value is None or raw_value == "":
        return default
    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{key} must be an integer, got {raw_value!r}") from exc
    if value < minimum:
        raise ValueError(f"{key} must be >= {minimum}, got {value}")
    return value


def load_settings(env_path: Optional[Path] = None) -> Settings:
    """Load settings from .env, then override them with real environment variables."""
    if env_path is None:
        env_path = BASE_DIR / ".env"

    values = _parse_env_file(env_path)
    values.update({key: value for key, value in os.environ.items() if value is not None})

    chunk_size = _read_int(values, "CHUNK_SIZE", DEFAULT_CHUNK_SIZE, minimum=100)
    chunk_overlap = _read_int(values, "CHUNK_OVERLAP", DEFAULT_CHUNK_OVERLAP, minimum=0)
    if chunk_overlap >= chunk_size:
        chunk_overlap = max(0, chunk_size // 5)
    llm_model = values.get("LLM_MODEL", Settings.llm_model).strip()
    if llm_model.lower() == "qwen3:4b":
        llm_model = "gemma4:e4b"

    enable_web_search = values.get("ENABLE_WEB_SEARCH", "True").strip().lower() == "true"
    try:
        web_search_threshold = float(values.get("WEB_SEARCH_THRESHOLD", "0.35").strip())
    except ValueError:
        web_search_threshold = 0.35
    raw_domains = values.get("WEB_SEARCH_PRIORITY_DOMAINS", "utc.edu.vn")
    web_search_priority_domains = tuple(
        domain.strip().lower()
        for domain in raw_domains.split(",")
        if domain.strip()
    ) or ("utc.edu.vn",)

    return Settings(
        embed_base_url=values.get(
            "EMBED_BASE_URL",
            values.get("OLLAMA_URL", Settings.embed_base_url),
        ).rstrip("/"),
        llm_base_url=values.get(
            "LLM_BASE_URL",
            values.get("OLLAMA_URL", Settings.llm_base_url),
        ).rstrip("/"),
        api_key=values.get("VLLM_API_KEY", values.get("OPENAI_API_KEY", Settings.api_key)),
        embed_model=values.get("EMBED_MODEL", Settings.embed_model),
        llm_model=llm_model,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        top_k=_read_int(values, "TOP_K", DEFAULT_TOP_K, minimum=1),
        llm_max_tokens=_read_int(values, "LLM_MAX_TOKENS", DEFAULT_LLM_MAX_TOKENS, minimum=256),
        vector_dir=Path(values.get("VECTOR_DIR", str(VECTOR_DIR))),
        raw_dir=Path(values.get("RAW_DIR", str(RAW_DIR))),
        enable_web_search=enable_web_search,
        web_search_threshold=web_search_threshold,
        web_search_priority_domains=web_search_priority_domains,
    )


def _slugify(value: str, fallback: str = "doc") -> str:
    normalized = re.sub(r"[^0-9A-Za-zÀ-ỹ]+", "_", value.strip(), flags=re.UNICODE)
    normalized = normalized.strip("_").lower()
    return normalized[:80] or fallback


def _batched(items: List[Any], batch_size: int) -> Iterable[List[Any]]:
    for start in range(0, len(items), batch_size):
        yield items[start:start + batch_size]


class OllamaEmbedder:
    """Embedding client for OpenAI-compatible /v1/embeddings endpoint."""

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8103",
        model: str = "bge-m3",
        api_key: str = "EMPTY",
        timeout: int = 120,
    ):
        import requests

        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()
        self.dimension: Optional[int] = None

    def encode(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        response = self.session.post(
            f"{self.base_url}/v1/embeddings",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "input": texts},
            timeout=self.timeout,
        )
        response.raise_for_status()
        data = response.json()
        items = data.get("data")
        if not isinstance(items, list) or len(items) != len(texts):
            raise RuntimeError("Embedding response did not match input batch size")
        embeddings = [item.get("embedding") for item in items]
        if embeddings and self.dimension is None:
            self.dimension = len(embeddings[0])
        return embeddings


class OllamaLLM:
    """Chat client for OpenAI-compatible /v1/chat/completions endpoint."""

    FINAL_MARKERS = (
        "Final answer:",
        "Final Answer:",
        "Câu trả lời:",
        "Trả lời:",
        "ANSWER:",
    )

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8103",
        model: str = "qwen35-opus",
        api_key: str = "EMPTY",
        timeout: int = 180,
    ):
        import requests

        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()

    @staticmethod
    def _extract_thinking(text: str) -> tuple:
        """Trich xuat thinking va answer tu text. Tra ve (thinking, answer)."""
        thinking = ""
        # Pattern: <think>...</think> 
        m = re.search(r'<think>(.*?)</think>', text, flags=re.IGNORECASE | re.DOTALL)
        if m:
            thinking = m.group(1).strip()
            text = text[m.end():].strip()
        # Also check for </think> without opening tag (some models)
        elif '</think>' in text.lower():
            parts = re.split(r'</think>', text, flags=re.IGNORECASE, maxsplit=1)
            thinking = parts[0].strip()
            # Remove <think> if present at start
            thinking = re.sub(r'^<think>\s*', '', thinking, flags=re.IGNORECASE)
            text = parts[1].strip() if len(parts) > 1 else ''
        return thinking, text

    @classmethod
    def extract_answer(cls, data: Dict[str, Any]) -> str:
        """Trich xuat answer, bo thinking. (giu backward compat)"""
        _, answer = cls.extract_answer_with_thinking(data)
        return answer

    @classmethod
    def extract_answer_with_thinking(cls, data: Dict[str, Any]) -> tuple:
        """Tra ve (thinking, answer)."""
        choices = data.get("choices") or []
        if not choices:
            raise RuntimeError("LLM returned no choices")
        message = choices[0].get("message") or {}
        content = str(message.get("content") or "").strip()
        reasoning = str(message.get("reasoning") or "").strip()

        # If reasoning field exists, it IS the thinking
        if reasoning:
            # Try to extract thinking tags from content first
            t_from_content, answer = cls._extract_thinking(content)
            if answer:
                return (reasoning + "\n" + t_from_content).strip(), answer
            # Content might be the answer, reasoning is the thinking
            return reasoning, content if content else reasoning

        # No reasoning - try extracting thinking tags from content
        if content:
            thinking, answer = cls._extract_thinking(content)
            if answer:
                return thinking, answer
            # Check for marker-based final answer
            marked = cls._extract_after_marker(content)
            return thinking, marked or content

        raise RuntimeError("LLM returned empty assistant content")

    @classmethod
    def _extract_after_marker(cls, text: str) -> Optional[str]:
        for marker in cls.FINAL_MARKERS:
            index = text.rfind(marker)
            if index != -1:
                answer = text[index + len(marker):].strip()
                return answer or None
        return None

    def _prepare_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        prepared = [dict(message) for message in messages]
        # Khong them /no_think - de model tu sinh thinking
        return prepared

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.2,
        max_tokens: int = 1600,
    ) -> str:
        response = self.session.post(
            f"{self.base_url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": self.model,
                "messages": self._prepare_messages(messages),
                "temperature": temperature,
                "max_tokens": max_tokens,
                "enable_thinking": True,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()
        return self.extract_answer(response.json())


class BM25Index:
    """Lightweight BM25 keyword index for hybrid search.
    
    No heavy dependencies — pure Python. Indexes chunks by word tokens
    and scores with Okapi BM25 formula.
    """
    def __init__(self, k1: float = 1.2, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.documents: List[str] = []
        self.doc_lengths: List[int] = []
        self.avgdl: float = 0.0
        # Inverted index: term -> {doc_idx: term_freq}
        self.inverted: Dict[str, Dict[int, int]] = {}
        self.idf: Dict[str, float] = {}
        self._built = False

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """Tokenize Vietnamese text: lowercase, remove stopwords, min 2 chars."""
        tokens = re.findall(r"[a-zà-ỹđ]{2,}", text.lower(), flags=re.UNICODE)
        return [t for t in tokens if t not in QUERY_STOPWORDS and len(t) >= 2]

    def index(self, documents: List[str]):
        """Build BM25 index from document list."""
        self.documents = documents
        self.doc_lengths = [len(self._tokenize(doc)) for doc in documents]
        self.avgdl = sum(self.doc_lengths) / max(1, len(self.doc_lengths))
        
        doc_count = len(documents)
        doc_freq: Dict[str, int] = {}
        
        for idx, doc in enumerate(documents):
            tokens = self._tokenize(doc)
            term_freq: Dict[str, int] = {}
            for token in tokens:
                term_freq[token] = term_freq.get(token, 0) + 1
            for term, freq in term_freq.items():
                if term not in self.inverted:
                    self.inverted[term] = {}
                self.inverted[term][idx] = freq
                doc_freq[term] = doc_freq.get(term, 0) + 1
        
        # Compute IDF
        for term, df in doc_freq.items():
            self.idf[term] = math.log(1.0 + (doc_count - df + 0.5) / (df + 0.5))
        
        self._built = True

    def search(self, query: str, top_k: int = 20) -> List[tuple]:
        """Return [(doc_idx, bm25_score), ...] sorted descending."""
        if not self._built:
            return []
        
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []
        
        scores: Dict[int, float] = {}
        for token in query_tokens:
            if token not in self.inverted:
                continue
            idf = self.idf.get(token, 0.0)
            for doc_idx, freq in self.inverted[token].items():
                doc_len = self.doc_lengths[doc_idx]
                numerator = freq * (self.k1 + 1.0)
                denominator = freq + self.k1 * (1.0 - self.b + self.b * doc_len / max(1, self.avgdl))
                scores[doc_idx] = scores.get(doc_idx, 0.0) + idf * numerator / denominator
        
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return ranked[:top_k]


class UTCRAGPipeline:
    """RAG pipeline for the UTC assistant."""

    FALLBACK_ANSWER = (
        "Xin lỗi, tôi chưa có thông tin về vấn đề này. Bạn vui lòng liên hệ "
        "trực tiếp với nhà trường qua website utc.edu.vn hoặc số điện thoại "
        "(024) 37663311 để được hỗ trợ."
    )

    SYSTEM_PROMPT = (
        "Bạn là Trợ lý ảo của Trường Đại học Giao thông Vận tải (UTC).\n"
        "QUY ĐỊNH BẮT BUỘC VỀ NGÔN NGỮ SUY NGHĨ (THINKING LANGUAGE):\n"
        "• Bạn PHẢI thực hiện toàn bộ quá trình suy nghĩ, lập luận (reasoning/thinking process) bằng TIẾNG VIỆT.\n"
        "• Tuyệt đối không suy nghĩ bằng tiếng Anh hay bất kỳ ngôn ngữ nào khác trong thẻ <think> hay phần lập luận nội bộ.\n"
        "• Trả lời sinh viên bằng tiếng Việt thân thiện, chuyên nghiệp.\n"
        "\n"
        "QUY TẮC CỐT LÕI:\n"
        "1. CHỈ trả lời dựa trên NGỮ CẢNH được cung cấp bên dưới.\n"
        "2. Nếu không có thông tin → nói: 'Xin lỗi, tôi chưa có thông tin về vấn đề này. "
        "Bạn vui lòng liên hệ trực tiếp với nhà trường qua website utc.edu.vn "
        "hoặc số điện thoại (024) 37663311 để được hỗ trợ.'\n"
        "3. Không bịa thông tin. Không suy đoán. Không thêm thông tin ngoài ngữ cảnh.\n"
        "4. Trả lời ngắn gọn, đi thẳng vấn đề. Không lan man.\n"
        "5. Nếu câu hỏi chưa rõ → hỏi lại ngắn gọn.\n"
        "6. Nếu chỉ có một phần thông tin → trả lời phần có, nói rõ phần còn thiếu.\n"
        "\n"
        "ĐỊNH DẠNG:\n"
        "• Dùng văn bản thuần (KHÔNG dùng **, # heading, blockquote, code block).\n"
        "• ĐƯỢC PHÉP dùng bảng khi cần hiển thị dữ liệu dạng bảng (quy đổi điểm, học phí...).\n"
        "• Khi dùng bảng: trình bày dạng text căn đều, dùng dấu cách để căn cột, có dòng phân cách bằng dấu gạch ngang.\n"
        "  Ví dụ bảng đẹp (căn đều các cột):\n"
        "  Điểm 10      Điểm chữ    Điểm 4    Xếp loại\n"
        "  ─────────────────────────────────────────\n"
        "  9.5 - 10.0      A+          4.0      Xuất sắc\n"
        "  8.5 - 9.4       A           3.8      Giỏi\n"
        "  7.0 - 8.4       B           3.0      Khá\n"
        "  5.5 - 6.9       C           2.0      Trung bình\n"
        "  4.0 - 5.4       D           1.0      Yếu\n"
        "  0.0 - 3.9       F             0      Kém\n"
        "• KHÔNG dùng pipe | để phân cách cột vì gây xô lệch và khó đọc.\n"
        "• KHÔNG dùng **, # heading, blockquote, code block, bảng markdown.\n"
        "• Nếu không phải dữ liệu bảng: dùng icon Unicode, gạch đầu dòng (-), đánh số (1.), thụt dòng (2 spaces).\n"
        "• Mỗi dòng 1 ý. Không viết đoạn dài.\n"
        "• Phân nhóm bằng icon + tiêu đề ngắn:\n"
        "  ✅ Tóm tắt / Trả lời chính\n"
        "  🌐 Website / hệ thống\n"
        "  🔐 Tài khoản / mật khẩu\n"
        "  📝 Các bước thực hiện\n"
        "  📌 Căn cứ / quy định\n"
        "  ⚠️ Lưu ý / cảnh báo\n"
        "  💰 Học phí / tài chính\n"
        "  📅 Thời hạn / mốc thời gian\n"
        "  🏢 Phòng ban / đơn vị liên hệ\n"
        "  📄 Hồ sơ / giấy tờ\n"
        "  🎓 Học bổng / đào tạo\n"
        "• Mỗi nhóm chỉ 1 icon. Không dùng icon đùa cợt.\n"
        "• Ưu tiên thông tin quan trọng nhất lên đầu.\n"
        "• Giữa các nhóm để 1 dòng trống.\n"
        "\n"
        "QUAN TRỌNG:\n"
        "• Không nhắc tên file nguồn.\n"
        "• Đảm bảo toàn bộ câu trả lời và quá trình suy nghĩ đều sử dụng tiếng Việt.\n"
        "• Nếu câu hỏi cần dữ liệu cá nhân mà không có → nói rõ ngữ cảnh chưa có.\n"
        "\n"
        "NGHIÊM CẤM THAY ĐỔI SỐ LIỆU:\n"
        "• Copy CHÍNH XÁC các con số, tỉ lệ phần trăm, mức tiền, ngày tháng từ ngữ cảnh.\n"
        "• 100% phải là 100%, không được viết thành 10% hay số khác.\n"
        "• Nếu ngữ cảnh nói 'miễn 100% học phí' thì phải ghi 'miễn 100% học phí'.\n"
        "• Nếu ngữ cảnh nói 'giảm 70% học phí' thì phải ghi 'giảm 70% học phí'.\n"
        "• Đọc kỹ số trước khi viết. Sai số là lỗi nghiêm trọng nhất."
    )

    def __init__(
        self,
        settings: Optional[Settings] = None,
        ollama_url: Optional[str] = None,
        embed_base_url: Optional[str] = None,
        llm_base_url: Optional[str] = None,
        embed_model: Optional[str] = None,
        llm_model: Optional[str] = None,
    ):
        settings = settings or load_settings()
        overrides: Dict[str, Any] = {}
        if ollama_url:
            overrides["embed_base_url"] = ollama_url.rstrip("/")
            overrides["llm_base_url"] = ollama_url.rstrip("/")
        if embed_base_url:
            overrides["embed_base_url"] = embed_base_url.rstrip("/")
        if llm_base_url:
            overrides["llm_base_url"] = llm_base_url.rstrip("/")
        if embed_model:
            overrides["embed_model"] = embed_model
        if llm_model:
            overrides["llm_model"] = llm_model
        self.settings = replace(settings, **overrides) if overrides else settings

        self.embedder: Optional[OllamaEmbedder] = None
        self.llm: Optional[OllamaLLM] = None
        self.chroma_client = None
        self.collection = None
        self.bm25: Optional[BM25Index] = None  # Hybrid: BM25 keyword index

    @staticmethod
    def _parse_headings(text: str) -> List[Tuple[int, str, int]]:
        """Extract heading hierarchy: (line_index, heading_text, level)."""
        headings: List[Tuple[int, str, int]] = []
        lines = text.split("\n")
        for idx, raw in enumerate(lines):
            line = raw.strip()
            if not line:
                continue
            # Skip TOC entries (lines with consecutive dots like "1. Title ........ 4")
            if "....." in line:
                continue
            # Skip small page markers (e.g. "STSV * 5", "6 * STSV")
            if re.match(r"^(STSV\s*\*|[\d]+\s*\*\s*STSV)", line):
                continue
            # PHẦN X.Y:  (level 2)
            if re.match(r"^PHẦN\s+\d+\.\d+[.:]", line):
                headings.append((idx, line, 2))
            # PHẦN X:   (level 1)
            elif re.match(r"^PHẦN\s+\d+[.:]", line):
                headings.append((idx, line, 1))
            # Chương I, II, ...
            elif re.match(r"^Chương\s+[IVX]+", line):
                headings.append((idx, line, 2))
            # X. TÊN MỤC  (roman numeral sections like I., II., X.)
            elif re.match(r"^[IVX]+\.\s+\S", line) and len(line) < 120:
                headings.append((idx, line, 2))
            # N. TÊN MỤC  (numbered sections: 1., 2., 3.)
            elif re.match(r"^\d+\.\s+[A-ZÀ-ỸĐ]", line) and len(line) < 120:
                headings.append((idx, line, 3))
        return headings

    @staticmethod
    def _heading_path_for_line(
        line_idx: int,
        headings: List[Tuple[int, str, int]],
    ) -> str:
        """Build heading breadcrumb for a given line index."""
        path_parts: List[str] = []
        current_level2: Optional[str] = None
        for h_idx, h_text, h_level in headings:
            if h_idx > line_idx:
                break
            if h_level == 1:
                path_parts = [h_text]
                current_level2 = None
            elif h_level == 2:
                if len(path_parts) > 1:
                    path_parts = path_parts[:1]
                current_level2 = h_text
            elif h_level == 3:
                if current_level2:
                    if len(path_parts) > 1:
                        path_parts = path_parts[:1]
                    path_parts = path_parts[:1] + [current_level2, h_text]
                else:
                    if len(path_parts) > 1:
                        path_parts = path_parts[:1]
                    path_parts.append(h_text)
        return " > ".join(path_parts) if path_parts else ""

    @staticmethod
    def chunk_text(
        text: str,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_CHUNK_OVERLAP,
        heading_path: str = "",
    ) -> List[Dict[str, Any]]:
        if not text or len(text.strip()) < 50:
            return []

        chunk_size = max(100, chunk_size)
        overlap = max(0, min(overlap, chunk_size // 2))
        paragraphs = [
            re.sub(r"[ \t]+", " ", paragraph).strip()
            for paragraph in re.split(r"\n\s*\n", text)
            if len(paragraph.strip()) >= 50
        ]

        chunks: List[str] = []
        for paragraph in paragraphs:
            if len(paragraph) <= chunk_size:
                chunks.append(paragraph)
                continue

            start = 0
            while start < len(paragraph):
                end = min(len(paragraph), start + chunk_size)
                if end < len(paragraph):
                    boundary = paragraph.rfind(" ", start + int(chunk_size * 0.6), end)
                    if boundary > start:
                        end = boundary

                chunk = paragraph[start:end].strip()
                if len(chunk) >= 50:
                    chunks.append(chunk)
                if end >= len(paragraph):
                    break

                next_start = max(0, end - overlap)
                if next_start > 0:
                    previous_space = paragraph.rfind(" ", 0, next_start)
                    if previous_space != -1:
                        next_start = previous_space + 1
                if next_start <= start:
                    next_start = end
                start = next_start

        prefix = f"{heading_path} | " if heading_path else ""
        return [
            {
                "content": prefix + content,
                "chunk_id": f"chunk_{index:04d}",
                "char_count": len(content),
                "heading": heading_path,
            }
            for index, content in enumerate(chunks)
        ]

    def load_documents(self, raw_dir: Optional[Path] = None) -> List[Dict[str, str]]:
        raw_dir = raw_dir or self.settings.raw_dir
        documents: List[Dict[str, str]] = []
        for filepath in sorted(raw_dir.glob("*.txt")):
            if filepath.name in GENERATED_RAW_FILES:
                continue
            content = filepath.read_text(encoding="utf-8", errors="replace")
            title = filepath.stem
            if content.startswith("# "):
                title = content.split("\n", 1)[0].replace("# ", "").strip()
            documents.append(
                {
                    "source": str(filepath),
                    "title": title,
                    "content": content,
                }
            )

        documents.sort(
            key=lambda item: (
                0 if "so_tay" in item["source"].lower() else
                1 if "faq" in item["source"].lower() else 2,
                item["title"],
            )
        )
        print(f"  Đã tải {len(documents)} tài liệu")
        return documents

    def load_embedder(self) -> OllamaEmbedder:
        if self.embedder is None:
            print(f"  Khởi tạo Ollama Embedder ({self.settings.embed_model})...")
            self.embedder = OllamaEmbedder(
                self.settings.embed_base_url,
                self.settings.embed_model,
                self.settings.api_key,
            )
            print("  Embedder sẵn sàng")
        return self.embedder

    def load_llm(self) -> OllamaLLM:
        if self.llm is None:
            print(f"  Khởi tạo Ollama LLM ({self.settings.llm_model})...")
            self.llm = OllamaLLM(
                self.settings.llm_base_url,
                self.settings.llm_model,
                self.settings.api_key,
            )
        return self.llm

    def init_vector_db(self, reset: bool = False) -> chromadb.Collection:
        self.settings.vector_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(
            path=str(self.settings.vector_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        if reset:
            try:
                self.chroma_client.delete_collection(COLLECTION_NAME)
            except Exception:
                pass
        self.collection = self.chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        # Build BM25 index over all chunks for hybrid search
        if self.collection.count() > 0 and self.bm25 is None:
            all_data = self.collection.get(include=["documents"])
            self.bm25 = BM25Index()
            self.bm25.index(all_data["documents"] or [])
        print(f"  ChromaDB '{COLLECTION_NAME}' sẵn sàng ({self.collection.count()} chunks)")
        return self.collection

    @classmethod
    def _is_structural_boundary(cls, line: str) -> bool:
        """Detect lines that start a new structural unit (Điều, Chương, Mục, PHẦN)."""
        if re.match(r"^Điều\s+\d+[.:]", line):
            return True
        if re.match(r"^Chương\s+[IVX]+", line):
            return True
        if re.match(r"^PHẦN\s+\d+", line):
            return True
        if re.match(r"^Mục\s+\d+[.:]", line):
            return True
        if re.match(r"^[IVX]+\.\s+\S", line) and len(line) < 120 and "....." not in line:
            return True
        # Numbered top-level sections (1. TÊN, 2. TÊN) — but not sub-items like 1. sentence
        if re.match(r"^\d+\.\s+[A-ZÀ-ỸĐ]{2,}", line) and len(line) < 120 and "....." not in line:
            return True
        return False

    @classmethod
    def _flush_buffer(
        cls,
        buffer: List[str],
        buffer_start_line: int,
        headings: List[Tuple[int, str, int]],
        chunk_size: int,
    ) -> List[Dict[str, Any]]:
        """Convert accumulated lines into one or more chunks with heading prefix."""
        if not buffer:
            return []
        heading = cls._heading_path_for_line(buffer_start_line, headings)
        prefix = f"{heading} | " if heading else ""
        content = " ".join(buffer)

        if len(content) <= chunk_size * 1.5:
            return [{
                "content": prefix + content,
                "chunk_id": "",
                "char_count": len(content),
                "heading": heading,
            }]

        # Split long structural unit into sub-chunks, all sharing same heading
        sub_chunks: List[Dict[str, Any]] = []
        start = 0
        while start < len(content):
            end = min(len(content), start + chunk_size)
            if end < len(content):
                boundary = content.rfind(" ", start, end)
                if boundary > start:
                    end = boundary
            sub = content[start:end].strip()
            if len(sub) >= 50:
                sub_chunks.append({
                    "content": prefix + sub,
                    "chunk_id": "",
                    "char_count": len(sub),
                    "heading": heading,
                })
            start = end
        return sub_chunks

    @classmethod
    def _chunk_document(
        cls,
        text: str,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        overlap: int = DEFAULT_CHUNK_OVERLAP,
    ) -> List[Dict[str, Any]]:
        """Chunk by document structure: flush at Điều/Chương/Mục boundaries."""
        headings = cls._parse_headings(text)
        if not headings:
            return cls.chunk_text(text, chunk_size=chunk_size, overlap=overlap)

        lines = text.split("\n")
        all_chunks: List[Dict[str, Any]] = []
        buffer: List[str] = []
        buffer_start_line = 0

        for line_idx, raw_line in enumerate(lines):
            line = raw_line.strip()

            # Structural boundary: flush current unit before starting new one
            if cls._is_structural_boundary(line) and buffer:
                all_chunks.extend(
                    cls._flush_buffer(buffer, buffer_start_line, headings, chunk_size)
                )
                buffer = []
                buffer_start_line = line_idx

            if not line:
                continue

            if not buffer:
                buffer_start_line = line_idx
            buffer.append(line)

        # Flush final unit
        if buffer:
            all_chunks.extend(
                cls._flush_buffer(buffer, buffer_start_line, headings, chunk_size)
            )

        # Assign chunk IDs
        for i, c in enumerate(all_chunks):
            c["chunk_id"] = f"chunk_{i:04d}"

        return all_chunks

    def _chunk_id(self, doc: Dict[str, str], chunk: Dict[str, Any]) -> str:
        source_slug = _slugify(Path(doc["source"]).stem)
        digest = hashlib.sha1(chunk["content"].encode("utf-8")).hexdigest()[:10]
        return f"{source_slug}_{chunk['chunk_id']}_{digest}"

    def index_documents(self, reset: bool = False) -> int:
        embedder = self.load_embedder()
        collection = self.init_vector_db(reset=reset)
        documents = self.load_documents()

        existing_ids = set()
        if not reset:
            try:
                existing_ids = set(collection.get()["ids"])
            except Exception:
                existing_ids = set()

        pending: List[Dict[str, Any]] = []
        for doc in documents:
            chunks = self._chunk_document(
                doc["content"],
                chunk_size=self.settings.chunk_size,
                overlap=self.settings.chunk_overlap,
            )
            for chunk in chunks:
                chunk_id = self._chunk_id(doc, chunk)
                if chunk_id in existing_ids:
                    continue
                metadata = {
                    "source": doc["source"],
                    "title": doc["title"],
                    "chunk_id": chunk["chunk_id"],
                }
                if chunk.get("heading"):
                    metadata["heading"] = chunk["heading"]
                pending.append(
                    {
                        "id": chunk_id,
                        "text": chunk["content"],
                        "metadata": metadata,
                    }
                )

        total_chunks = 0
        for batch in _batched(pending, 16):
            embeddings = embedder.encode([item["text"] for item in batch])
            collection.add(
                ids=[item["id"] for item in batch],
                embeddings=embeddings,
                documents=[item["text"] for item in batch],
                metadatas=[item["metadata"] for item in batch],
            )
            total_chunks += len(batch)
            if total_chunks % 50 == 0 or total_chunks == len(pending):
                print(f"    ... {total_chunks}/{len(pending)} chunks")

        print(f"  Đã index {total_chunks} chunks mới (tổng: {collection.count()})")
        return total_chunks

    def index_structured(self, reset: bool = False) -> int:
        """Index dung structured chunks tu TOC JSON (metadata giau)."""
        from src.structured_chunker import chunk_for_indexing

        embedder = self.load_embedder()
        collection = self.init_vector_db(reset=reset)

        chunks = chunk_for_indexing()
        print(f"  Structured chunks: {len(chunks)}")

        existing_ids = set()
        if not reset:
            try:
                existing_ids = set(collection.get()["ids"])
            except Exception:
                existing_ids = set()

        pending: List[Dict[str, Any]] = []
        for i, chunk in enumerate(chunks):
            content = chunk["content"]
            meta = chunk["metadata"]
            chunk_id = hashlib.sha1(content.encode("utf-8")).hexdigest()[:12]
            chunk_id = f"struct_{meta.get('type','s')}_{i:04d}_{chunk_id}"

            if chunk_id in existing_ids:
                continue

            metadata = {
                "source": "so_tay_sinh_vien_k66.pdf",
                "title": meta.get("title", ""),
                "type": meta.get("type", ""),
                "breadcrumb": meta.get("breadcrumb", ""),
                "pages": str(meta.get("pages", [])),
            }
            # Add optional fields
            for key in ("phan", "phan_so", "chuong", "chuong_so", "dieu", "dieu_so"):
                if meta.get(key):
                    metadata[key] = meta[key]

            pending.append({
                "id": chunk_id,
                "text": content,
                "metadata": metadata,
            })

        total_chunks = 0
        for batch in _batched(pending, 16):
            embeddings = embedder.encode([item["text"] for item in batch])
            collection.add(
                ids=[item["id"] for item in batch],
                embeddings=embeddings,
                documents=[item["text"] for item in batch],
                metadatas=[item["metadata"] for item in batch],
            )
            total_chunks += len(batch)
            if total_chunks % 50 == 0 or total_chunks == len(pending):
                print(f"    ... {total_chunks}/{len(pending)} chunks")

        print(f"  Da index {total_chunks} structured chunks (tong: {collection.count()})")
        self._index_version += 1  # Invalidate cached queries on re-index
        return total_chunks

    @staticmethod
    def _query_terms(query: str) -> List[str]:
        return [
            term
            for term in re.findall(r"[\wÀ-ỹ]+", query.lower(), flags=re.UNICODE)
            if len(term) >= 3 and term not in QUERY_STOPWORDS
        ]

    # --- Topic embeddings (pre-computed once, reused) ---
    _topic_embeddings: Optional[Dict[str, List[float]]] = None
    _topic_threshold: float = 0.55  # Minimum cosine similarity to apply filter

    def _ensure_topic_embeddings(self):
        """Pre-compute embeddings for topic labels (lazy, once)."""
        if self._topic_embeddings is not None:
            return
        embedder = self.load_embedder()
        labels = list(TOPIC_FILTERS.keys())
        if not labels:
            self._topic_embeddings = {}
            return
        vectors = embedder.encode(labels)
        self._topic_embeddings = dict(zip(labels, vectors))

    @staticmethod
    def _cosine_sim(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = (sum(x * x for x in a)) ** 0.5
        norm_b = (sum(x * x for x in b)) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    @classmethod
    def _expand_query(cls, query: str) -> str:
        """Mo rong query voi tu dong nghia (keyword-based, lightweight)."""
        query_lower = query.lower()
        expanded_terms = set()
        for keyword, synonyms in QUERY_EXPANSIONS.items():
            if keyword in query_lower:
                expanded_terms.update(synonyms)
        if expanded_terms:
            return query + " " + " ".join(expanded_terms)
        return query

    def _detect_topic_semantic(self, query: str) -> Optional[Dict[str, str]]:
        """Phat hien chu de bang embedding similarity (thay keyword substring).
        
        Tra ve topic filter neu similarity > threshold.
        Tra ve None neu khong match ro rang (fallback: search toan bo).
        """
        self._ensure_topic_embeddings()
        if not self._topic_embeddings:
            return None
        
        embedder = self.load_embedder()
        query_vec = embedder.encode([query])[0]
        
        best_topic = None
        best_sim = 0.0
        for topic, vec in self._topic_embeddings.items():
            sim = self._cosine_sim(query_vec, vec)
            if sim > best_sim:
                best_sim = sim
                best_topic = topic
        
        if best_topic and best_sim >= self._topic_threshold:
            return TOPIC_FILTERS.get(best_topic)
        return None

    def _mmr_rerank(
        self, query: str, items: List[Dict[str, Any]], lambda_param: float = 0.7
    ) -> List[Dict[str, Any]]:
        """MMR diversity rerank: chon chunk vua lien quan vua khac biet."""
        if len(items) <= 1:
            return items
        selected = [items[0]]
        remaining = items[1:]
        while remaining and len(selected) < len(items):
            mmr_scores = []
            for item in remaining:
                relevance = item["score"]
                redundancy = max(
                    self._text_similarity(item["content"], s["content"])
                    for s in selected
                )
                mmr = lambda_param * relevance - (1 - lambda_param) * redundancy
                mmr_scores.append(mmr)
            best_idx = mmr_scores.index(max(mmr_scores))
            selected.append(remaining.pop(best_idx))
        return selected

    @staticmethod
    def _text_similarity(a: str, b: str) -> float:
        """Jaccard similarity don gian giua 2 text."""
        set_a = set(re.findall(r"\w{3,}", a.lower()))
        set_b = set(re.findall(r"\w{3,}", b.lower()))
        if not set_a or not set_b:
            return 0.0
        return len(set_a & set_b) / len(set_a | set_b)

    @classmethod
    def _rerank(cls, query: str, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        terms = cls._query_terms(query)
        phrases = [
            " ".join(terms[index:index + size])
            for size in (2, 3)
            for index in range(0, max(0, len(terms) - size + 1))
        ]

        reranked = []
        for item in items:
            haystack = f"{item['title']} {item['content']}".lower()
            term_matches = sum(1 for term in set(terms) if term in haystack)
            phrase_matches = sum(1 for phrase in phrases if phrase in haystack)
            bonus = min(0.45, term_matches * 0.04 + phrase_matches * 0.12)
            updated = dict(item)
            updated["score"] = item["score"] + bonus
            updated["vector_score"] = item["score"]
            updated["keyword_bonus"] = bonus
            reranked.append(updated)

        return sorted(reranked, key=lambda item: item["score"], reverse=True)

    @staticmethod
    def _extract_domain(url: str) -> str:
        parsed = urllib.parse.urlparse(url)
        return parsed.netloc.lower().split(":")[0]

    def _is_priority_domain(self, url: str) -> bool:
        domain = self._extract_domain(url)
        return any(
            domain == allowed or domain.endswith(f".{allowed}")
            for allowed in self.settings.web_search_priority_domains
        )

    def _search_web_once(
        self,
        query: str,
        max_results: int = 3,
        domain_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        import requests
        from bs4 import BeautifulSoup

        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        search_query = f"site:{domain_filter} {query}" if domain_filter else query
        url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(search_query)}"

        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")
            results = []

            for result in soup.select(".web-result"):
                title_a = result.select_one(".result__a")
                snippet_div = result.select_one(".result__snippet")

                if title_a and snippet_div:
                    title = title_a.get_text().strip()
                    raw_url = title_a.get("href", "")

                    parsed_url = urllib.parse.urlparse(raw_url)
                    qs = urllib.parse.parse_qs(parsed_url.query)
                    clean_url = qs.get("uddg", [raw_url])[0]

                    snippet = snippet_div.get_text().strip()

                    results.append({
                        "content": snippet,
                        "source": clean_url,
                        "source_url": clean_url,
                        "title": title,
                        "heading": "Tìm kiếm Internet",
                        "breadcrumb": "Nguồn Internet",
                        "type": "web",
                        "pages": "1",
                        "score": 1.0
                    })

                    if len(results) >= max_results:
                        break
            return results
        except Exception as e:
            print(f"Error during fallback web search: {e}")
            return []

    def _search_web_fallback(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        seen_sources: set[str] = set()

        for domain in self.settings.web_search_priority_domains:
            for item in self._search_web_once(query, max_results=max_results, domain_filter=domain):
                source_url = item.get("source", "")
                if source_url in seen_sources:
                    continue
                seen_sources.add(source_url)
                results.append(item)
                if len(results) >= max_results:
                    return results

        general_results = self._search_web_once(query, max_results=max_results * 2)
        priority_results = []
        other_results = []
        for item in general_results:
            source_url = item.get("source", "")
            if source_url in seen_sources:
                continue
            seen_sources.add(source_url)
            if self._is_priority_domain(source_url):
                priority_results.append(item)
            else:
                other_results.append(item)

        results.extend(priority_results)
        results.extend(other_results)
        return results[:max_results]

    def should_use_web_search(self, retrieved: List[Dict[str, Any]]) -> bool:
        """Use web search only when local retrieval is missing or too weak."""
        if not self.settings.enable_web_search:
            return False
        if not retrieved:
            return True
        return float(retrieved[0].get("score", 0.0)) < self.settings.web_search_threshold

    def web_search(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """Public wrapper so callers can trigger the same web fallback consistently."""
        return self._search_web_fallback(query, max_results=max_results)

    def retrieve(self, query: str, top_k: Optional[int] = None) -> List[Dict[str, Any]]:
        query = query.strip()
        if not query:
            raise ValueError("Question must not be empty")

        # === CACHE LOOKUP ===
        cached = self._cache_lookup(query)
        if cached is not None:
            return cached[: (top_k or self.settings.top_k)]

        if self.collection is None:
            self.init_vector_db()

        embedder = self.load_embedder()
        collection_count = self.collection.count()
        if collection_count == 0:
            return []

        # === PREPROCESSING: query expansion + semantic topic filter ===
        expanded_query = self._expand_query(query)
        topic_filter = self._detect_topic_semantic(query)

        requested_top_k = top_k or self.settings.top_k
        # Always fetch more candidates for fallback fusion
        candidate_count = min(collection_count, max(requested_top_k * 3, 15))
        query_embeddings = embedder.encode([expanded_query])

        # Build ChromaDB where filter neu semantic detect duoc topic (similarity > 0.55)
        where_filter = None
        has_topic_filter = False
        if topic_filter:
            phan_so = topic_filter.get("phan_so")
            if phan_so:
                where_filter = {"phan_so": phan_so}
                has_topic_filter = True

        # Primary search: with topic filter if detected
        results = self.collection.query(
            query_embeddings=query_embeddings,
            n_results=candidate_count,
            include=["documents", "metadatas", "distances"],
            where=where_filter,
        )

        # Fallback: also search WITHOUT filter to catch cross-section matches
        fallback_results = None
        if has_topic_filter:
            fallback_results = self.collection.query(
                query_embeddings=query_embeddings,
                n_results=max(3, requested_top_k),
                include=["documents", "metadatas", "distances"],
            )

        # RRF-like or distance-based deduplication & fusion
        seen = set()
        retrieved = []

        ids = results.get("ids") or [[]]
        if ids and ids[0]:
            for index in range(len(ids[0])):
                metadata = results["metadatas"][0][index] or {}
                content = results["documents"][0][index]
                content_hash = hashlib.md5(content.encode()).hexdigest()
                if content_hash in seen:
                    continue
                seen.add(content_hash)
                distance = results["distances"][0][index]
                retrieved.append(
                    {
                        "content": content,
                        "source": metadata.get("source", ""),
                        "title": metadata.get("title", ""),
                        "heading": metadata.get("heading", ""),
                        "breadcrumb": metadata.get("breadcrumb", ""),
                        "type": metadata.get("type", ""),
                        "pages": metadata.get("pages", ""),
                        "score": 1.0 - distance,
                    }
                )

        # Merge fallback results
        if fallback_results:
            fallback_ids = fallback_results.get("ids") or [[]]
            if fallback_ids and fallback_ids[0]:
                for index in range(len(fallback_ids[0])):
                    content = fallback_results["documents"][0][index]
                    content_hash = hashlib.md5(content.encode()).hexdigest()
                    if content_hash in seen:
                        continue
                    seen.add(content_hash)
                    metadata = fallback_results["metadatas"][0][index] or {}
                    distance = fallback_results["distances"][0][index]
                    retrieved.append(
                        {
                            "content": content,
                            "source": metadata.get("source", ""),
                            "title": metadata.get("title", ""),
                            "heading": metadata.get("heading", ""),
                            "breadcrumb": metadata.get("breadcrumb", ""),
                            "type": metadata.get("type", ""),
                            "pages": metadata.get("pages", ""),
                            # penalize fallback score slightly to favor filtered matches
                            "score": (1.0 - distance) * 0.9,
                        }
                    )

        # Sort by score descending
        retrieved.sort(key=lambda x: x["score"], reverse=True)

        # === WEB SEARCH FALLBACK ===
        if self.should_use_web_search(retrieved):
            print(
                f"DEBUG: Max similarity score {retrieved[0]['score'] if retrieved else 0.0} "
                f"is below threshold {self.settings.web_search_threshold}. "
                f"Activating Web Search Fallback for: '{query}'"
            )
            web_results = self.web_search(query, max_results=3)
            if web_results:
                retrieved = web_results

        return retrieved[:requested_top_k]


    # ---------------------------------------------------------------
    # Semantic cache: cache top-50 queries by cosine similarity
    # ---------------------------------------------------------------
    _query_cache: Dict[str, tuple] = {}  # query_norm -> (result, timestamp, index_version)
    _cache_max_size = 50
    _cache_ttl_seconds = 600  # 10 minutes
    _index_version: int = 0  # Bump on re-index to invalidate all cache

    def _cache_lookup(self, query: str) -> Optional[List[Dict[str, Any]]]:
        """Kiem tra cache: exact match hoac fuzzy > 0.8, skip expired/stale."""
        query_norm = query.lower().strip()
        now = time.time()
        if query_norm in self._query_cache:
            result, ts, ver = self._query_cache[query_norm]
            if ver == self._index_version and (now - ts) < self._cache_ttl_seconds:
                return result
            del self._query_cache[query_norm]  # Expired or stale version
        # Fuzzy: check Jaccard > 0.85
        q_terms = set(re.findall(r"\w{3,}", query_norm))
        if not q_terms:
            return None
        for cached_q, (cached_result, ts, ver) in list(self._query_cache.items()):
            if ver != self._index_version or (now - ts) >= self._cache_ttl_seconds:
                del self._query_cache[cached_q]
                continue
            c_terms = set(re.findall(r"\w{3,}", cached_q))
            if c_terms and len(q_terms & c_terms) / len(q_terms | c_terms) > 0.85:
                return cached_result
        return None

    def _cache_store(self, query: str, result: List[Dict[str, Any]]) -> None:
        """Luu ket qua vao cache kem timestamp + index version."""
        query_norm = query.lower().strip()
        # Evict expired entries first
        now = time.time()
        expired = [k for k, (_, ts, ver) in self._query_cache.items()
                    if ver != self._index_version or (now - ts) >= self._cache_ttl_seconds]
        for k in expired:
            del self._query_cache[k]
        if len(self._query_cache) >= self._cache_max_size:
            oldest = next(iter(self._query_cache))
            del self._query_cache[oldest]
        self._query_cache[query_norm] = (result, now, self._index_version)

    @staticmethod
    def build_context(retrieved: List[Dict[str, Any]], max_tokens: int = 2400) -> str:
        """Build context voi XML tags. Token estimate: ~2.5 chars/token (Vietnamese)."""
        parts = []
        total_est_tokens = 0
        for index, item in enumerate(retrieved):
            content = item["content"].strip()
            est_tokens = len(content) // 2.5  # Vietnamese: ~2.5 chars per token
            if total_est_tokens + est_tokens > max_tokens:
                break
            typ = item.get("type", "unknown")
            breadcrumb = item.get("breadcrumb", "")
            pages = item.get("pages", "")
            attrs = f'id="{index + 1}" type="{typ}"'
            if breadcrumb:
                attrs += f' section="{breadcrumb}"'
            if pages:
                attrs += f' pages="{pages}"'

            tag = f'<chunk {attrs}>\n{content}\n</chunk>'
            parts.append(tag)
            total_est_tokens += est_tokens
        return "\n\n".join(parts)

    def _hybrid_retrieve(
        self, query: str, top_k: int, expand: bool = True
    ) -> List[Dict[str, Any]]:
        """Hybrid retrieval: BM25 (keyword) + Dense (semantic) → RRF fusion.
        
        Reciprocal Rank Fusion: score = Σ 1/(k + rank_i) for each retriever.
        k=60 (standard). Final top_k by fused score.
        """
        if self.collection is None:
            self.init_vector_db()

        embedder = self.load_embedder()
        col_count = self.collection.count()

        # ── Dense (semantic) search ──
        search_query = self._expand_query(query) if expand else query
        query_vec = embedder.encode([search_query])
        dense_results = self.collection.query(
            query_embeddings=query_vec,
            n_results=min(col_count, max(top_k * 3, 15)),
            include=["documents", "metadatas", "distances"],
        )

        # ── BM25 (keyword) search ──
        bm25_ranked = []
        if self.bm25 and self.bm25._built:
            bm25_ranked = self.bm25.search(query, top_k=min(col_count, top_k * 3))

        # ── RRF Fusion ──
        k_rrf = 60
        fused_map: Dict[str, tuple] = {}

        # Add dense results with RRF
        ids = dense_results.get("ids") or [[]]
        if ids and ids[0]:
            for rank, i in enumerate(range(len(ids[0]))):
                content = dense_results["documents"][0][i]
                metadata = dense_results["metadatas"][0][i] or {}
                chash = hashlib.md5(content.encode()).hexdigest()
                dist = dense_results["distances"][0][i]
                rrf = 1.0 / (k_rrf + rank + 1)
                fused_map[chash] = (metadata, rrf, content, 1.0 - dist)

        # Add BM25 results with RRF
        if self.bm25 and bm25_ranked:
            all_docs = self.collection.get(include=["documents", "metadatas"])
            for rank, (doc_idx, _bm25_score) in enumerate(bm25_ranked):
                if doc_idx >= len(all_docs["documents"]):
                    continue
                content = all_docs["documents"][doc_idx]
                metadata = all_docs["metadatas"][doc_idx] or {}
                chash = hashlib.md5(content.encode()).hexdigest()
                rrf = 1.0 / (k_rrf + rank + 1)
                if chash in fused_map:
                    old_meta, old_rrf, old_content, old_dense = fused_map[chash]
                    fused_map[chash] = (old_meta, old_rrf + rrf, old_content, old_dense)
                else:
                    fused_map[chash] = (metadata, rrf, content, 0.5)  # BM25-only: mid score

        # Sort by fused RRF score
        fused = sorted(fused_map.values(), key=lambda x: x[1], reverse=True)

        retrieved = []
        for metadata, rrf_score, content, _dense_score in fused[:top_k]:
            retrieved.append({
                "content": content,
                "source": metadata.get("source", ""),
                "title": metadata.get("title", ""),
                "heading": metadata.get("heading", ""),
                "breadcrumb": metadata.get("breadcrumb", ""),
                "type": metadata.get("type", ""),
                "pages": metadata.get("pages", ""),
                "score": rrf_score,
            })
        return retrieved

    def query(self, question: str, top_k: Optional[int] = None) -> Tuple[str, str, List[Dict[str, Any]]]:
        """Tra ve (thinking, answer, sources)."""
        question = question.strip()
        if not question:
            raise ValueError("Question must not be empty")

        retrieved = self.retrieve(question, top_k=top_k)
        if not retrieved:
            return "", self.FALLBACK_ANSWER, []

        context = self.build_context(retrieved)
        llm = self.load_llm()
        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"NGỮ CẢNH THAM KHẢO:\n{context}\n\n"
                    f"CÂU HỎI CỦA SINH VIÊN: {question}\n\n"
                    "Hãy trả lời câu hỏi trên dựa vào ngữ cảnh được cung cấp. "
                    "Chỉ đưa ra câu trả lời cuối cùng."
                ),
            },
        ]
        response = llm.session.post(
            f"{llm.base_url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {llm.api_key}"},
            json={
                "model": llm.model,
                "messages": llm._prepare_messages(messages),
                "temperature": 0.2,
                "max_tokens": self.settings.llm_max_tokens,
            },
            timeout=llm.timeout,
        )
        response.raise_for_status()
        thinking, answer = llm.extract_answer_with_thinking(response.json())
        return thinking, answer, retrieved


    def evaluate_retrieval(self, test_questions: list) -> dict:
        """Danh gia retrieval: hit rate + MRR."""
        hits = 0
        total = 0
        reciprocal_ranks = []
        for q in test_questions:
            question = q["question"]
            expected_kw = q.get("expected_keywords", [])
            if not expected_kw:
                continue
            results = self.retrieve(question, top_k=5)
            total += 1
            for rank, item in enumerate(results, 1):
                content_lower = item["content"].lower()
                if any(kw.lower() in content_lower for kw in expected_kw):
                    hits += 1
                    reciprocal_ranks.append(1.0 / rank)
                    break
            else:
                reciprocal_ranks.append(0.0)
        hit_rate = hits / max(1, total)
        mrr = sum(reciprocal_ranks) / max(1, len(reciprocal_ranks))
        return {"hit_rate": round(hit_rate, 4), "mrr": round(mrr, 4), "total": total, "hits": hits}


def main() -> None:
    import sys

    pipeline = UTCRAGPipeline()

    if len(sys.argv) > 1 and sys.argv[1] == "index":
        print("=== INDEXING DOCUMENTS (Ollama local) ===")
        pipeline.index_documents(reset=True)
    elif len(sys.argv) > 1 and sys.argv[1] == "index-structured":
        print("=== INDEXING STRUCTURED CHUNKS ===")
        pipeline.index_structured(reset=True)
    elif len(sys.argv) > 1 and sys.argv[1] == "ask":
        question = " ".join(sys.argv[2:]) or "Trường UTC có những ngành đào tạo nào?"
        print(f"\nQ: {question}\n")
        answer, sources = pipeline.query(question)
        print(f"A: {answer}\n")
        for source in sources:
            print(f"  [{source['score']:.3f}] {source['title']}")
    elif len(sys.argv) > 1 and sys.argv[1] == "eval":
        import json
        with open("data/autotest/questions.json") as f:
            questions = json.load(f)
        result = pipeline.evaluate_retrieval(questions)
        print(f"Hit Rate: {result['hit_rate']*100:.1f}% | MRR: {result['mrr']:.3f} | {result['hits']}/{result['total']}")
    elif len(sys.argv) > 1 and sys.argv[1] == "retrieve":
        question = " ".join(sys.argv[2:]) or "Trường UTC có những ngành đào tạo nào?"
        for source in pipeline.retrieve(question):
            print(f"[{source['score']:.3f}] {source['title']} - {source['content'][:160]}")
    else:
        print("Usage: python -m src.rag_pipeline index | ask <câu hỏi> | retrieve <câu hỏi>")


if __name__ == "__main__":
    main()

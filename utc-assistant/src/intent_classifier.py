"""Phase-1 intent classifier with heuristic fallback and optional model artifact."""

from __future__ import annotations

import math
import re
from typing import Any, Dict, Optional

from src.model_registry import ModelRegistry, get_model_registry


INTENT_TOPIC_MAP: Dict[str, str] = {
    "hoc_phi": "Học phí",
    "lich_thi": "Lịch thi",
    "thu_tuc": "Thủ tục",
    "hoc_bong": "Học bổng",
    "ky_tuc_xa": "Ký túc xá",
    "tai_khoan_he_thong": "Tài khoản hệ thống",
    "hoc_tap_ca_nhan": "Học tập cá nhân",
    "tin_tuc_su_kien": "Tin tức - sự kiện",
    "ngoai_mien_utc": "Ngoài miền UTC",
    "khac": "Khác",
}

ALLOWED_INTENTS = set(INTENT_TOPIC_MAP)

PERSONAL_PATTERNS = [
    r"\bđiểm\s+(số|trung bình|tổng kết|tích lũy|học kỳ|của (tôi|em|mình))\b",
    r"\bgpa\b",
    r"\b(của|cho)\s+(tôi|em|mình)\b",
    r"\btôi\s+(có|bị|được|nên|cần|phải|muốn)\b",
    r"\b(môn|tín chỉ)\s+(của|cho)\s+(tôi|em)\b",
    r"\bhọc\s+(lại|cải thiện|tiếp)\b",
    r"\b(bảng|xem)\s+điểm\b",
    r"\bkết\s+quả\s+học\s+tập\b",
]

GREETING_PATTERNS = [
    r"^(xin chào|chào|hello|hi)\b",
    r"\bcảm ơn\b",
    r"\bbạn là ai\b",
    r"\bgiúp tôi\b",
]

UTC_HINT_PATTERNS = [
    r"\butc\b",
    r"\bđại học giao thông vận tải\b",
    r"\bsv\.utc\.edu\.vn\b",
    r"\butc\.edu\.vn\b",
    r"\bphòng đào tạo\b",
    r"\bphòng công tác sinh viên\b",
]

OUT_OF_DOMAIN_PATTERNS = [
    r"\bthời tiết\b",
    r"\bgiá vàng\b",
    r"\bbitcoin\b",
    r"\bchứng khoán\b",
    r"\bbóng đá\b",
    r"\bworld cup\b",
    r"\btổng thống\b",
    r"\bđiện thoại\b",
    r"\blaptop\b",
    r"\bphim\b",
    r"\bbài hát\b",
]

INTENT_KEYWORDS: Dict[str, tuple[list[str], float]] = {
    "hoc_phi": (["học phí", "hoc phi", "đóng tiền", "nộp tiền", "miễn giảm"], 0.94),
    "lich_thi": (["lịch thi", "lich thi", "lịch học", "hoc phan", "học phần", "thi lại"], 0.92),
    "thu_tuc": (["thủ tục", "thu tuc", "xác nhận", "xac nhan", "giấy tờ", "hồ sơ"], 0.9),
    "hoc_bong": (["học bổng", "hoc bong", "trợ cấp", "khuyến khích học tập"], 0.91),
    "ky_tuc_xa": (["ký túc xá", "ky tuc xa", "ktx", "nội trú"], 0.93),
    "tai_khoan_he_thong": (["mật khẩu", "đăng nhập", "qldt", "email utc", "sv.utc.edu.vn", "lms"], 0.9),
    "tin_tuc_su_kien": (["thông báo mới", "mới nhất", "tin tức", "sự kiện", "hạn cuối", "deadline"], 0.82),
}


def _safe_sigmoid(value: float) -> float:
    value = max(min(value, 10.0), -10.0)
    return 1.0 / (1.0 + math.exp(-value))


class IntentClassifier:
    def __init__(self, registry: Optional[ModelRegistry] = None):
        self.registry = registry or get_model_registry()

    def classify(self, question: str, current_user: Optional[dict[str, Any]] = None) -> Dict[str, Any]:
        question = question.strip()
        model_result = self._classify_with_model(question)
        if model_result is not None:
            return model_result
        return self._classify_with_heuristics(question, current_user=current_user)

    def _classify_with_model(self, question: str) -> Optional[Dict[str, Any]]:
        model = self.registry.load_intent_classifier()
        if model is None or not question:
            return None
        try:
            predicted = model.predict([question])[0]
            intent = str(predicted).strip()
            label_map = self.registry.load_intent_label_map()
            if label_map:
                intent = label_map.get(intent, intent)
            if intent not in ALLOWED_INTENTS:
                return None

            confidence = 0.75
            if hasattr(model, "predict_proba"):
                probabilities = model.predict_proba([question])[0]
                confidence = float(max(probabilities))
            elif hasattr(model, "decision_function"):
                scores = model.decision_function([question])
                raw_value = scores[0]
                if isinstance(raw_value, (list, tuple)):
                    confidence = float(max(_safe_sigmoid(float(item)) for item in raw_value))
                else:
                    confidence = float(_safe_sigmoid(float(raw_value)))

            heuristic = self._classify_with_heuristics(question)
            return {
                "intent": intent,
                "confidence": round(confidence, 4),
                "signals": heuristic["signals"],
                "source": "artifact",
            }
        except Exception:
            return None

    def _classify_with_heuristics(
        self,
        question: str,
        current_user: Optional[dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        normalized = question.lower()
        has_current_user = bool(current_user and current_user.get("id"))
        signals = {
            "personal_question": has_current_user and any(
                re.search(pattern, normalized) for pattern in PERSONAL_PATTERNS
            ),
            "greeting_or_meta": any(re.search(pattern, normalized) for pattern in GREETING_PATTERNS),
            "has_utc_terms": any(re.search(pattern, normalized) for pattern in UTC_HINT_PATTERNS),
            "out_of_domain": any(re.search(pattern, normalized) for pattern in OUT_OF_DOMAIN_PATTERNS),
            "news_question": any(keyword in normalized for keyword in ("mới nhất", "thông báo", "tin tức", "sự kiện", "deadline")),
        }

        if signals["personal_question"]:
            return self._result("hoc_tap_ca_nhan", 0.95, signals)
        if signals["out_of_domain"] and not signals["has_utc_terms"]:
            return self._result("ngoai_mien_utc", 0.92, signals)

        for intent, (keywords, confidence) in INTENT_KEYWORDS.items():
            if any(keyword in normalized for keyword in keywords):
                return self._result(intent, confidence, signals)

        if signals["news_question"]:
            return self._result(
                "tin_tuc_su_kien" if signals["has_utc_terms"] else "ngoai_mien_utc",
                0.78,
                signals,
            )
        if signals["greeting_or_meta"] and len(normalized.split()) <= 6:
            return self._result("khac", 0.72, signals)
        if signals["has_utc_terms"]:
            return self._result("khac", 0.62, signals)
        return self._result("khac", 0.55, signals)

    @staticmethod
    def _result(intent: str, confidence: float, signals: Dict[str, bool]) -> Dict[str, Any]:
        return {
            "intent": intent,
            "confidence": round(confidence, 4),
            "signals": signals,
            "source": "heuristic",
        }


_DEFAULT_CLASSIFIER = IntentClassifier()


def get_intent_classifier() -> IntentClassifier:
    return _DEFAULT_CLASSIFIER


def classify(question: str, current_user: Optional[dict[str, Any]] = None) -> Dict[str, Any]:
    return get_intent_classifier().classify(question, current_user=current_user)


def intent_to_topic(intent: str) -> str:
    return INTENT_TOPIC_MAP.get(intent, "Khác")

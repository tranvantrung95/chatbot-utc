import tempfile
import unittest
from pathlib import Path

from src.intent_classifier import IntentClassifier
from src.model_registry import ModelRegistry
from src.route_policy import build_retrieval_probe, select_route


class IntentClassifierTests(unittest.TestCase):
    def test_classifier_detects_personal_question(self):
        classifier = IntentClassifier()

        result = classifier.classify(
            "Điểm trung bình của tôi hiện tại là bao nhiêu?",
            current_user={"id": "student-1"},
        )

        self.assertEqual(result["intent"], "hoc_tap_ca_nhan")
        self.assertTrue(result["signals"]["personal_question"])

    def test_classifier_detects_hoc_phi(self):
        classifier = IntentClassifier()

        result = classifier.classify("Học phí học kỳ này đóng khi nào?")

        self.assertEqual(result["intent"], "hoc_phi")

    def test_classifier_falls_back_when_artifact_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            registry = ModelRegistry(models_dir=Path(tmp))
            classifier = IntentClassifier(registry=registry)

            result = classifier.classify("Ký túc xá mở đăng ký khi nào?")

        self.assertEqual(result["intent"], "ky_tuc_xa")
        self.assertEqual(result["source"], "heuristic")


class RoutePolicyTests(unittest.TestCase):
    def test_route_selects_student_context_for_personal_question(self):
        intent_result = {
            "intent": "hoc_tap_ca_nhan",
            "confidence": 0.95,
            "signals": {"personal_question": True, "greeting_or_meta": False},
        }
        probe = build_retrieval_probe([{"score": 0.9}, {"score": 0.8}, {"score": 0.7}])

        decision = select_route("Điểm của tôi", intent_result, probe)

        self.assertEqual(decision["route"], "student_context_plus_rag")
        self.assertTrue(decision["used_student_context"])

    def test_route_selects_web_first_for_news(self):
        intent_result = {
            "intent": "tin_tuc_su_kien",
            "confidence": 0.8,
            "signals": {"personal_question": False, "greeting_or_meta": False},
        }
        probe = build_retrieval_probe([{"score": 0.02}])

        decision = select_route("Thông báo mới nhất của UTC", intent_result, probe)

        self.assertEqual(decision["route"], "web_first")
        self.assertTrue(decision["use_web_search"])

    def test_route_selects_web_first_for_out_of_domain(self):
        intent_result = {
            "intent": "ngoai_mien_utc",
            "confidence": 0.9,
            "signals": {"personal_question": False, "greeting_or_meta": False},
        }
        probe = build_retrieval_probe([])

        decision = select_route("Giá vàng hôm nay", intent_result, probe)

        self.assertEqual(decision["route"], "web_first")

    def test_route_selects_direct_fallback_for_meta_low_confidence(self):
        intent_result = {
            "intent": "khac",
            "confidence": 0.72,
            "signals": {"personal_question": False, "greeting_or_meta": True},
        }
        probe = build_retrieval_probe([])

        decision = select_route("Xin chào", intent_result, probe)

        self.assertEqual(decision["route"], "direct_fallback")

    def test_route_selects_rag_internal_for_regular_internal_question(self):
        intent_result = {
            "intent": "hoc_phi",
            "confidence": 0.9,
            "signals": {"personal_question": False, "greeting_or_meta": False},
        }
        probe = build_retrieval_probe([{"score": 0.42}, {"score": 0.31}, {"score": 0.22}])

        decision = select_route("Học phí ngành CNTT là bao nhiêu?", intent_result, probe)

        self.assertEqual(decision["route"], "rag_internal")


if __name__ == "__main__":
    unittest.main()

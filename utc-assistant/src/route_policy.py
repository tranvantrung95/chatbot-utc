"""Phase-1 route policy for UTC Assistant chat flows."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def build_retrieval_probe(retrieved: Optional[List[Dict[str, Any]]]) -> Dict[str, Any]:
    retrieved = retrieved or []
    if not retrieved:
        top1_score = 0.0
    else:
        first = retrieved[0]
        if "_llm_score" in first:
            top1_score = float(first["_llm_score"])
        elif "dense_score" in first:
            top1_score = float(first["dense_score"])
        else:
            top1_score = float(retrieved[0].get("dense_score", retrieved[0].get("score", 0.0))) if retrieved else 0.0
            
    result_count = len(retrieved)
    has_web_results = any(item.get("type") == "web" for item in retrieved)
    is_low_confidence = result_count == 0 or top1_score < 0.55 or result_count < 3
    return {
        "top1_score": round(top1_score, 4),
        "result_count": result_count,
        "has_web_results": has_web_results,
        "is_low_confidence": is_low_confidence,
    }


def summarize_retrieval_tier(retrieved: Optional[List[Dict[str, Any]]]) -> str:
    probe = build_retrieval_probe(retrieved)
    if probe["has_web_results"]:
        return "web"
    if probe["result_count"] == 0:
        return "none"
    if probe["is_low_confidence"]:
        return "partial"
    return "full"


def select_route(
    question: str,
    intent_result: Dict[str, Any],
    retrieval_probe: Dict[str, Any],
    current_user: Optional[dict[str, Any]] = None,
) -> Dict[str, Any]:
    del question
    del current_user

    intent = intent_result.get("intent", "khac")
    signals = intent_result.get("signals", {})

    if signals.get("greeting_or_meta") and retrieval_probe.get("is_low_confidence"):
        route = "direct_fallback"
    elif intent == "hoc_tap_ca_nhan" or signals.get("personal_question"):
        route = "student_context_plus_rag"
    elif intent in {"tin_tuc_su_kien", "ngoai_mien_utc"}:
        route = "web_first"
    else:
        route = "rag_internal"

    used_student_context = route == "student_context_plus_rag"
    use_web_search = route == "web_first"
    if route == "web_first":
        retrieval_tier = "web"
    elif retrieval_probe.get("result_count", 0) == 0:
        retrieval_tier = "none"
    elif retrieval_probe.get("is_low_confidence"):
        retrieval_tier = "partial"
    else:
        retrieval_tier = "full"

    return {
        "route": route,
        "used_student_context": used_student_context,
        "use_web_search": use_web_search,
        "retrieval_tier": retrieval_tier,
    }

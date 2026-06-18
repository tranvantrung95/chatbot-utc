"""Conversation summarization: nén lịch sử chat dài thành tóm tắt ngắn.

Khi cuộc hội thoại vượt quá 8 messages, tự động tóm tắt các messages cũ
và chỉ giữ 4 messages gần nhất ở dạng đầy đủ.
"""

from __future__ import annotations

from typing import List, Optional

from src.database import get_db


SUMMARY_PROMPT = """Tóm tắt đoạn hội thoại sau thành 2-3 câu tiếng Việt, 
giữ lại các thông tin quan trọng: câu hỏi chính, câu trả lời chính, 
quyết định hoặc thông tin then chốt. Chỉ trả về phần tóm tắt, không thêm gì khác.

HỘI THOẠI:
{history}

TÓM TẮT:"""


class ConversationSummarizer:
    """Tóm tắt hội thoại dài để tiết kiệm context window."""
    
    MAX_RECENT_MESSAGES = 4  # Keep last N messages verbatim
    SUMMARIZE_THRESHOLD = 8  # Trigger summarization at this message count
    
    def __init__(self, pipeline):
        self.pipeline = pipeline
    
    def should_summarize(self, conversation_id: str) -> bool:
        """Kiểm tra xem conversation có cần tóm tắt không."""
        conn = get_db()
        count = conn.execute(
            "SELECT COUNT(*) FROM messages WHERE conversation_id=?",
            (conversation_id,),
        ).fetchone()[0]
        conn.close()
        return count >= self.SUMMARIZE_THRESHOLD
    
    def build_context(
        self, conversation_id: str, existing_summary: str = ""
    ) -> tuple:
        """Build conversation context cho LLM prompt.
        
        Returns: (summary_text, recent_messages_text)
        - summary_text: phần tóm tắt của các messages cũ (có thể rỗng)
        - recent_messages_text: N messages gần nhất dạng đầy đủ
        """
        conn = get_db()
        rows = conn.execute(
            "SELECT role, content FROM messages WHERE conversation_id=? "
            "ORDER BY created_at ASC",
            (conversation_id,),
        ).fetchall()
        conn.close()
        
        if len(rows) <= self.SUMMARIZE_THRESHOLD:
            # Chưa cần summarize: trả về toàn bộ
            parts = []
            for role, content in rows:
                label = "Sinh viên" if role == "student" else "Trợ lý"
                parts.append(f"{label}: {content}")
            return "", "LỊCH SỬ HỘI THOẠI:\n" + "\n".join(parts)
        
        # Tách: old (cần summarize) + recent (giữ nguyên)
        old_messages = rows[:-self.MAX_RECENT_MESSAGES]
        recent = rows[-self.MAX_RECENT_MESSAGES:]
        
        # Nếu đã có summary từ trước, giữ lại
        summary = existing_summary
        
        # Nếu chưa có summary, tạo mới từ old messages
        if not summary and len(old_messages) >= 2:
            summary = self._summarize(old_messages)
        
        # Build recent text
        recent_parts = []
        for role, content in recent:
            label = "Sinh viên" if role == "student" else "Trợ lý"
            recent_parts.append(f"{label}: {content}")
        recent_text = "HỘI THOẠI GẦN ĐÂY:\n" + "\n".join(recent_parts)
        
        return summary, recent_text
    
    def _summarize(self, messages: list) -> str:
        """Gọi LLM để tóm tắt đoạn hội thoại cũ."""
        history_text = "\n".join(
            f"{'SV' if r == 'student' else 'Bot'}: {c[:300]}"
            for r, c in messages
        )
        
        llm = self.pipeline.load_llm()
        prompt = SUMMARY_PROMPT.format(history=history_text)
        
        try:
            response = llm.session.post(
                f"{llm.base_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {llm.api_key}"},
                json={
                    "model": llm.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 200,
                    "enable_thinking": False,
                },
                timeout=30,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            return content.strip()
        except Exception:
            return ""

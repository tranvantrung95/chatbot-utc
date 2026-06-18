"""Streaming SSE endpoint cho chat + thinking real-time."""
import json
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from src.api_server import (
    app, settings, ensure_runtime_files, get_current_user,
    get_pipeline, chat_limiter, intent_to_topic,
    now_epoch,
    build_chat_messages, build_source_items, log_question_event,
    resolve_chat_execution_plan,
)


class StreamChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)
    conversation_id: str = Field(default="")


@app.post("/api/chat/stream")
async def api_chat_stream(
    payload: StreamChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """SSE streaming: gui thinking + answer real-time."""
    ensure_runtime_files()
    if not chat_limiter.check(current_user["id"]):
        raise HTTPException(status_code=429, detail="Quá nhiều câu hỏi.")

    question = payload.question.strip()
    started_at = now_epoch()
    pipeline = get_pipeline(settings)
    execution = resolve_chat_execution_plan(
        pipeline,
        question=question,
        current_user=current_user,
        top_k=payload.top_k,
    )
    retrieved = execution["retrieved"]
    student_ctx = execution["student_ctx"]

    # Multi-turn: load conversation history from SQLite (with summarization for long chats)
    conv_history = ""
    if payload.conversation_id:
        try:
            from src.database import get_db
            from src.conversation_summarizer import ConversationSummarizer
            
            summarizer = ConversationSummarizer(pipeline)
            if summarizer.should_summarize(payload.conversation_id):
                # Long conversation: summarize old + keep recent
                summary, recent = summarizer.build_context(payload.conversation_id)
                if summary:
                    conv_history = f"TÓM TẮT HỘI THOẠI TRƯỚC ĐÓ:\n{summary}\n\n{recent}\n\n"
                else:
                    conv_history = f"{recent}\n\n"
            else:
                # Short conversation: full history
                conn = get_db()
                rows = conn.execute(
                    "SELECT role, content FROM messages WHERE conversation_id=? "
                    "ORDER BY created_at ASC",
                    (payload.conversation_id,)
                ).fetchall()
                conn.close()
                if rows:
                    history_parts = []
                    for role, content in rows:
                        label = "Sinh viên" if role == "student" else "Trợ lý"
                        history_parts.append(f"{label}: {content}")
                    if history_parts:
                        conv_history = "LỊCH SỬ HỘI THOẠI:\n" + "\n".join(history_parts) + "\n\n"
        except Exception:
            pass

    async def event_stream() -> AsyncGenerator[str, None]:
        thinking_buffer = ""
        answer_buffer = ""

        if execution["route_decision"]["route"] == "direct_fallback" or not retrieved:
            done_payload = {
                "type": "done",
                "sources": [],
                "intent": execution["intent_result"]["intent"],
                "intent_confidence": execution["intent_result"]["confidence"],
                "route": execution["route_decision"]["route"],
                "retrieval_tier": execution["route_decision"]["retrieval_tier"],
                "used_web_search": execution["route_decision"]["use_web_search"],
                "used_student_context": execution["route_decision"]["used_student_context"],
            }
            yield f"data: {json.dumps({'type': 'answer', 'content': pipeline.FALLBACK_ANSWER})}\n\n"
            yield f"data: {json.dumps(done_payload)}\n\n"
            return
        llm = pipeline.load_llm()
        messages = build_chat_messages(
            pipeline,
            question=question,
            retrieved=retrieved,
            student_ctx=student_ctx,
            conv_history=conv_history,
        )

        try:
            response = llm.session.post(
                f"{llm.base_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {llm.api_key}"},
                json={
                    "model": llm.model,
                    "messages": llm._prepare_messages(messages),
                    "temperature": 0.2,
                    "max_tokens": settings.llm_max_tokens,
                    "enable_thinking": True,
                    "stream": True,
                },
                timeout=llm.timeout,
                stream=True,
            )
            response.raise_for_status()

            in_thinking = True

            for line in response.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                except json.JSONDecodeError:
                    continue

                choices = chunk.get("choices") or []
                if not choices:
                    continue

                delta = choices[0].get("delta") or {}
                reasoning = delta.get("reasoning", "")
                content = delta.get("content", "")

                if reasoning:
                    thinking_buffer += reasoning
                    yield f"data: {json.dumps({'type': 'thinking', 'content': reasoning})}\n\n"
                elif content:
                    answer_buffer += content
                    yield f"data: {json.dumps({'type': 'answer', 'content': content})}\n\n"

            # Build sources
            source_items = build_source_items(retrieved)

            # Save to DB if conversation_id provided
            bot_msg_id = ""
            if payload.conversation_id:
                try:
                    from src.database import get_db, now, uid
                    conn = get_db()
                    ts = now()
                    sid = uid()
                    conn.execute(
                        "INSERT INTO messages(id,conversation_id,role,content,thinking,sources_json,created_at) VALUES(?,?,?,?,?,?,?)",
                        (sid, payload.conversation_id, "student", question, "", "[]", ts))
                    bot_msg_id = uid()
                    conn.execute(
                        "INSERT INTO messages(id,conversation_id,role,content,thinking,sources_json,created_at) VALUES(?,?,?,?,?,?,?)",
                        (bot_msg_id, payload.conversation_id, "bot", answer_buffer, thinking_buffer,
                         json.dumps(source_items, ensure_ascii=False), ts + 1))
                    conn.execute("UPDATE conversations SET updated_at=?, title=? WHERE id=? AND title='Cuộc trò chuyện mới'",
                                 (ts + 1, question[:80], payload.conversation_id))
                    conn.commit()
                    conn.close()
                except Exception:
                    pass

            done_payload = {
                "type": "done",
                "sources": source_items,
                "message_id": bot_msg_id,
                "intent": execution["intent_result"]["intent"],
                "intent_confidence": execution["intent_result"]["confidence"],
                "route": execution["route_decision"]["route"],
                "retrieval_tier": execution["route_decision"]["retrieval_tier"],
                "used_web_search": execution["route_decision"]["use_web_search"],
                "used_student_context": execution["route_decision"]["used_student_context"],
            }
            yield f"data: {json.dumps(done_payload)}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)})}\n\n"

        # Log question
        latency_sec = round(now_epoch() - started_at, 2)
        log_question_event(
            question=question,
            current_user=current_user,
            answer=answer_buffer or pipeline.FALLBACK_ANSWER,
            thinking=thinking_buffer,
            latency_sec=latency_sec,
            topic=intent_to_topic(execution["intent_result"]["intent"]),
            intent=execution["intent_result"]["intent"],
            intent_confidence=execution["intent_result"]["confidence"],
            route=execution["route_decision"]["route"],
            retrieval_tier=execution["route_decision"]["retrieval_tier"],
            used_student_context=execution["route_decision"]["used_student_context"],
            used_web_search=execution["route_decision"]["use_web_search"],
            top1_score=execution["retrieval_probe"]["top1_score"],
            result_count=execution["retrieval_probe"]["result_count"],
            conversation_id=payload.conversation_id,
        )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )

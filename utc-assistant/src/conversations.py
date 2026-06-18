"""Multi-turn conversation management."""
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field

from src.database import get_db, now, uid
from src.api_server import app, get_current_user


class CreateConversationRequest(BaseModel):
    title: str = Field(default="Cuộc trò chuyện mới", max_length=200)


@app.post("/api/conversations")
def create_conversation(payload: CreateConversationRequest, current_user=Depends(get_current_user)):
    conn = get_db()
    cid = uid()
    ts = now()
    conn.execute(
        "INSERT INTO conversations (id,user_id,title,created_at,updated_at) VALUES (?,?,?,?,?)",
        (cid, current_user["id"], payload.title, ts, ts),
    )
    conn.commit()
    conn.close()
    return {"id": cid, "title": payload.title}


@app.get("/api/conversations")
def list_conversations(current_user=Depends(get_current_user)):
    conn = get_db()
    rows = conn.execute(
        "SELECT id,title,created_at,updated_at FROM conversations WHERE user_id=? ORDER BY updated_at DESC LIMIT 50",
        (current_user["id"],),
    ).fetchall()
    conn.close()
    return {"items": [{"id": r["id"], "title": r["title"], "created_at": r["created_at"], "updated_at": r["updated_at"]} for r in rows]}


@app.get("/api/conversations/{conv_id}")
def get_conversation(conv_id: str, current_user=Depends(get_current_user)):
    conn = get_db()
    conv = conn.execute("SELECT id,title FROM conversations WHERE id=? AND user_id=?", (conv_id, current_user["id"])).fetchone()
    if not conv:
        conn.close()
        raise HTTPException(404, "Không tìm thấy cuộc trò chuyện")
    msgs = conn.execute(
        "SELECT id,role,content,thinking,sources_json,created_at FROM messages WHERE conversation_id=? ORDER BY created_at", (conv_id,)
    ).fetchall()
    conn.close()
    import json
    return {"id": conv["id"], "title": conv["title"], "messages": [
        {"id": m["id"], "role": m["role"], "content": m["content"], "thinking": m["thinking"],
         "sources": json.loads(m["sources_json"]), "created_at": m["created_at"]} for m in msgs
    ]}


@app.delete("/api/conversations/{conv_id}")
def delete_conversation(conv_id: str, current_user=Depends(get_current_user)):
    conn = get_db()
    conn.execute("DELETE FROM conversations WHERE id=? AND user_id=?", (conv_id, current_user["id"]))
    conn.commit()
    conn.close()
    return {"message": "Đã xóa"}

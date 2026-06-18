"""Feedback: upvote/downvote bot answers."""
from fastapi import Depends, HTTPException
from pydantic import BaseModel, Field

from src.database import get_db, now, uid
from src.api_server import app, get_current_user


class RateRequest(BaseModel):
    message_id: str
    rating: str = Field(pattern="^(up|down)$")
    reason: str = Field(default="", max_length=200)
    comment: str = Field(default="", max_length=1000)


@app.post("/api/feedback/rate")
def rate_answer(payload: RateRequest, current_user=Depends(get_current_user)):
    conn = get_db()
    msg = conn.execute("SELECT id FROM messages WHERE id=?", (payload.message_id,)).fetchone()
    if not msg:
        conn.close()
        raise HTTPException(404, "Không tìm thấy tin nhắn")
    conn.execute(
        "INSERT INTO feedback_ratings (id,message_id,user_id,rating,reason,comment,created_at) VALUES (?,?,?,?,?,?,?)",
        (uid(), payload.message_id, current_user["id"], payload.rating, payload.reason, payload.comment, now()),
    )
    conn.commit()
    conn.close()
    return {"message": "Đã ghi nhận đánh giá"}


@app.get("/api/feedback/stats")
def feedback_stats(current_user=Depends(get_current_user)):
    conn = get_db()
    up = conn.execute("SELECT COUNT(*) FROM feedback_ratings WHERE rating='up'").fetchone()[0]
    down = conn.execute("SELECT COUNT(*) FROM feedback_ratings WHERE rating='down'").fetchone()[0]
    conn.close()
    total = up + down
    return {"up": up, "down": down, "total": total, "satisfaction": round(up / max(1, total) * 100, 1)}

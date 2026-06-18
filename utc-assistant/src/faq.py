"""FAQ: most-asked questions from chat history."""
from src.database import get_db
from src.api_server import app


@app.get("/api/faq")
def get_faq(limit: int = 10):
    conn = get_db()
    rows = conn.execute(
        "SELECT content, COUNT(*) as cnt FROM messages WHERE role='student' GROUP BY content ORDER BY cnt DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    if rows:
        return {"items": [r["content"] for r in rows]}
    return {"items": [
        "Học phí đóng thế nào?",
        "Cách tính điểm trung bình tích lũy?",
        "Điều kiện nhận học bổng?",
        "Ký túc xá đăng ký ra sao?",
        "Lịch thi xem ở đâu?",
    ]}

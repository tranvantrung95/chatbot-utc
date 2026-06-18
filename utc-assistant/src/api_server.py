"""FastAPI backend for UTC Assistant frontend integration."""

from __future__ import annotations

import bcrypt
import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Literal, Optional
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from src.document_store import list_documents, save_imported_text
from src.intent_classifier import classify as classify_intent, intent_to_topic
from src.rag_pipeline import Settings, UTCRAGPipeline, load_settings
from src.route_policy import build_retrieval_probe, select_route, summarize_retrieval_tier


BASE_DIR = Path(__file__).resolve().parent.parent
RUNTIME_DIR = BASE_DIR / "data" / "runtime"
USERS_FILE = RUNTIME_DIR / "users.json"
NEWS_FILE = RUNTIME_DIR / "news.json"
FEEDBACK_FILE = RUNTIME_DIR / "feedback.json"
BUGS_FILE = RUNTIME_DIR / "bugs.json"
QUESTIONS_FILE = RUNTIME_DIR / "questions.json"
ACTIVITY_FILE = RUNTIME_DIR / "activities.json"
ROUTER_EVENTS_FILE = RUNTIME_DIR / "router_events.jsonl"

SESSION_TTL_SECONDS = 60 * 60 * 24
FALLBACK_ANSWER_PREFIX = "Xin lỗi, tôi chưa có thông tin"

DATA_LOCK = threading.Lock()
SESSIONS: dict[str, "SessionData"] = {}
AUTH_SCHEME = HTTPBearer(auto_error=False)


@dataclass
class SessionData:
    user_id: str
    expires_at: float


class RegisterRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    identifier: str = Field(min_length=3, max_length=120)
    email: str = Field(min_length=5, max_length=200)
    password: str = Field(min_length=6, max_length=200)
    role: Literal["student", "admin"] = "student"


class LoginRequest(BaseModel):
    identifier: str = Field(min_length=3, max_length=200)
    password: str = Field(min_length=6, max_length=200)


class ForgotPasswordRequest(BaseModel):
    email: str = Field(min_length=5, max_length=200)


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=6, max_length=200)
    new_password: str = Field(min_length=6, max_length=200)


class ChatRequest(BaseModel):
    question: str = Field(min_length=2, max_length=2000)
    top_k: int = Field(default=5, ge=1, le=20)


class FeedbackRequest(BaseModel):
    subject: str = Field(min_length=2, max_length=120)
    satisfaction: str = Field(min_length=2, max_length=80)
    content: str = Field(min_length=5, max_length=4000)
    email: str = Field(min_length=5, max_length=200)


class BugRequest(BaseModel):
    bug_type: str = Field(min_length=2, max_length=120)
    severity: str = Field(min_length=2, max_length=40)
    description: str = Field(min_length=5, max_length=4000)
    screenshot_note: str = Field(default="", max_length=500)


class DocumentImportRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    source: str = Field(min_length=2, max_length=200)
    content: str = Field(min_length=50, max_length=100000)


def now_epoch() -> float:
    return time.time()


DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 100


def paginate(items: list[Any], page: int, page_size: int) -> dict[str, Any]:
    page = max(1, page)
    page_size = max(1, min(page_size, MAX_PAGE_SIZE))
    total = len(items)
    total_pages = max(1, (total + page_size - 1) // page_size)
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "page": page,
        "page_size": page_size,
        "total": total,
        "total_pages": total_pages,
    }


class RateLimiter:
    """In-memory sliding-window rate limiter."""

    def __init__(self, max_requests: int, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = {}
        self._lock = threading.Lock()

    def check(self, key: str) -> bool:
        epoch = now_epoch()
        with self._lock:
            timestamps = self._hits.get(key, [])
            timestamps = [ts for ts in timestamps if epoch - ts < self.window_seconds]
            if len(timestamps) >= self.max_requests:
                self._hits[key] = timestamps
                return False
            timestamps.append(epoch)
            self._hits[key] = timestamps
            return True


chat_limiter = RateLimiter(max_requests=5, window_seconds=60)
login_limiter = RateLimiter(max_requests=200, window_seconds=60)


def format_datetime(epoch: Optional[float] = None) -> str:
    return time.strftime("%d/%m/%Y %H:%M", time.localtime(epoch or now_epoch()))


def today_key(epoch: Optional[float] = None) -> str:
    return time.strftime("%Y-%m-%d", time.localtime(epoch or now_epoch()))


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


def parse_source_from_text(path: Path) -> str:
    try:
        for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
            stripped = line.strip()
            if stripped.lower().startswith("# nguồn import:"):
                return stripped.split(":", 1)[1].strip() or "Kho tri thức UTC"
    except OSError:
        pass
    return "Kho tri thức UTC"


def classify_topic(question: str) -> str:
    result = classify_intent(question)
    return intent_to_topic(result.get("intent", "khac"))


def read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temp_path.replace(path)


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def append_activity(action: str, user: str, status_text: str) -> None:
    with DATA_LOCK:
        activities = read_json(ACTIVITY_FILE, [])
        activities.append(
            {
                "id": f"act-{uuid4().hex[:10]}",
                "action": action,
                "user": user,
                "status": status_text,
                "time": format_datetime(),
                "epoch": now_epoch(),
            }
        )
        activities = activities[-200:]
        write_json(ACTIVITY_FILE, activities)


def _retrieve_internal_candidates(
    pipeline: UTCRAGPipeline,
    question: str,
    top_k: int,
) -> list[dict[str, Any]]:
    retrieved = pipeline._hybrid_retrieve(question, top_k=top_k)
    if retrieved and all(float(item.get("score", 0.0)) < 0.016 for item in retrieved):
        dense_only = pipeline.retrieve(question, top_k=top_k)
        if dense_only and not any(item.get("type") == "web" for item in dense_only):
            retrieved = dense_only

    if len(retrieved) > 5 and not any(item.get("type") == "web" for item in retrieved):
        try:
            from src.deep_reranker import get_llm_reranker

            reranker = get_llm_reranker(pipeline)
            retrieved = reranker.rerank(question, retrieved[:10], top_k=min(5, top_k))
        except Exception:
            pass
    return retrieved


def _load_student_context(question: str, current_user: dict[str, Any], enabled: bool) -> str:
    if not enabled:
        return ""
    try:
        from src.student_data import get_student_context

        return get_student_context(current_user) + "\n\n"
    except Exception:
        return ""


def resolve_chat_execution_plan(
    pipeline: UTCRAGPipeline,
    question: str,
    current_user: dict[str, Any],
    top_k: int,
) -> dict[str, Any]:
    question = question.strip()
    intent_result = classify_intent(question, current_user=current_user)
    internal_retrieved = _retrieve_internal_candidates(pipeline, question, top_k)
    internal_probe = build_retrieval_probe(internal_retrieved)
    route_decision = select_route(
        question,
        intent_result=intent_result,
        retrieval_probe=internal_probe,
        current_user=current_user,
    )

    route = route_decision["route"]
    retrieved = list(internal_retrieved)
    used_web_search = False

    if route == "direct_fallback":
        retrieved = []
    elif route == "web_first":
        web_results = pipeline.web_search(question, max_results=min(5, top_k))
        if web_results:
            retrieved = web_results
            used_web_search = True
        else:
            retrieved = list(internal_retrieved)
    else:
        if pipeline.should_use_web_search(internal_retrieved):
            web_results = pipeline.web_search(question, max_results=min(5, top_k))
            if web_results:
                retrieved = web_results
                used_web_search = True

    student_ctx = _load_student_context(
        question,
        current_user=current_user,
        enabled=route_decision["used_student_context"],
    )
    retrieval_tier = summarize_retrieval_tier(retrieved)
    if route == "web_first" and not used_web_search and internal_retrieved:
        retrieval_tier = summarize_retrieval_tier(internal_retrieved)

    return {
        "intent_result": intent_result,
        "route_decision": {
            **route_decision,
            "retrieval_tier": retrieval_tier,
            "use_web_search": used_web_search or route_decision["use_web_search"],
        },
        "internal_retrieved": internal_retrieved,
        "retrieved": retrieved,
        "student_ctx": student_ctx,
        "retrieval_probe": build_retrieval_probe(retrieved),
    }


def build_tier_hint(retrieval_tier: str) -> str:
    if retrieval_tier == "partial":
        return (
            "LƯU Ý: Ngữ cảnh cung cấp bên dưới có độ tin cậy THẤP hoặc không đầy đủ. "
            "Hãy trả lời phần có căn cứ, và nói rõ phần chưa có thông tin.\n\n"
        )
    if retrieval_tier == "web":
        return (
            "LƯU Ý: Không tìm thấy thông tin đủ tốt trong kho tri thức nội bộ UTC. "
            "Ngữ cảnh dưới đây đến từ tìm kiếm web. "
            "Hãy tổng hợp cẩn thận, ưu tiên thông tin có căn cứ rõ ràng, "
            "và nói rõ nếu nguồn web chưa đủ chắc chắn.\n\n"
        )
    return ""


def build_chat_messages(
    pipeline: UTCRAGPipeline,
    question: str,
    retrieved: list[dict[str, Any]],
    student_ctx: str = "",
    conv_history: str = "",
) -> list[dict[str, str]]:
    context = pipeline.build_context(retrieved)
    tier_hint = build_tier_hint(summarize_retrieval_tier(retrieved))
    return [
        {"role": "system", "content": pipeline.SYSTEM_PROMPT},
        {
            "role": "user",
            "content": (
                f"{conv_history}"
                f"{student_ctx}"
                f"{tier_hint}"
                f"NGỮ CẢNH THAM KHẢO:\n{context}\n\n"
                f"CÂU HỎI CỦA SINH VIÊN: {question}\n\n"
                "Hãy thực hiện toàn bộ quá trình suy nghĩ (thinking) bằng tiếng Việt và trả lời câu hỏi trên bằng tiếng Việt dựa vào ngữ cảnh được cung cấp."
            ),
        },
    ]


def build_source_items(sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items = []
    for item in sources:
        source_value = item.get("source", "")
        items.append(
            {
                "title": item.get("title", ""),
                "source": source_value,
                "type": item.get("type", ""),
                "source_name": Path(source_value).name if source_value and "://" not in source_value else source_value,
                "source_url": source_value if source_value.startswith(("http://", "https://")) else "",
                "heading": item.get("breadcrumb", item.get("heading", "")),
                "score": round(float(item.get("score", 0.0)), 4),
                "content": item.get("content", "")[:500],
            }
        )
    return items


def append_router_event(payload: dict[str, Any]) -> None:
    with DATA_LOCK:
        append_jsonl(ROUTER_EVENTS_FILE, payload)


def log_question_event(
    *,
    question: str,
    current_user: dict[str, Any],
    answer: str,
    thinking: str,
    latency_sec: float,
    topic: str,
    intent: str,
    intent_confidence: float,
    route: str,
    retrieval_tier: str,
    used_student_context: bool,
    used_web_search: bool,
    top1_score: float,
    result_count: int,
    conversation_id: str = "",
) -> dict[str, Any]:
    success = not answer.strip().startswith(FALLBACK_ANSWER_PREFIX)
    entry = {
        "id": f"q-{uuid4().hex[:10]}",
        "question": question,
        "topic": topic,
        "intent": intent,
        "intent_confidence": round(float(intent_confidence), 4),
        "route": route,
        "retrieval_tier": retrieval_tier,
        "used_student_context": used_student_context,
        "used_web_search": used_web_search,
        "top1_score": round(float(top1_score), 4),
        "result_count": result_count,
        "asker": current_user["identifier"],
        "time": format_datetime(),
        "status": "Đã trả lời" if success else "Cần kiểm tra",
        "rating": "Chưa có",
        "answer": answer,
        "thinking": thinking,
        "success": success,
        "latency_sec": latency_sec,
        "conversation_id": conversation_id,
        "epoch": now_epoch(),
    }
    router_event = {
        "timestamp": now_epoch(),
        "user_id": current_user["id"],
        "question": question,
        "intent": intent,
        "intent_confidence": round(float(intent_confidence), 4),
        "route": route,
        "retrieval_tier": retrieval_tier,
        "top1_score": round(float(top1_score), 4),
        "result_count": result_count,
        "used_student_context": used_student_context,
        "used_web_search": used_web_search,
        "answer_success": success,
        "conversation_id": conversation_id,
    }
    with DATA_LOCK:
        question_logs = read_json(QUESTIONS_FILE, [])
        question_logs.append(entry)
        question_logs = question_logs[-500:]
        write_json(QUESTIONS_FILE, question_logs)
        append_jsonl(ROUTER_EVENTS_FILE, router_event)
    append_activity("Xử lý câu hỏi", current_user["name"], entry["status"])
    return entry


def role_label(role: str) -> str:
    return "Quản trị" if role == "admin" else "Sinh viên"


def seed_users() -> list[dict[str, Any]]:
    return [
        {
            "id": "u_admin_001",
            "name": "Phạm Quốc Cường",
            "identifier": "admin@utc.edu.vn",
            "email": "admin@utc.edu.vn",
            "faculty": "Trung tâm Công nghệ thông tin",
            "role": "admin",
            "status": "Đang hoạt động",
            "created_at": "15/07/2025",
            "password_hash": hash_password("12345678"),
        },
        {
            "id": "u_student_001",
            "name": "Nguyễn Minh Anh",
            "identifier": "K66CNTT001",
            "email": "minhanh.k66@sv.utc.edu.vn",
            "faculty": "Công nghệ thông tin",
            "role": "student",
            "status": "Đang hoạt động",
            "created_at": "12/09/2025",
            "password_hash": hash_password("12345678"),
        },
    ]


def seed_news() -> list[dict[str, Any]]:
    return [
        {
            "id": "news-001",
            "title": "Thông báo kế hoạch học tập học kỳ II",
            "summary": "Sinh viên theo dõi mốc đăng ký học phần, lịch học chính thức và hướng dẫn điều chỉnh lớp học phần.",
            "date": "18/05/2026",
            "category": "Đào tạo",
            "url": "https://www.utc.edu.vn/tin-tuc",
        },
        {
            "id": "news-002",
            "title": "Ngày hội tư vấn hướng nghiệp ngành giao thông vận tải",
            "summary": "Chương trình kết nối sinh viên với doanh nghiệp, cựu sinh viên và các đơn vị tuyển dụng.",
            "date": "14/05/2026",
            "category": "Hoạt động",
            "url": "https://www.utc.edu.vn/tin-tuc",
        },
    ]


def ensure_runtime_files() -> None:
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    if not USERS_FILE.exists():
        write_json(USERS_FILE, seed_users())
    if not NEWS_FILE.exists():
        write_json(NEWS_FILE, seed_news())
    for path in (FEEDBACK_FILE, BUGS_FILE, QUESTIONS_FILE, ACTIVITY_FILE):
        if not path.exists():
            write_json(path, [])


def list_users() -> list[dict[str, Any]]:
    return read_json(USERS_FILE, seed_users())


def save_users(users: list[dict[str, Any]]) -> None:
    write_json(USERS_FILE, users)


def user_public(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": user["id"],
        "name": user["name"],
        "identifier": user["identifier"],
        "email": user["email"],
        "faculty": user.get("faculty", ""),
        "role": user["role"],
        "status": user["status"],
        "created_at": user.get("created_at", ""),
        "role_label": role_label(user["role"]),
    }


def get_pipeline(settings: Settings) -> UTCRAGPipeline:
    if not hasattr(get_pipeline, "_instance"):
        pipeline = UTCRAGPipeline(settings=settings)
        pipeline.init_vector_db()
        setattr(get_pipeline, "_instance", pipeline)
    return getattr(get_pipeline, "_instance")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(AUTH_SCHEME),
) -> dict[str, Any]:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Chưa đăng nhập.")

    token = credentials.credentials
    with DATA_LOCK:
        session_data = SESSIONS.get(token)
        if session_data is None or session_data.expires_at < now_epoch():
            SESSIONS.pop(token, None)
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Phiên đăng nhập đã hết hạn.")

    users = list_users()
    user = next((item for item in users if item["id"] == session_data.user_id), None)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tài khoản không tồn tại.")
    return user


def require_admin(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền truy cập.")
    return current_user


app = FastAPI(title="UTC Assistant API", version="1.0.0")
settings = load_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=(
        r"https?://("
        r"localhost|127\.0\.0\.1|"
        r"192\.168\.\d{1,3}\.\d{1,3}|"
        r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
        r"172\.(1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3}"
        r")(:\d+)?"
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.middleware("http")
async def cors_on_error(request, call_next):
    """Dam bao CORS headers co tren ca error responses."""
    from fastapi.responses import Response
    try:
        response = await call_next(request)
    except Exception:
        response = Response(
            content='{"detail":"Internal Server Error"}',
            status_code=500,
            media_type="application/json",
        )
    response.headers["Access-Control-Allow-Origin"] = request.headers.get("origin", "*")
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


@app.on_event("startup")
def on_startup() -> None:
    ensure_runtime_files()
    from src.database import init_db
    init_db()


@app.get("/api/health")
def api_health() -> dict[str, Any]:
    return {
        "status": "ok",
        "service": "utc-assistant-api",
        "time": format_datetime(),
    }


@app.post("/api/auth/register")
def api_register(payload: RegisterRequest) -> dict[str, Any]:
    ensure_runtime_files()
    with DATA_LOCK:
        users = list_users()
        identifier = payload.identifier.strip()
        email = payload.email.strip().lower()
        if any(user["identifier"].lower() == identifier.lower() for user in users):
            raise HTTPException(status_code=400, detail="Mã định danh đã tồn tại.")
        if any(user["email"].lower() == email for user in users):
            raise HTTPException(status_code=400, detail="Email đã được sử dụng.")

        user = {
            "id": f"u_{uuid4().hex[:10]}",
            "name": payload.full_name.strip(),
            "identifier": identifier,
            "email": email,
            "faculty": "Chưa cập nhật",
            "role": payload.role,
            "status": "Đang hoạt động",
            "created_at": format_datetime(),
            "password_hash": hash_password(payload.password),
        }
        users.append(user)
        save_users(users)

    append_activity("Đăng ký tài khoản", user["name"], "Đã tạo")
    return {"message": "Đăng ký thành công.", "user": user_public(user)}


@app.post("/api/auth/login")
def api_login(payload: LoginRequest) -> dict[str, Any]:
    ensure_runtime_files()
    if not login_limiter.check("login"):
        raise HTTPException(status_code=429, detail="Quá nhiều yêu cầu. Vui lòng thử lại sau.")
    identifier = payload.identifier.strip().lower()
    users = list_users()
    user = next(
        (
            item
            for item in users
            if item["identifier"].lower() == identifier or item["email"].lower() == identifier
        ),
        None,
    )
    if user is None or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Thông tin đăng nhập không hợp lệ.")
    if user.get("status") == "Tạm khóa":
        raise HTTPException(status_code=403, detail="Tài khoản đang bị tạm khóa.")

    token = uuid4().hex
    with DATA_LOCK:
        SESSIONS[token] = SessionData(user_id=user["id"], expires_at=now_epoch() + SESSION_TTL_SECONDS)

    append_activity("Đăng nhập", user["name"], "Thành công")
    return {"token": token, "user": user_public(user)}


@app.get("/api/auth/me")
def api_me(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    return {"user": user_public(current_user)}


@app.post("/api/auth/logout")
def api_logout(credentials: HTTPAuthorizationCredentials | None = Depends(AUTH_SCHEME)) -> dict[str, str]:
    if credentials is not None:
        with DATA_LOCK:
            SESSIONS.pop(credentials.credentials, None)
    return {"message": "Đã đăng xuất."}


@app.post("/api/auth/forgot-password")
def api_forgot_password(payload: ForgotPasswordRequest) -> dict[str, str]:
    users = list_users()
    email = payload.email.strip().lower()
    user = next((item for item in users if item["email"].lower() == email), None)
    if user is not None:
        append_activity("Yêu cầu quên mật khẩu", user["name"], "Đã tiếp nhận")
    return {"message": "Nếu email tồn tại, hệ thống sẽ gửi hướng dẫn đặt lại mật khẩu."}


@app.post("/api/auth/change-password")
def api_change_password(
    payload: ChangePasswordRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, str]:
    if not verify_password(payload.current_password, current_user.get("password_hash", "")):
        raise HTTPException(status_code=400, detail="Mật khẩu hiện tại không đúng.")
    if payload.current_password == payload.new_password:
        raise HTTPException(status_code=400, detail="Mật khẩu mới phải khác mật khẩu hiện tại.")

    with DATA_LOCK:
        users = list_users()
        for user in users:
            if user["id"] == current_user["id"]:
                user["password_hash"] = hash_password(payload.new_password)
                break
        save_users(users)
    append_activity("Đổi mật khẩu", current_user["name"], "Thành công")
    return {"message": "Đổi mật khẩu thành công."}


@app.get("/api/news")
def api_news() -> dict[str, Any]:
    ensure_runtime_files()
    return {"items": read_json(NEWS_FILE, seed_news())}


@app.get("/api/documents")
def api_documents(
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    current_user: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    records = list_documents(settings.raw_dir)
    items = []
    for record in records:
        extension = Path(record.filename).suffix.lower().replace(".", "").upper() or "TXT"
        items.append(
            {
                "id": record.filename,
                "name": record.title,
                "type": extension,
                "source": parse_source_from_text(record.path),
                "status": "Đã sẵn sàng" if record.char_count >= 50 else "Lỗi xử lý",
                "updated_at": record.modified_at,
                "owner": "Hệ thống",
                "filename": record.filename,
                "char_count": record.char_count,
                "chunk_count": record.chunk_count,
            }
        )
    return paginate(items, page, page_size)


@app.post("/api/documents/import")
def api_documents_import(
    payload: DocumentImportRequest,
    current_user: dict[str, Any] = Depends(require_admin),
) -> dict[str, str]:
    output = save_imported_text(
        raw_dir=settings.raw_dir,
        title=payload.title.strip(),
        body=payload.content.strip(),
        source_name=payload.source.strip(),
    )
    append_activity("Import tài liệu", current_user["name"], output.name)
    return {"message": "Import tài liệu thành công.", "filename": output.name}


@app.get("/api/users")
def api_users(
    q: str = "",
    role: str = "all",
    status_filter: str = "all",
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    current_user: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    del current_user
    users = [user_public(user) for user in list_users()]
    if role != "all":
        users = [user for user in users if user["role"] == role]
    if status_filter != "all":
        users = [user for user in users if user["status"] == status_filter]
    query = q.strip().lower()
    if query:
        users = [
            user
            for user in users
            if query in user["name"].lower()
            or query in user["identifier"].lower()
            or query in user["email"].lower()
        ]
    return paginate(users, page, page_size)


@app.post("/api/users/{user_id}/toggle-lock")
def api_users_toggle_lock(
    user_id: str,
    current_user: dict[str, Any] = Depends(require_admin),
) -> dict[str, str]:
    with DATA_LOCK:
        users = list_users()
        user = next((item for item in users if item["id"] == user_id), None)
        if user is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng.")
        user["status"] = "Tạm khóa" if user["status"] == "Đang hoạt động" else "Đang hoạt động"
        save_users(users)
    append_activity("Đổi trạng thái tài khoản", current_user["name"], user["status"])
    return {"message": "Đã cập nhật trạng thái tài khoản.", "status": user["status"]}


@app.post("/api/users/{user_id}/reset-password")
def api_users_reset_password(
    user_id: str,
    current_user: dict[str, Any] = Depends(require_admin),
) -> dict[str, str]:
    with DATA_LOCK:
        users = list_users()
        user = next((item for item in users if item["id"] == user_id), None)
        if user is None:
            raise HTTPException(status_code=404, detail="Không tìm thấy người dùng.")
        user["password_hash"] = hash_password("12345678")
        save_users(users)
    append_activity("Đặt lại mật khẩu", current_user["name"], user["name"])
    return {"message": "Đặt lại mật khẩu thành công. Mật khẩu mặc định: 12345678"}


@app.post("/api/chat")
def api_chat(
    payload: ChatRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    ensure_runtime_files()
    if not chat_limiter.check(current_user["id"]):
        raise HTTPException(status_code=429, detail="Quá nhiều câu hỏi. Vui lòng chờ một lát.")
    question = payload.question.strip()
    started_at = now_epoch()
    pipeline = get_pipeline(settings)
    execution = resolve_chat_execution_plan(
        pipeline,
        question=question,
        current_user=current_user,
        top_k=payload.top_k,
    )
    route = execution["route_decision"]["route"]
    sources = execution["retrieved"]
    if route == "direct_fallback" or not sources:
        thinking = ""
        answer = pipeline.FALLBACK_ANSWER
    else:
        llm = pipeline.load_llm()
        messages = build_chat_messages(
            pipeline,
            question=question,
            retrieved=sources,
            student_ctx=execution["student_ctx"],
        )
        response = llm.session.post(
            f"{llm.base_url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {llm.api_key}"},
            json={
                "model": llm.model,
                "messages": llm._prepare_messages(messages),
                "temperature": 0.2,
                "max_tokens": settings.llm_max_tokens,
            },
            timeout=llm.timeout,
        )
        response.raise_for_status()
        thinking, answer = llm.extract_answer_with_thinking(response.json())
    latency_sec = round(now_epoch() - started_at, 2)
    source_items = build_source_items(sources)

    topic = intent_to_topic(execution["intent_result"]["intent"])
    log_question_event(
        question=question,
        current_user=current_user,
        answer=answer,
        thinking=thinking,
        latency_sec=latency_sec,
        topic=topic,
        intent=execution["intent_result"]["intent"],
        intent_confidence=execution["intent_result"]["confidence"],
        route=execution["route_decision"]["route"],
        retrieval_tier=execution["route_decision"]["retrieval_tier"],
        used_student_context=execution["route_decision"]["used_student_context"],
        used_web_search=execution["route_decision"]["use_web_search"],
        top1_score=execution["retrieval_probe"]["top1_score"],
        result_count=execution["retrieval_probe"]["result_count"],
    )

    return {
        "thinking": thinking,
        "answer": answer,
        "sources": source_items,
        "topic": topic,
        "latency_sec": latency_sec,
        "intent": execution["intent_result"]["intent"],
        "intent_confidence": execution["intent_result"]["confidence"],
        "route": execution["route_decision"]["route"],
        "retrieval_tier": execution["route_decision"]["retrieval_tier"],
    }


@app.get("/api/questions")
def api_questions(
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    current_user: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    del current_user
    items = read_json(QUESTIONS_FILE, [])
    items.sort(key=lambda item: float(item.get("epoch", 0.0)), reverse=True)
    return paginate(items, page, page_size)


@app.post("/api/feedback")
def api_feedback(
    payload: FeedbackRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, str]:
    feedback_item = {
        "id": f"fb-{uuid4().hex[:10]}",
        "topic": payload.subject.strip(),
        "student": current_user["identifier"],
        "satisfaction": payload.satisfaction.strip(),
        "content": payload.content.strip(),
        "email": payload.email.strip(),
        "status": "Chờ phản hồi",
        "time": format_datetime(),
        "epoch": now_epoch(),
    }
    with DATA_LOCK:
        items = read_json(FEEDBACK_FILE, [])
        items.append(feedback_item)
        items = items[-500:]
        write_json(FEEDBACK_FILE, items)
    append_activity("Gửi feedback", current_user["name"], feedback_item["status"])
    return {"message": "Đã tiếp nhận feedback.", "id": feedback_item["id"]}


@app.get("/api/feedback")
def api_feedback_list(
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    current_user: dict[str, Any] = Depends(require_admin),
) -> dict[str, Any]:
    del current_user
    items = read_json(FEEDBACK_FILE, [])
    items.sort(key=lambda item: float(item.get("epoch", 0.0)), reverse=True)
    return paginate(items, page, page_size)


@app.post("/api/bugs")
def api_bugs(
    payload: BugRequest,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, str]:
    bug = {
        "id": f"bug-{uuid4().hex[:10]}",
        "title": payload.description.strip().splitlines()[0][:140],
        "type": payload.bug_type.strip(),
        "severity": payload.severity.strip(),
        "description": payload.description.strip(),
        "status": "Đã tiếp nhận",
        "assignee": "Chưa phân công",
        "reporter": current_user["identifier"],
        "time": format_datetime(),
        "epoch": now_epoch(),
        "screenshot_note": payload.screenshot_note.strip(),
    }
    with DATA_LOCK:
        items = read_json(BUGS_FILE, [])
        items.append(bug)
        items = items[-500:]
        write_json(BUGS_FILE, items)
    append_activity("Gửi báo cáo lỗi", current_user["name"], bug["status"])
    return {"message": "Đã tiếp nhận báo cáo lỗi.", "id": bug["id"]}


@app.get("/api/bugs")
def api_bug_list(
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    items = read_json(BUGS_FILE, [])
    if current_user["role"] != "admin":
        items = [item for item in items if item.get("reporter") == current_user["identifier"]]
    items.sort(key=lambda item: float(item.get("epoch", 0.0)), reverse=True)
    return paginate(items, page, page_size)


@app.get("/api/dashboard")
def api_dashboard(current_user: dict[str, Any] = Depends(require_admin)) -> dict[str, Any]:
    del current_user
    users = list_users()
    documents = list_documents(settings.raw_dir)
    feedback_items = read_json(FEEDBACK_FILE, [])
    bugs = read_json(BUGS_FILE, [])
    questions = read_json(QUESTIONS_FILE, [])
    activities = read_json(ACTIVITY_FILE, [])

    total_questions = len(questions)
    success_count = sum(1 for item in questions if item.get("success"))
    success_rate = round((success_count / total_questions) * 100, 1) if total_questions else 0.0
    avg_latency = (
        round(sum(float(item.get("latency_sec", 0.0)) for item in questions) / total_questions, 2)
        if total_questions
        else 0.0
    )

    today = time.localtime()
    access_by_day = []
    for offset in range(6, -1, -1):
        day_epoch = time.mktime(
            (
                today.tm_year,
                today.tm_mon,
                today.tm_mday - offset,
                0,
                0,
                0,
                0,
                0,
                -1,
            )
        )
        key = today_key(day_epoch)
        count = sum(1 for item in questions if today_key(float(item.get("epoch", 0.0))) == key)
        access_by_day.append(
            {
                "day": time.strftime("%a", time.localtime(day_epoch)).replace("Mon", "T2").replace("Tue", "T3").replace("Wed", "T4").replace("Thu", "T5").replace("Fri", "T6").replace("Sat", "T7").replace("Sun", "CN"),
                "value": count,
            }
        )

    topic_counter: dict[str, int] = {}
    for item in questions:
        topic = str(item.get("topic", "Khác"))
        topic_counter[topic] = topic_counter.get(topic, 0) + 1
    total_topic = sum(topic_counter.values()) or 1
    topic_percent = [
        {"label": topic, "value": round(count * 100 / total_topic)}
        for topic, count in sorted(topic_counter.items(), key=lambda row: row[1], reverse=True)
    ][:5]
    if not topic_percent:
        topic_percent = [{"label": "Khác", "value": 0}]

    kpis = [
        {"label": "Tổng lượt truy cập", "value": str(len(activities) + total_questions), "delta": f"+{min(total_questions, 99)}"},
        {"label": "Số lượng câu hỏi", "value": str(total_questions), "delta": f"+{total_questions}"},
        {
            "label": "Người dùng đang hoạt động",
            "value": str(sum(1 for user in users if user.get("status") == "Đang hoạt động")),
            "delta": f"+{sum(1 for user in users if user.get('role') == 'student')}",
        },
        {"label": "Tài liệu đã xử lý", "value": str(len(documents)), "delta": f"+{len(documents)}"},
        {"label": "Feedback mới", "value": str(len(feedback_items)), "delta": f"+{len(feedback_items)}"},
        {
            "label": "Báo cáo lỗi chờ xử lý",
            "value": str(sum(1 for bug in bugs if bug.get("status") != "Đã hoàn tất")),
            "delta": f"-{sum(1 for bug in bugs if bug.get('status') == 'Đã hoàn tất')}",
        },
    ]

    activities.sort(key=lambda item: float(item.get("epoch", 0.0)), reverse=True)
    recent_activities = activities[:10]

    return {
        "kpis": kpis,
        "access_by_day": access_by_day,
        "question_topics": topic_percent,
        "success_rate": success_rate,
        "avg_latency_sec": avg_latency,
        "recent_activities": recent_activities,
    }


_SUGGESTIONS_CACHE: list[str] = []


def _load_suggestions() -> list[str]:
    """Trích xuất chủ đề từ mục lục tài liệu đã index."""
    global _SUGGESTIONS_CACHE
    if _SUGGESTIONS_CACHE:
        return _SUGGESTIONS_CACHE

    suggestions = []
    raw_dir = settings.raw_dir
    records = list_documents(raw_dir)
    for record in records:
        if record.is_generated:
            continue
        try:
            content = record.path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        # Tìm phần mục lục và trích xuất tiêu đề
        in_toc = False
        for line in content.split("\n")[:250]:
            stripped = line.strip()
            if not stripped:
                continue
            if "MỤC LỤC" in stripped.upper():
                in_toc = True
                continue
            if in_toc:
                # Dừng khi hết mục lục
                if stripped.startswith("STSV") or stripped.startswith("Ghi chép"):
                    break
                # Lọc các dòng có dấu chấm (dòng mục lục)
                if "......." in stripped or "……" in stripped:
                    # Tách tiêu đề khỏi số trang
                    title = stripped.split(".......")[0].split("……")[0].strip()
                    # Bỏ số/chữ số La Mã ở đầu dòng (vd: "1. ", "IV. ", "XII. ")
                    import re
                    title = re.sub(r'^[IVXLCDMivxlcdm]+\.\s*', '', title)
                    title = re.sub(r'^\d+\.?\s*', '', title)
                    title = title.strip()
                    if title and len(title) > 5 and not title.startswith("Phần"):
                        suggestions.append(title)
                elif stripped.startswith("Phần") and "......." in stripped:
                    title = stripped.split(".......")[0].strip()
                    if title:
                        suggestions.append(title)

    # Chuẩn hóa: loại bỏ trùng lặp gần đúng, giới hạn 10 mục
    seen: set[str] = set()
    unique: list[str] = []
    for s in suggestions:
        # Bỏ các mục không mong muốn
        skip_keywords = ["lời nói đầu", "mục lục"]
        if any(kw in s.lower() for kw in skip_keywords):
            continue
        key = s.lower()[:30]
        if key not in seen:
            seen.add(key)
            unique.append(s)
        if len(unique) >= 10:
            break

    _SUGGESTIONS_CACHE = unique
    return unique


@app.get("/api/suggestions")
def api_suggestions() -> dict[str, Any]:
    return {"items": _load_suggestions()}

# Import stream endpoint
import src.chat_stream  # noqa: F401 - registers /api/chat/stream

# v2 modules
import src.conversations  # noqa: F401
import src.feedback  # noqa: F401
import src.faq  # noqa: F401
import src.student_data  # noqa: F401

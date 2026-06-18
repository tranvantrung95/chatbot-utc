"""Student personal data: grades, progress, recommendations (mock)."""
from fastapi import Depends

from src.api_server import app, get_current_user


# ── Mock course catalog ──────────────────────────
CNTT_COURSES = [
    {"code": "MAT201", "name": "Toán giải tích 2", "credits": 3, "semester": 1, "prereq": []},
    {"code": "MAT202", "name": "Đại số tuyến tính", "credits": 3, "semester": 1, "prereq": []},
    {"code": "PHY101", "name": "Vật lý đại cương", "credits": 3, "semester": 1, "prereq": []},
    {"code": "IT101", "name": "Nhập môn CNTT", "credits": 3, "semester": 1, "prereq": []},
    {"code": "IT102", "name": "Lập trình cơ bản (C)", "credits": 3, "semester": 1, "prereq": []},
    {"code": "IT201", "name": "Cấu trúc dữ liệu & GT", "credits": 4, "semester": 2, "prereq": ["IT102"]},
    {"code": "IT202", "name": "Lập trình hướng đối tượng", "credits": 3, "semester": 2, "prereq": ["IT102"]},
    {"code": "IT203", "name": "Kiến trúc máy tính", "credits": 3, "semester": 2, "prereq": ["IT101"]},
    {"code": "MAT301", "name": "Xác suất thống kê", "credits": 3, "semester": 3, "prereq": ["MAT201"]},
    {"code": "IT301", "name": "Cơ sở dữ liệu", "credits": 4, "semester": 3, "prereq": ["IT201"]},
    {"code": "IT302", "name": "Mạng máy tính", "credits": 3, "semester": 3, "prereq": ["IT101"]},
    {"code": "IT303", "name": "Hệ điều hành", "credits": 3, "semester": 3, "prereq": ["IT203"]},
    {"code": "IT401", "name": "Công nghệ phần mềm", "credits": 3, "semester": 4, "prereq": ["IT201", "IT202"]},
    {"code": "IT402", "name": "Phát triển ứng dụng Web", "credits": 3, "semester": 4, "prereq": ["IT301"]},
    {"code": "IT403", "name": "Trí tuệ nhân tạo", "credits": 3, "semester": 4, "prereq": ["IT201", "MAT301"]},
    {"code": "IT501", "name": "An toàn thông tin", "credits": 3, "semester": 5, "prereq": ["IT302", "IT303"]},
    {"code": "IT502", "name": "Điện toán đám mây", "credits": 3, "semester": 5, "prereq": ["IT302"]},
    {"code": "IT601", "name": "Đồ án tốt nghiệp", "credits": 10, "semester": 8, "prereq": ["IT401", "IT501"]},
]


def _mock_grades(user: dict) -> dict:
    """Generate consistent mock grades based on user ID hash."""
    import hashlib
    # Generate a deterministic hash integer from user's ID
    user_id = user.get("id", "default_id")
    h = int(hashlib.md5(user_id.encode()).hexdigest()[:8], 16)

    completed_courses = []
    total_earned = 0
    total_points = 0.0
    completed_codes = set()

    for c in CNTT_COURSES:
        if c["semester"] > 5:  # Only completed up to semester 5
            continue
        # Deterministic grade based on hash + course code
        seed = (h + hash(c["code"])) % 100
        if seed < 60:
            qt = round(7.0 + (seed % 30) / 10, 1)
            thi = round(max(4.0, qt - 1.5 + (seed % 10) / 10), 1)
            grade_letter = "A" if qt + thi > 16 else "B" if qt + thi > 13 else "C" if qt + thi > 9 else "D"
        elif seed < 85:
            qt = round(5.0 + (seed % 30) / 10, 1)
            thi = round(max(3.0, qt - 1.0 + (seed % 10) / 10), 1)
            grade_letter = "C" if qt + thi > 9 else "D"
        else:
            qt = round(3.0 + (seed % 30) / 10, 1)
            thi = round(max(1.0, qt - 1.0 + (seed % 10) / 10), 1)
            grade_letter = "F" if qt + thi < 4 else "D"

        total = round(qt * 0.3 + thi * 0.7, 1) if c["code"] != "IT601" else 0
        grade_4 = {"A": 4.0, "B": 3.0, "C": 2.0, "D": 1.0, "F": 0.0}.get(grade_letter[0], 0.0)

        completed_courses.append({
            **c,
            "qt": qt, "thi": thi, "total": total,
            "grade": grade_letter, "grade_4": grade_4,
            "passed": grade_letter != "F",
        })
        completed_codes.add(c["code"])
        if grade_letter != "F":
            total_earned += c["credits"]
            total_points += grade_4 * c["credits"]

    gpa = round(total_points / max(1, total_earned), 2) if total_earned > 0 else 0.0

    # Recommendations: courses not yet taken, prereqs met
    recommendations = []
    for c in CNTT_COURSES:
        if c["code"] in completed_codes:
            continue
        
        # Check prerequisites
        available = True
        for req in c.get("prereq", []):
            # Check if prerequisite was passed
            req_passed = False
            for comp in completed_courses:
                if comp["code"] == req and comp["passed"]:
                    req_passed = True
                    break
            if not req_passed:
                available = False
                break
                
        recommendations.append({
            **c,
            "available": available
        })

    # Warnings: GPA warning, failed courses, low credits
    warnings = []
    if gpa < 2.0:
        warnings.append("Cảnh báo học vụ: GPA dưới 2.0")
    
    failed_courses = [c["name"] for c in completed_courses if not c["passed"]]
    if failed_courses:
        warnings.append(f"Cảnh báo nợ môn: {', '.join(failed_courses)}")

    return {
        "completed_courses": completed_courses,
        "gpa": gpa,
        "total_credits_earned": total_earned,
        "total_credits_required": 150,
        "recommendations": recommendations,
        "warnings": warnings
    }


@app.get("/api/student/progress")
def get_progress(current_user=Depends(get_current_user)):
    data = _mock_grades(current_user)
    return {
        "gpa": data["gpa"],
        "earned": data["total_credits_earned"],
        "required": data["total_credits_required"],
        "percent": round(data["total_credits_earned"] / data["total_credits_required"] * 100, 1),
        "warnings": data["warnings"],
    }


@app.get("/api/student/recommendations")
def get_recommendations(current_user=Depends(get_current_user)):
    data = _mock_grades(current_user)
    return {
        "available": [
            {"code": r["code"], "name": r["name"], "credits": r["credits"], "semester": r["semester"]}
            for r in data["recommendations"] if r["available"]
        ],
        "locked": [
            {"code": r["code"], "name": r["name"], "credits": r["credits"], "semester": r["semester"]}
            for r in data["recommendations"] if not r["available"]
        ],
    }


@app.get("/api/student/grades")
def get_grades(current_user=Depends(get_current_user)):
    data = _mock_grades(current_user)
    return {
        "courses": data["completed_courses"],
        "gpa": data["gpa"],
        "earned": data["total_credits_earned"],
        "required": data["total_credits_required"],
    }


def get_student_context(user: dict) -> str:
    """Generates a dynamic system context string containing the student's progress and grades."""
    data = _mock_grades(user)
    courses_str = ", ".join(f"{c['name']} ({c['code']}): {c['grade']}" for c in data['completed_courses'])
    return (
        "DƯ LIỆU HỌC TẬP THỰC TẾ CỦA SINH VIÊN:\n"
        f"- Họ tên: {user.get('name', 'Sinh viên')}\n"
        f"- Mã sinh viên: {user.get('identifier', 'Chưa có')}\n"
        f"- Email: {user.get('email', 'Chưa có')}\n"
        f"- Khoa: {user.get('faculty', 'Chưa cập nhật')}\n"
        f"- GPA: {data['gpa']}/4.0\n"
        f"- Tín chỉ đã tích lũy: {data['total_credits_earned']}/{data['total_credits_required']}\n"
        f"- Các môn gần đây: {courses_str}\n"
        + ("\n".join(f"- {w}" for w in data['warnings']) if data['warnings'] else "")
    )

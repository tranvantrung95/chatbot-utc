---
name: run-backend-tests
description: Run the pytest suite for the backend application.
---

# run-backend-tests

## Mục đích
Chạy các bài kiểm tra tự động (unit tests, integration tests) cho hệ thống Backend FastAPI và RAG.

## Khi nào nên dùng
Dùng khi bạn vừa sửa code backend, thêm tính năng mới, hoặc trước khi commit code để đảm bảo không làm vỡ các tính năng cũ. Người dùng có thể gọi bằng lệnh "chạy test", "kiểm tra lỗi code".

## Các bước thực hiện (Dành cho AI)
1. Di chuyển vào thư mục `utc-assistant/`.
2. Chạy thư viện pytest qua môi trường ảo:
   ```bash
   if [ -f "venv/bin/python" ]; then
       venv/bin/python -m pytest tests/ -v
   else
       python -m pytest tests/ -v
   fi
   ```
3. Đọc log kết quả. Nếu có lỗi (FAILED), tự động đề xuất nguyên nhân và hỏi người dùng có muốn sửa lỗi đó không. Nếu PASS 100%, chúc mừng người dùng.

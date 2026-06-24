---
name: run-teacher-eval
description: Run the RAG teacher evaluation script to benchmark the LLM's accuracy.
---

# run-teacher-eval

## Mục đích
Chạy tập test tự động để LLM Giám khảo (Teacher) đánh giá độ chính xác, tính đầy đủ, và thời gian phản hồi của hệ thống RAG hiện tại.

## Khi nào nên dùng
Dùng khi người dùng yêu cầu đánh giá RAG, "chấm điểm RAG", hoặc muốn kiểm tra sau khi cập nhật hệ thống/dữ liệu.

## Các bước thực hiện (Dành cho AI)
1. Di chuyển (thông qua cwd) vào thư mục `utc-assistant/`.
2. Kiểm tra xem file `data/autotest/questions.json` có tồn tại không.
3. Chạy lệnh bash sau:
   ```bash
   if [ -f "venv/bin/python" ]; then
       venv/bin/python -m src.eval_runner --questions data/autotest/questions.json --output data/runtime/teacher_eval_report.json
   else
       python -m src.eval_runner --questions data/autotest/questions.json --output data/runtime/teacher_eval_report.json
   fi
   ```
4. Đợi tiến trình kết thúc. Đọc file `data/runtime/teacher_eval_report.json` và in ra cho người dùng một bảng báo cáo Markdown tóm tắt, bao gồm:
   - Tổng quan (số lượng test, điểm trung bình, thời gian phản hồi).
   - Danh sách lỗi (nếu có).
   - Tóm tắt một số câu hỏi tiêu biểu.

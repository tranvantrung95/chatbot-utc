---
name: generate-utc-report
description: Generate analytical or progress reports using gen_report.py
---

# generate-utc-report

## Mục đích
Tạo báo cáo tự động từ mã nguồn hoặc dữ liệu để thống kê tiến độ, lỗi, hoặc phân tích ứng dụng.

## Khi nào nên dùng
Dùng khi người dùng yêu cầu xuất báo cáo, "tạo report", hoặc muốn xem file phân tích tổng quan từ `gen_report.py`.

## Các bước thực hiện (Dành cho AI)
1. Di chuyển vào thư mục `utc-assistant/`.
2. Kiểm tra xem file script sinh báo cáo (`gen_report.py`) thực sự nằm ở đâu (thường ở thư mục gốc hoặc `scripts/`).
3. Chạy lệnh:
   ```bash
   if [ -f "venv/bin/python" ]; then
       venv/bin/python gen_report.py
   else
       python gen_report.py
   fi
   ```
4. Tìm và đọc file báo cáo vừa được tạo (thường là PDF hoặc Markdown), sau đó tóm tắt các điểm chính cho người dùng.

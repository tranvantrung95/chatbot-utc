---
name: rag-index-refresh
description: Rebuild the RAG vector database (ChromaDB) from documents.
---

# rag-index-refresh

## Mục đích
Đọc lại các tài liệu từ thư mục `data/` và tái cấu trúc (vectorize) lại ChromaDB.

## Khi nào nên dùng
Dùng khi người dùng nói vừa cập nhật/thêm file tài liệu mới vào `data/`, hoặc yêu cầu "build lại data", "làm mới index".

## Các bước thực hiện (Dành cho AI)
1. Di chuyển vào thư mục `utc-assistant/`.
2. Chạy lệnh:
   ```bash
   if [ -f "venv/bin/python" ]; then
       venv/bin/python -m src.build_full
   else
       python -m src.build_full
   fi
   ```
   *(Lưu ý: Thay thế `src.build_full` bằng script ingest thực tế nếu cần).*
3. Báo cáo lại cho người dùng số lượng chunks/tài liệu đã được index thành công (dựa vào log trả về).

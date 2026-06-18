# Source: Luồng xử lý dữ liệu
**Figure:** Hình 4.6
**Type:** process
**Description:** PDF Sổ tay SV (92 trang) → Marker-PDF OCR → Trích xuất Mục lục TOC JSON → Structured Chunking (Phần→Chương→Mục) → Gán metadata (phan_so, title, page) → Embedding bge-m3 (1024d) → ChromaDB collection 'utc_knowledge' → Sẵn sàng truy vấn.

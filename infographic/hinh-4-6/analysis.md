---
title: "Luồng xử lý dữ liệu"
topic: technical
data_type: process
complexity: moderate
source_language: vi
user_language: vi
---

## Main Topic
PDF Sổ tay SV (92 trang) → Marker-PDF OCR → Trích xuất Mục lục TOC JSON → Structured Chunking (Phần→Chương→Mục) → Gán metadata (phan_so, title, page) → Embedding bge-m3 (1024d) → ChromaDB collection 'utc_knowledge' → Sẵn sàng truy vấn.

## Learning Objectives
1. Understand the structure and components of luồng xử lý dữ liệu
2. Identify key relationships between components
3. Apply this knowledge to the UTC Assistant system context

## Target Audience
- Knowledge Level: Intermediate (sinh viên, giảng viên CNTT)
- Context: Báo cáo môn học Mô hình Ngôn ngữ Lớn
- Expectations: Hiểu rõ kiến trúc và luồng hoạt động

## Content Type Analysis
- Data Structure: process
- Layout Recommendation: linear-progression
- Style Recommendation: ikea-manual
- Aspect: landscape

## Layout × Style Signals
- Content type: process → suggests linear-progression
- Tone: technical/academic → suggests ikea-manual
- Audience: academic → professional
- Complexity: moderate → balanced density

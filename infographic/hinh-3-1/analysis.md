---
title: "Kiến trúc tổng quan RAG"
topic: technical
data_type: system-structure
complexity: moderate
source_language: vi
user_language: vi
---

## Main Topic
RAG pipeline: Offline (PDF→OCR→Chunking→Embedding→ChromaDB) + Online (Câu hỏi→Query Embedding→Retrieval→LLM Reranker→Generation→Trả lời). Kỹ thuật Lewis et al. (2020).

## Learning Objectives
1. Understand the structure and components of kiến trúc tổng quan rag
2. Identify key relationships between components
3. Apply this knowledge to the UTC Assistant system context

## Target Audience
- Knowledge Level: Intermediate (sinh viên, giảng viên CNTT)
- Context: Báo cáo môn học Mô hình Ngôn ngữ Lớn
- Expectations: Hiểu rõ kiến trúc và luồng hoạt động

## Content Type Analysis
- Data Structure: system-structure
- Layout Recommendation: structural-breakdown
- Style Recommendation: technical-schematic
- Aspect: landscape

## Layout × Style Signals
- Content type: system-structure → suggests structural-breakdown
- Tone: technical/academic → suggests technical-schematic
- Audience: academic → professional
- Complexity: moderate → balanced density

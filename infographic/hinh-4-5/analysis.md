---
title: "Pipeline RAG 3 tầng"
topic: technical
data_type: process
complexity: moderate
source_language: vi
user_language: vi
---

## Main Topic
Câu hỏi → Query Expansion (từ đồng nghĩa VN) → Topic Filter (metadata) → Tầng 1: Bi-encoder Dense (bge-m3) + Tầng 2: BM25 Sparse → RRF Fusion → Tầng 3: LLM Reranker → MMR → Context → LLM Generation → Trả lời + trích dẫn.

## Learning Objectives
1. Understand the structure and components of pipeline rag 3 tầng
2. Identify key relationships between components
3. Apply this knowledge to the UTC Assistant system context

## Target Audience
- Knowledge Level: Intermediate (sinh viên, giảng viên CNTT)
- Context: Báo cáo môn học Mô hình Ngôn ngữ Lớn
- Expectations: Hiểu rõ kiến trúc và luồng hoạt động

## Content Type Analysis
- Data Structure: process
- Layout Recommendation: linear-progression
- Style Recommendation: pop-laboratory
- Aspect: landscape

## Layout × Style Signals
- Content type: process → suggests linear-progression
- Tone: technical/academic → suggests pop-laboratory
- Audience: academic → professional
- Complexity: moderate → balanced density

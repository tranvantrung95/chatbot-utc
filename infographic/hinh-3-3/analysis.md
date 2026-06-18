---
title: "Quy trình Naive RAG"
topic: technical
data_type: process
complexity: moderate
source_language: vi
user_language: vi
---

## Main Topic
4 bước Naive RAG: 1.Indexing (PDF→Chunks→DB), 2.Embedding (Text→Vector 1024d), 3.Retrieving (Query→Top-K chunks), 4.Generating (Context+LLM→Answer). Có feedback loop từ Generating về Retrieving.

## Learning Objectives
1. Understand the structure and components of quy trình naive rag
2. Identify key relationships between components
3. Apply this knowledge to the UTC Assistant system context

## Target Audience
- Knowledge Level: Intermediate (sinh viên, giảng viên CNTT)
- Context: Báo cáo môn học Mô hình Ngôn ngữ Lớn
- Expectations: Hiểu rõ kiến trúc và luồng hoạt động

## Content Type Analysis
- Data Structure: process
- Layout Recommendation: circular-flow
- Style Recommendation: ikea-manual
- Aspect: landscape

## Layout × Style Signals
- Content type: process → suggests circular-flow
- Tone: technical/academic → suggests ikea-manual
- Audience: academic → professional
- Complexity: moderate → balanced density

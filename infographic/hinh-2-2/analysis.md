---
title: "Cơ chế Scaled Dot-Product Attention"
topic: technical
data_type: process
complexity: moderate
source_language: vi
user_language: vi
---

## Main Topic
Công thức Attention(Q,K,V) = softmax(QK^T/√d_k) × V. Các bước: Query và Key → MatMul → Scale (÷√d_k) → Mask → Softmax → MatMul với Value → Output.

## Learning Objectives
1. Understand the structure and components of cơ chế scaled dot-product attention
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

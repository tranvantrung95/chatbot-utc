---
title: "Kiến trúc Transformer"
topic: technical
data_type: system-structure
complexity: moderate
source_language: vi
user_language: vi
---

## Main Topic
Kiến trúc Transformer gồm Encoder (N=6 tầng: Self-Attention + Feed-Forward + Add&Norm) và Decoder (N=6 tầng: Masked Self-Attention + Cross-Attention + Feed-Forward + Add&Norm). Kết nối qua Cross-Attention. Đầu ra qua Linear + Softmax.

## Learning Objectives
1. Understand the structure and components of kiến trúc transformer
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

# Infographic Prompt: KIẾN TRÚC RAG

## Configuration
- **Layout:** structural-breakdown
- **Style:** technical-schematic
- **Aspect Ratio:** 16:9
- **Language:** Vietnamese (tiếng Việt)
- **Target Tool:** Midjourney / DALL-E 3 / ComfyUI

---

## Prompt (English — for image generation tools)

```
Create a technical schematic of RAG architecture in Vietnamese, split into Offline and Online phases.

LAYOUT: Structural-breakdown. Two large sub-sections: TOP half = "TIỀN XỬ LÝ (Offline)" with blue background tint — flow: "Sổ tay SV PDF (92 trang)" → "OCR Marker-PDF" → "Structured Chunking (Phần→Chương→Mục)" → "Embedding bge-m3 (1024d)" → "ChromaDB Vector Store". BOTTOM half = "TRUY VẤN (Online)" with green background tint — flow: "Câu hỏi người dùng" → "Query Embedding" → "Retrieval (similarity search)" [reads from ChromaDB] → "LLM Reranker (top-K)" → "LLM Generation qwen35-opus" → "Trả lời + Nguồn tham khảo".

STYLE: Technical schematic blueprint. Clean division between offline/online. Database cylinder icons for ChromaDB. Gear icons for processing steps.

TEXT (Vietnamese):
- Title: "Hình 3.1: Kiến trúc tổng quan RAG (Lewis et al., 2020)"
- Section headers bold, step labels in smaller font

ASPECT: 16:9 landscape.
```

---

## Usage Instructions

1. Copy the prompt above
2. Paste into your image generation tool (Midjourney, DALL-E, Stable Diffusion, ComfyUI)
3. For Midjourney: add `--ar 16:9 --style raw` at the end
4. For DALL-E: set aspect ratio to `16:9`
5. Generate 2-4 variations and pick the best one
6. Save as PNG and insert into the report at the corresponding figure position

# Infographic Prompt: PIPELINE RAG 3 TẦNG

## Configuration
- **Layout:** linear-progression
- **Style:** pop-laboratory
- **Aspect Ratio:** 16:9
- **Language:** Vietnamese (tiếng Việt)
- **Target Tool:** Midjourney / DALL-E 3 / ComfyUI

---

## Prompt (English — for image generation tools)

```
Create a laboratory-style linear flow infographic of the 3-tier RAG pipeline in Vietnamese.

LAYOUT: Linear-progression left to right. Start: "Câu hỏi" → "Query Expansion (từ đồng nghĩa VN)" → "Topic Filter (metadata)". Then split into two parallel paths: upper "Tầng 1: Bi-encoder Dense Retrieval (bge-m3)" in blue, lower "Tầng 2: BM25 Sparse Retrieval" in green. Both converge at "RRF Fusion". Then single path: "Tầng 3: LLM Reranker (chọn top-K)" in orange → "MMR (đa dạng hóa)" → "Ngữ cảnh (context)" → "LLM Generation (qwen35-opus)" → "Trả lời + trích dẫn nguồn".

STYLE: Pop-laboratory — blueprint grid, coordinate markers, glass beaker/flask icons at processing steps, precision measurement annotations, lab bench aesthetic. Color-coded tiers with specimen labels.

TEXT (Vietnamese):
- Title: "Hình 4.5: Pipeline RAG 3 tầng: Bi-encoder → BM25 → LLM Reranker"
- All step labels as above
- Annotations: "Tầng 1", "Tầng 2", "Tầng 3" as tier badges

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

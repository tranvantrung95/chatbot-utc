# Infographic Prompt: TỔNG QUAN HỆ THỐNG TƯ VẤN NỘI QUY UTC

## Configuration
- **Layout:** hub-spoke
- **Style:** technical-schematic
- **Aspect Ratio:** 16:9
- **Language:** Vietnamese (tiếng Việt)
- **Target Tool:** Midjourney / DALL-E 3 / ComfyUI

---

## Prompt (English — for image generation tools)

```
Create a technical schematic infographic in Vietnamese about the UTC University Regulation Advisory System.

LAYOUT: Hub-spoke diagram. Central hub is the "Chatbot Tư vấn Nội quy UTC". Spokes radiate to: (left) "Sinh viên" asking questions, (right) "Pipeline RAG 3 tầng" processing, (bottom) "ChromaDB" vector store + "LLM qwen35-opus", (top) "Quản trị viên" managing via admin panel.

STYLE: Technical schematic — blueprint lines, engineering precision, white background with navy blue (#1a237e) and teal (#00838f) accent colors. Clean typography, gear/processor icons.

TEXT (Vietnamese):
- Title: "Hình 1.1: Sơ đồ tổng quan bài toán hệ thống tư vấn nội quy UTC"
- Labels: Sinh viên UTC, Chatbot Tư vấn Nội quy, Pipeline RAG, ChromaDB Vector Store, LLM qwen35-opus, Quản trị viên, Trang Quản trị
- Flow arrows: "đặt câu hỏi" → "truy vấn" → "ngữ cảnh + prompt" → "trả lời streaming SSE"
- Data annotations: "Sổ tay SV 92 trang", "Embedding bge-m3 1024d"

ASPECT: 16:9 landscape. Clean, professional, academic.
```

---

## Usage Instructions

1. Copy the prompt above
2. Paste into your image generation tool (Midjourney, DALL-E, Stable Diffusion, ComfyUI)
3. For Midjourney: add `--ar 16:9 --style raw` at the end
4. For DALL-E: set aspect ratio to `16:9`
5. Generate 2-4 variations and pick the best one
6. Save as PNG and insert into the report at the corresponding figure position

# Infographic Prompt: KIẾN TRÚC TỔNG THỂ UTC ASSISTANT

## Configuration
- **Layout:** structural-breakdown
- **Style:** pop-laboratory
- **Aspect Ratio:** 16:9
- **Language:** Vietnamese (tiếng Việt)
- **Target Tool:** Midjourney / DALL-E 3 / ComfyUI

---

## Prompt (English — for image generation tools)

```
Create a laboratory-style exploded architecture diagram of UTC Assistant system in Vietnamese.

LAYOUT: Structural-breakdown with 4 horizontal layers. Layer 1 (top, green): "Frontend - Next.js 15" containing "Trang Sinh viên (chatbot UI)" and "Trang Quản trị (dashboard)". Layer 2 (blue): "Backend - FastAPI Python 3.14" containing "REST API + SSE Streaming", "RAG Pipeline (3 tầng)", "Auth Middleware (JWT)". Layer 3 (yellow): "Data Layer" containing "ChromaDB Vector Store" and "SQLite (Activities, Config)". Layer 4 (red): "AI Services" containing "Embedding BAAI/bge-m3" and "LLM qwen35-opus". Vertical connection lines between layers.

STYLE: Pop-laboratory — blueprint grid background with coordinate markers (A1-G7), lab notebook aesthetic, specimen labels, measurement annotations. Each layer has distinct pastel background.

TEXT (Vietnamese):
- Title: "Hình 4.4: Kiến trúc tổng thể hệ thống UTC Assistant"
- Layer labels, component names, connection annotations "HTTP/SSE", "API calls"

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

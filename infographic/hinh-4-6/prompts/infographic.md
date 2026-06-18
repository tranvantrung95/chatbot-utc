# Infographic Prompt: LUỒNG XỬ LÝ DỮ LIỆU

## Configuration
- **Layout:** linear-progression
- **Style:** ikea-manual
- **Aspect Ratio:** 16:9
- **Language:** Vietnamese (tiếng Việt)
- **Target Tool:** Midjourney / DALL-E 3 / ComfyUI

---

## Prompt (English — for image generation tools)

```
Create an IKEA-manual style data processing flow infographic in Vietnamese.

LAYOUT: Linear progression. Start: "Sổ tay SV PDF (92 trang)" document icon → "Marker-PDF (OCR + cấu trúc)" scanner icon → "Trích xuất Mục lục (TOC JSON)" tree-structure icon → "Structured Chunking (Phần→Chương→Mục)" puzzle pieces → "Gán metadata (phan_so, title, page)" tag icons → "Embedding bge-m3 (1024d)" grid icon → "ChromaDB Collection: utc_knowledge" database cylinder → final checkmark "Cơ sở tri thức sẵn sàng".

STYLE: IKEA manual — minimal black outlines, single accent color (IKEA blue), flat icons, simple arrows between steps, instructional numbering. No shading, very clean.

TEXT (Vietnamese):
- Title: "Hình 4.6: Luồng xử lý dữ liệu: PDF → OCR → Chunk → ChromaDB"
- Step numbers 1-7 with labels
- Final annotation: "Sẵn sàng truy vấn"

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

# Infographic Prompt: KIẾN TRÚC TRANSFORMER

## Configuration
- **Layout:** structural-breakdown
- **Style:** technical-schematic
- **Aspect Ratio:** 16:9
- **Language:** Vietnamese (tiếng Việt)
- **Target Tool:** Midjourney / DALL-E 3 / ComfyUI

---

## Prompt (English — for image generation tools)

```
Create a technical exploded-view infographic of the Transformer architecture in Vietnamese.

LAYOUT: Structural-breakdown. Two main blocks side by side: Left = "Encoder (N=6 tầng)" in blue (#1565c0), Right = "Decoder (N=6 tầng)" in orange (#e65100). Encoder detail: Input Embedding → Multi-Head Self-Attention → Add & Norm → Feed Forward → Add & Norm. Decoder detail: Output Embedding → Masked Multi-Head Self-Attention → Add & Norm → Multi-Head Cross-Attention → Add & Norm → Feed Forward → Add & Norm. Connection arrow from Encoder to Decoder Cross-Attention. Final: Linear → Softmax → Output Tokens.

STYLE: Technical schematic blueprint style. White background, blueprint grid lines subtly visible. Component blocks with sharp edges and drop shadows. Connection arrows with technical annotations.

TEXT (Vietnamese):
- Title: "Hình 2.1: Kiến trúc Transformer (Vaswani et al., 2017)"
- Component labels as above
- Annotation: "Cơ chế Self-Attention xử lý song song toàn bộ chuỗi"

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

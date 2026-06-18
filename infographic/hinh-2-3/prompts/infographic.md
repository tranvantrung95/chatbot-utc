# Infographic Prompt: MULTI-HEAD ATTENTION

## Configuration
- **Layout:** structural-breakdown
- **Style:** technical-schematic
- **Aspect Ratio:** 16:9
- **Language:** Vietnamese (tiếng Việt)
- **Target Tool:** Midjourney / DALL-E 3 / ComfyUI

---

## Prompt (English — for image generation tools)

```
Create a technical schematic showing Multi-Head Attention mechanism in Vietnamese.

LAYOUT: Structural-breakdown showing parallel heads. Top: Single "Input" box. Then h=8 parallel "head" blocks stacked vertically, each labeled "head₁" through "head_h". Each head: "Linear(Q,K,V)" → "Scaled Dot-Product Attention". All heads converge to "Concat" → "Linear Projection W^O" → "Output". 

STYLE: Technical schematic with clean lines, navy/teal color scheme. Each head is a thin horizontal strip.

TEXT (Vietnamese):
- Title: "Hình 2.3: Cơ chế Multi-Head Attention"
- Labels: Input, head₁...head_h, Concat, Linear Projection W^O, Output
- Annotation: "h=8 head, d_k=64 mỗi head"

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

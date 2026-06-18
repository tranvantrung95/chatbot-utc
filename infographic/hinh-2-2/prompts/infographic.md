# Infographic Prompt: SCALED DOT-PRODUCT ATTENTION

## Configuration
- **Layout:** linear-progression
- **Style:** pop-laboratory
- **Aspect Ratio:** 16:9
- **Language:** Vietnamese (tiếng Việt)
- **Target Tool:** Midjourney / DALL-E 3 / ComfyUI

---

## Prompt (English — for image generation tools)

```
Create a laboratory-style infographic showing the Scaled Dot-Product Attention formula flow in Vietnamese.

LAYOUT: Linear progression left to right. Input blocks at left: Q (Query, blue), K (Key, green), V (Value, orange). Flow: Q×K^T → "Scale ÷√d_k" → "Mask (opt.)" → "Softmax" → "×V" → "Output". Each step is a rounded rectangle with the operation inside.

STYLE: Pop-laboratory — blueprint grid background, coordinate markers (A1, B2, C3 style), lab equipment aesthetic. Formula displayed prominently: Attention(Q,K,V) = softmax(QK^T/√d_k) × V in large math font.

TEXT (Vietnamese):
- Title: "Hình 2.2: Cơ chế Scaled Dot-Product Attention"
- Formula in center
- Labels at each step

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

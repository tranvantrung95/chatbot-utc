# Infographic Prompt: MINH HỌA EMBEDDING

## Configuration
- **Layout:** linear-progression
- **Style:** hand-drawn-edu
- **Aspect Ratio:** 16:9
- **Language:** Vietnamese (tiếng Việt)
- **Target Tool:** Midjourney / DALL-E 3 / ComfyUI

---

## Prompt (English — for image generation tools)

```
Create a hand-drawn educational infographic illustrating text embedding in Vietnamese.

LAYOUT: Linear progression. Three text inputs side by side: "Học phí được đóng theo kỳ", "Sinh viên nộp tiền học phí", "Quy định về ký túc xá UTC". Each feeds into a "bge-m3 Encoder" box (macaron pastel colored). Each outputs a 1024-dim vector visualization (colorful bar chart strips). Between first two vectors: "cosine sim = 0.94 ✓" (connected, close). Between first and third: "cosine sim = 0.12 ✗" (separated, far).

STYLE: Hand-drawn edu — macaron pastel colors (mint green, peach, lavender, baby blue), hand-drawn wobble lines, stick figure characters, chalk-like texture, playful but educational.

TEXT (Vietnamese):
- Title: "Hình 3.4: Minh họa quá trình embedding văn bản thành vector"
- Input text labels
- Similarity annotations
- "BAAI/bge-m3 — 1024 chiều"

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

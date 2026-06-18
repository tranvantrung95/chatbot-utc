# Source: Kiến trúc Transformer
**Figure:** Hình 2.1
**Type:** system-structure
**Description:** Kiến trúc Transformer gồm Encoder (N=6 tầng: Self-Attention + Feed-Forward + Add&Norm) và Decoder (N=6 tầng: Masked Self-Attention + Cross-Attention + Feed-Forward + Add&Norm). Kết nối qua Cross-Attention. Đầu ra qua Linear + Softmax.

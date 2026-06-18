# Source: Cơ chế Scaled Dot-Product Attention
**Figure:** Hình 2.2
**Type:** process
**Description:** Công thức Attention(Q,K,V) = softmax(QK^T/√d_k) × V. Các bước: Query và Key → MatMul → Scale (÷√d_k) → Mask → Softmax → MatMul với Value → Output.

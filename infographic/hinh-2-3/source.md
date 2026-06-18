# Source: Cơ chế Multi-Head Attention
**Figure:** Hình 2.3
**Type:** system-structure
**Description:** Multi-Head Attention chạy h=8 head song song. Mỗi head: Linear(Q,K,V) → Scaled Dot-Product Attention → Concat tất cả head → Linear Projection W^O → Output.

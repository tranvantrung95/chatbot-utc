

# ═══ MỤC LỤC ═══
H("MỤC LỤC", 1)
toc_items = [
    ("Lời cảm ơn","3"),("Mục lục","4"),("Danh mục các từ viết tắt","6"),
    ("Danh mục bảng biểu","7"),("Danh mục hình ảnh","8"),("Mở đầu","10"),
    ("Chương 1. Tổng quan bài toán xây dựng hệ thống tư vấn nội quy trường Đại học Giao thông Vận tải","12"),
    ("  1.1. Đặt vấn đề","12"),
    ("  1.2. Mục tiêu và phạm vi đồ án","13"),
    ("  1.3. Công nghệ và công cụ sử dụng","13"),
    ("    1.3.1. Công nghệ sử dụng","13"),
    ("    1.3.2. Công cụ sử dụng","14"),
    ("Chương 2. Mô hình ngôn ngữ lớn","15"),
    ("  2.1. Tổng quan mô hình ngôn ngữ lớn","15"),
    ("  2.2. Kiến trúc Transformer","16"),
    ("    2.2.1. Tổng quan kiến trúc","16"),
    ("    2.2.2. Encoder – Decoder","17"),
    ("    2.2.3. Cơ chế self-attention","18"),
    ("  2.3. Prompt Engineering","19"),
    ("Chương 3. Truy vấn tạo sinh tăng cường","21"),
    ("  3.1. Tổng quan về RAG","21"),
    ("  3.2. Phân loại RAG","22"),
    ("  3.3. Quy trình thực hiện phương pháp RAG ngây thơ (Naive RAG)","23"),
    ("    3.3.1. Indexing","24"),
    ("    3.3.2. Nhúng từ (Embedding)","26"),
    ("    3.3.3. Retrieving","27"),
    ("    3.3.4. Generating","28"),
    ("Chương 4. Xây dựng hệ thống tư vấn nội quy trường Đại học Giao thông Vận tải","30"),
    ("  4.1. Phân tích thiết kế hệ thống","30"),
    ("    4.1.1. Sơ đồ ca sử dụng","30"),
    ("    4.1.2. Đặc tả các chức năng","31"),
    ("  4.2. Xây dựng trang web tư vấn viên nội quy","35"),
    ("    4.2.1. Cài đặt chatbot sử dụng phương pháp RAG","35"),
    ("    4.2.2. Phân lớp câu hỏi của người dùng","39"),
    ("    4.2.3. Giao diện trang web tư vấn viên nội quy","40"),
    ("  4.3. Xây dựng trang web quản trị tư vấn nội quy","41"),
    ("    4.3.1. Giao diện chức năng xác thực","41"),
    ("    4.3.2. Giao diện chức năng thống kê","43"),
    ("    4.3.3. Giao diện chức năng cập nhật dữ liệu","44"),
    ("KẾT LUẬN VÀ KIẾN NGHỊ","47"),
    ("DANH MỤC TÀI LIỆU THAM KHẢO","49"),
]
for item, page in toc_items:
    P(f"{item} {'.' * max(2, 72 - len(item))} {page}", s=12)
BR()

# ═══ DANH MỤC CÁC TỪ VIẾT TẮT ═══
H("DANH MỤC CÁC TỪ VIẾT TẮT", 1)
TBL(["Dạng viết tắt", "Dạng đầy đủ", "Ý nghĩa"], [
    ["LLM","Large Language Model","Mô hình ngôn ngữ lớn"],
    ["RAG","Retrieval-Augmented Generation","Truy vấn tạo sinh tăng cường"],
    ["NLP","Natural Language Processing","Xử lý ngôn ngữ tự nhiên"],
    ["BERT","Bidirectional Encoder Representations from Transformers","Biểu diễn mã hóa hai chiều từ Transformer"],
    ["GPT","Generative Pre-trained Transformer","Transformer sinh tiền huấn luyện"],
    ["Transformer","—","Kiến trúc mạng neural dựa trên cơ chế tự chú ý"],
    ["CoT","Chain of Thought","Chuỗi suy luận"],
    ["ICL","In-Context Learning","Học trong ngữ cảnh"],
    ["MLM","Masked Language Modeling","Mô hình hóa ngôn ngữ dạng mặt nạ"],
    ["MRR","Mean Reciprocal Rank","Xếp hạng đảo ngược trung bình"],
    ["BM25","Best Matching 25","Thuật toán xếp hạng văn bản"],
    ["RRF","Reciprocal Rank Fusion","Kết hợp xếp hạng đảo ngược"],
    ["SSE","Server-Sent Events","Sự kiện gửi từ máy chủ"],
    ["OCR","Optical Character Recognition","Nhận dạng ký tự quang học"],
    ["API","Application Programming Interface","Giao diện lập trình ứng dụng"],
    ["UTC","University of Transport and Communications","Trường Đại học Giao thông Vận tải"],
    ["DB","Database","Cơ sở dữ liệu"],
    ["FE","Frontend","Giao diện người dùng"],
    ["BE","Backend","Máy chủ xử lý"],
    ["RoPE","Rotary Position Embedding","Nhúng vị trí xoay"],
    ["GQA","Grouped Query Attention","Tự chú ý nhóm truy vấn"],
])
BR()

# ═══ DANH MỤC BẢNG BIỂU ═══
H("DANH MỤC BẢNG BIỂU", 1)
for t in [
    "Bảng 1.1: Các công nghệ chính sử dụng trong hệ thống",
    "Bảng 1.2: Các công cụ phát triển và triển khai",
    "Bảng 2.1: Một số mô hình LLM tiêu biểu và số lượng tham số",
    "Bảng 2.2: So sánh các chiến lược Prompt Engineering",
    "Bảng 3.1: So sánh các phân loại RAG (Naive, Advanced, Modular)",
    "Bảng 3.2: Các phương pháp embedding phổ biến",
    "Bảng 3.3: So sánh các chiến lược retrieval (Sparse, Dense, Hybrid)",
    "Bảng 4.1: Đặc tả ca sử dụng - Tra cứu nội quy",
    "Bảng 4.2: Đặc tả ca sử dụng - Quản lý dữ liệu",
    "Bảng 4.3: Đặc tả ca sử dụng - Thống kê và báo cáo",
    "Bảng 4.4: Cấu trúc metadata trong mỗi chunk của ChromaDB",
    "Bảng 4.5: Các API endpoint chính của UTC Assistant",
    "Bảng 4.6: Các lớp câu hỏi và chiến lược xử lý",
]:
    P(f"{t} {'·' * max(2, 68 - len(t))} Trang", s=12)
BR()

# ═══ DANH MỤC HÌNH ẢNH ═══
H("DANH MỤC HÌNH ẢNH", 1)
for f in [
    "Hình 1.1: Sơ đồ tổng quan bài toán hệ thống tư vấn nội quy UTC",
    "Hình 2.1: Kiến trúc Transformer (Vaswani et al., 2017)",
    "Hình 2.2: Cơ chế Self-Attention – Scaled Dot-Product Attention",
    "Hình 2.3: Cơ chế Multi-Head Attention",
    "Hình 2.4: Sơ đồ minh họa các chiến lược Prompt Engineering",
    "Hình 3.1: Kiến trúc tổng quan RAG (Lewis et al., 2020)",
    "Hình 3.2: Phân loại các biến thể RAG",
    "Hình 3.3: Quy trình Naive RAG: Indexing → Retrieval → Generation",
    "Hình 3.4: Minh họa quá trình embedding văn bản thành vector",
    "Hình 4.1: Sơ đồ ca sử dụng tổng quan hệ thống UTC Assistant",
    "Hình 4.2: Sơ đồ ca sử dụng chi tiết - Nhóm chức năng sinh viên",
    "Hình 4.3: Sơ đồ ca sử dụng chi tiết - Nhóm chức năng quản trị",
    "Hình 4.4: Kiến trúc tổng thể hệ thống UTC Assistant",
    "Hình 4.5: Pipeline RAG 3 tầng: Bi-encoder → BM25 Hybrid → LLM Reranker",
    "Hình 4.6: Luồng xử lý dữ liệu: PDF → OCR → Chunk → ChromaDB",
    "Hình 4.7: Giao diện chatbot tư vấn nội quy (trang sinh viên)",
    "Hình 4.8: Giao diện đăng nhập trang quản trị",
    "Hình 4.9: Giao diện thống kê - Dashboard quản trị",
    "Hình 4.10: Giao diện cập nhật dữ liệu - Trang quản lý tài liệu",
]:
    P(f"{f} {'·' * max(2, 68 - len(f))} Trang", s=12)
BR()

# ═══ MỞ ĐẦU ═══
H("MỞ ĐẦU", 1)

H("1. Bối cảnh và lý do chọn đề tài", 2)
P("Trong bối cảnh chuyển đổi số diễn ra mạnh mẽ trên mọi lĩnh vực, giáo dục đại học cũng không nằm ngoài xu hướng này. Trường Đại học Giao thông Vận tải (UTC) với quy mô hàng chục nghìn sinh viên đang phải đối mặt với thách thức lớn trong việc hỗ trợ sinh viên tra cứu thông tin về nội quy, quy chế của nhà trường. Sổ tay sinh viên dày 92 trang chứa đựng lượng lớn quy chế, quy định quan trọng về đào tạo, học phí, kỷ luật, ký túc xá... nhưng sinh viên thường gặp khó khăn khi tra cứu do tài liệu dài, cấu trúc phức tạp và không có công cụ tìm kiếm hiệu quả.")
P("Sự phát triển vượt bậc của các mô hình ngôn ngữ lớn (LLM) trong những năm gần đây đã mở ra những khả năng mới trong việc xây dựng các hệ thống hỏi đáp thông minh. Kết hợp LLM với kỹ thuật Truy vấn tạo sinh tăng cường (Retrieval-Augmented Generation - RAG) cho phép xây dựng các hệ thống có khả năng trả lời câu hỏi dựa trên tài liệu tham khảo cụ thể, giảm thiểu hiện tượng \"ảo giác\" (hallucination) và đảm bảo câu trả lời có căn cứ. Xuất phát từ nhu cầu thực tế đó, đề tài \"Xây dựng hệ thống tư vấn nội quy trường Đại học Giao thông Vận tải sử dụng mô hình ngôn ngữ lớn và RAG\" được lựa chọn thực hiện.")

H("2. Mục tiêu nghiên cứu", 2)
P("Mục tiêu tổng quát của đồ án là xây dựng một hệ thống trợ lý ảo (chatbot) có khả năng tư vấn, giải đáp các câu hỏi của sinh viên liên quan đến nội quy, quy chế của Trường Đại học Giao thông Vận tải một cách chính xác, nhanh chóng và hoạt động 24/7. Các mục tiêu cụ thể bao gồm:")
P("(1) Nghiên cứu và nắm vững nền tảng lý thuyết về mô hình ngôn ngữ lớn, bao gồm kiến trúc Transformer, cơ chế self-attention và các kỹ thuật Prompt Engineering.")
P("(2) Nghiên cứu và ứng dụng kỹ thuật Truy vấn tạo sinh tăng cường (RAG) để xây dựng pipeline xử lý tài liệu và truy xuất thông tin từ cơ sở dữ liệu vector.")
P("(3) Thiết kế và xây dựng hệ thống hoàn chỉnh bao gồm: chatbot tư vấn nội quy cho sinh viên và trang web quản trị cho cán bộ quản lý.")
P("(4) Đánh giá chất lượng và hiệu năng hệ thống trên dữ liệu thực tế của nhà trường.")

H("3. Đối tượng và phạm vi nghiên cứu", 2)
P("Đối tượng nghiên cứu: Mô hình ngôn ngữ lớn (LLM), kỹ thuật RAG, kiến trúc Transformer, các phương pháp embedding và truy xuất thông tin, công nghệ xây dựng ứng dụng web (FastAPI, Next.js).")
P("Phạm vi nghiên cứu: Tập trung vào việc xây dựng hệ thống tư vấn dựa trên dữ liệu Sổ tay sinh viên K66 (năm học 2024-2025) của Trường Đại học Giao thông Vận tải. Hệ thống hỗ trợ tiếng Việt, bao gồm hai giao diện chính: chatbot cho sinh viên và trang quản trị cho cán bộ.")

H("4. Phương pháp nghiên cứu", 2)
P("Báo cáo sử dụng kết hợp phương pháp nghiên cứu lý thuyết và thực nghiệm. Về lý thuyết, báo cáo tổng hợp và phân tích các công trình nghiên cứu nền tảng từ các hội nghị hàng đầu (NeurIPS, ICML, ACL) và tài liệu chuyên khảo. Về thực nghiệm, báo cáo xây dựng hệ thống thực tế trên nền tảng FastAPI (Python 3.14) và Next.js 15, sử dụng mô hình embedding BAAI/bge-m3 và LLM qwen35-opus, đánh giá trên tập dữ liệu Sổ tay sinh viên K66 (92 trang) với 50 câu hỏi kiểm thử.")

H("5. Bố cục báo cáo", 2)
P("Chương 1 trình bày tổng quan về bài toán xây dựng hệ thống tư vấn nội quy, bao gồm đặt vấn đề, mục tiêu, phạm vi và các công nghệ sử dụng. Chương 2 đi sâu vào nền tảng lý thuyết về mô hình ngôn ngữ lớn, kiến trúc Transformer và kỹ thuật Prompt Engineering. Chương 3 trình bày về kỹ thuật Truy vấn tạo sinh tăng cường (RAG) và quy trình thực hiện Naive RAG. Chương 4 mô tả chi tiết quá trình phân tích, thiết kế và xây dựng hệ thống tư vấn nội quy UTC. Cuối cùng là phần Kết luận và Kiến nghị, tổng kết những kết quả đạt được và đề xuất hướng phát triển.")
BR()

print("TOC + Front matter + Mo dau done.")
doc.save(OUT)

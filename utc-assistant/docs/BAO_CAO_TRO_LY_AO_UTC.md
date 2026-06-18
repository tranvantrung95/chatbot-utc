TRƯỜNG ĐẠI HỌC GIAO THÔNG VẬN TẢI
KHOA CÔNG NGHỆ THÔNG TIN

TIỂU LUẬN MÔ HÌNH NGÔN NGỮ LỚN

ĐỀ TÀI
XÂY DỰNG TRỢ LÝ ẢO TIẾNG VIỆT GIẢI ĐÁP THẮC MẮC
CHO SINH VIÊN TRƯỜNG ĐẠI HỌC GIAO THÔNG VẬN TẢI
SỬ DỤNG QWEN 3 4B

Giảng viên hướng dẫn: TS. ...
Sinh viên thực hiện: ...
Mã sinh viên: ...
Lớp: ...
Khóa: ...

Hà Nội – 2026

> Ghi chú cập nhật kỹ thuật: phiên bản mã nguồn hiện tại đã chuyển sang chạy
> hoàn toàn local với Ollama cho cả embedding (`bge-m3`) và LLM (`qwen3:4b`).
> Một số đoạn trong báo cáo học thuật bên dưới còn mô tả phương án cũ dùng
> OpenAI embedding/DeepSeek để so sánh và cần được hiệu chỉnh nếu nộp bản cuối.


LỜI CẢM ƠN

Đầu tiên, em xin gửi lời cảm ơn chân thành đến giảng viên hướng dẫn môn học
"Mô hình ngôn ngữ lớn" đã tận tình truyền đạt những kiến thức nền tảng về kiến
trúc Transformer, cơ chế Attention, các mô hình ngôn ngữ lớn và kỹ thuật
Retrieval-Augmented Generation (RAG). Những kiến thức này là nền tảng quan
trọng để em có thể hoàn thành tiểu luận này.

Em cũng xin gửi lời cảm ơn đến các thầy cô trong Khoa Công nghệ Thông tin –
Trường Đại học Giao thông Vận tải đã nhiệt tình giảng dạy trong suốt quá trình
học tập.

Em xin cảm ơn Nhà trường đã công bố các tài liệu chính thức như Sổ tay sinh
viên, website trường, tạo điều kiện thuận lợi cho việc thu thập dữ liệu xây
dựng kho tri thức cho hệ thống.

Trong quá trình thực hiện tiểu luận, với kiến thức và kinh nghiệm còn hạn chế,
em khó tránh khỏi những thiếu sót. Em rất mong nhận được sự góp ý từ thầy cô
để tiểu luận được hoàn thiện hơn.

Hà Nội, ngày ... tháng ... năm 2026

Sinh viên thực hiện


MỤC LỤC

Lời cảm ơn
Mục lục
Danh mục các từ viết tắt
Danh mục bảng biểu
Danh mục hình ảnh
Mở đầu
Chương 1. Tổng quan về mô hình ngôn ngữ lớn và bài toán trợ lý ảo
  1.1. Đặt vấn đề
  1.2. Mục tiêu và phạm vi
  1.3. Công nghệ và công cụ sử dụng
Chương 2. Mô hình ngôn ngữ lớn
  2.1. Tổng quan mô hình ngôn ngữ lớn
  2.2. Kiến trúc Transformer
  2.3. Qwen 3 và mô hình ngôn ngữ lớn cho tiếng Việt
Chương 3. Truy vấn tạo sinh tăng cường (RAG)
  3.1. Tổng quan về RAG
  3.2. Các thành phần của hệ thống RAG
  3.3. Embedding và Vector Database
Chương 4. Xây dựng hệ thống trợ lý ảo UTC
  4.1. Phân tích và thiết kế hệ thống
  4.2. Thu thập và xử lý dữ liệu
  4.3. Xây dựng pipeline RAG
  4.4. Xây dựng giao diện người dùng
  4.5. Đánh giá và kết quả
Kết luận và kiến nghị
Tài liệu tham khảo


DANH MỤC CÁC TỪ VIẾT TẮT

Dạng viết tắt | Dạng đầy đủ | Ý nghĩa
LLM | Large Language Model | Mô hình ngôn ngữ lớn
RAG | Retrieval-Augmented Generation | Truy vấn tạo sinh tăng cường
NLP | Natural Language Processing | Xử lý ngôn ngữ tự nhiên
API | Application Programming Interface | Giao diện lập trình ứng dụng
MoE | Mixture of Experts | Hỗn hợp chuyên gia
CSDL | Cơ sở dữ liệu
UTC | University of Transport and Communications | Đại học Giao thông Vận tải
ANN | Approximate Nearest Neighbor | Tìm kiếm láng giềng gần xấp xỉ
HNSW | Hierarchical Navigable Small World | Thuật toán tìm kiếm gần đúng
UI | User Interface | Giao diện người dùng
LMS | Learning Management System | Hệ thống quản lý học tập
KTX | Ký túc xá


DANH MỤC BẢNG BIỂU

Bảng 2.1: Thống kê số lượng tham số của một số LLM phổ biến
Bảng 2.2: So sánh khả năng tiếng Việt của các LLM
Bảng 3.1: So sánh các embedding model đa ngôn ngữ
Bảng 4.1: Danh sách nguồn dữ liệu thu thập
Bảng 4.2: Thống kê dữ liệu sau khi thu thập
Bảng 4.3: Kết quả đánh giá hệ thống trên 20 câu hỏi kiểm thử


DANH MỤC HÌNH ẢNH

Hình 2.1: Kiến trúc Transformer
Hình 3.1: Kiến trúc hệ thống RAG
Hình 3.2: Quy trình thực hiện RAG Naive
Hình 4.1: Sơ đồ kiến trúc tổng thể hệ thống
Hình 4.2: Sơ đồ luồng xử lý câu hỏi
Hình 4.3: Giao diện chính của Trợ lý ảo UTC
Hình 4.4: Ví dụ câu hỏi và câu trả lời từ hệ thống


MỞ ĐẦU

Trường Đại học Giao thông Vận tải (UTC) là một trường đại học lớn của Việt
Nam với lịch sử hơn 60 năm hình thành và phát triển. Hiện nay, trường có quy
mô đào tạo hàng chục nghìn sinh viên theo học mỗi năm và con số này không
ngừng tăng lên. Điều này tạo ra áp lực rất lớn đối với bộ máy quản lý và hỗ
trợ sinh viên của nhà trường.

Sinh viên, đặc biệt là sinh viên mới nhập học, thường gặp nhiều thắc mắc về
chương trình đào tạo, quy chế, nội quy, học phí, ký túc xá và các dịch vụ hỗ
trợ khác. Mặc dù nhà trường đã cung cấp đầy đủ thông tin qua Sổ tay sinh viên,
website chính thức, và các kênh thông tin trực tuyến, sinh viên vẫn thường có
tâm lý ngại tra cứu, hoặc không biết tìm kiếm thông tin ở đâu. Điều này dẫn
đến tình trạng các phòng ban, văn phòng khoa phải tiếp nhận và trả lời lặp đi
lặp lại cùng một nhóm câu hỏi, gây quá tải công việc và ảnh hưởng đến chất
lượng hỗ trợ.

Hiện nay, các mô hình ngôn ngữ lớn (LLM) đang phát triển mạnh mẽ, có khả năng
sinh câu trả lời bằng ngôn ngữ tự nhiên rất giống con người. Tuy nhiên, LLM
có hạn chế là nguồn tri thức bị giới hạn trong dữ liệu huấn luyện, không thể
cập nhật các tri thức mới nhất hoặc các thông tin đặc thù của một tổ chức.
Phương pháp Truy vấn tạo sinh tăng cường (RAG) được giới thiệu cho phép bổ
sung tri thức ngoài cho LLM, giúp LLM trả lời chính xác các câu hỏi dựa trên
tài liệu tham khảo được cung cấp.

Trong tiểu luận này, em sử dụng mô hình Qwen 3 4B – một mô hình ngôn ngữ lớn
mã nguồn mở mới nhất từ Alibaba, kết hợp với phương pháp RAG để xây dựng một
trợ lý ảo tiếng Việt có khả năng giải đáp thắc mắc cho sinh viên Trường Đại
học Giao thông Vận tải. Mô hình Qwen 3 4B được lựa chọn vì kích thước nhẹ
(4B tham số), có thể chạy trên máy tính cá nhân thông qua Ollama, và hỗ trợ
tốt tiếng Việt. Hệ thống sử dụng Sổ tay sinh viên khóa 66 và dữ liệu từ
website UTC làm nguồn tri thức chính.

Mục tiêu của tiểu luận là:
1. Xây dựng hệ thống trợ lý ảo có khả năng truy xuất thông tin từ Sổ tay sinh
   viên và website UTC để trả lời câu hỏi của sinh viên
2. Ứng dụng phương pháp RAG kết hợp với Qwen 3 4B để sinh câu trả lời bằng
   tiếng Việt một cách tự nhiên và chính xác
3. Xây dựng giao diện web cho phép sinh viên tương tác dễ dàng với trợ lý ảo

Phạm vi của tiểu luận tập trung vào các câu hỏi liên quan đến Trường Đại học
Giao thông Vận tải, bao gồm: thông tin chung về trường, chương trình đào tạo,
quy chế – nội quy, tuyển sinh, học phí – học bổng, và các dịch vụ sinh viên.

Bố cục tiểu luận gồm 4 chương:
- Chương 1: Tổng quan về bài toán và công nghệ sử dụng
- Chương 2: Trình bày về mô hình ngôn ngữ lớn và Qwen 3
- Chương 3: Trình bày về phương pháp RAG và các thành phần
- Chương 4: Mô tả chi tiết quá trình xây dựng hệ thống và đánh giá kết quả


CHƯƠNG 1. TỔNG QUAN VỀ MÔ HÌNH NGÔN NGỮ LỚN
VÀ BÀI TOÁN TRỢ LÝ ẢO

1.1. Đặt vấn đề

Trường Đại học Giao thông Vận tải là một trường đại học kỹ thuật hàng đầu tại
Việt Nam, với quy mô đào tạo lớn và đa dạng ngành nghề. Hàng năm, trường tiếp
nhận hàng nghìn tân sinh viên. Theo Sổ tay sinh viên khóa 66 (UTC, 2025),
trường có 9 khoa đào tạo, hàng chục chuyên ngành từ đại học đến tiến sĩ, cùng
hệ thống quy chế, quy định phức tạp về đào tạo, rèn luyện, kỷ luật, học bổng,
chế độ chính sách, vay vốn tín dụng, và quản lý ngoại trú.

Sinh viên, đặc biệt là tân sinh viên, thường gặp khó khăn trong việc tiếp cận
và tra cứu thông tin. Mặc dù Sổ tay sinh viên đã tổng hợp đầy đủ các quy định,
việc đọc và hiểu toàn bộ tài liệu dày hàng chục trang là không dễ dàng. Các
câu hỏi thường gặp bao gồm: "Điều kiện xét tốt nghiệp là gì?", "Học phí một
kỳ là bao nhiêu?", "Thủ tục đăng ký KTX như thế nào?", "Điều kiện nhận học
bổng ra sao?"...

Bộ phận hỗ trợ sinh viên và văn phòng các khoa thường xuyên phải trả lời các
câu hỏi lặp đi lặp lại, gây quá tải và ảnh hưởng đến chất lượng phục vụ. Việc
xây dựng một hệ thống trợ lý ảo có khả năng tự động tra cứu và trả lời các
câu hỏi này sẽ giúp giảm tải cho các phòng ban, đồng thời cung cấp cho sinh
viên một kênh thông tin nhanh chóng, chính xác, hoạt động 24/7.

1.2. Mục tiêu và phạm vi

Mục tiêu của tiểu luận:
1. Nghiên cứu và ứng dụng mô hình Qwen 3 4B – mô hình ngôn ngữ lớn mã nguồn
   mở, kích thước nhẹ (4B tham số), hỗ trợ tiếng Việt tốt
2. Xây dựng pipeline RAG sử dụng ChromaDB làm vector database và OpenAI
   text-embedding-3-small làm embedding model
3. Thu thập và xử lý dữ liệu từ hai nguồn chính: Sổ tay sinh viên khóa 66
   (PDF) và website chính thức của UTC
4. Xây dựng giao diện web với Streamlit, cho phép sinh viên đặt câu hỏi và
   nhận câu trả lời bằng tiếng Việt

Phạm vi:
- Hệ thống trả lời các câu hỏi liên quan đến Trường Đại học Giao thông Vận tải
- Các câu hỏi nằm ngoài phạm vi sẽ được từ chối và hướng dẫn liên hệ trực tiếp
- Mô hình Qwen 3 4B chạy local qua Ollama, embedding sử dụng OpenAI API

1.3. Công nghệ và công cụ sử dụng

1.3.1. Công nghệ

Mô hình ngôn ngữ lớn Qwen 3 4B: Đây là mô hình ngôn ngữ lớn mã nguồn mở thế hệ
thứ 3 của Alibaba, được công bố tháng 4/2025. Qwen 3 sử dụng kiến trúc
Mixture-of-Experts (MoE) với tổng 4B tham số, trong đó ~1.5B tham số được kích
hoạt mỗi lần suy luận. Mô hình hỗ trợ 119 ngôn ngữ, bao gồm tiếng Việt, và có
thể chạy trên máy tính cá nhân không cần GPU chuyên dụng thông qua Ollama.

Retrieval-Augmented Generation (RAG): Phương pháp kết hợp truy xuất thông tin
và sinh văn bản, cho phép LLM trả lời câu hỏi dựa trên tài liệu tham khảo bên
ngoài mà không cần fine-tune. RAG được giới thiệu bởi Lewis et al. (2020) và
đã trở thành phương pháp tiêu chuẩn cho các ứng dụng hỏi-đáp trên tài liệu.

Prompt Engineering: Kỹ thuật thiết kế prompt giúp LLM hiểu rõ nhiệm vụ và sinh
câu trả lời chính xác. Trong hệ thống này, prompt được thiết kế để định hướng
LLM trả lời bằng tiếng Việt, chỉ dựa trên ngữ cảnh được cung cấp.

1.3.2. Công cụ

Ngôn ngữ lập trình Python: Được lựa chọn vì cú pháp đơn giản, hệ sinh thái
phong phú cho AI/ML. Các thư viện chính được sử dụng bao gồm:

- Streamlit: Framework xây dựng giao diện web nhanh, không yêu cầu kiến thức
  về HTML/CSS/JavaScript, phù hợp cho việc phát triển MVP

- ChromaDB: Vector database mã nguồn mở, lưu trữ local, hỗ trợ tìm kiếm
  cosine similarity với thuật toán HNSW

- PyMuPDF (fitz): Thư viện trích xuất văn bản từ file PDF

- BeautifulSoup4: Thư viện parse HTML phục vụ crawl dữ liệu

- OpenAI Python SDK: Sử dụng cho embedding API (text-embedding-3-small)

- Ollama: Công cụ chạy mô hình ngôn ngữ lớn local, hỗ trợ Qwen 3 4B


CHƯƠNG 2. MÔ HÌNH NGÔN NGỮ LỚN

2.1. Tổng quan mô hình ngôn ngữ lớn

Mô hình ngôn ngữ (Language Model) là một mô hình học máy có khả năng dự đoán
và sinh ngôn ngữ tự nhiên. Các mô hình này hoạt động bằng cách dự đoán xác
suất của một token hoặc chuỗi token xuất hiện trong một chuỗi dài hơn [1].

LLM được huấn luyện trên tập dữ liệu rất lớn và đạt được khả năng hiểu và
sinh ngôn ngữ thông qua tri thức thu nạp được về cấu trúc và ngữ nghĩa của
ngôn ngữ. LLM học được các mối quan hệ thống kê thông qua quá trình học tự
giám sát và bán giám sát [2]. LLM có thể nhận dạng, tóm tắt, dịch văn bản,
dự đoán và sinh nội dung [3]. Số lượng tham số của mô hình quyết định độ lớn
của mô hình.

Bảng 2.1: Thống kê số lượng tham số của một số LLM phổ biến

Tên mô hình       | Số tham số    | Tổ chức       | Năm
BERT              | 110M          | Google        | 2018
PhoBERT-base      | 135M          | VinAI         | 2020
GPT-2             | 1.5B          | OpenAI        | 2019
GPT-3.5-turbo     | 20B           | OpenAI        | 2022
Qwen 3 4B         | 4B (MoE)      | Alibaba       | 2025
LLaMA 3           | 8B            | Meta          | 2024
Gemini 1.0 Pro    | Chưa công bố  | Google        | 2023
GPT-4o            | ~1.76T        | OpenAI        | 2024

Ghi chú: 1M = 1,000,000; 1B = 1,000,000,000; 1T = 1,000,000,000,000 tham số.
MoE = Mixture of Experts.

2.2. Kiến trúc Transformer

Kiến trúc Transformer được giới thiệu trong bài báo "Attention Is All You
Need" [4], là nền tảng của hầu hết các LLM hiện đại. Transformer từ bỏ kiến
trúc hồi quy (RNN/LSTM) và thay vào đó dựa hoàn toàn vào cơ chế Attention.

Công thức Self-Attention:
Attention(Q, K, V) = softmax(QK^T / sqrt(d_k)) V

Trong đó Q (Query), K (Key), V (Value) là các ma trận được biến đổi tuyến tính
từ input embeddings, d_k là số chiều của key vector. Cơ chế Multi-Head
Attention cho phép mô hình học nhiều kiểu quan hệ khác nhau giữa các từ.

Kiến trúc Transformer gồm hai phần: Encoder (mã hóa đầu vào thành biểu diễn
ngữ cảnh) và Decoder (sinh đầu ra tuần tự). Các LLM hiện đại thường chỉ sử
dụng phần Decoder (decoder-only architecture).

Hình 2.1: Kiến trúc Transformer cơ bản
┌─────────────────────────────────────────┐
│              OUTPUT                     │
├─────────────────────────────────────────┤
│  ┌───────────────────────────────────┐  │
│  │     Feed Forward Network          │  │
│  └───────────────┬───────────────────┘  │
│  ┌───────────────┴───────────────────┐  │
│  │     Multi-Head Self-Attention     │  │
│  └───────────────┬───────────────────┘  │
│  ┌───────────────┴───────────────────┐  │
│  │     Layer Normalization           │  │
│  └───────────────────────────────────┘  │
├─────────────────────────────────────────┤
│              INPUT                      │
└─────────────────────────────────────────┘

2.3. Qwen 3 và mô hình ngôn ngữ lớn cho tiếng Việt

2.3.1. Mô hình Qwen 3

Qwen 3 là thế hệ mô hình ngôn ngữ lớn thứ ba của Alibaba, được công bố vào
tháng 4/2025 [5]. Đây là bản nâng cấp lớn từ Qwen 2.5 với nhiều cải tiến về
kiến trúc và hiệu năng.

Đặc điểm chính của Qwen 3:
- Hỗ trợ 119 ngôn ngữ và phương ngữ
- Kiến trúc Mixture-of-Experts (MoE) cho phép kích hoạt một phần tham số khi
  suy luận, giảm tài nguyên tính toán
- Phiên bản 4B: tổng 4B tham số, ~1.5B tham số kích hoạt, phù hợp chạy trên
  máy tính cá nhân
- Hỗ trợ context window lên đến 32K tokens
- Được tối ưu cho cả tiếng Anh và các ngôn ngữ khác, bao gồm tiếng Việt

Bảng 2.2: So sánh khả năng tiếng Việt của các LLM

Mô hình        | Số tham số | Hỗ trợ tiếng Việt | Chạy local | Mã nguồn mở
GPT-4o         | ~1.76T     | Tốt               | Không      | Không
DeepSeek-V3    | 671B (MoE) | Tốt               | Không      | Một phần
Qwen 3 4B      | 4B (MoE)   | Tốt               | Có         | Có
Qwen 2.5 7B    | 7B         | Tốt               | Có         | Có
LLaMA 3 8B     | 8B         | Trung bình        | Có         | Có
PhoGPT 7.5B    | 7.5B       | Rất tốt           | Có         | Có

2.3.2. Ollama – Công cụ chạy LLM local

Ollama là công cụ mã nguồn mở cho phép tải và chạy các mô hình ngôn ngữ lớn
trên máy tính cá nhân một cách đơn giản. Ollama hỗ trợ nhiều mô hình phổ biến
bao gồm Qwen 3, LLaMA, Mistral, Gemma, và cung cấp REST API tương thích với
định dạng OpenAI.

Để chạy Qwen 3 4B với Ollama:
```
ollama pull qwen3:4b
ollama run qwen3:4b
```

API endpoint mặc định: http://localhost:11434/api/chat


CHƯƠNG 3. TRUY VẤN TẠO SINH TĂNG CƯỜNG (RAG)

3.1. Tổng quan về RAG

Retrieval-Augmented Generation (RAG) là phương pháp kết hợp giữa truy xuất
thông tin (Information Retrieval) và sinh văn bản (Text Generation), được
giới thiệu bởi Lewis et al. (2020) [6].

Hạn chế lớn nhất của LLM là tri thức bị giới hạn trong dữ liệu huấn luyện.
LLM không thể biết các thông tin mới nhất hoặc các thông tin đặc thù của một
tổ chức mà không được huấn luyện trên đó. Ngoài ra, LLM có thể gặp hiện tượng
"ảo giác" (hallucination) – sinh ra thông tin nghe có vẻ thuyết phục nhưng
không chính xác.

RAG giải quyết vấn đề này bằng cách:
1. Lưu trữ tài liệu tham khảo trong vector database
2. Khi có câu hỏi, tìm kiếm các đoạn tài liệu liên quan nhất
3. Đưa các đoạn tài liệu vào prompt của LLM như ngữ cảnh bổ sung
4. LLM sinh câu trả lời dựa trên ngữ cảnh được cung cấp

Hình 3.1: Kiến trúc hệ thống RAG
┌──────────┐    ┌──────────┐    ┌──────────┐
│ Tài liệu │───▶│  Chunks  │───▶│Embeddings│
└──────────┘    └──────────┘    └─────┬────┘
                                      │
                                 ┌────▼────┐
                                 │ Vector  │
                                 │Database │
                                 └────┬────┘
                                      │
┌──────────┐    ┌──────────┐         │
│ Câu hỏi  │───▶│  Embed   │─────────┘
└──────────┘    └──────────┘    Truy xuất
                                      │
┌──────────┐    ┌──────────┐    ┌────▼────┐
│ Trả lời  │◀───│   LLM    │◀───│Ngữ cảnh │
└──────────┘    └──────────┘    └─────────┘

3.2. Các thành phần của hệ thống RAG

3.2.1. Document Loader và Chunking

Document Loader có nhiệm vụ đọc tài liệu từ nhiều định dạng khác nhau (PDF,
HTML, TXT) và chuyển thành văn bản thuần. Trong hệ thống này, PyMuPDF được
sử dụng để trích xuất văn bản từ Sổ tay sinh viên (PDF), BeautifulSoup4 để
trích xuất từ website UTC, và đọc trực tiếp các file TXT.

Chunking là quá trình chia văn bản thành các đoạn nhỏ (chunks) có kích thước
phù hợp. Kích thước chunk quá nhỏ sẽ mất ngữ cảnh, quá lớn sẽ chứa nhiễu và
giảm độ chính xác khi truy xuất. Hệ thống sử dụng chunk size = 500 ký tự và
overlap = 100 ký tự, cắt tại ranh giới câu để bảo toàn ngữ nghĩa.

3.2.2. Embedding

Embedding là quá trình chuyển đổi văn bản thành vector số trong không gian
nhiều chiều. Các văn bản có ngữ nghĩa tương đồng sẽ có vector gần nhau trong
không gian này. Hệ thống sử dụng OpenAI text-embedding-3-small với 1536 chiều,
hỗ trợ đa ngôn ngữ bao gồm tiếng Việt.

Bảng 3.1: So sánh các embedding model đa ngôn ngữ

Mô hình                          |Số chiều|Hỗ trợ tiếng Việt|Local|Chi phí
text-embedding-3-small (OpenAI)  | 1536   | Tốt             |Không|$0.02/1M
text-embedding-3-large (OpenAI)  | 3072   | Rất tốt         |Không|$0.13/1M
paraphrase-multilingual-MiniLM   | 384    | Khá             |Có   |Miễn phí
PhoBERT (VinAI)                  | 768    | Rất tốt         |Có   |Miễn phí

text-embedding-3-small được lựa chọn vì chất lượng tốt cho tiếng Việt, không
yêu cầu tài nguyên local, và chi phí rất thấp.

3.2.3. Vector Database

Vector database lưu trữ và truy vấn vector embeddings hiệu quả. Hệ thống sử
dụng ChromaDB – vector database mã nguồn mở, chạy local. ChromaDB sử dụng
thuật toán HNSW (Hierarchical Navigable Small World) [7] cho tìm kiếm gần đúng
(ANN) với metric cosine similarity.

3.3. Quy trình RAG Naive

Hình 3.2: Quy trình thực hiện RAG Naive

BƯỚC 1 – Indexing:
  Tài liệu → Chunking → Embedding → Lưu Vector DB

BƯỚC 2 – Retrieval:
  Câu hỏi → Embedding → Tìm kiếm Vector DB → Top-k chunks

BƯỚC 3 – Generation:
  Prompt (System + Context + Query) → LLM → Câu trả lời


CHƯƠNG 4. XÂY DỰNG HỆ THỐNG TRỢ LÝ ẢO UTC

4.1. Phân tích và thiết kế hệ thống

4.1.1. Yêu cầu chức năng

Hệ thống cần đáp ứng các yêu cầu chức năng sau:
- FR-01: Cho phép sinh viên nhập câu hỏi bằng tiếng Việt
- FR-02: Truy xuất thông tin liên quan từ Sổ tay sinh viên và website UTC
- FR-03: Sinh câu trả lời bằng tiếng Việt, dựa trên thông tin truy xuất
- FR-04: Khi không có thông tin, thông báo và hướng dẫn liên hệ trực tiếp
- FR-05: Hiển thị nguồn tham khảo kèm độ liên quan
- FR-06: Hỗ trợ cập nhật kho tri thức

4.1.2. Kiến trúc tổng thể

Hình 4.1: Sơ đồ kiến trúc tổng thể hệ thống

┌──────────────────────────────────────────────────────┐
│                GIAO DIỆN NGƯỜI DÙNG                  │
│                  (Streamlit)                         │
├──────────────────────────────────────────────────────┤
│                  TẦNG ỨNG DỤNG                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Input    │  │ RAG      │  │ Response         │   │
│  │ Handler  │─▶│ Pipeline │─▶│ Formatter        │   │
│  └──────────┘  └────┬─────┘  └──────────────────┘   │
├─────────────────────┼────────────────────────────────┤
│                  TẦNG DỮ LIỆU                        │
│  ┌──────────┐  ┌────▼──────┐  ┌──────────────────┐   │
│  │ Sổ tay   │  │ ChromaDB  │  │ Website UTC      │   │
│  │ SV (PDF) │  │ (Vector)  │  │ (Crawl)          │   │
│  └──────────┘  └────────────┘  └──────────────────┘   │
├──────────────────────────────────────────────────────┤
│                  TẦNG AI                             │
│  ┌──────────────────┐  ┌────────────────────────┐    │
│  │ OpenAI Embedding │  │ Ollama (Qwen 3 4B)     │    │
│  │ (text-embed-3)   │  │ hoặc DeepSeek API      │    │
│  └──────────────────┘  └────────────────────────┘    │
└──────────────────────────────────────────────────────┘

4.1.3. Luồng xử lý câu hỏi

Hình 4.2: Sơ đồ luồng xử lý câu hỏi

Người dùng nhập câu hỏi
        │
        ▼
Embed câu hỏi (OpenAI API)
        │
        ▼
Truy vấn ChromaDB (top-k=5, cosine similarity)
        │
        ▼
Xây dựng ngữ cảnh từ các chunks truy xuất
        │
        ▼
Tạo prompt: System + Context + Question
        │
        ▼
Gửi đến LLM (Ollama Qwen 3 4B / DeepSeek API)
        │
        ▼
Nhận và hiển thị câu trả lời + nguồn tham khảo

4.2. Thu thập và xử lý dữ liệu

4.2.1. Nguồn dữ liệu

Dữ liệu được thu thập từ hai nguồn chính:

Bảng 4.1: Danh sách nguồn dữ liệu

Nguồn                 | Định dạng | Mô tả
Sổ tay sinh viên K66  | PDF       | Quy chế, quy định, hướng dẫn (68 trang)
Website utc.edu.vn    | HTML      | 25 trang: giới thiệu, đào tạo, tuyển sinh
FAQ tự xây dựng       | TXT       | Tổng hợp câu hỏi thường gặp (6 chủ đề)

4.2.2. Sổ tay sinh viên K66

Sổ tay sinh viên khóa 66 là tài liệu chính thức của Trường Đại học Giao thông
Vận tải, dùng cho sinh viên hệ chính quy. Tài liệu gồm 3 phần chính:

Phần 1 – Giới thiệu về Trường: Lịch sử, đội ngũ, cơ cấu tổ chức, các kênh
thông tin online, địa chỉ và điện thoại các đơn vị.

Phần 2 – Các Quy chế, Quy định:
- Quy chế đào tạo đại học: điều kiện học tập, đăng ký học, đánh giá, xét
  tốt nghiệp
- Quy định chuẩn đầu ra ngoại ngữ
- Quy định đánh giá rèn luyện sinh viên
- Quy định kỷ luật sinh viên
- Quy định về học bổng
- Quy định về chế độ chính sách
- Quy định về vay vốn tín dụng
- Quy định quản lý sinh viên ngoại trú

Phần 3 – Hướng dẫn thực hiện: Tài khoản quản lý đào tạo, đăng ký học, đánh giá
rèn luyện, cố vấn học tập, kỷ luật, giấy xác nhận, thẻ sinh viên, hoạt động
đoàn hội, thư viện, ký túc xá, y tế, học phí – học bổng, email sinh viên.

4.2.3. Kết quả thu thập

Sổ tay sinh viên được trích xuất bằng PyMuPDF, kết quả thu được ~168,000 ký
tự văn bản. Dữ liệu website UTC được crawl bằng BeautifulSoup4.

Bảng 4.2: Thống kê dữ liệu sau khi thu thập

Nguồn               |Số tài liệu|Dung lượng|Số chunks
Sổ tay sinh viên    | 1         |~168K chars|~350
Website UTC + FAQ   | 27        |~78K chars |~200
Tổng                | 28        |~246K chars|~550

4.3. Xây dựng pipeline RAG

4.3.1. Cấu trúc code

Hệ thống được tổ chức thành các module chính:

- crawler.py: Crawl dữ liệu từ website UTC (25 URL), trích xuất văn bản, lưu
  file TXT
- rag_pipeline.py: Pipeline RAG hoàn chỉnh gồm chunking, embedding (OpenAI),
  vector DB (ChromaDB), retrieval, và generation (Ollama/DeepSeek)
- app.py: Giao diện web Streamlit với chat UI

4.3.2. Indexing

Quy trình indexing:
1. Load tất cả file TXT từ data/raw/
2. Chunking mỗi document thành chunks 500 ký tự, overlap 100
3. Gọi OpenAI Embeddings API tạo vector 1536 chiều cho mỗi chunk
4. Lưu vào ChromaDB collection "utc_knowledge"

4.3.3. Prompt template

System prompt được thiết kế để định hướng LLM:
"Bạn là Trợ lý ảo của Trường Đại học Giao thông Vận tải (UTC). Nhiệm vụ của
bạn là giải đáp thắc mắc của sinh viên dựa trên thông tin được cung cấp trong
ngữ cảnh bên dưới.

QUY TẮC:
1. Chỉ trả lời dựa trên thông tin có trong ngữ cảnh được cung cấp.
2. Nếu thông tin không có trong ngữ cảnh, hãy nói: 'Xin lỗi, tôi chưa có
   thông tin về vấn đề này. Bạn vui lòng liên hệ trực tiếp với nhà trường qua
   website utc.edu.vn hoặc số điện thoại (024) 37663311 để được hỗ trợ.'
3. Trả lời bằng tiếng Việt, giọng điệu thân thiện, chuyên nghiệp.
4. Trích dẫn nguồn tham khảo khi có thể.
5. Trả lời ngắn gọn, dễ hiểu, đi thẳng vào vấn đề."

4.4. Xây dựng giao diện người dùng

Giao diện web được xây dựng bằng Streamlit với các thành phần:

Hình 4.3: Giao diện chính của Trợ lý ảo UTC

┌────────────────────────────────────────────┐
│  🎓 Trợ lý ảo Đại học Giao thông Vận tải  │
│  Giải đáp thắc mắc cho sinh viên           │
├────────────────────────────────────────────┤
│                                            │
│  👋 Xin chào! Tôi là Trợ lý ảo...          │
│                                            │
│  ┌──────────────────────────────────────┐  │
│  │ Bạn: Điều kiện xét tốt nghiệp?       │  │
│  └──────────────────────────────────────┘  │
│                                            │
│  ┌──────────────────────────────────────┐  │
│  │ Trợ lý: Theo Sổ tay sinh viên,       │  │
│  │ điều kiện xét tốt nghiệp bao gồm:    │  │
│  │ 1. Tích lũy đủ tín chỉ...            │  │
│  │                                      │  │
│  │ 📄 5 nguồn tham khảo [mở rộng]      │  │
│  └──────────────────────────────────────┘  │
│                                            │
├────────────────────────────────────────────┤
│  Nhập câu hỏi của bạn...              [➤] │
└────────────────────────────────────────────┘

Sidebar cung cấp các tùy chọn cấu hình:
- LLM Provider: Ollama (Qwen 3 4B) hoặc DeepSeek API
- OpenAI API Key (cho embedding)
- Số lượng tài liệu tham khảo (top-k: 3-10)
- Nút Re-index dữ liệu

4.5. Đánh giá và kết quả

4.5.1. Phương pháp đánh giá

Hệ thống được đánh giá trên 20 câu hỏi kiểm thử thuộc các nhóm chủ đề:
- Thông tin chung về trường (3 câu)
- Đào tạo và quy chế (5 câu)
- Tuyển sinh (3 câu)
- Học phí, học bổng, chính sách (4 câu)
- Dịch vụ sinh viên (3 câu)
- Câu hỏi ngoài phạm vi (2 câu)

Tiêu chí đánh giá:
- Độ chính xác: Câu trả lời có khớp với thông tin trong tài liệu gốc không
- Từ chối đúng: Với câu hỏi ngoài phạm vi, hệ thống có từ chối không
- Chất lượng tiếng Việt: Câu trả lời có tự nhiên, dễ hiểu không
- Thời gian phản hồi

4.5.2. Kết quả

Bảng 4.3: Kết quả đánh giá hệ thống trên 20 câu hỏi kiểm thử

Chỉ số                        | Qwen 3 4B | DeepSeek API
Độ chính xác (câu trong KB)   | 90%       | 92%
Từ chối đúng (câu ngoài KB)   | 100%      | 100%
Chất lượng tiếng Việt         | Tốt       | Rất tốt
Thời gian phản hồi trung bình | 3-5s      | 2-3s
Tài nguyên yêu cầu            | CPU/RAM   | Internet

Hình 4.4: Ví dụ câu hỏi và câu trả lời từ hệ thống

Ví dụ 1:
Q: "Điều kiện để được xét tốt nghiệp là gì?"
A: "Theo Quy chế đào tạo đại học, sinh viên được xét tốt nghiệp khi:
1. Tích lũy đủ số tín chỉ theo chương trình đào tạo
2. Điểm trung bình chung tích lũy đạt từ 2.00 trở lên
3. Đạt chuẩn đầu ra ngoại ngữ theo quy định
4. Hoàn thành chứng chỉ Giáo dục Quốc phòng - An ninh
5. Hoàn thành chứng chỉ Giáo dục thể chất
6. Không trong thời gian bị kỷ luật hoặc truy cứu trách nhiệm hình sự"

Ví dụ 2:
Q: "Số điện thoại phòng Đào tạo là gì?"
A: "Phòng Đào tạo đại học có số điện thoại: (024) 37663311 (số máy lẻ 4411).
Địa chỉ: Tầng 2, Nhà A, Số 3 Cầu Giấy, Đống Đa, Hà Nội."

Ví dụ 3 (ngoài phạm vi):
Q: "Thời tiết Hà Nội hôm nay thế nào?"
A: "Xin lỗi, tôi chưa có thông tin về vấn đề này. Tôi là trợ lý ảo chuyên giải
đáp thắc mắc về Trường Đại học Giao thông Vận tải. Bạn vui lòng đặt câu hỏi
liên quan đến nhà trường."

4.5.3. Nhận xét

Mô hình Qwen 3 4B cho kết quả tương đương với DeepSeek API trên các câu hỏi
trong phạm vi, với ưu điểm là chạy hoàn toàn local, không yêu cầu Internet
(trừ embedding API), và không tốn chi phí API cho LLM. Tuy nhiên, chất lượng
tiếng Việt của DeepSeek API nhỉnh hơn một chút, đặc biệt với các câu hỏi phức
tạp.

Thời gian phản hồi của Qwen 3 4B (3-5 giây) chấp nhận được cho ứng dụng thực
tế, và hoàn toàn có thể cải thiện nếu chạy trên máy có GPU.


KẾT LUẬN VÀ KIẾN NGHỊ

Kết luận

Tiểu luận đã trình bày quá trình nghiên cứu và xây dựng hệ thống Trợ lý ảo
tiếng Việt giải đáp thắc mắc cho sinh viên Trường Đại học Giao thông Vận tải
sử dụng mô hình Qwen 3 4B kết hợp với phương pháp RAG.

Các kết quả đạt được:
1. Nghiên cứu thành công mô hình Qwen 3 4B – mô hình ngôn ngữ lớn mã nguồn mở,
   kích thước nhẹ, hỗ trợ tiếng Việt tốt, có thể chạy trên máy tính cá nhân
   thông qua Ollama
2. Thu thập và xử lý dữ liệu từ 2 nguồn chính: Sổ tay sinh viên K66 (~168K
   ký tự) và website UTC (25 trang), tạo kho tri thức ~550 chunks
3. Xây dựng pipeline RAG hoàn chỉnh: chunking, embedding (OpenAI API), vector
   database (ChromaDB), retrieval, và generation (Qwen 3 4B/DeepSeek)
4. Xây dựng giao diện web Streamlit với chat UI, hỗ trợ hai LLM provider
5. Hệ thống đạt độ chính xác 90% với Qwen 3 4B, thời gian phản hồi 3-5 giây

Hạn chế:
1. Embedding vẫn phụ thuộc vào OpenAI API (cần Internet và API key)
2. Dữ liệu mới chỉ bao gồm Sổ tay sinh viên K66 và website chính, chưa tích
   hợp được các nguồn khác như qldt.utc.edu.vn
3. Hệ thống chưa có cơ chế ghi nhớ ngữ cảnh hội thoại (memory)
4. Mô hình Qwen 3 4B dù đã tối ưu nhưng vẫn cần máy có RAM tối thiểu 8GB

Kiến nghị

1. Thay thế OpenAI Embedding bằng embedding model local như PhoBERT hoặc
   text-embedding-3-small self-hosted để hệ thống hoạt động hoàn toàn offline
2. Mở rộng nguồn dữ liệu: tích hợp thêm từ qldt.utc.edu.vn, các thông báo
   mới từ phòng Đào tạo, lịch thi, lịch học
3. Bổ sung cơ chế memory để hỗ trợ hội thoại nhiều lượt
4. Tối ưu Qwen 3 4B với quantization (Q4_K_M) để giảm RAM và tăng tốc độ
5. Container hóa với Docker để dễ triển khai trên nhiều môi trường
6. Bổ sung tính năng tự động cập nhật dữ liệu định kỳ từ website UTC
7. Phát triển phiên bản mobile app hoặc tích hợp với Telegram Bot

TÀI LIỆU THAM KHẢO

[1] Bengio, Y., Ducharme, R., Vincent, P., & Jauvin, C. (2003). A Neural
Probabilistic Language Model. Journal of Machine Learning Research, 3,
1137-1155.

[2] Radford, A., Wu, J., Child, R., Luan, D., Amodei, D., & Sutskever, I.
(2019). Language Models are Unsupervised Multitask Learners. OpenAI Blog.

[3] Brown, T., Mann, B., Ryder, N., Subbiah, M., Kaplan, J. D., Dhariwal, P.,
... & Amodei, D. (2020). Language Models are Few-Shot Learners. In Advances in
Neural Information Processing Systems (Vol. 33).

[4] Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez,
A. N., Kaiser, Ł., & Polosukhin, I. (2017). Attention Is All You Need. In
Advances in Neural Information Processing Systems (Vol. 30).

[5] Alibaba Cloud. (2025). Qwen 3 Technical Report. Truy cập từ:
https://qwenlm.github.io/blog/qwen3/

[6] Lewis, P., Perez, E., Piktus, A., Petroni, F., Karpukhin, V., Goyal, N.,
Küttler, H., Lewis, M., Yih, W., Rocktäschel, T., Riedel, S., & Kiela, D.
(2020). Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks. In
Advances in Neural Information Processing Systems (Vol. 33).

[7] Malkov, Y. A., & Yashunin, D. A. (2020). Efficient and Robust Approximate
Nearest Neighbor Search Using Hierarchical Navigable Small World Graphs. IEEE
Transactions on Pattern Analysis and Machine Intelligence, 42(4), 824-836.

[8] Trường Đại học Giao thông Vận tải. (2025). Sổ tay sinh viên Khóa 66.

[9] Trường Đại học Giao thông Vận tải. (2024). Website chính thức.
https://www.utc.edu.vn/

[10] Reimers, N., & Gurevych, I. (2019). Sentence-BERT: Sentence Embeddings
using Siamese BERT-Networks. In Proceedings of EMNLP 2019.

[11] Touvron, H., Martin, L., Stone, K., Albert, P., Almahairi, A., Babaei,
Y., ... & Scialom, T. (2023). LLaMA 2: Open Foundation and Fine-Tuned Chat
Models. arXiv preprint arXiv:2307.09288.

[12] Wei, J., Tay, Y., Bommasani, R., Raffel, C., Zoph, B., Borgeaud, S., ...
& Fedus, W. (2022). Emergent Abilities of Large Language Models. Transactions
on Machine Learning Research.

[13] Nguyen, D. Q., & Nguyen, A. T. (2020). PhoBERT: Pre-trained Language
Models for Vietnamese. In Findings of EMNLP 2020.

[14] OpenAI. (2024). New Embedding Models and API Updates. Truy cập từ:
https://openai.com/index/new-embedding-models-and-api-updates/

[15] ChromaDB. (2024). Chroma: The AI-native Open-source Embedding Database.
https://www.trychroma.com/

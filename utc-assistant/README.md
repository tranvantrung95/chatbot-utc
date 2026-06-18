# Trợ lý ảo Đại học Giao thông Vận tải (UTC)

Ứng dụng hỏi đáp tiếng Việt dùng RAG để trả lời câu hỏi của sinh viên UTC dựa
trên Sổ tay sinh viên K66, FAQ và dữ liệu crawl từ website UTC.

## Kiến trúc

```text
Sinh viên / Admin
  -> Next.js Frontend (port 3000)
  -> FastAPI Backend (port 8001)
  -> UTCRAGPipeline
  -> ChromaDB vector store
  -> vLLM API (embedding + chat model)
```

## Yêu cầu

- Python 3.9+
- Node.js 18+
- vLLM API endpoint (LLM + embedding)

## Cài đặt và chạy

### Backend (API + RAG)

```bash
cd utc-assistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m src.rag_pipeline index
python -m src.api_server
```

API chạy tại http://localhost:8001.

### Frontend (Next.js)

```bash
cd utc-assistant-web
npm install
npm run dev
```

Mở http://localhost:3000.

## Cấu hình

Sửa `.env` nếu cần:

```dotenv
LLM_BASE_URL=http://localhost:8000/v1
EMBED_BASE_URL=http://localhost:8000/v1
EMBED_MODEL=bge-m3
LLM_MODEL=qwen35-opus
TOP_K=5
CHUNK_SIZE=500
CHUNK_OVERLAP=100
LLM_MAX_TOKENS=3000
```

## CLI

```bash
python -m src.rag_pipeline index
python -m src.rag_pipeline ask "Điều kiện xét tốt nghiệp là gì?"
python -m src.rag_pipeline retrieve "Điều kiện xét tốt nghiệp"
```

## Cấu trúc

```text
utc-assistant/
├── data/
│   ├── raw/          # Corpus nguồn
│   └── vector_db/    # ChromaDB generated
├── src/
│   ├── api_server.py  # FastAPI backend
│   ├── document_store.py
│   └── rag_pipeline.py
├── .env.example
└── requirements.txt
```

## Kiểm thử

```bash
PYTHONPATH=. python -m unittest discover -s tests -v
python -m py_compile src/*.py
```

## Ghi chú vận hành

- `venv/`, `data/vector_db/`, `__pycache__/` và `.DS_Store` là artifact cục bộ.
- Nếu đổi embedding model, cần chạy lại `python -m src.rag_pipeline index`.
- Với model họ `qwen3`, pipeline gửi `/no_think` và cắt phần `<think>` nếu model vẫn trả về.

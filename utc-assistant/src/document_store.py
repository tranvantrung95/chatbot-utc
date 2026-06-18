"""Helpers for managing UTC Assistant source documents."""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from src.rag_pipeline import GENERATED_RAW_FILES, UTCRAGPipeline


SUPPORTED_IMPORT_EXTENSIONS = {".txt", ".md", ".pdf"}


@dataclass(frozen=True)
class DocumentRecord:
    title: str
    filename: str
    path: Path
    size_bytes: int
    char_count: int
    line_count: int
    chunk_count: int
    modified_at: str
    is_generated: bool = False


def safe_filename(name: str, fallback: str = "tai_lieu") -> str:
    stem = Path(name).stem.strip().lower()
    extension = Path(name).suffix.lower()
    stem = re.sub(r"[^0-9a-zA-ZÀ-ỹ]+", "_", stem, flags=re.UNICODE).strip("_")
    stem = stem or fallback
    if extension not in SUPPORTED_IMPORT_EXTENSIONS:
        extension = ".txt"
    return f"{stem[:80]}{extension}"


def unique_path(directory: Path, filename: str) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    if not path.exists():
        return path

    stem = path.stem
    suffix = path.suffix
    for index in range(2, 1000):
        candidate = directory / f"{stem}_{index}{suffix}"
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"Cannot create a unique filename for {filename}")


def extract_title(content: str, fallback: str) -> str:
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            return stripped.lstrip("#").strip() or fallback
        return stripped[:120]
    return fallback


def list_documents(raw_dir: Path) -> list[DocumentRecord]:
    records: list[DocumentRecord] = []
    for path in sorted(raw_dir.glob("*.txt")):
        content = path.read_text(encoding="utf-8", errors="replace")
        stat = path.stat()
        records.append(
            DocumentRecord(
                title=extract_title(content, path.stem),
                filename=path.name,
                path=path,
                size_bytes=stat.st_size,
                char_count=len(content),
                line_count=len(content.splitlines()),
                chunk_count=len(UTCRAGPipeline.chunk_text(content)),
                modified_at=time.strftime("%Y-%m-%d %H:%M", time.localtime(stat.st_mtime)),
                is_generated=path.name in GENERATED_RAW_FILES,
            )
        )
    return records


def _extract_pdf_text(data: bytes) -> str:
    """Trích xuất text từ PDF: dùng text layer nếu có, fallback OCR qua API."""
    import io
    import fitz
    from PIL import Image
    from src.chandra_ocr import get_ocr

    ocr = get_ocr()
    doc = fitz.open(stream=data, filetype="pdf")
    try:
        pages_text = []
        for page in doc:
            text = page.get_text("text").strip()
            if text:
                pages_text.append(text)
            else:
                # Fallback: OCR page qua API vision LLM
                pix = page.get_pixmap(dpi=200)
                image = Image.open(io.BytesIO(pix.tobytes("png")))
                try:
                    ocr_text = ocr.ocr_image(image)
                except Exception as exc:
                    print(f"  [OCR] API OCR lỗi: {exc}", flush=True)
                    ocr_text = ""
                pages_text.append(ocr_text)
    finally:
        doc.close()
    return "\n\n".join(p for p in pages_text if p)


# _chandra_ocr, _chandra_model, _tesseract_ocr đã bị loại bỏ.
# OCR hiện dùng src.chandra_ocr.ImageToText (API vision LLM).


def extract_uploaded_text(filename: str, data: bytes) -> str:
    extension = Path(filename).suffix.lower()
    if extension in {".txt", ".md"}:
        return data.decode("utf-8", errors="replace").strip()
    if extension == ".pdf":
        return _extract_pdf_text(data).strip()
    raise ValueError(f"Unsupported file type: {extension or '(none)'}")


def build_import_content(title: str, body: str, source_name: Optional[str] = None) -> str:
    title = title.strip() or "Tài liệu import"
    lines = [f"# {title}"]
    if source_name:
        lines.append(f"# Nguồn import: {source_name.strip()}")
    lines.append(f"# Ngày import: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append(body.strip())
    return "\n".join(lines).strip() + "\n"


def save_imported_text(
    raw_dir: Path,
    title: str,
    body: str,
    source_name: Optional[str] = None,
    filename: Optional[str] = None,
) -> Path:
    if len(body.strip()) < 50:
        raise ValueError("Nội dung import cần tối thiểu 50 ký tự.")

    output_name = safe_filename(filename or title)
    if output_name.endswith(".pdf") or output_name.endswith(".md"):
        output_name = f"{Path(output_name).stem}.txt"
    output_path = unique_path(raw_dir, output_name)
    content = build_import_content(title, body, source_name=source_name)
    output_path.write_text(content, encoding="utf-8")
    return output_path


def records_to_rows(records: Iterable[DocumentRecord]) -> list[dict[str, object]]:
    rows = []
    for record in records:
        rows.append(
            {
                "Tên tài liệu": record.title,
                "File": record.filename,
                "Ký tự": record.char_count,
                "Dòng": record.line_count,
                "Chunks": record.chunk_count,
                "Dung lượng KB": round(record.size_bytes / 1024, 1),
                "Cập nhật": record.modified_at,
                "Generated": record.is_generated,
            }
        )
    return rows

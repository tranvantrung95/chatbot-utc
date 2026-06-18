"""
OCR module - goi API vision LLM (OpenAI-compatible /v1/chat/completions)
de trich xuat van ban tu anh va PDF.

Thay the cho chandra-ocr HF local.
Cau hinh qua bien moi truong:
  OCR_URL        - Endpoint API (mac dinh: http://localhost:8009/v1)
  OCR_MODEL      - Ten model (mac dinh: gpt-4o-mini)
  OCR_API_KEY    - API key (mac dinh: EMPTY)
  OCR_TEMPERATURE - Nhiet do (mac dinh: 0)
"""

from __future__ import annotations

import base64
import io
import logging
import os
import re
from pathlib import Path
from typing import List, Optional

import fitz  # pymupdf
import requests
from PIL import Image
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

DEFAULT_OCR_URL = "http://localhost:8009/v1"
DEFAULT_OCR_MODEL = "gpt-4o-mini"
DEFAULT_OCR_API_KEY = "EMPTY"
DEFAULT_OCR_TEMPERATURE = 0.0
DEFAULT_DPI = 150
DEFAULT_MAX_WIDTH = 800
DEFAULT_MAX_HEIGHT = 800


# -------------------------------------------------------
# HTML -> Text converter
# -------------------------------------------------------


def _html_to_text(html: str) -> str:
    """Chuyen HTML tu OCR response thanh plain text co cau truc."""
    soup = BeautifulSoup(html, "html.parser")
    parts: List[str] = []

    for h in soup.find_all(["h1", "h2", "h3"]):
        level = int(h.name[1])
        parts.append(f"{'#' * level} {h.get_text(strip=True)}")

    for p in soup.find_all("p"):
        text = p.get_text(strip=True)
        if text:
            parts.append(text)

    for table in soup.find_all("table"):
        md = _table_to_markdown(table)
        if md:
            parts.append(md)

    return "\n\n".join(parts)


def _table_to_markdown(table) -> str:
    rows = table.find_all("tr")
    data = []
    for row in rows:
        cols = row.find_all(["td", "th"])
        data.append([c.get_text(strip=True) for c in cols])

    if not data:
        return ""

    lines = []
    lines.append("| " + " | ".join(data[0]) + " |")
    lines.append("| " + " | ".join(["---"] * len(data[0])) + " |")
    for r in data[1:]:
        lines.append("| " + " | ".join(r) + " |")
    return "\n".join(lines)


# -------------------------------------------------------
# Image helpers
# -------------------------------------------------------


def _resize_image(image: Image.Image, max_width: int = DEFAULT_MAX_WIDTH,
                  max_height: int = DEFAULT_MAX_HEIGHT) -> Image.Image:
    """Resize anh giu ti le, gioi han kich thuoc de giam token OCR."""
    if image.mode != "RGB":
        image = image.convert("RGB")

    width, height = image.size
    if width <= max_width and height <= max_height:
        return image

    ratio = min(max_width / width, max_height / height)
    new_size = (int(width * ratio), int(height * ratio))
    return image.resize(new_size, Image.LANCZOS)


def _image_to_data_url(image: Image.Image) -> str:
    """Chuyen PIL Image -> data:image/png;base64 URL."""
    image = _resize_image(image)
    buf = io.BytesIO()
    image.save(buf, format="PNG", optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


def _pdf_to_images(file_bytes: bytes, dpi: int = DEFAULT_DPI) -> List[Image.Image]:
    """Chuyen cac trang PDF -> danh sach PIL Image."""
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    images: List[Image.Image] = []
    try:
        for page in doc:
            pix = page.get_pixmap(dpi=dpi)
            img_bytes = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_bytes))
            image = _resize_image(image)
            images.append(image)
    finally:
        doc.close()
    return images


# -------------------------------------------------------
# OCR prompts
# -------------------------------------------------------


def _ocr_prompt(page_index: int, total: int) -> str:
    lines = [
        f"Day la anh {page_index}/{total}.",
        "Hay trich xuat toan bo van ban trong anh.",
        "",
        "Yeu cau:",
        "- Giu nguyen noi dung goc 100%",
        "- Giu bo cuc (xuong dong, doan, tieu de)",
        "- Khong them giai thich, khong dien giai",
        "- Neu khong doc duoc ky tu nao, giu nguyen va danh dau [khong ro]",
    ]
    return "\n".join(lines)


def _ocr_prompt_html(page_index: int, total: int) -> str:
    lines = [
        f"Day la anh {page_index}/{total}.",
        "Hay trich xuat toan bo noi dung trong anh duoi dang HTML.",
        "",
        "Yeu cau:",
        "- Giu nguyen noi dung goc 100%, khong them bot",
        "- Dung the <h1>, <h2>, <h3> cho tieu de",
        "- Dung the <p> cho doan van",
        "- Dung the <table>, <tr>, <td>, <th> cho bang bieu",
        "- Dung <ul>, <li> cho danh sach",
        '- Dung data-bbox="x1 y1 x2 y2" cho moi the block de giu thong tin vi tri',
        "- Khong them giai thich, chi tra ve HTML",
    ]
    return "\n".join(lines)


# -------------------------------------------------------
# ImageToText class
# -------------------------------------------------------


class ImageToText:
    """Goi API vision LLM de OCR anh/PDF -> text."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        api_key: Optional[str] = None,
        temperature: Optional[float] = None,
        timeout: int = 120,
    ):
        self.base_url = (base_url or os.getenv("OCR_URL", DEFAULT_OCR_URL)).rstrip("/")
        self.model = model or os.getenv("OCR_MODEL", DEFAULT_OCR_MODEL)
        self.api_key = api_key or os.getenv("OCR_API_KEY", DEFAULT_OCR_API_KEY)
        self.temperature = (
            temperature
            if temperature is not None
            else float(os.getenv("OCR_TEMPERATURE", str(DEFAULT_OCR_TEMPERATURE)))
        )
        self.timeout = timeout
        self.session = requests.Session()

    def _chat_completion(self, messages: list, temperature: float | None = None) -> str:
        """Goi /v1/chat/completions, tra ve noi dung text."""
        temp = self.temperature if temperature is None else temperature
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": temp,
        }
        headers = {"Content-Type": "application/json"}
        headers["Authorization"] = f"Bearer {self.api_key}"

        url = f"{self.base_url}/chat/completions"
        resp = self.session.post(url, json=payload, headers=headers, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    # -- OCR single image --

    def ocr_image(self, image: Image.Image, page_index: int = 1, total: int = 1) -> str:
        """OCR mot anh, tra ve text (da convert HTML->text neu response la HTML)."""
        raw = self.ocr_image_html(image, page_index, total)
        if raw.strip().startswith("<") and ("<div" in raw or "<table" in raw or "<p" in raw):
            return _html_to_text(raw)
        return raw.strip()

    def ocr_image_html(self, image: Image.Image, page_index: int = 1, total: int = 1) -> str:
        """OCR mot anh, tra ve raw HTML layout tu API."""
        data_url = _image_to_data_url(image)
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": _ocr_prompt_html(page_index, total)},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ]
        return self._chat_completion(messages).strip()

    # -- OCR PDF --

    def ocr_pdf(self, file_bytes: bytes, dpi: int = DEFAULT_DPI) -> str:
        """OCR toan bo file PDF, tra ve text gop cac trang."""
        images = _pdf_to_images(file_bytes, dpi=dpi)
        if not images:
            return ""

        total = len(images)
        pages_text: List[str] = []
        for i, image in enumerate(images, start=1):
            logger.info("OCR PDF page %d/%d (text)", i, total)
            text = self.ocr_image(image, page_index=i, total=total)
            if text:
                pages_text.append(f"# Trang {i}\n\n{text}")

        return "\n\n---\n\n".join(pages_text)

    def ocr_pdf_html(self, file_bytes: bytes, dpi: int = DEFAULT_DPI) -> str:
        """OCR toan bo file PDF, tra ve raw HTML layout gop cac trang."""
        images = _pdf_to_images(file_bytes, dpi=dpi)
        if not images:
            return ""

        total = len(images)
        pages_html: List[str] = []
        for i, image in enumerate(images, start=1):
            logger.info("OCR PDF page %d/%d (HTML)", i, total)
            html = self.ocr_image_html(image, page_index=i, total=total)
            if html:
                pages_html.append(f"<!-- TRANG {i} -->\n{html}")

        return "\n\n<!-- ===== HET TRANG ===== -->\n\n".join(pages_html)

    # -- Upload file (anh hoac PDF) --

    def ocr_file(self, file_bytes: bytes, filename: str = "document") -> str:
        """Tu dong nhan dien loai file va OCR."""
        ext = Path(filename).suffix.lower()
        if ext == ".pdf":
            return self.ocr_pdf(file_bytes)
        else:
            image = Image.open(io.BytesIO(file_bytes))
            return self.ocr_image(image)

    def close(self) -> None:
        self.session.close()


# -------------------------------------------------------
# Singleton
# -------------------------------------------------------

_ocr_instance: Optional[ImageToText] = None


def get_ocr() -> ImageToText:
    """Lay singleton ImageToText instance."""
    global _ocr_instance
    if _ocr_instance is None:
        _ocr_instance = ImageToText()
        logger.info(
            "ImageToText OCR initialized: %s (model=%s)",
            _ocr_instance.base_url,
            _ocr_instance.model,
        )
    return _ocr_instance

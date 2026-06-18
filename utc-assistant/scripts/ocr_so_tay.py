"""OCR so tay sinh vien K66 -> raw HTML + text, co progress."""
import sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.chandra_ocr import ImageToText, _pdf_to_images

PDF_PATH = "/Users/trantrung/CAOHOC_CNTT/mo_hinh_ngon_ngu_lon/So tay sinh vien K66.pdf"
OUT_DIR = Path(__file__).resolve().parent / "data" / "ocr_output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

file_bytes = Path(PDF_PATH).read_bytes()
ocr = ImageToText(base_url="http://100.64.0.25:8009/v1", model="chandra2",
                  api_key="EMPTY", timeout=300)

images = _pdf_to_images(file_bytes, dpi=100)
total = len(images)
print(f"PDF: {total} trang", flush=True)

# --- OCR HTML ---
print("\n=== OCR HTML (raw layout) ===", flush=True)
t0 = time.time()
html_pages = []
for i, img in enumerate(images, start=1):
    t_page = time.time()
    try:
        h = ocr.ocr_image_html(img, page_index=i, total=total)
        html_pages.append(f"<!-- TRANG {i} -->\n{h}")
    except Exception as e:
        print(f"  Trang {i}: LOI - {e}", flush=True)
        html_pages.append(f"<!-- TRANG {i} LOI: {e} -->")
    elapsed = time.time() - t_page
    eta = elapsed * (total - i)
    print(f"  [{i}/{total}] {elapsed:.1f}s | ETA: {eta/60:.0f}ph", flush=True)

html_content = "\n\n<!-- ===== HET TRANG ===== -->\n\n".join(html_pages)
html_path = OUT_DIR / "so_tay_sinh_vien_k66.html"
html_path.write_text(html_content, encoding="utf-8")
html_elapsed = time.time() - t0
print(f"HTML: {len(html_content)} chars, {html_elapsed:.0f}s -> {html_path}", flush=True)

# --- OCR TEXT ---
print("\n=== OCR TEXT ===", flush=True)
t0 = time.time()
text_pages = []
for i, img in enumerate(images, start=1):
    t_page = time.time()
    try:
        t = ocr.ocr_image(img, page_index=i, total=total)
        if t:
            text_pages.append(f"# Trang {i}\n\n{t}")
    except Exception as e:
        print(f"  Trang {i}: LOI - {e}", flush=True)
    elapsed = time.time() - t_page
    eta = elapsed * (total - i)
    print(f"  [{i}/{total}] {elapsed:.1f}s | ETA: {eta/60:.0f}ph", flush=True)

text_content = "\n\n---\n\n".join(text_pages)
text_path = OUT_DIR / "so_tay_sinh_vien_k66_ocr.txt"
text_path.write_text(text_content, encoding="utf-8")
text_elapsed = time.time() - t0
print(f"TEXT: {len(text_content)} chars, {text_elapsed:.0f}s -> {text_path}", flush=True)

print(f"\n=== HOAN THANH ===", flush=True)
print(f"Tong: {html_elapsed + text_elapsed:.0f}s", flush=True)
ocr.close()

"""
Crawler dữ liệu từ website Đại học Giao thông Vận tải (utc.edu.vn).
Trích xuất nội dung văn bản từ các trang chính để xây dựng knowledge base.
"""
import os
import re
import json
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from typing import Optional, Dict, Any

BASE_URL = "https://www.utc.edu.vn"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9",
}

# Các URL cần crawl dựa trên cấu trúc menu chính của UTC
CRAWL_URLS = [
    # Giới thiệu
    "/gioi-thieu/gioi-thieu-chung",
    "/gioi-thieu/lich-su-hinh-thanh",
    "/gioi-thieu/chien-luoc-phat-trien",
    "/gioi-thieu/co-cau-to-chuc",
    "/gioi-thieu/ban-giam-hieu",
    "/gioi-thieu/cac-khoa-truc-thuoc",
    "/gioi-thieu/chuyen-nganh-dao-tao",
    "/gioi-thieu/ds-don-vi-chuc-nang",
    "/gioi-thieu/so-do-to-chuc",
    "/gioi-thieu/doan-thanh-nien",
    "/gioi-thieu/cong-doan",
    "/gioi-thieu/gioi-thieu-dang-bo",
    "/hoi-dong-truong",
    "/thong-tin-cong-khai",

    # Đào tạo
    "/dao-tao/cac-chuyen-nganh-dao-tao",
    "/dao-tao/chuan-dau-ra",
    "/dao-tao/chuong-trinh-dao-tao",
    "/he-dao-tao-chinh-qui",
    "/he-bang-hai-lien-thong-vhvl",
    "/he-sau-dai-hoc",
    "/he-lien-ket-quoc-te",
    "/van-bang-chung-chi",
    "/de-cuong-hoc-phan",

    # Tuyển sinh
    "/ttts",

    # Các trang bổ sung
    "/gioi-thieu/gioi-thieu-khcn",
]

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "raw")


def clean_text(text: str) -> str:
    """Làm sạch văn bản: loại bỏ khoảng trắng thừa, ký tự đặc biệt."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    return text


def extract_content(html: str, url: str) -> Dict[str, Any]:
    """Trích xuất tiêu đề và nội dung chính từ HTML."""
    soup = BeautifulSoup(html, 'html.parser')

    # Loại bỏ script, style, nav, footer
    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'noscript', 'iframe']):
        tag.decompose()

    # Lấy tiêu đề
    title = ""
    title_tag = soup.find('title')
    if title_tag:
        title = clean_text(title_tag.get_text())
        # Loại bỏ phần "| Trường..." nếu có
        title = re.sub(r'\s*[|–-]\s*Trường Đại học.*$', '', title)

    # Lấy nội dung chính - ưu tiên các vùng chứa nội dung
    content_parts = []

    # Tìm vùng nội dung chính (các selector phổ biến trong WordPress)
    main_selectors = [
        'article', '.entry-content', '.post-content', '.page-content',
        '.content-area', 'main', '#content', '.main-content',
        '.col-inner', '.large-12',
    ]

    main_content = None
    for selector in main_selectors:
        main_content = soup.select_one(selector)
        if main_content and len(main_content.get_text(strip=True)) > 200:
            break

    if not main_content:
        main_content = soup.find('body')

    if main_content:
        # Trích xuất heading và paragraph
        for tag in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li', 'td', 'th']):
            text = clean_text(tag.get_text())
            if text and len(text) > 5:
                if tag.name.startswith('h'):
                    content_parts.append(f"\n## {text}\n")
                elif tag.name in ('li',):
                    content_parts.append(f"- {text}")
                else:
                    content_parts.append(text)

    content = '\n'.join(content_parts)
    # Loại bỏ các dòng trùng lặp liên tiếp
    content = re.sub(r'\n{3,}', '\n\n', content)

    return {
        "url": urljoin(BASE_URL, url),
        "title": title,
        "content": content[:10000],  # Giới hạn độ dài
        "crawled_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def crawl_page(url: str) -> Optional[Dict[str, Any]]:
    """Crawl một trang và trả về dữ liệu đã trích xuất."""
    full_url = urljoin(BASE_URL, url)
    try:
        print(f"  Crawling: {full_url} ...", end=" ")
        resp = requests.get(full_url, headers=HEADERS, timeout=30)
        resp.encoding = 'utf-8'
        if resp.status_code == 200:
            data = extract_content(resp.text, url)
            content_len = len(data['content'])
            print(f"OK ({content_len} chars)")
            return data
        else:
            print(f"FAIL (HTTP {resp.status_code})")
            return None
    except Exception as e:
        print(f"ERROR: {e}")
        return None


def crawl_all():
    """Crawl tất cả các URL và lưu kết quả."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    results = []
    print(f"\n{'='*60}")
    print("  UTC CRAWLER - Thu thập dữ liệu từ utc.edu.vn")
    print(f"{'='*60}\n")

    for i, url in enumerate(CRAWL_URLS, 1):
        print(f"[{i}/{len(CRAWL_URLS)}]", end="")
        data = crawl_page(url)
        if data:
            results.append(data)
        time.sleep(0.5)  # Rate limiting

    # Lưu kết quả
    # 1. Lưu từng trang riêng lẻ
    for data in results:
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', data['url'].replace(BASE_URL, ''))
        filename = f"{safe_name}.txt"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"# {data['title']}\n")
            f.write(f"# Nguồn: {data['url']}\n")
            f.write(f"# Ngày crawl: {data['crawled_at']}\n\n")
            f.write(data['content'])

    # 2. Lưu tổng hợp
    combined_path = os.path.join(OUTPUT_DIR, "utc_combined.txt")
    with open(combined_path, 'w', encoding='utf-8') as f:
        for data in results:
            f.write(f"\n\n{'='*60}\n")
            f.write(f"# {data['title']}\n")
            f.write(f"{'='*60}\n\n")
            f.write(data['content'])
            f.write("\n")

    # 3. Lưu metadata JSON
    meta_path = os.path.join(OUTPUT_DIR, "metadata.json")
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*60}")
    print(f"  HOÀN THÀNH: {len(results)}/{len(CRAWL_URLS)} trang thành công")
    print(f"  Dữ liệu lưu tại: {OUTPUT_DIR}")
    print(f"{'='*60}\n")

    return results


if __name__ == "__main__":
    crawl_all()

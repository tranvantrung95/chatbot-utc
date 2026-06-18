"""
Boc tach muc luc + noi dung tu HTML OCR so tay sinh vien.
Output JSON: TOC tree + positions (list cac toa do content blocks).
"""
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

HTML_PATH = Path(__file__).resolve().parent.parent / "data" / "ocr_output" / "so_tay_sinh_vien_k66.html"
OUT_PATH = Path(__file__).resolve().parent.parent / "data" / "ocr_output" / "so_tay_sinh_vien_k66_toc.json"


def parse_bbox(bbox_str):
    parts = bbox_str.strip().split()
    if len(parts) == 4:
        return {"page": 0, "x1": int(parts[0]), "y1": int(parts[1]),
                "x2": int(parts[2]), "y2": int(parts[3])}
    return None


def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())


def extract_type_and_number(title):
    """Extract type (article/clause/point) and number from title."""
    title = title.strip()
    # "Điều 1. ..." -> article, number=1
    m = re.match(r'^Điều\s+(\d+)[.:]', title)
    if m:
        return "article", m.group(1)
    # "Chương I" -> chapter
    m = re.match(r'^Chương\s+(.+)$', title)
    if m:
        return "chapter", m.group(1).strip()
    # "1. Tên mục" -> clause
    m = re.match(r'^(\d+)[.)]\s', title)
    if m:
        return "clause", m.group(1)
    # "a) ..." or "a. ..." -> point
    m = re.match(r'^([a-z])[.)]\s', title)
    if m:
        return "point", m.group(1)
    # "Phần 1:" -> part
    m = re.match(r'^Phần\s+([\d.]+)[.:]', title)
    if m:
        return "part", m.group(1)
    # "I.", "II." -> section (roman)
    m = re.match(r'^([IVX]+)[.)]\s', title)
    if m:
        return "section", m.group(1)
    return "section", ""


def determine_rank(type_str):
    ranks = {"part": 1, "chapter": 2, "section": 3, "article": 4, "clause": 5, "point": 6}
    return ranks.get(type_str, 5)


def main():
    with open(HTML_PATH, encoding="utf-8") as f:
        html = f.read()

    # --- Split pages ---
    pages_raw = re.split(r'<!-- TRANG (\d+) -->', html)
    pages_data = []
    i = 1
    while i < len(pages_raw):
        pn = int(pages_raw[i])
        content = re.sub(r'<!-- ===== HET TRANG ===== -->', '', pages_raw[i + 1] if i + 1 < len(pages_raw) else "")
        pages_data.append({"page": pn, "html": content})
        i += 2

    # --- Extract ALL content blocks from ALL pages (with bbox) ---
    # Each block: {page, bbox, label, text, tag}
    all_blocks = []
    for pd in pages_data:
        soup = BeautifulSoup(pd["html"], "html.parser")
        for div in soup.find_all("div"):
            bbox = parse_bbox(div.get("data-bbox", ""))
            if not bbox:
                continue
            bbox["page"] = pd["page"]
            label = div.get("data-label", "")
            text = re.sub(r'\s+', ' ', div.get_text(" ", strip=True)).strip()
            if not text or len(text) < 2:
                continue
            # Detect heading tag
            htag = div.find(["h1", "h2", "h3", "h4", "h5"])
            all_blocks.append({
                "page": pd["page"],
                "bbox": bbox,
                "label": label,
                "text": text,
                "tag": htag.name if htag else None,
                "is_heading": htag is not None and label == "Section-Header",
            })

    print(f"All content blocks: {len(all_blocks)}")

    # --- Extract TOC from pages 4-5 ---
    toc_raw = []
    for pd in pages_data:
        if pd["page"] not in (4, 5):
            continue
        soup = BeautifulSoup(pd["html"], "html.parser")
        for div in soup.find_all("div"):
            label = div.get("data-label", "")
            text = div.get_text(" ", strip=True)
            if not text or re.match(r'^\d+\s*\*\s*STSV|^STSV\s*\*|^MỤC LỤC$', text):
                continue
            bbox = parse_bbox(div.get("data-bbox", ""))

            if label == "Table-Of-Contents" and div.find("table"):
                for row in div.find_all("tr"):
                    cells = row.find_all("td")
                    row_text = " ".join(c.get_text(" ", strip=True) for c in cells)
                    if row_text and len(row_text) > 5:
                        toc_raw.append({"text": row_text, "bbox": bbox})
            elif label == "Text" and re.search(r'[.…]{2,}', text):
                toc_raw.append({"text": text, "bbox": bbox})

    # Parse page ref from TOC
    toc_entries = []
    for e in toc_raw:
        text = e["text"]
        m = re.search(r'[.…\s]{2,}(\d+)\s*$', text)
        if m:
            toc_entries.append({
                "title": text[:m.start()].strip(),
                "page_ref": int(m.group(1)),
                "toc_bbox": e["bbox"],
            })

    print(f"TOC entries: {len(toc_entries)}")

    # --- Match TOC -> heading block ---
    def match_score(toc_title, h_text):
        tn, hn = norm(toc_title), norm(h_text)
        if tn == hn: return 100
        if len(tn) > 6 and tn in hn: return 90
        if len(hn) > 6 and hn in tn: return 85
        tw = set(re.findall(r'\w{3,}', tn))
        hw = set(re.findall(r'\w{3,}', hn))
        if not tw or not hw: return 0
        return int(len(tw & hw) / max(len(tw), len(hw)) * 50)

    heading_blocks = [b for b in all_blocks if b["is_heading"]]

    for e in toc_entries:
        best_score, best_b = 0, None
        for b in heading_blocks:
            s = match_score(e["title"], b["text"])
            if s > best_score:
                best_score, best_b = s, b
        e["heading_block"] = best_b if best_score >= 35 else None
        e["score"] = best_score

    matched = sum(1 for e in toc_entries if e["heading_block"])
    print(f"Matched: {matched}/{len(toc_entries)}")

    # --- Assign all content blocks to their TOC entry ---
    # Each TOC entry gets all blocks from its heading page to next heading page
    def assign_content_blocks(toc_entries, all_blocks):
        for i, e in enumerate(toc_entries):
            if not e.get("heading_block"):
                e["content_blocks"] = []
                continue

            start_page = e["heading_block"]["page"]
            # Find end page: next TOC entry's heading page - 1
            end_page = 999
            for j in range(i + 1, len(toc_entries)):
                if toc_entries[j].get("heading_block"):
                    end_page = toc_entries[j]["heading_block"]["page"] - 1
                    break

            blocks = []
            for b in all_blocks:
                if start_page <= b["page"] <= end_page:
                    blocks.append(b)
            e["content_blocks"] = blocks

    assign_content_blocks(toc_entries, all_blocks)

    # --- Build TOC tree ---
    def toc_level(title):
        if re.match(r'^Phần\s+\d+[.:]\s', title): return 0
        if re.match(r'^Phần\s+\d+\.\d+', title): return 1
        if re.match(r'^[IVX]+\.\s', title): return 1
        if re.match(r'^\d+\.\s', title): return 2
        if 'lời nói đầu' in title.lower(): return 0
        return 1

    def build_tree(entries):
        root = []
        stack = [{"lv": -1, "kids": root}]
        for e in entries:
            lv = toc_level(e["title"])
            content_blocks = e.get("content_blocks", [])
            positions = [b["bbox"] for b in content_blocks]
            all_text = "\n".join(b["text"] for b in content_blocks)
            word_count = len(re.findall(r'\b\w+\b', all_text))

            typ, num = extract_type_and_number(e["title"])

            # Sub-sections = heading blocks within this section that are NOT the main heading
            sub_headings = [b for b in content_blocks
                           if b["is_heading"] and b != e.get("heading_block")]

            # Build children recursively from sub-headings
            children = []
            for sh in sub_headings:
                ctyp, cnum = extract_type_and_number(sh["text"])
                children.append({
                    "type": ctyp,
                    "rank": determine_rank(ctyp),
                    "number": cnum,
                    "title": sh["text"],
                    "content": "",
                    "word_count": len(re.findall(r'\b\w+\b', sh["text"])),
                    "positions": [sh["bbox"]],
                    "references": [],
                    "children": [],
                    "keywords": "",
                })

            node = {
                "type": typ,
                "rank": determine_rank(typ),
                "number": num,
                "title": e["title"],
                "content": all_text[:3000],
                "content_blocks": content_blocks,  # GIU LAI content_blocks
                "word_count": word_count,
                "positions": positions,
                "references": [],
                "children": children,
                "keywords": "",
                # Extra metadata
                "page_ref": e["page_ref"],
                "match_score": e.get("score"),
            }
            while stack and stack[-1]["lv"] >= lv:
                stack.pop()
            stack[-1]["kids"].append(node)
            stack.append({"lv": lv, "kids": node["children"]})
        return root

    toc_tree = build_tree(toc_entries)

    # --- Count pages used ---
    pages_used = set()
    for b in all_blocks:
        pages_used.add(b["page"])

    # --- Output ---
    result = {
        "document_id": "so_tay_sinh_vien_k66",
        "header": {
            "content": "SỔ TAY SINH VIÊN - DÙNG CHO SINH VIÊN HỆ CHÍNH QUY KHÓA 66\nTRƯỜNG ĐẠI HỌC GIAO THÔNG VẬN TẢI\nHÀ NỘI - 2025",
            "positions": [],  # will be filled from cover pages
        },
        "document_type": "Sổ tay",
        "document_name": "Sổ tay sinh viên K66 - Trường Đại học Giao thông Vận tải",
        "document_number": "K66",
        "issue_date": "2025",
        "effective_date": "2025",
        "expiration_date": "",
        "signer": "",
        "replaced_documents": "",
        "issuing_body": "Trường Đại học Giao thông Vận tải",
        "status": "",
        "attachment_url": "",
        "related_documents": [],
        "legal_basis": [],
        "stats": {
            "total_pages": len(pages_data),
            "total_blocks": len(all_blocks),
            "toc_entries": len(toc_entries),
            "matched": matched,
        },
        "toc": toc_tree,
    }

    # Fill header positions from page 1
    header_positions = []
    for b in all_blocks:
        if b["page"] in (1, 3):  # cover pages
            header_positions.append(b["bbox"])
    result["header"]["positions"] = header_positions[:10]

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Stats
    def count_nodes(tree):
        return sum(1 + count_nodes(n.get("children", [])) for n in tree)

    total_positions = sum(len(e.get("content_blocks", [])) for e in toc_entries)
    print(f"\nDone -> {OUT_PATH}")
    print(f"  Tree nodes: {count_nodes(toc_tree)}")
    print(f"  Total positions: {total_positions}")
    print(f"  File size: {OUT_PATH.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()

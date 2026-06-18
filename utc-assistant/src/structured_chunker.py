"""
Structured chunker final - chunk tu TOC JSON, dung content_blocks.
Moi TOC entry co content -> 1+ chunks (split neu qua dai).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
TOC_PATH = DATA_DIR / "ocr_output" / "so_tay_sinh_vien_k66_toc.json"


def load_toc(path: Optional[Path] = None) -> dict:
    with open(path or TOC_PATH, encoding="utf-8") as f:
        return json.load(f)


def split_text(text: str, max_size: int = 2500, overlap: int = 200) -> List[str]:
    """Split text at paragraph/sentence boundaries with overlap.
    Guarantees: no mid-word cuts, no content loss from truncation.
    """
    if len(text) <= max_size:
        return [text]

    # Step 1: split at paragraph boundaries
    paragraphs = re.split(r'\n{2,}', text)
    chunks, current = [], ""

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        candidate = (current + "\n\n" + para) if current else para
        if len(candidate) <= max_size:
            current = candidate
        else:
            # Current chunk is full — save it
            if current:
                chunks.append(current)
            # Handle the new paragraph
            if len(para) <= max_size:
                current = para
            else:
                # Paragraph too long — split at sentence boundaries
                # Vietnamese sentence endings: . ! ? ... )  "  »  :
                sub_chunks = _split_long_paragraph(para, max_size)
                # All sub-chunks except the last are complete
                for sc in sub_chunks[:-1]:
                    chunks.append(sc)
                current = sub_chunks[-1]

    if current:
        chunks.append(current)

    # Step 2: add overlap prefix (from previous chunk's tail)
    # Overlap is a PREFIX only — does NOT reduce chunk content size
    result = []
    for i, c in enumerate(chunks):
        if i > 0 and overlap > 0:
            prev_tail = chunks[i - 1][-overlap:]
            # Only add overlap if previous chunk ends at a word boundary
            if prev_tail and not prev_tail[0].isspace():
                c = "[...] " + prev_tail.strip() + "\n---\n" + c
        result.append(c)

    return result


def _split_long_paragraph(para: str, max_size: int) -> List[str]:
    """Split a long paragraph at sentence boundaries. Never cut mid-word."""
    # Split at sentence endings: .!? followed by space+uppercase or newline
    # Also handle Vietnamese: ...  )  »  :
    sentences = re.split(r'(?<=[.!?])\s+(?=[A-ZÀ-ỸĐ])', para)

    # If regex produced too few splits, try line-based split
    if len(sentences) <= 1:
        sentences = re.split(r'\n+', para)
    
    # If STILL too few splits, use word-based (guaranteed to split)
    if len(sentences) <= 1:
        return _split_long_sentence(para, max_size)

    chunks = []
    current = ""

    for sent in sentences:
        sent = sent.strip()
        if not sent:
            continue
        candidate = (current + " " + sent) if current else sent
        if len(candidate) <= max_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            # If single sentence is still too long, split at clause/phrase boundaries
            if len(sent) > max_size:
                sub_parts = _split_long_sentence(sent, max_size)
                for sp in sub_parts[:-1]:
                    chunks.append(sp)
                current = sub_parts[-1]
            else:
                current = sent

    if current:
        chunks.append(current)

    return chunks if chunks else [para[:max_size]]


def _split_long_sentence(sent: str, max_size: int) -> List[str]:
    """Split an overlong sentence at comma/semicolon/colon boundaries."""
    # Try splitting at clause markers
    parts = re.split(r'(?<=[,;:])\s+', sent)

    if len(parts) <= 1:
        # Last resort: split at word boundaries (spaces), never mid-word
        words = sent.split()
        chunks, current = [], ""
        for w in words:
            candidate = (current + " " + w) if current else w
            if len(candidate) <= max_size:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                current = w
        if current:
            chunks.append(current)
        return chunks

    chunks, current = [], ""
    for part in parts:
        part = part.strip()
        if not part:
            continue
        candidate = (current + " " + part) if current else part
        if len(candidate) <= max_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            if len(part) > max_size:
                # Recursive: split at word level
                sub = _split_long_sentence(part, max_size)
                for s in sub[:-1]:
                    chunks.append(s)
                current = sub[-1]
            else:
                current = part
    if current:
        chunks.append(current)

    return chunks if chunks else [sent[:max_size]]


def collect_entries_with_content(node: dict, ancestors: List[dict]) -> List[dict]:
    """Duyet cay, thu thap tat ca node co content_blocks khong rong."""
    results = []
    blocks = node.get("content_blocks", [])
    title = node.get("title", "")
    children = node.get("children", [])

    # Build breadcrumb
    def bc(ancs, cur):
        parts = []
        for a in ancs:
            t, n = a.get("type", ""), a.get("number", "")
            if t == "part": parts.append(f"Phan {n}")
            elif t == "chapter": parts.append(f"Chuong {n}")
            elif t == "article": parts.append(f"Dieu {n}")
        t, n = cur.get("type", ""), cur.get("number", "")
        if t == "part": parts.append(f"Phan {n}")
        elif t == "chapter": parts.append(f"Chuong {n}")
        elif t == "article": parts.append(f"Dieu {n}")
        else: parts.append(cur.get("title", "")[:50])
        return " > ".join(parts)

    if blocks:
        results.append({
            "node": node,
            "ancestors": ancestors,
            "breadcrumb": bc(ancestors, node),
        })

    for child in children:
        results.extend(collect_entries_with_content(child, ancestors + [node]))

    return results


def _clean_ocr_text(text: str) -> str:
    """Remove OCR artifacts: repeated digit patterns, garbage sequences."""
    lines = text.split('\n')
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned.append('')
            continue
        # Detect garbage: repeating digit-dot patterns like "1.1.4.1.1.4..."
        # Check for pattern X.Y.Z. repeated many times (OCR hallucination)
        garbage_pattern = re.findall(r'(\d+\.\d+\.\d+\.){4,}', stripped)
        if garbage_pattern:
            # Remove the garbage part, keep any legitimate prefix
            # Find where garbage starts
            for gp in garbage_pattern:
                idx = stripped.find(gp)
                if idx > 0:
                    stripped = stripped[:idx].strip()
                else:
                    stripped = ""
                break
        cleaned.append(stripped)
    return '\n'.join(cleaned)


def chunk_for_indexing(
    toc_path: Optional[Path] = None,
    min_size: int = 200,
    max_size: int = 2500,
) -> List[Dict[str, Any]]:
    """Main entry: tra ve list chunks {content, metadata}."""
    toc_data = load_toc(toc_path)
    all_chunks = []

    for root in toc_data.get("toc", []):
        entries = collect_entries_with_content(root, [])

        for entry in entries:
            node = entry["node"]
            blocks = node.get("content_blocks", [])
            if not blocks:
                continue

            # Build full text from content_blocks, then clean OCR artifacts
            text = "\n\n".join(b.get("text", "") for b in blocks if b.get("text"))
            text = _clean_ocr_text(text)
            if len(text) < min_size:
                continue

            # Build metadata
            ancestors = entry["ancestors"]
            breadcrumb = entry["breadcrumb"]
            pages = sorted(set(b.get("page", 0) for b in blocks if b.get("page")))
            positions = [b.get("bbox", {}) for b in blocks if b.get("bbox")]

            base_meta = {
                "title": node.get("title", "")[:120],
                "type": node.get("type", "section"),
                "number": node.get("number", ""),
                "breadcrumb": breadcrumb,
                "pages": pages,
            }

            for a in ancestors + [node]:
                at, an, atitle = a.get("type", ""), a.get("number", ""), a.get("title", "")
                if at == "part":
                    base_meta["phan"] = atitle
                    base_meta["phan_so"] = an
                elif at == "chapter":
                    base_meta["chuong"] = atitle
                    base_meta["chuong_so"] = an
                elif at == "article":
                    base_meta["dieu"] = atitle
                    base_meta["dieu_so"] = an

            # Split if too large
            parts = split_text(text, max_size, overlap=200)
            for pi, part in enumerate(parts):
                meta = dict(base_meta)
                meta["char_count"] = len(part)
                meta["word_count"] = len(re.findall(r"\b\w+\b", part))
                if pi > 0:
                    meta["title"] = f"{base_meta['title']} (p.{pi + 1})"
                all_chunks.append({"content": part, "metadata": meta})

    return all_chunks


def print_stats(chunks):
    types = {}
    total, sizes = 0, []
    for c in chunks:
        t = c["metadata"].get("type", "?")
        types[t] = types.get(t, 0) + 1
        total += len(c["content"])
        sizes.append(len(c["content"]))
    print(f"Chunks: {len(chunks)} | {total} chars | avg {total // max(1, len(chunks))} | range {min(sizes)}-{max(sizes)}")
    print(f"Types: {dict(sorted(types.items()))}")


if __name__ == "__main__":
    chunks = chunk_for_indexing()
    print_stats(chunks)

    print("\n=== SAMPLES ===")
    for c in chunks[:3]:
        m = c["metadata"]
        print(f"\n[{m['type']}] {m['breadcrumb']}")
        print(f"  pages={m.get('pages',[])} | size={len(c['content'])}c")
        print(f"  {c['content'][:150]}...")

    # Show a Phần 2.1 chunk
    for c in chunks:
        if "Phan 2.1" in c["metadata"].get("breadcrumb", ""):
            m = c["metadata"]
            print(f"\n[PHAN 2.1] {m['breadcrumb']}")
            print(f"  pages={m.get('pages',[])} | size={len(c['content'])}c")
            print(f"  {c['content'][:200]}...")
            break

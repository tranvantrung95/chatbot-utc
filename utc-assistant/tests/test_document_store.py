import tempfile
import unittest
from pathlib import Path

from src.document_store import (
    extract_uploaded_text,
    list_documents,
    safe_filename,
    save_imported_text,
)


class DocumentStoreTests(unittest.TestCase):
    def test_safe_filename_normalizes_extension(self):
        self.assertEqual(safe_filename("Quy chế đào tạo.pdf"), "quy_chế_đào_tạo.pdf")
        self.assertEqual(safe_filename("bad.exe"), "bad.txt")

    def test_extract_uploaded_text_for_txt(self):
        text = extract_uploaded_text("note.txt", "Nội dung tiếng Việt".encode("utf-8"))
        self.assertEqual(text, "Nội dung tiếng Việt")

    def test_save_imported_text_creates_unique_txt_record(self):
        with tempfile.TemporaryDirectory() as tmp:
            raw_dir = Path(tmp)
            body = "Nội dung import phục vụ kiểm thử. " * 4

            first = save_imported_text(raw_dir, "Quy chế mới", body, filename="quy_che.pdf")
            second = save_imported_text(raw_dir, "Quy chế mới", body, filename="quy_che.pdf")
            records = list_documents(raw_dir)

        self.assertEqual(first.name, "quy_che.txt")
        self.assertEqual(second.name, "quy_che_2.txt")
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].title, "Quy chế mới")

    def test_save_imported_text_rejects_tiny_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                save_imported_text(Path(tmp), "Ngắn", "quá ngắn")


if __name__ == "__main__":
    unittest.main()

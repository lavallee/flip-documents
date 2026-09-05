"""Exercise real optional converters against known original coordinates."""

import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

import fidelity_fixtures as fixtures

from flip_documents.cli import cells, extract


@unittest.skipUnless(
    importlib.util.find_spec("markitdown"), "requires optional MarkItDown extras"
)
class FidelityTest(unittest.TestCase):
    def test_docx_paragraph_and_table_text(self):
        with tempfile.TemporaryDirectory() as root:
            src, out = Path(root) / "table.docx", Path(root) / "out.md"
            fixtures.docx(src)
            extract(src, out)
            text = out.read_text()
            self.assertIn("café & library", text)
            self.assertIn("00123", text)
            self.assertLess(text.index("First paragraph"), text.index("Code"))
            self.assertLess(text.index("Code"), text.index("Last paragraph"))
            self.assertIn("-12.50", text)

    def test_xlsx_preserves_types_sparse_coordinates_and_formula(self):
        with tempfile.TemporaryDirectory() as root:
            src, out = Path(root) / "sparse.xlsx", Path(root) / "out.json"
            fixtures.xlsx(src)
            before = hashlib.sha256(src.read_bytes()).hexdigest()
            receipt = cells(src, out)
            data = json.loads(out.read_text())
            self.assertEqual([s["name"] for s in data["sheets"]], ["Sparse", "Second"])
            records = {c["coordinate"]: c for c in data["sheets"][0]["cells"]}
            self.assertEqual(records["A2"]["value"], "00123")
            self.assertEqual(records["A2"]["data_type"], "s")
            self.assertEqual(records["A4"]["value"], "00999")
            self.assertEqual(records["B2"]["value"], 12.5)
            self.assertEqual(records["B2"]["number_format"], "0.00")
            self.assertEqual(records["B4"]["value"], -1.25)
            self.assertEqual(records["D4"]["value"], 0)
            self.assertNotIn("C2", records)
            self.assertNotIn("A3", records)
            self.assertEqual(records["D2"]["value"], "=B2*2")
            self.assertIsNone(records["D2"]["cached_value"])
            self.assertEqual(records["D2"]["cache_status"], "unavailable-or-blank")
            self.assertEqual(records["E2"]["value"], "=B2*2")
            self.assertEqual(records["E2"]["cached_value"], 25)
            self.assertEqual(records["E2"]["cache_status"], "present")
            self.assertEqual(receipt["method"], "structured")
            self.assertEqual(receipt["input_sha256"], before)
            self.assertEqual(hashlib.sha256(src.read_bytes()).hexdigest(), before)
            with self.assertRaises(ValueError):
                cells(src, out)

    def test_pptx_uses_presentation_order_not_filename_order(self):
        with tempfile.TemporaryDirectory() as root:
            src, out = Path(root) / "slides.pptx", Path(root) / "out.md"
            fixtures.pptx(src)
            extract(src, out)
            lines = [
                line
                for line in out.read_text().splitlines()
                if line.startswith("Slide original")
            ]
            self.assertEqual(
                lines, [f"Slide original {i}" for i in [12, *range(1, 12)]]
            )

    def test_pdf_page_order_and_exact_numeric_text(self):
        with tempfile.TemporaryDirectory() as root:
            src, out = Path(root) / "text.pdf", Path(root) / "out.md"
            fixtures.pdf(src)
            extract(src, out)
            text = out.read_text()
            self.assertIn("00123", text)
            self.assertIn("-12.50", text)
            self.assertLess(text.index("Page ONE"), text.index("Page TWO"))

    def test_real_raster_pdf_refuses_without_ocr(self):
        with tempfile.TemporaryDirectory() as root:
            src, out = Path(root) / "scan.pdf", Path(root) / "out.md"
            fixtures.scan(src)
            with self.assertRaisesRegex(ValueError, "no readable text"):
                extract(src, out)
            self.assertFalse(out.exists())

import hashlib
import io
import json
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

from flip_documents.cli import capture, extract, filename, main

PDF = b"%PDF-1.4\nSynthetic fixture, not a valid rendered PDF.\n%%EOF\n"


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/download")
            self.end_headers()
            return
        body = b"<html>Sign in</html>" if self.path == "/login.pdf" else PDF
        self.send_response(200)
        self.send_header("Content-Type", "application/pdf")
        self.send_header(
            "Content-Disposition", 'attachment; filename="../../report.pdf"'
        )
        self.send_header(
            "Content-Length", str(len(body) + (20 if self.path == "/truncated" else 0))
        )
        self.end_headers()
        self.wfile.write(body)


class DocumentsTest(unittest.TestCase):
    def test_plugin_path_is_one_unwrapped_line(self):
        path = Path("/long-environment-name" * 8) / "site-packages/flip_documents/bundle"
        with patch("flip_documents.cli.plugin_path", return_value=path), patch(
            "sys.stdout", new_callable=io.StringIO
        ) as output:
            self.assertEqual(main(["--plugin-path"]), 0)
            self.assertEqual(output.getvalue(), str(path) + "\n")

    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f"http://127.0.0.1:{cls.server.server_port}"

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def test_original_redirect_receipt(self):
        with tempfile.TemporaryDirectory() as root:
            dest = Path(root) / "capture"
            result = capture(self.url + "/redirect", dest)
            self.assertEqual((dest / "report.pdf").read_bytes(), PDF)
            self.assertEqual(result["sha256"], hashlib.sha256(PDF).hexdigest())
            self.assertEqual(result["input_url"], self.url + "/redirect")
            self.assertEqual(result["canonical_url"], self.url + "/download")
            self.assertEqual(
                json.loads((dest / "flip.json").read_text())["flip"]["bytes"], len(PDF)
            )

    def test_failures_leave_no_capture(self):
        for path, limit in [
            ("/login.pdf", 1000),
            ("/download", 5),
            ("/truncated", 1000),
        ]:
            with self.subTest(path=path), tempfile.TemporaryDirectory() as root:
                dest = Path(root) / "capture"
                with self.assertRaises((ValueError, OSError)):
                    capture(self.url + path, dest, max_bytes=limit)
                self.assertFalse(dest.exists())
                self.assertEqual(list(Path(root).iterdir()), [])

    def test_filename_and_existing_destination(self):
        self.assertEqual(
            filename(
                "https://example.org",
                "application/pdf",
                'attachment; filename="..\\..\\flip.json"',
            ),
            "document.pdf",
        )
        with tempfile.TemporaryDirectory() as root:
            dest = Path(root)
            (dest / "owned").write_text("keep")
            with self.assertRaises(ValueError):
                capture(self.url + "/download", dest)
            self.assertEqual((dest / "owned").read_text(), "keep")

    def test_extractor_refuses_overwrite_or_unsupported(self):
        with tempfile.TemporaryDirectory() as root:
            src = Path(root) / "source.docx"
            src.write_bytes(b"original")
            with self.assertRaises(ValueError):
                extract(src, src)
            with self.assertRaises(ValueError):
                extract(Path(root) / "source.zip", Path(root) / "out.txt")
            self.assertEqual(src.read_bytes(), b"original")

    def test_no_text_leaves_no_derivative(self):
        import sys
        from types import SimpleNamespace

        fake = SimpleNamespace(
            MarkItDown=lambda **kw: SimpleNamespace(
                convert=lambda src: SimpleNamespace(markdown="")
            )
        )
        with (
            tempfile.TemporaryDirectory() as root,
            patch.dict(sys.modules, {"markitdown": fake}),
        ):
            src, out = Path(root) / "scan.pdf", Path(root) / "out.txt"
            src.write_bytes(PDF)
            with self.assertRaisesRegex(ValueError, "no readable text"):
                extract(src, out)
            self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()

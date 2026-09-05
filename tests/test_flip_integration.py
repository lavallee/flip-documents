"""Opt-in real Flip integration: set FLIP_TEST_BIN to Flip >=0.22 executable."""

import http.server
import json
import os
import subprocess
import tempfile
import threading
import unittest
from pathlib import Path

import fidelity_fixtures as fixtures


@unittest.skipUnless(
    os.environ.get("FLIP_TEST_BIN"), "set FLIP_TEST_BIN for actual Flip integration"
)
class FlipIntegrationTest(unittest.TestCase):
    def test_capture_extract_recheck(self):
        root_package = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            src = root / "example.docx"
            subprocess.run(
                ["python", str(root_package / "examples/make_document.py"), str(src)],
                check=True,
                capture_output=True,
            )
            body = src.read_bytes()

            class Handler(http.server.BaseHTTPRequestHandler):
                def log_message(self, *args):
                    pass

                def do_GET(self):
                    self.send_response(200)
                    self.send_header(
                        "Content-Type",
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)

            server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            try:
                home = root / "home"
                home.mkdir()
                (home / "config.toml").write_text(
                    '[fetchers.web]\ndocuments = "flip-documents capture {url} {dest}"\n[extractors.docx]\ndocuments = "flip-documents extract {src} {out}"\n[extractors.xlsx]\ncells = "flip-documents cells {src} {out}"\n'
                )
                env = dict(
                    os.environ, FLIP_HOME=str(home), FLIP_ACTOR="agent:integration-test"
                )
                notebook = root / "notebook"

                def flip(*args, cwd=root):
                    result = subprocess.run(
                        [env["FLIP_TEST_BIN"], *args],
                        cwd=cwd,
                        env=env,
                        capture_output=True,
                        text=True,
                        check=False,
                    )
                    self.assertEqual(
                        result.returncode, 0, result.stdout + result.stderr
                    )
                    return result.stdout

                flip("plugin", "doctor", str(root_package))
                flip("plugin", "link", str(root_package))
                flip("new", "notebook", "--kind", "ledger", "--dest", str(notebook))
                flip("session", "start", "capture-test", cwd=notebook)
                url = f"http://127.0.0.1:{server.server_port}/example.docx"
                flip("add-source", url, "--via", "documents", cwd=notebook)
                flip(
                    "extract",
                    "A1",
                    "--via",
                    "documents",
                    "--method",
                    "text-layer",
                    cwd=notebook,
                )
                self.assertIn(
                    "unchanged",
                    flip("source", "recheck", "A1", "--via", "documents", cwd=notebook),
                )
                rows = [
                    json.loads(row)
                    for row in (notebook / "derived/_derivations.jsonl")
                    .read_text()
                    .splitlines()
                ]
                self.assertTrue(rows[0]["inputs"][0]["path"].endswith("example.docx"))
                self.assertIn("markitdown", rows[0]["tool_version"])
                self.assertIn(
                    "library opens on Tuesday",
                    (notebook / "sources/text/A1.txt").read_text(),
                )
                workbook = root / "sparse.xlsx"
                fixtures.xlsx(workbook)
                flip("add-source", str(workbook), "--kind", "file", cwd=notebook)
                flip(
                    "extract",
                    "F1",
                    "--via",
                    "cells",
                    "--method",
                    "structured",
                    cwd=notebook,
                )
                artifact = json.loads((notebook / "sources/text/F1.txt").read_text())
                records = {
                    cell["coordinate"]: cell for cell in artifact["sheets"][0]["cells"]
                }
                self.assertEqual(records["A2"]["value"], "00123")
                self.assertEqual(records["D2"]["value"], "=B2*2")
                ledger = [
                    json.loads(line)
                    for line in (notebook / "derived/_derivations.jsonl")
                    .read_text()
                    .splitlines()
                ]
                self.assertEqual(ledger[-1]["method"], "structured")
                self.assertIn("openpyxl", ledger[-1]["tool_version"])
                flip(
                    "session",
                    "end",
                    "capture-test",
                    "--summary",
                    "Synthetic capture, extraction and unchanged recheck passed.",
                    cwd=notebook,
                )
                # This deliberately tiny DOCX triggers Flip's thin-capture warning.
                flip("doctor", cwd=notebook)
            finally:
                server.shutdown()
                server.server_close()
                thread.join()

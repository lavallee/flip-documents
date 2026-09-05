---
name: document-evidence
description: Capture a document URL and inspect an explicit reading derivative before citing it.
---

Set FLIP_ACTOR and open a Flip session before research. Capture with `flip
add-source URL --via documents`. Inspect the original: a receipt proves what
was downloaded, not that it is the intended edition or complete publication.

For DOCX, XLSX, PPTX or text-layer PDF, use `flip extract ID --via documents
--method text-layer` after configuring the optional converter. Inspect the
result. MarkItDown Markdown is a reading derivative: it can omit formatting,
images, comments and formulas; it is not OCR or an analytical spreadsheet.
Verify quotations against the original, and calculations against original
cells with an independently logged calculation. If conversion produces no
text, choose a separately configured OCR lane and record that different method.

Grade only after reading. Record claims through Flip with honest source roles.
Run `flip doctor`, resolve errors, read warnings, and close the session with a
cold-pickup summary. The plugin never edits notebook entities or ledgers itself.

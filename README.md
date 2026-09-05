# flip-documents

Save an original document from its URL, then optionally derive Markdown with
[MarkItDown](https://github.com/microsoft/markitdown). The commands work without
Flip. The Flip bundle adds an evidence workflow and a skill; it never activates
commands or changes machine configuration.

Version 0.2.0 adds structured spreadsheet extraction. Capture uses Python's standard library.
Extraction is an optional adapter to a broader maintained converter.

```sh
pip install .
flip-documents capture https://example.org/report.pdf ./capture
pip install '.[markitdown]'
flip-documents extract ./capture/report.pdf ./reading.md
flip-documents cells workbook.xlsx cells.json
```

Capture creates the downloaded file and `flip.json`, containing input and final
URL, retrieval time, SHA-256, size, media type, method and user agent. It follows
HTTP redirects and requests identity encoding. It refuses HTML login/error
pages, empty responses, incomplete declared bodies, nonempty destinations and
responses over 100 MB (override with `--max-bytes`). It does not unpack archives,
run Office macros, authenticate, crawl, or delegate web pages elsewhere. Only
HTTP(S) is supported. Filenames are sanitized. URL query strings are preserved
in receipts: keep captures containing signed or otherwise private URLs private.

Capture recognizes PDF, Office, CSV and ZIP media types and common binary
signatures. Recognition is not format validation: inspect the actual document.
Other formats can be preserved when their binary signature is recognized, but
that does not imply extraction support. HTML detection is a useful refusal,
not proof that every successful response is the intended document.

Extraction supports DOCX, XLSX, PPTX and text-layer PDF through the optional
MarkItDown dependency, with plugins disabled and no remote service configured.
It prints an input/output hash receipt and converter version to stdout. Save
that receipt for standalone use. No output is written when conversion finds
no text. Existing derivatives are never overwritten. Scans require another
explicit OCR tool. Markdown can lose layout, comments, image content, precision,
and spreadsheet semantics; verify quotes and numbers against original pages or
cells. This is not a formula evaluator or an analytical data export.

## Spreadsheet cells

Use `cells` when identifiers, coordinates and typed values matter. It
adapts openpyxl, already included in the optional spreadsheet dependencies, and
writes `flip.documents-cells/1` JSON. Sheet order, names and visibility are
retained. Each nonblank cell records its coordinate, value, type and number
format. String codes such as `00123` remain strings, gaps stay visible through
coordinates, and formula text is separate from its cached result. A missing or
blank cache is labeled `unavailable-or-blank`; caches may be stale and are never
recalculated. Dates and times use ISO text plus their original number format. Numbers are
openpyxl-decoded Python integers/floats, not exact XML decimal text; keep the
original for decimal-sensitive analysis.

This matters because XLSX Markdown conversion can infer numeric types and turn
`00123` into `123.0`, or render uncached formulas as `NaN`. Use Markdown for
reading; use `cells` plus the original workbook for checking values. Cell JSON
omits styles, merged ranges, charts and comments. It refuses worksheets without
declared dimensions or whose declared range exceeds one million cells. It never
runs formulas, opens linked workbooks, or rewrites the original.

## Flip integration

Requires Flip 0.22 or newer. Add these lanes to your chosen Flip configuration:

```toml
[fetchers.web]
documents = "flip-documents capture {url} {dest}"

[extractors.docx]
documents = "flip-documents extract {src} {out}"
[extractors.xlsx]
cells = "flip-documents cells {src} {out}"
# Optional lossy reading lane:
documents = "flip-documents extract {src} {out}"
[extractors.pptx]
documents = "flip-documents extract {src} {out}"
[extractors.pdf]
documents = "flip-documents extract {src} {out}"
```

```sh
flip plugin doctor .
flip plugin link .
# In a notebook, after setting FLIP_ACTOR and opening a session:
flip add-source https://example.org/report.pdf --via documents
flip extract A1 --via documents --method text-layer
# For a captured XLSX source instead:
# flip extract F1 --via cells --method structured
```

Linking makes the workflow and skill discoverable. This bundle is definition-only;
no executable activation or `flip plugin enable` step is required. Installing
the wheel packages the same definitions; locate and validate them with:

```sh
flip-documents --plugin-path
flip plugin doctor "$(flip-documents --plugin-path)"
flip plugin link "$(flip-documents --plugin-path)"
```

Flip owns source custody and the derivation ledger. The standalone commands
never mutate a notebook. A standalone capture receipt and a Flip source grade
are different things: read and grade after capture.

## Development

```sh
PYTHONPATH=src python -m unittest discover -s tests -v
```

Tests use a local HTTP server and synthetic document bytes to verify original
byte custody, redirect provenance, malicious filenames, HTML refusals, download
limits, truncation and preservation of existing work. The example creates a
minimal DOCX for a converter smoke test. Additional synthetic fixtures check
DOCX paragraph/table text, sparse XLSX codes and formulas, reordered 12-slide
PPTX presentation order, two-page PDF text, and refusal of a real raster-only
PDF without OCR. These targeted checks do not prove arbitrary publisher files
convert correctly. MIT; no upstream converter code is
vendored. MarkItDown has its own dependencies and license terms.

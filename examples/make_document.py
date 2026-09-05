"""Create a public-clean minimal DOCX for a real converter smoke test."""

import sys
from pathlib import Path
from zipfile import ZipFile

path = Path(sys.argv[1] if len(sys.argv) > 1 else "example.docx")
with ZipFile(path, "x") as z:
    z.writestr(
        "[Content_Types].xml",
        '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>',
    )
    z.writestr(
        "_rels/.rels",
        '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>',
    )
    z.writestr(
        "word/document.xml",
        '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>Public example: the library opens on Tuesday. This synthetic document exists only to demonstrate original byte capture and explicit text extraction. It contains no private research, personal records, or claims about any real library.</w:t></w:r></w:p></w:body></w:document>',
    )
print(path)

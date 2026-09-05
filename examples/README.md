Run `python examples/make_document.py example.docx`, then
`flip-documents extract example.docx reading.md` after installing the optional
converter. Expected output includes `Public example: the library opens on
Tuesday.` The returned receipt identifies MarkItDown and both hashes. This
minimal synthetic document checks a working converter installation, not general
Office fidelity. The generator refuses to overwrite an existing file.

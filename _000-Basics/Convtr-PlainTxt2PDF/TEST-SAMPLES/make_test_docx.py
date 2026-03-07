"""Creates a minimal valid .docx test file for the PlainTxt2PDF conversion test."""
import zipfile
import os

out = os.path.join(os.path.dirname(__file__), "test_docx_sample.docx")

doc_xml = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
    '<w:body>'
    '<w:p><w:r><w:t>Hello from the Antigravity .docx test file!</w:t></w:r></w:p>'
    '<w:p><w:r><w:t>This file was auto-generated to verify .docx to PDF conversion.</w:t></w:r></w:p>'
    '<w:p><w:r><w:t>Line 3: Confirming multi-paragraph extraction works correctly.</w:t></w:r></w:p>'
    '<w:p><w:r><w:t>Line 4: Mission accomplished if you can read this in the PDF!</w:t></w:r></w:p>'
    '</w:body>'
    '</w:document>'
)

ct_xml = (
    '<?xml version="1.0"?>'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="xml" ContentType="application/xml"/>'
    '</Types>'
)

with zipfile.ZipFile(out, "w") as z:
    z.writestr("word/document.xml", doc_xml)
    z.writestr("[Content_Types].xml", ct_xml)

print(f"Created: {out}")

---
name: converting-pdf-to-markdown
description: Extracts text from PDF files and converts them to clean Markdown (.md) with headings, bullet lists, tables, and code blocks inferred from font size and layout. Use when the user mentions PDF to Markdown, extracting PDF content, converting a PDF for LLM ingestion, or making a PDF editable.
---

# PDF2md Skill

## When to Use This Skill
- User wants to convert a PDF to Markdown
- User says "extract text from PDF", "make a PDF editable", or "PDF to Markdown"
- User needs PDF content ingested into an LLM, knowledge base, or docs system
- User wants to recover content from a PDF when the source file is lost

---

## Supported Input
- Text-based PDFs (the majority — exported from Word, Google Docs, browsers, etc.)
- **Not supported:** Scanned/image-only PDFs (require OCR — see note below)

---

## Workflow

- [ ] 1. Confirm `--input` is a text-based PDF (not a scanned image)
- [ ] 2. Run `scripts/pdf2md.py`
- [ ] 3. Review the output `.md` — spot-check headings and tables
- [ ] 4. Clean up any layout artifacts if needed

---

## Commands

**Basic usage — output saved next to input:**
```bash
python3 scripts/pdf2md.py --input "report.pdf"
```

**Custom output path:**
```bash
python3 scripts/pdf2md.py --input "report.pdf" --output "docs/report.md"
```

**Full options:**
```bash
python3 scripts/pdf2md.py --help
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--input` | *(required)* | Path to input `.pdf` |
| `--output` | Same name as input, `.md` | Output `.md` file path |
| `--heading-scale` | `1.2` | Font size multiplier threshold for heading detection |
| `--no-tables` | off | Skip table extraction (faster, plain text only) |

---

## How Heading Detection Works

The script compares each text block's font size against the page's median font size:
- `>= median × (scale + 0.4)` → `# H1`
- `>= median × (scale + 0.15)` → `## H2`
- `>= median × scale` → `### H3`

Adjust `--heading-scale` up (e.g. `1.4`) if too many false positives, down (e.g. `1.1`) if headings are being missed.

---

## Limitations

- Complex multi-column layouts may produce interleaved text
- Tables with merged cells may not align perfectly
- Scanned PDFs will output empty or garbled text — use OCR tools (e.g. `tesseract`) first

---

## Dependencies

| Library | Where | Purpose |
|---|---|---|
| `pdfplumber` | `_libs/` | PDF text + table extraction |

**If missing:**
```bash
python3 -m pip install pdfplumber --target ../../_libs/
```

---

## Resources
- `scripts/pdf2md.py` — core conversion script
- `TEST-SAMPLES/` — sample PDFs for testing

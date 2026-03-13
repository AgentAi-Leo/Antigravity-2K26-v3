---
name: converting-plain-text-to-pdf
description: Converts .txt, .rtf, or .doc files into a clean, single-page PDF with no logos, footers, or labels. Use when the user wants a simple conversion of a plain text, RTF, or legacy Word document to PDF with no extra formatting.
---

# PlainTxt2PDF Skill

## When to Use This Skill
- User wants to convert a `.txt`, `.rtf`, or `.doc`, `.docx` file to `.pdf`
- User says "just a plain PDF", "simple convert", or "no logo/footer"
- User needs a quick single-file output (not split by prompt/section)

---

## Supported Input Formats

| Extension | Reader | Notes |
|---|---|---|
| `.txt` | Built-in | UTF-8, line-by-line |
| `.rtf` | `striprtf` (in `_libs/`) | Falls back to regex stripping if unavailable |
| `.doc`, `.docx` | `antiword` → LibreOffice → binary extraction | Each tried in order |

> **For best `.doc`, `.docx` results** install antiword: `brew install antiword`

---

## Workflow

- [x] 1. Confirm `--input` path exists (`.txt`, `.rtf`, or `.doc`, `.docx`)
- [x] 2. Run `scripts/plain_txt2pdf.py`
- [x] 3. Verify the output `.pdf` was created
- [/] 4. Surface the result for the user via `scripts/show_result.sh <output.pdf>`

---

## Commands

**Basic usage — output saved next to the input file:**
```bash
python3 scripts/plain_txt2pdf.py --input "myfile.txt"
python3 scripts/plain_txt2pdf.py --input "report.rtf"
python3 scripts/plain_txt2pdf.py --input "memo.doc"
```

**Custom output path:**
```bash
python3 scripts/plain_txt2pdf.py --input "myfile.rtf" --output "out/result.pdf"
```

**Custom font size and margins:**
```bash
python3 scripts/plain_txt2pdf.py --input "myfile.txt" --font-size 12 --margin 25
```

**Full options:**
```bash
python3 scripts/plain_txt2pdf.py --help
```

**Surface in UI (recommended after any of above):**
```bash
bash scripts/show_result.sh "output.pdf"
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--input` | *(required)* | Path to input file (`.txt`, `.rtf`, `.doc`, `.docx`) |
| `--output` | Same name as input, `.pdf` | Output file path |
| `--font-size` | `11` | Body font size (pt) |
| `--margin` | `20` | Page margin (mm) |

---

## Dependencies

| Library | Where | Purpose |
|---|---|---|
| `fpdf2` | `_libs/` | PDF generation |
| `striprtf` | `_libs/` | RTF text extraction |
| `antiword` | System (optional) | Best-quality `.doc`, `.docx` extraction |

**If fpdf2/striprtf are missing, install to shared libs:**
```bash
python3 -m pip install fpdf2 striprtf --target ../../_libs/
```

**For `.doc`, `.docx` quality output:**
```bash
brew install antiword
```

---

## Watch Folder Mode

When the `Convtr-PlainTxt2PDF` skill is selected in the Antigravity Dashboard, a **📂 Watch Folder Auto-Process** toggle is available.

### How It Works
1. **Enable the toggle** in the dashboard
2. **Enter any folder path** on your machine (e.g., `~/Desktop/MyWatchFolder`)
3. **Select a polling interval**: `Every 15 minutes`, `Every 1 minute`, or `Every :05`
4. Any `.txt`, `.rtf`, `.doc`, or `.docx` files placed in the folder are **automatically converted to PDF**
5. Output PDFs go to `<folder>/zProcessed/YYYY-MM-DD/`
6. Original files are **purged** after successful conversion

### CLI Usage (Standalone)
```bash
python3 scripts/watch_folder_processor.py --folder "/path/to/folder"
python3 scripts/watch_folder_processor.py --folder "/path/to/folder" --dry-run
python3 scripts/watch_folder_processor.py --help
```

---

## Resources
- `scripts/plain_txt2pdf.py` — core conversion script
- `scripts/watch_folder_processor.py` — watch folder batch processor

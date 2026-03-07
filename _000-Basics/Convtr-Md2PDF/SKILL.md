---
name: converting-markdown-to-pdf
description: Converts a Markdown (.md) file into a formatted PDF with styled headings, bullet lists, code blocks, and body text. Use when the user mentions Markdown-to-PDF, .md file export, README to PDF, or document rendering from Markdown.
---

# Md2PDF Skill

## When to Use This Skill
- User wants to convert a `.md` (Markdown) file to a `.pdf`
- User says "render my README as a PDF", "export Markdown", or "Markdown to PDF"
- User needs headings, lists, and code blocks to be visually distinct in the output

---

## Supported Markdown Elements

| Element | Syntax | Rendering |
|---|---|---|
| H1 heading | `# Title` | Large bold |
| H2 heading | `## Section` | Medium bold |
| H3 heading | `### Sub` | Small bold |
| Bullet list | `- item` or `* item` | Indented with `•` |
| Code block | ` ``` ... ``` ` | Monospace, grey background |
| Body text | plain lines | Regular helvetica |
| Blank line | empty line | Vertical spacing |

> **Note:** Inline `**bold**`, `*italic*`, and `` `code` `` markers are stripped to plain text. Full inline rendering is not supported.

---

## Workflow

- [x] 1. Confirm `--input` path exists and is a `.md` file
- [x] 2. Run `scripts/md2pdf.py` with desired options (`--input` or `--url`)
- [x] 3. Verify the output `.pdf` was created
- [/] 4. Surface the result for the user via `scripts/show_result.sh <output.pdf>`

---

## Commands

**Basic usage:**
```bash
python3 scripts/md2pdf.py --input "README.md"
```

**Custom output path:**
```bash
python3 scripts/md2pdf.py --input "docs/guide.md" --output "out/guide.pdf"
```

**Capture complex web page (Notion/HTML) with icons/emojis:**
```bash
python3 scripts/md2pdf.py --url "https://notion.site/page-link" --capture --output "my_page.pdf"
```

**Full options:**
```bash
python3 scripts/md2pdf.py --help
```

**Surface in UI (recommended after any of above):**
```bash
bash scripts/show_result.sh "output.pdf"
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--input` | *(optional)* | Path to input `.md` file |
| `--url` | *(optional)* | Remote URL (Markdown or Web Page) |
| `--capture` | `False` | **Capture Mode**: High-fidelity PDF (uses Chrome) |
| `--output` | Default name | Output file path |
| `--font-size` | `11` | Body font size (pt) |
| `--margin` | `20` | Page margin (mm) |

---

## Dependencies

`fpdf2` must be resolvable. The script checks in order:
1. `../libs/` (local to this skill)
2. `../../Txt2PDF/libs/` (shared fallback if Txt2PDF skill is installed)
3. System path

**If missing, install locally:**
```bash
python3 -m pip install fpdf2 --target libs/
```

---

## Resources
- `scripts/md2pdf.py` — core conversion script

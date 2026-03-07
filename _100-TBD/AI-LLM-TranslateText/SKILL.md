---
name: translating-text-with-ai
description: Translates text or document files between any languages using an LLM. Preserves Markdown formatting. Use when the user asks to translate text, a file, or a document into another language.
---

# AI-LLM-TranslateText Skill

## When to Use This Skill
- User says "translate this", "translate to [language]", or "localize this content"
- Translating Markdown docs, README files, or plain text while preserving structure
- Batch-translating multiple strings or files

---

## Prerequisites

```bash
export GEMINI_API_KEY="..."    # default
# OR: OPENAI_API_KEY / ANTHROPIC_API_KEY
```

---

## Workflow
- [ ] 1. Set API key
- [ ] 2. Run `scripts/translate_text.py --text "..." --to Spanish`
- [ ] 3. Review and use the translated output

---

## Commands

```bash
# Translate a string
python3 scripts/translate_text.py --text "Hello, world!" --to Spanish

# Translate a file (preserves Markdown formatting)
python3 scripts/translate_text.py --input README.md --to French --output README.fr.md

# Detect source language automatically (default)
python3 scripts/translate_text.py --text "Bonjour le monde" --to English

# Specify source language explicitly
python3 scripts/translate_text.py --input doc.md --from English --to Japanese

# Batch translate a directory of .md files
python3 scripts/translate_text.py --input-dir ./docs/ --to German --output-dir ./docs-de/
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--text` | — | Inline text to translate |
| `--input` | — | Input file path |
| `--input-dir` | — | Directory of `.txt`/`.md` files |
| `--to` | *(required)* | Target language name |
| `--from` | auto-detect | Source language |
| `--output` | stdout | Output file path |
| `--output-dir` | `./translated/` | Output directory (batch mode) |
| `--provider` | `gemini` | `gemini`, `openai`, `anthropic` |
| `--model` | `gemini-3-flash-preview` | Override model |

---

## Resources
- `scripts/translate_text.py` — core script (stdlib urllib, no pip required)

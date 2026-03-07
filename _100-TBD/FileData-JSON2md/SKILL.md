---
name: converting-json-to-markdown
description: Converts JSON files or strings into human-readable Markdown — arrays of objects become tables, nested objects become sections and bullet lists. Use when the user mentions JSON to Markdown, pretty-printing JSON for docs, or formatting API responses as readable Markdown.
---

# FileData-JSON2md Skill

## When to Use This Skill
- User wants to convert a `.json` file or JSON string to Markdown
- User says "format this JSON for docs", "JSON to Markdown", or "pretty print JSON as Markdown"
- Preparing API responses or config files for human reading or LLM ingestion

---

## Output Logic

| JSON structure | Markdown output |
|---|---|
| Array of flat objects | Markdown table |
| Array of mixed/nested | Numbered list with nested bullets |
| Top-level object | Sections (`##`) per key, recursively rendered |
| Primitive (string/number) | Plain inline code |

---

## Workflow
- [ ] 1. Provide `--input` (file) or `--json` (inline string)
- [ ] 2. Run `scripts/json2md.py`
- [ ] 3. Review output structure and adjust `--depth` if needed

---

## Commands

```bash
# From file
python3 scripts/json2md.py --input "response.json"

# From inline JSON string
python3 scripts/json2md.py --json '{"name": "Alice", "score": 99}'

# Limit nesting depth
python3 scripts/json2md.py --input "deep.json" --depth 3

# Save output
python3 scripts/json2md.py --input "data.json" --output "data.md"
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--input` | — | Input `.json` file path |
| `--json` | — | Inline JSON string |
| `--output` | stdout | Output `.md` file path |
| `--depth` | unlimited | Max nesting depth to render |
| `--title` | filename/untitled | Top-level `#` heading |

---

## Resources
- `scripts/json2md.py` — core conversion (stdlib only, no pip install)

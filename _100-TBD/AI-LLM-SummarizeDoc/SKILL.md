---
name: summarizing-documents-with-llm
description: Summarizes any text, Markdown, or PDF file using an LLM API call. Handles long documents by chunking automatically. Use when the user asks to summarize a document, get a TL;DR, or condense a file with AI.
---

# AI-LLM-SummarizeDoc Skill

## When to Use This Skill
- User says "summarize this", "TL;DR this document", "condense this file", or "get key points from this"
- Generating executive summaries for long docs
- Summarizing PDF content after PDF2md conversion

---

## Prerequisites

```bash
export OPENAI_API_KEY="sk-..."         # OpenAI (default)
# OR
export ANTHROPIC_API_KEY="sk-ant-..."  # Anthropic Claude
```

---

## Workflow
- [ ] 1. Set API key
- [ ] 2. Run `scripts/summarize_doc.py --input file.txt`
- [ ] 3. Review output — adjust `--style` or `--length` if needed

---

## Commands

```bash
# Summarize a file
python3 scripts/summarize_doc.py --input report.txt

# Custom style and length
python3 scripts/summarize_doc.py --input report.md \
  --style "executive bullet points" --length short

# Use Anthropic Claude
python3 scripts/summarize_doc.py --input doc.txt --provider anthropic

# Save summary to file
python3 scripts/summarize_doc.py --input report.pdf.md --output summary.md

# Summarize inline text
python3 scripts/summarize_doc.py --text "Long text here..."
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--input` | — | Input file (`.txt`, `.md`) |
| `--text` | — | Inline text to summarize |
| `--output` | stdout | Save summary to file |
| `--style` | `"concise paragraph"` | Summary style/format instruction |
| `--length` | `medium` | `short` (~100 words), `medium` (~250), `long` (~500) |
| `--provider` | `openai` | `openai` or `anthropic` |
| `--model` | `gpt-4o` / `claude-3-5-sonnet` | Override model |
| `--chunk-size` | `3000` | Token chunk size for long docs |

---

## Resources
- `scripts/summarize_doc.py` — core script (stdlib urllib, no pip required)

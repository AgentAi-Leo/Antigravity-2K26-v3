---
name: splitting-text-into-chunks
description: Splits large text files or strings into token-safe chunks for LLM context windows, with optional overlap. Use when the user asks to chunk a document, split text for LLM, create overlapping chunks, or prepare a document for RAG ingestion.
---

# AI-LLM-ChunkSplitter Skill

## When to Use This Skill
- User says "chunk this document", "split for LLM", "context window too large", or "prepare for RAG"
- Pre-processing long docs before sending to an LLM
- Building a vector store — each chunk becomes an embedding unit

---

## Chunking Strategies

| Strategy | Description |
|---|---|
| `tokens` | Split by estimated token count (default) |
| `chars` | Split by character count |
| `sentences` | Split by sentence boundaries |
| `paragraphs` | Split by blank lines |

---

## Workflow
- [ ] 1. Run `scripts/chunk_splitter.py` on your input file
- [ ] 2. Adjust `--size` and `--overlap` to fit your model's context window
- [ ] 3. Review the output chunks

---

## Commands

```bash
# Chunk a file into ~1000-token chunks
python3 scripts/chunk_splitter.py --input document.txt

# Custom size and 10% overlap
python3 scripts/chunk_splitter.py --input doc.md --size 800 --overlap 80

# Split by paragraphs
python3 scripts/chunk_splitter.py --input doc.txt --strategy paragraphs

# Output as JSON array (for downstream processing)
python3 scripts/chunk_splitter.py --input doc.txt --format json --output chunks.json

# Output as numbered .txt files
python3 scripts/chunk_splitter.py --input doc.txt --format files --output-dir ./chunks/
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--input` | *(required)* | Input text/Markdown file |
| `--size` | `1000` | Chunk size (tokens or chars) |
| `--overlap` | `0` | Overlap between chunks |
| `--strategy` | `tokens` | `tokens`, `chars`, `sentences`, `paragraphs` |
| `--format` | `json` | `json`, `files`, or `plain` |
| `--output` | stdout | Output file path (for JSON/plain) |
| `--output-dir` | `./chunks/` | Directory for `files` format |

---

## Token Estimation

Uses `len(text.split()) * 1.3` as a fast token approximation (no tiktoken required). For exact GPT-4 token counts, install `tiktoken`:
```bash
python3 -m pip install tiktoken --target ../../_libs/
```

---

## Resources
- `scripts/chunk_splitter.py` — core script (stdlib only + optional tiktoken)

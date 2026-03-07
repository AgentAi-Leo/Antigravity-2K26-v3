---
name: generating-text-embeddings
description: Generates vector embeddings for text strings or documents using the OpenAI Embeddings API. Outputs JSON arrays suitable for vector databases or similarity search. Use when the user asks to embed text, generate vectors, create embeddings for RAG, or prepare text for similarity search.
---

# AI-LLM-EmbedText Skill

## When to Use This Skill
- User says "embed this text", "generate vectors", "prepare for RAG", or "similarity search"
- Building a vector store or knowledge base
- Computing semantic similarity between documents

---

## Prerequisites

```bash
export OPENAI_API_KEY="sk-..."
```

---

## Workflow
- [ ] 1. Set `OPENAI_API_KEY`
- [ ] 2. Run `scripts/embed_text.py` with your input
- [ ] 3. Use the output JSON embeddings downstream (vector DB, cosine similarity, etc.)

---

## Commands

```bash
# Embed a single text string
python3 scripts/embed_text.py --text "What is machine learning?"

# Embed all lines of a file (one embedding per line)
python3 scripts/embed_text.py --input texts.txt --output embeddings.json

# Embed chunks from a directory (e.g. output from ChunkSplitter)
python3 scripts/embed_text.py --input-dir ./chunks/ --output embeddings.json

# Compute cosine similarity between two texts
python3 scripts/embed_text.py --compare "Machine learning" "Deep learning"

# Use a different embedding model
python3 scripts/embed_text.py --text "Hello" --model text-embedding-3-small
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--text` | — | Single text string to embed |
| `--input` | — | File with one text per line |
| `--input-dir` | — | Directory of `.txt`/`.md` files to embed |
| `--output` | stdout | Save embeddings JSON to file |
| `--model` | `text-embedding-3-large` | OpenAI embedding model |
| `--compare` | — | Two strings to embed and compare (cosine similarity) |

---

## Output Format

```json
[
  {"text": "What is ML?", "embedding": [0.012, -0.034, ...], "model": "text-embedding-3-large"},
  ...
]
```

---

## Resources
- `scripts/embed_text.py` — core script (stdlib urllib, no pip required)

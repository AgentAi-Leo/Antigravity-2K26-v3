---
name: querying-documents-with-rag
description: Implements a local Retrieval-Augmented Generation (RAG) pipeline. Embeds a set of documents using Gemini embeddings, stores a local vector index, and answers questions by retrieving the most relevant chunks and passing them to an LLM. Use when the user asks to query documents, answer questions from files, search a knowledge base, or build a RAG pipeline.
---

# AI-LLM-RAGQuery Skill

## When to Use This Skill
- User says "query these documents", "answer questions from this folder", "search my knowledge base", or "build a RAG pipeline"
- Building a local chatbot over a private document set
- Semantic search across a large collection of `.txt`/`.md` files

---

## How It Works

```
Documents → Chunk → Embed (Gemini) → Save index.json
Query → Embed query → Cosine similarity → Top-K chunks → LLM → Answer
```

---

## Prerequisites

```bash
export GEMINI_API_KEY="..."    # for both embeddings and generation
```

---

## Workflow
- [ ] 1. Index your documents: `scripts/rag_query.py --index --docs ./docs/`
- [ ] 2. Query: `scripts/rag_query.py --query "What is the refund policy?"`
- [ ] 3. (Optional) Save the index once, reuse for future queries

---

## Commands

```bash
# Step 1: Index a folder of documents (saves index.json)
python3 scripts/rag_query.py --index --docs ./docs/

# Step 1b: Index a single file
python3 scripts/rag_query.py --index --docs ./manual.md

# Step 2: Query using the saved index
python3 scripts/rag_query.py --query "What is the refund policy?"

# One-shot: index + query together
python3 scripts/rag_query.py --index --docs ./docs/ --query "How do I reset my password?"

# Control chunks returned to LLM
python3 scripts/rag_query.py --query "..." --top-k 5

# Use a custom index file location
python3 scripts/rag_query.py --index --docs ./docs/ --index-file ./my_index.json
python3 scripts/rag_query.py --query "..." --index-file ./my_index.json

# Just retrieve chunks, don't call LLM (search-only mode)
python3 scripts/rag_query.py --query "refund policy" --search-only
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--index` | off | Build/update the vector index |
| `--docs` | — | Path to `.txt`/`.md` file or directory |
| `--query` | — | Question to answer |
| `--search-only` | off | Return chunks only, skip LLM |
| `--top-k` | `3` | Number of chunks to retrieve |
| `--chunk-size` | `500` | Tokens per chunk |
| `--index-file` | `./rag_index.json` | Index storage location |
| `--provider` | `gemini` | `gemini` or `openai` |
| `--model` | `gemini-3-flash-preview` | LLM for generation |
| `--embed-model` | `gemini-embedding-001` | Embedding model |

---

## Index File Format
The index is a plain JSON file — portable, inspectable, no vector DB required:
```json
[
  {"source": "docs/faq.md", "chunk": 1, "text": "...", "embedding": [0.01, -0.03, ...]}
]
```

---

## Resources
- `scripts/rag_query.py` — full RAG pipeline (stdlib urllib + math, no pip required)

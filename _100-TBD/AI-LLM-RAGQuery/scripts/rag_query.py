import os
import sys
import json
import math
import argparse
import urllib.request
import urllib.error


# ── Embedding helpers ─────────────────────────────────────────────────────────

def _embed_gemini(texts: list, model: str, api_key: str) -> list:
    embeddings = []
    for text in texts:
        body = {"content": {"parts": [{"text": text}]}}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent?key={api_key}"
        req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                embeddings.append(json.loads(resp.read())["embedding"]["values"])
        except urllib.error.HTTPError as e:
            print(f"Embedding error HTTP {e.code}: {e.read().decode()[:200]}")
            sys.exit(1)
    return embeddings


def _embed_openai(texts: list, model: str, api_key: str) -> list:
    body = {"input": texts, "model": model}
    req = urllib.request.Request(
        "https://api.openai.com/v1/embeddings",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return [item["embedding"] for item in json.loads(resp.read())["data"]]


def _cosine(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    return dot / (mag_a * mag_b) if mag_a and mag_b else 0.0


# ── Text chunking ─────────────────────────────────────────────────────────────

def _chunk(text: str, size: int) -> list:
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunk_words = words[i:i + size]
        chunks.append(" ".join(chunk_words))
        i += size
    return [c for c in chunks if c.strip()]


# ── LLM generation ────────────────────────────────────────────────────────────

def _generate_gemini(system: str, user: str, model: str, api_key: str) -> str:
    body = {"contents": [{"role": "user", "parts": [{"text": f"{system}\n\n{user}"}]}],
            "generationConfig": {"maxOutputTokens": 2048}}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())["candidates"][0]["content"]["parts"][0]["text"].strip()


def _generate_openai(system: str, user: str, model: str, api_key: str) -> str:
    body = {"model": model, "messages": [{"role": "system", "content": system},
                                          {"role": "user", "content": user}], "max_tokens": 2048}
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {api_key}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())["choices"][0]["message"]["content"].strip()


# ── Index building ────────────────────────────────────────────────────────────

def _collect_files(path: str) -> list:
    if os.path.isfile(path):
        return [path]
    files = []
    for root, _, fnames in os.walk(path):
        for f in fnames:
            if os.path.splitext(f)[1].lower() in {".txt", ".md"}:
                files.append(os.path.join(root, f))
    return sorted(files)


def build_index(docs_path: str, chunk_size: int, index_file: str,
                embed_model: str, provider: str, api_key: str) -> list:
    files = _collect_files(docs_path)
    if not files:
        print(f"No .txt/.md files found in '{docs_path}'")
        sys.exit(1)

    print(f"Indexing {len(files)} file(s)...")
    index = []
    for fpath in files:
        with open(fpath, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()
        chunks = _chunk(text, chunk_size)
        print(f"  {os.path.basename(fpath)}: {len(chunks)} chunk(s)")
        embed_fn = _embed_gemini if provider == "gemini" else _embed_openai
        embeddings = embed_fn(chunks, embed_model, api_key)
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            index.append({"source": fpath, "chunk": i + 1, "text": chunk, "embedding": emb})

    with open(index_file, "w", encoding="utf-8") as f:
        json.dump(index, f)
    print(f"Index saved: {index_file}  ({len(index)} chunks total)")
    return index


# ── Query ─────────────────────────────────────────────────────────────────────

def query_index(question: str, index: list, top_k: int,
                embed_model: str, provider: str, api_key: str,
                gen_model: str, search_only: bool) -> None:
    embed_fn = _embed_gemini if provider == "gemini" else _embed_openai
    q_emb = embed_fn([question], embed_model, api_key)[0]

    # Score all chunks
    scored = [(entry, _cosine(q_emb, entry["embedding"])) for entry in index]
    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:top_k]

    print(f"\n📎 Top {top_k} relevant chunks:\n")
    context_parts = []
    for i, (entry, score) in enumerate(top, 1):
        src = os.path.basename(entry["source"])
        snippet = entry["text"][:120].replace("\n", " ")
        print(f"  {i}. [{score:.3f}] {src} (chunk {entry['chunk']}): {snippet}...")
        context_parts.append(f"[Source: {src}, chunk {entry['chunk']}]\n{entry['text']}")

    if search_only:
        return

    context = "\n\n---\n\n".join(context_parts)
    system = (
        "You are a helpful assistant. Answer the question using ONLY the provided context. "
        "If the answer is not in the context, say 'I don't have information about that in the provided documents.' "
        "Cite the source filename when referencing specific information."
    )
    user = f"Context:\n{context}\n\nQuestion: {question}"

    print(f"\n🤖 Answer:\n")
    if provider == "gemini":
        answer = _generate_gemini(system, user, gen_model, api_key)
    else:
        answer = _generate_openai(system, user, gen_model, api_key)
    print(answer)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Local RAG pipeline: index docs, query with LLM.")
    parser.add_argument("--index",      action="store_true", help="Build/update vector index")
    parser.add_argument("--docs",       default=None,        help="File or directory to index")
    parser.add_argument("--query",      default=None,        help="Question to answer")
    parser.add_argument("--search-only", action="store_true", help="Retrieve chunks only, skip LLM")
    parser.add_argument("--top-k",      type=int, default=3, help="Chunks to retrieve (default: 3)")
    parser.add_argument("--chunk-size", type=int, default=500, help="Words per chunk (default: 500)")
    parser.add_argument("--index-file", default="./rag_index.json", help="Index storage path")
    parser.add_argument("--provider",   default="gemini",    choices=["gemini", "openai"])
    parser.add_argument("--model",      default=None,        help="LLM model override")
    parser.add_argument("--embed-model", default=None,       help="Embedding model override")
    args = parser.parse_args()

    if not args.index and not args.query:
        parser.error("Specify --index, --query, or both.")
    if args.index and not args.docs:
        parser.error("--index requires --docs")

    # Resolve API key and model defaults
    if args.provider == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            print("Error: GEMINI_API_KEY not set.\nGet one free at: https://aistudio.google.com")
            sys.exit(1)
        embed_model = args.embed_model or "gemini-embedding-001"
        gen_model   = args.model       or "gemini-3-flash-preview"
    else:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            print("Error: OPENAI_API_KEY not set."); sys.exit(1)
        embed_model = args.embed_model or "text-embedding-3-large"
        gen_model   = args.model       or "gpt-4o"

    # Build index
    if args.index:
        index = build_index(args.docs, args.chunk_size, args.index_file,
                            embed_model, args.provider, api_key)
    else:
        if not os.path.exists(args.index_file):
            print(f"Error: index file '{args.index_file}' not found. Run --index first.")
            sys.exit(1)
        print(f"Loading index: {args.index_file}")
        with open(args.index_file, "r", encoding="utf-8") as f:
            index = json.load(f)
        print(f"  {len(index)} chunks loaded.")

    # Query
    if args.query:
        query_index(args.query, index, args.top_k,
                    embed_model, args.provider, api_key,
                    gen_model, args.search_only)


if __name__ == "__main__":
    main()

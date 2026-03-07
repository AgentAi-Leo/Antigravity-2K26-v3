import os
import sys
import json
import math
import argparse
import urllib.request
import urllib.error


def _call_embeddings(texts: list, model: str, api_key: str) -> list:
    body = {"input": texts, "model": model}
    req = urllib.request.Request(
        "https://api.openai.com/v1/embeddings",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
            return [item["embedding"] for item in data["data"]]
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {err[:300]}")
        sys.exit(1)


def _call_gemini_embeddings(texts: list, model: str, api_key: str) -> list:
    """Google Gemini Embeddings API — one request per text."""
    embeddings = []
    for text in texts:
        body = {"content": {"parts": [{"text": text}]}}
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:embedContent?key={api_key}"
        req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                embeddings.append(json.loads(resp.read())["embedding"]["values"])
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="replace")
            print(f"HTTP {e.code}: {err[:300]}"); sys.exit(1)
    return embeddings


def _cosine_similarity(a: list, b: list) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    return dot / (mag_a * mag_b) if mag_a and mag_b else 0.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate text embeddings using OpenAI.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text",      help="Single text string to embed")
    group.add_argument("--input",     help="File with one text per line")
    group.add_argument("--input-dir", help="Directory of .txt/.md files to embed")
    group.add_argument("--compare",   nargs=2, metavar=("TEXT_A", "TEXT_B"),
                       help="Two texts to compare (outputs cosine similarity)")
    parser.add_argument("--output",   default=None, help="Save embeddings JSON to file")
    parser.add_argument("--model",    default=None, help="Model override (gemini: text-embedding-004, openai: text-embedding-3-large)")
    parser.add_argument("--provider", default="gemini", choices=["openai", "gemini"])
    args = parser.parse_args()

    if args.provider == "gemini":
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            print("Error: GEMINI_API_KEY not set.\nGet one free at: https://aistudio.google.com"); sys.exit(1)
        model_name = args.model or "gemini-embedding-001"
        embed_fn = lambda texts: _call_gemini_embeddings(texts, model_name, api_key)
        batch_size = 1
    else:
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            print("Error: OPENAI_API_KEY not set."); sys.exit(1)
        model_name = args.model or "text-embedding-3-large"
        embed_fn = lambda texts: _call_embeddings(texts, model_name, api_key)
        batch_size = 100

    if args.compare:
        embeddings = embed_fn(list(args.compare))
        sim = _cosine_similarity(embeddings[0], embeddings[1])
        print(f"Cosine similarity: {sim:.4f}")
        print(f"  '{args.compare[0]}' vs '{args.compare[1]}'")
        return

    # Collect texts
    texts = []
    if args.text:
        texts = [args.text]
    elif args.input:
        if not os.path.exists(args.input):
            print(f"Error: '{args.input}' not found."); sys.exit(1)
        with open(args.input, "r", encoding="utf-8") as f:
            texts = [line.strip() for line in f if line.strip()]
    elif args.input_dir:
        if not os.path.isdir(args.input_dir):
            print(f"Error: '{args.input_dir}' is not a directory."); sys.exit(1)
        for fname in sorted(os.listdir(args.input_dir)):
            if os.path.splitext(fname)[1].lower() in {".txt", ".md"}:
                with open(os.path.join(args.input_dir, fname), "r", encoding="utf-8") as f:
                    texts.append(f.read().strip())

    if not texts:
        print("No text to embed."); sys.exit(1)

    print(f"Embedding {len(texts)} text(s) with {model_name} ({args.provider})...")

    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        all_embeddings.extend(embed_fn(batch))

    results = [
        {"index": i + 1, "text": texts[i][:100] + ("..." if len(texts[i]) > 100 else ""),
         "model": model_name, "embedding": emb}
        for i, emb in enumerate(all_embeddings)
    ]

    output = json.dumps(results, indent=2)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output + "\n")
        print(f"Saved: {args.output}  ({len(results)} embeddings, dim={len(all_embeddings[0])})")
    else:
        # Print just a summary for single text
        if len(results) == 1:
            emb = all_embeddings[0]
            print(f"Embedding ({len(emb)} dims): [{', '.join(f'{x:.4f}' for x in emb[:5])}...]")
        else:
            print(output)


if __name__ == "__main__":
    main()

import os
import sys
import re
import json
import argparse


# ---------------------------------------------------------------------------
# Tokenization helpers
# ---------------------------------------------------------------------------

def _estimate_tokens(text: str) -> int:
    """Fast approximation: words * 1.3"""
    return int(len(text.split()) * 1.3)


def _exact_tokens(text: str, encoding) -> int:
    return len(encoding.encode(text))


def _get_token_fn(use_tiktoken: bool):
    if use_tiktoken:
        try:
            sys.path.insert(0, os.path.abspath(
                os.path.join(os.path.dirname(__file__), "..", "..", "_libs")))
            import tiktoken
            enc = tiktoken.get_encoding("cl100k_base")
            return lambda t: _exact_tokens(t, enc)
        except ImportError:
            print("Warning: tiktoken not found, falling back to word estimate.", file=sys.stderr)
    return _estimate_tokens


# ---------------------------------------------------------------------------
# Splitting strategies
# ---------------------------------------------------------------------------

def _split_chars(text: str, size: int, overlap: int) -> list:
    chunks, i = [], 0
    while i < len(text):
        chunks.append(text[i:i + size])
        i += max(size - overlap, 1)
    return chunks


def _split_sentences(text: str, size: int, overlap: int, token_fn) -> list:
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return _pack(sentences, size, overlap, token_fn)


def _split_paragraphs(text: str, size: int, overlap: int, token_fn) -> list:
    paras = [p.strip() for p in re.split(r'\n{2,}', text) if p.strip()]
    return _pack(paras, size, overlap, token_fn)


def _split_tokens(text: str, size: int, overlap: int, token_fn) -> list:
    words = text.split()
    chunks, i = [], 0
    while i < len(words):
        chunk_words = []
        total = 0
        j = i
        while j < len(words) and total < size:
            chunk_words.append(words[j])
            total = token_fn(" ".join(chunk_words))
            j += 1
        chunks.append(" ".join(chunk_words))
        step = max(len(chunk_words) - int(overlap / 1.3), 1)
        i += step
    return chunks


def _pack(units: list, size: int, overlap: int, token_fn) -> list:
    """Pack units into chunks respecting size and overlap."""
    chunks, current, current_tokens = [], [], 0
    for unit in units:
        unit_tokens = token_fn(unit)
        if current and current_tokens + unit_tokens > size:
            chunks.append("\n\n".join(current))
            # Keep overlap
            overlap_units = []
            overlap_total = 0
            for u in reversed(current):
                t = token_fn(u)
                if overlap_total + t <= overlap:
                    overlap_units.insert(0, u)
                    overlap_total += t
                else:
                    break
            current = overlap_units
            current_tokens = overlap_total
        current.append(unit)
        current_tokens += unit_tokens
    if current:
        chunks.append("\n\n".join(current))
    return chunks


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def _write_files(chunks: list, output_dir: str, stem: str) -> None:
    os.makedirs(output_dir, exist_ok=True)
    pad = len(str(len(chunks)))
    for i, chunk in enumerate(chunks, 1):
        path = os.path.join(output_dir, f"{stem}_{str(i).zfill(pad)}.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write(chunk + "\n")
    print(f"Saved {len(chunks)} chunk files to: {output_dir}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Split text into LLM-safe chunks.")
    parser.add_argument("--input",       required=True,    help="Input text/Markdown file")
    parser.add_argument("--size",        type=int, default=1000, help="Chunk size in tokens (default: 1000)")
    parser.add_argument("--overlap",     type=int, default=0,    help="Overlap between chunks (default: 0)")
    parser.add_argument("--strategy",    default="tokens",
                        choices=["tokens", "chars", "sentences", "paragraphs"],
                        help="Splitting strategy (default: tokens)")
    parser.add_argument("--format",      default="json",   choices=["json", "files", "plain"],
                        help="Output format (default: json)")
    parser.add_argument("--output",      default=None,     help="Output file (json/plain format)")
    parser.add_argument("--output-dir",  default="./chunks", help="Output directory (files format)")
    parser.add_argument("--tiktoken",    action="store_true", help="Use tiktoken for exact GPT token counts")
    args = parser.parse_args()

    if not os.path.exists(args.input):
        print(f"Error: '{args.input}' not found.")
        sys.exit(1)

    with open(args.input, "r", encoding="utf-8") as f:
        text = f.read()

    token_fn = _get_token_fn(args.tiktoken)

    if args.strategy == "chars":
        chunks = _split_chars(text, args.size, args.overlap)
    elif args.strategy == "sentences":
        chunks = _split_sentences(text, args.size, args.overlap, token_fn)
    elif args.strategy == "paragraphs":
        chunks = _split_paragraphs(text, args.size, args.overlap, token_fn)
    else:
        chunks = _split_tokens(text, args.size, args.overlap, token_fn)

    stem = os.path.splitext(os.path.basename(args.input))[0]

    if args.format == "files":
        _write_files(chunks, args.output_dir, stem)
    elif args.format == "plain":
        output = "\n\n---\n\n".join(chunks)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output + "\n")
            print(f"Saved: {args.output}  ({len(chunks)} chunks)")
        else:
            print(output)
    else:
        result = [{"index": i + 1, "tokens": token_fn(c), "text": c} for i, c in enumerate(chunks)]
        output = json.dumps(result, indent=2, ensure_ascii=False)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(output + "\n")
            print(f"Saved: {args.output}  ({len(chunks)} chunks)")
        else:
            print(output)


if __name__ == "__main__":
    main()

import os
import sys
import json
import argparse
import urllib.request
import urllib.error


LENGTH_WORDS = {"short": 100, "medium": 250, "long": 500}


def _call_openai(messages: list, model: str, api_key: str) -> str:
    body = {"model": model, "messages": messages, "max_tokens": 1024}
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())["choices"][0]["message"]["content"].strip()


def _call_anthropic(system: str, user: str, model: str, api_key: str) -> str:
    body = {
        "model": model,
        "max_tokens": 1024,
        "system": system,
        "messages": [{"role": "user", "content": user}],
    }
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=json.dumps(body).encode(),
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())["content"][0]["text"].strip()


def _call_gemini(system: str, user: str, model: str, api_key: str) -> str:
    full_prompt = f"{system}\n\n{user}" if system else user
    body = {"contents": [{"role": "user", "parts": [{"text": full_prompt}]}],
            "generationConfig": {"maxOutputTokens": 1024}}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())["candidates"][0]["content"]["parts"][0]["text"].strip()


def _chunk_text(text: str, max_chars: int = 12000) -> list:
    """Split on paragraph boundaries if text is too long."""
    if len(text) <= max_chars:
        return [text]
    paragraphs = text.split("\n\n")
    chunks, current = [], ""
    for p in paragraphs:
        if len(current) + len(p) > max_chars and current:
            chunks.append(current.strip())
            current = p
        else:
            current += ("\n\n" + p if current else p)
    if current.strip():
        chunks.append(current.strip())
    return chunks


def summarize(text: str, style: str, length: str, provider: str, model: str) -> str:
    word_count = LENGTH_WORDS.get(length, 250)
    system = f"You are an expert at summarizing documents. Be accurate and concise."
    user = (
        f"Summarize the following text in {style}. "
        f"Aim for approximately {word_count} words.\n\n"
        f"---\n{text}\n---"
    )

    if provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            print("Error: OPENAI_API_KEY not set."); sys.exit(1)
        return _call_openai(
            [{"role": "system", "content": system}, {"role": "user", "content": user}],
            model or "gpt-4o", api_key
        )
    elif provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            print("Error: ANTHROPIC_API_KEY not set."); sys.exit(1)
        return _call_anthropic(system, user, model or "claude-3-5-sonnet-20241022", api_key)
    else:  # gemini
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            print("Error: GEMINI_API_KEY not set.\nGet one free at: https://aistudio.google.com"); sys.exit(1)
        return _call_gemini(system, user, model or "gemini-3-flash-preview", api_key)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize a document using an LLM.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input", help="Input file path (.txt, .md)")
    group.add_argument("--text",  help="Inline text to summarize")
    parser.add_argument("--output",   default=None,             help="Save summary to file")
    parser.add_argument("--style",    default="concise paragraph", help="Summary style instruction")
    parser.add_argument("--length",   default="medium",         choices=["short", "medium", "long"])
    parser.add_argument("--provider", default="gemini",          choices=["openai", "anthropic", "gemini"])
    parser.add_argument("--model",    default=None,             help="Override model name")
    parser.add_argument("--chunk-size", type=int, default=12000, help="Chars per chunk for long docs (default: 12000)")
    args = parser.parse_args()

    if args.input:
        if not os.path.exists(args.input):
            print(f"Error: '{args.input}' not found."); sys.exit(1)
        with open(args.input, "r", encoding="utf-8") as f:
            text = f.read()
    else:
        text = args.text

    chunks = _chunk_text(text, args.chunk_size)

    if len(chunks) == 1:
        result = summarize(chunks[0], args.style, args.length, args.provider, args.model)
    else:
        print(f"Long document — summarizing {len(chunks)} chunks then combining...")
        chunk_summaries = [summarize(c, "concise paragraph", "short", args.provider, args.model) for c in chunks]
        combined = "\n\n".join(chunk_summaries)
        result = summarize(combined, args.style, args.length, args.provider, args.model)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result + "\n")
        print(f"Saved: {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()

import os
import sys
import json
import argparse
import urllib.request
import urllib.error


def _call_gemini(system: str, user: str, model: str, api_key: str) -> str:
    body = {"contents": [{"role": "user", "parts": [{"text": f"{system}\n\n{user}"}]}],
            "generationConfig": {"maxOutputTokens": 4096}}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())["candidates"][0]["content"]["parts"][0]["text"].strip()


def _call_openai(system: str, user: str, model: str, api_key: str) -> str:
    body = {"model": model, "messages": [{"role": "system", "content": system},
                                          {"role": "user", "content": user}], "max_tokens": 4096}
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())["choices"][0]["message"]["content"].strip()


def _call_anthropic(system: str, user: str, model: str, api_key: str) -> str:
    body = {"model": model, "max_tokens": 4096, "system": system,
            "messages": [{"role": "user", "content": user}]}
    req = urllib.request.Request("https://api.anthropic.com/v1/messages",
                                 data=json.dumps(body).encode(),
                                 headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())["content"][0]["text"].strip()


def translate(text: str, to_lang: str, from_lang: str, provider: str, model: str) -> str:
    from_clause = f"from {from_lang} " if from_lang else ""
    system = f"You are a professional translator. Translate accurately {from_clause}to {to_lang}. Preserve all Markdown formatting, code blocks, and structural elements exactly. Return ONLY the translated text."
    user = f"Translate the following {from_clause}to {to_lang}:\n\n{text}"

    if provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key: print("Error: OPENAI_API_KEY not set."); sys.exit(1)
        return _call_openai(system, user, model or "gpt-4o", api_key)
    elif provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key: print("Error: ANTHROPIC_API_KEY not set."); sys.exit(1)
        return _call_anthropic(system, user, model or "claude-3-5-sonnet-20241022", api_key)
    else:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key: print("Error: GEMINI_API_KEY not set.\nGet one free at: https://aistudio.google.com"); sys.exit(1)
        return _call_gemini(system, user, model or "gemini-3-flash-preview", api_key)


def main() -> None:
    parser = argparse.ArgumentParser(description="Translate text or files using an LLM.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text",      help="Inline text to translate")
    group.add_argument("--input",     help="Input file path")
    group.add_argument("--input-dir", help="Directory of .txt/.md files to translate")
    parser.add_argument("--to",       required=True, help="Target language (e.g. Spanish, French)")
    parser.add_argument("--from",     default=None,  dest="from_lang", help="Source language (default: auto-detect)")
    parser.add_argument("--output",   default=None,  help="Output file path")
    parser.add_argument("--output-dir", default="./translated", help="Output directory (batch mode)")
    parser.add_argument("--provider", default="gemini", choices=["gemini", "openai", "anthropic"])
    parser.add_argument("--model",    default=None,  help="Override model")
    args = parser.parse_args()

    if args.text:
        result = translate(args.text, args.to, args.from_lang, args.provider, args.model)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result + "\n")
            print(f"Saved: {args.output}")
        else:
            print(result)

    elif args.input:
        if not os.path.exists(args.input):
            print(f"Error: '{args.input}' not found."); sys.exit(1)
        with open(args.input, "r", encoding="utf-8") as f:
            text = f.read()
        print(f"Translating: {args.input} → {args.to}")
        result = translate(text, args.to, args.from_lang, args.provider, args.model)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result + "\n")
            print(f"Saved: {args.output}")
        else:
            print(result)

    else:
        if not os.path.isdir(args.input_dir):
            print(f"Error: '{args.input_dir}' not found."); sys.exit(1)
        os.makedirs(args.output_dir, exist_ok=True)
        files = [f for f in os.listdir(args.input_dir)
                 if os.path.splitext(f)[1].lower() in {".txt", ".md"}]
        if not files:
            print("No .txt/.md files found."); sys.exit(0)
        for fname in sorted(files):
            fpath = os.path.join(args.input_dir, fname)
            with open(fpath, "r", encoding="utf-8") as f:
                text = f.read()
            print(f"Translating: {fname}")
            result = translate(text, args.to, args.from_lang, args.provider, args.model)
            stem, ext = os.path.splitext(fname)
            out_path = os.path.join(args.output_dir, f"{stem}.{args.to.lower()}{ext}")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(result + "\n")
            print(f"  → Saved: {out_path}")


if __name__ == "__main__":
    main()

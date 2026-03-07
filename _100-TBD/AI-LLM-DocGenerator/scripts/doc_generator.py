import os
import sys
import json
import argparse
import urllib.request
import urllib.error


LANG_MAP = {".py": "python", ".js": "javascript", ".ts": "typescript",
            ".go": "go", ".rs": "rust", ".rb": "ruby", ".java": "java",
            ".cpp": "cpp", ".c": "c", ".sh": "bash"}

MODE_PROMPTS = {
    "docstrings": (
        "Add complete docstrings/comments to every function, class, and module. "
        "Use the language-appropriate format (Python: Google-style docstrings, JS/TS: JSDoc, Go: godoc). "
        "Return ONLY the complete updated source code with docstrings added. No explanation outside the code."
    ),
    "readme": (
        "Write a comprehensive README.md for this code. Include: ## Overview, ## Installation, "
        "## Usage (with examples), ## API Reference (for each function/class), ## Configuration. "
        "Return ONLY the Markdown content."
    ),
    "comments": (
        "Add inline comments explaining complex logic, non-obvious decisions, and important sections. "
        "Do not over-comment obvious lines. Return ONLY the complete updated source code."
    ),
}


def _detect_lang(filename: str) -> str:
    return LANG_MAP.get(os.path.splitext(filename)[1].lower(), "code")


def _call_gemini(system: str, user: str, model: str, api_key: str) -> str:
    body = {"contents": [{"role": "user", "parts": [{"text": f"{system}\n\n{user}"}]}],
            "generationConfig": {"maxOutputTokens": 8192}}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())["candidates"][0]["content"]["parts"][0]["text"].strip()


def _call_openai(system: str, user: str, model: str, api_key: str) -> str:
    body = {"model": model, "messages": [{"role": "system", "content": system},
                                          {"role": "user", "content": user}], "max_tokens": 8192}
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())["choices"][0]["message"]["content"].strip()


def _call_anthropic(system: str, user: str, model: str, api_key: str) -> str:
    body = {"model": model, "max_tokens": 8192, "system": system,
            "messages": [{"role": "user", "content": user}]}
    req = urllib.request.Request("https://api.anthropic.com/v1/messages",
                                 data=json.dumps(body).encode(),
                                 headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())["content"][0]["text"].strip()


def process_file(filepath: str, mode: str, lang: str, provider: str, model: str) -> str:
    with open(filepath, "r", encoding="utf-8") as f:
        code = f.read()
    filename = os.path.basename(filepath)
    detected = lang or _detect_lang(filename)
    system = MODE_PROMPTS[mode]
    user = f"File: `{filename}` ({detected})\n\n```{detected}\n{code}\n```"

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
        return _call_gemini(system, user, model or "gemini-3.1-pro-preview", api_key)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate documentation for code files.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input",     help="Single source file")
    group.add_argument("--input-dir", help="Directory of files to document")
    parser.add_argument("--lang",     default=None,         help="Language override")
    parser.add_argument("--mode",     default="docstrings",  choices=list(MODE_PROMPTS.keys()))
    parser.add_argument("--output",   default=None,          help="Output file (single mode)")
    parser.add_argument("--provider", default="gemini",      choices=["gemini", "openai", "anthropic"])
    parser.add_argument("--model",    default=None,          help="Override model")
    args = parser.parse_args()

    if args.input:
        if not os.path.exists(args.input):
            print(f"Error: '{args.input}' not found."); sys.exit(1)
        print(f"Documenting: {args.input}  (mode: {args.mode})")
        result = process_file(args.input, args.mode, args.lang, args.provider, args.model)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result + "\n")
            print(f"Saved: {args.output}")
        else:
            print(result)

    else:
        if not os.path.isdir(args.input_dir):
            print(f"Error: '{args.input_dir}' not found."); sys.exit(1)
        extensions = set(LANG_MAP.keys())
        files = [f for f in os.listdir(args.input_dir)
                 if os.path.splitext(f)[1].lower() in extensions]
        if not files:
            print("No supported source files found."); sys.exit(0)
        for fname in sorted(files):
            fpath = os.path.join(args.input_dir, fname)
            print(f"Documenting: {fname}")
            result = process_file(fpath, args.mode, args.lang, args.provider, args.model)
            ext = ".md" if args.mode == "readme" else os.path.splitext(fname)[1]
            out_name = os.path.splitext(fname)[0] + "_documented" + ext
            out_path = os.path.join(args.input_dir, out_name)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(result + "\n")
            print(f"  → Saved: {out_path}")


if __name__ == "__main__":
    main()

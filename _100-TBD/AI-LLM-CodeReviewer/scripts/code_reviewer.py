import os
import sys
import json
import argparse
import subprocess
import urllib.request
import urllib.error


FOCUS_PROMPTS = {
    "security": "Focus specifically on: authentication flaws, SQL injection, XSS, hardcoded secrets, insecure data handling, and authorization issues.",
    "bugs":     "Focus specifically on: logic errors, null pointer risks, off-by-one errors, race conditions, incorrect error handling, and edge cases.",
    "style":    "Focus specifically on: naming conventions, code duplication, function length, readability, and adherence to language idioms.",
    "performance": "Focus specifically on: unnecessary loops, redundant computations, memory leaks, N+1 query patterns, and inefficient algorithms.",
    "all":      "Cover all aspects: bugs, security, performance, style, and maintainability.",
}


def _build_prompt(code: str, filename: str, focus: str, lang: str) -> tuple[str, str]:
    focus_instruction = FOCUS_PROMPTS.get(focus, FOCUS_PROMPTS["all"])
    system = (
        "You are an expert code reviewer. Provide clear, actionable feedback. "
        "Format your response as Markdown with sections: ## Summary, ## Issues (with severity: 🔴 Critical / 🟡 Warning / 🔵 Info), ## Suggestions."
    )
    user = (
        f"Please review the following {lang} code from `{filename}`.\n"
        f"{focus_instruction}\n\n"
        f"```{lang}\n{code}\n```"
    )
    return system, user


def _call_gemini(system: str, user: str, model: str, api_key: str) -> str:
    full_prompt = f"{system}\n\n{user}"
    body = {"contents": [{"role": "user", "parts": [{"text": full_prompt}]}],
            "generationConfig": {"maxOutputTokens": 4096}}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read())["candidates"][0]["content"]["parts"][0]["text"].strip()


def _call_openai(system: str, user: str, model: str, api_key: str) -> str:
    body = {"model": model, "messages": [{"role": "system", "content": system},
                                          {"role": "user", "content": user}], "max_tokens": 4096}
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read())["choices"][0]["message"]["content"].strip()


def _call_anthropic(system: str, user: str, model: str, api_key: str) -> str:
    body = {"model": model, "max_tokens": 4096, "system": system,
            "messages": [{"role": "user", "content": user}]}
    req = urllib.request.Request("https://api.anthropic.com/v1/messages",
                                 data=json.dumps(body).encode(),
                                 headers={"x-api-key": api_key, "anthropic-version": "2023-06-01",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=90) as resp:
        return json.loads(resp.read())["content"][0]["text"].strip()


def _get_diff(commit: str | None) -> str:
    if commit:
        result = subprocess.run(["git", "show", commit], capture_output=True, text=True)
    else:
        result = subprocess.run(["git", "diff", "--staged"], capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: git command failed — {result.stderr.strip()}")
        sys.exit(1)
    return result.stdout


def _detect_lang(filename: str) -> str:
    ext_map = {".py": "python", ".js": "javascript", ".ts": "typescript",
               ".go": "go", ".rs": "rust", ".rb": "ruby", ".java": "java",
               ".cpp": "cpp", ".c": "c", ".sh": "bash", ".sql": "sql"}
    ext = os.path.splitext(filename)[1].lower()
    return ext_map.get(ext, "code")


def main() -> None:
    parser = argparse.ArgumentParser(description="AI code review for a file or git diff.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input",  help="Source file to review")
    group.add_argument("--diff",   action="store_true", help="Review git diff --staged")
    parser.add_argument("--commit",    default=None,   help="Review diff of specific commit hash")
    parser.add_argument("--focus",     default="all",  choices=list(FOCUS_PROMPTS.keys()))
    parser.add_argument("--output",    default=None,   help="Save Markdown report to file")
    parser.add_argument("--provider",  default="gemini", choices=["gemini", "openai", "anthropic"])
    parser.add_argument("--model",     default=None,   help="Override model")
    args = parser.parse_args()

    if args.input:
        if not os.path.exists(args.input):
            print(f"Error: '{args.input}' not found."); sys.exit(1)
        with open(args.input, "r", encoding="utf-8") as f:
            code = f.read()
        filename = os.path.basename(args.input)
        lang = _detect_lang(filename)
    else:
        code = _get_diff(args.commit)
        filename = args.commit or "staged changes"
        lang = "diff"

    if not code.strip():
        print("Nothing to review."); sys.exit(0)

    system, user = _build_prompt(code, filename, args.focus, lang)
    print(f"Reviewing {filename} (focus: {args.focus}, provider: {args.provider})...")

    if args.provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key: print("Error: OPENAI_API_KEY not set."); sys.exit(1)
        result = _call_openai(system, user, args.model or "gpt-4o", api_key)
    elif args.provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key: print("Error: ANTHROPIC_API_KEY not set."); sys.exit(1)
        result = _call_anthropic(system, user, args.model or "claude-3-5-sonnet-20241022", api_key)
    else:
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key: print("Error: GEMINI_API_KEY not set.\nGet one free at: https://aistudio.google.com"); sys.exit(1)
        result = _call_gemini(system, user, args.model or "gemini-3.1-pro-preview", api_key)

    output = f"# Code Review — `{filename}`\n\n> Focus: {args.focus}  |  Model: {args.model or args.provider}\n\n{result}"

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output + "\n")
        print(f"Saved: {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()

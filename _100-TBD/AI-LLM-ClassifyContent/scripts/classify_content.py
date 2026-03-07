import os
import sys
import json
import argparse
import urllib.request
import urllib.error


def _call_openai(system: str, user: str, model: str, api_key: str) -> str:
    body = {
        "model": model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_tokens": 256,
        "temperature": 0,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())["choices"][0]["message"]["content"].strip()


def _call_anthropic(system: str, user: str, model: str, api_key: str) -> str:
    body = {
        "model": model, "max_tokens": 256,
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
            "generationConfig": {"maxOutputTokens": 256, "temperature": 0}}
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())["candidates"][0]["content"]["parts"][0]["text"].strip()


def _build_prompt(text: str, categories: dict, score_mode: bool) -> tuple[str, str]:
    cat_list = "\n".join(f"- {k}: {v}" for k, v in categories.items())
    if score_mode:
        system = (
            "You are a content classifier. For each category, output a confidence score (0.0–1.0). "
            "Respond ONLY with a valid JSON object: {\"category_name\": score, ...}. No explanation."
        )
        user = f"Categories:\n{cat_list}\n\nText to classify:\n\"\"\"\n{text}\n\"\"\""
    else:
        cat_names = ", ".join(f'"{k}"' for k in categories)
        system = (
            f"You are a content classifier. Choose exactly one category from: {cat_names}. "
            "Respond ONLY with the category name. No explanation."
        )
        user = f"Categories:\n{cat_list}\n\nText to classify:\n\"\"\"\n{text}\n\"\"\""
    return system, user


def classify_one(text: str, categories: dict, score_mode: bool, provider: str, model: str) -> str | dict:
    system, user = _build_prompt(text, categories, score_mode)

    if provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            print("Error: OPENAI_API_KEY not set."); sys.exit(1)
        raw = _call_openai(system, user, model or "gpt-4o", api_key)
    elif provider == "anthropic":
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            print("Error: ANTHROPIC_API_KEY not set."); sys.exit(1)
        raw = _call_anthropic(system, user, model or "claude-3-5-sonnet-20241022", api_key)
    else:  # gemini
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            print("Error: GEMINI_API_KEY not set.\nGet one free at: https://aistudio.google.com"); sys.exit(1)
        raw = _call_gemini(system, user, model or "gemini-3-flash-preview", api_key)

    if score_mode:
        try:
            # Strip any markdown fences
            clean = raw.strip().strip("`").strip()
            if clean.startswith("json"):
                clean = clean[4:].strip()
            return json.loads(clean)
        except json.JSONDecodeError:
            return {"_raw": raw}
    return raw.strip().strip('"')


def main() -> None:
    parser = argparse.ArgumentParser(description="Classify text content using an LLM.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text",  help="Single text string to classify")
    group.add_argument("--input", help="File with one text per line")
    parser.add_argument("--categories",      default=None, help="Comma-separated category names")
    parser.add_argument("--categories-file", default=None, help="JSON file with category descriptions")
    parser.add_argument("--output",   default=None,    help="Save results JSON to file")
    parser.add_argument("--score",    action="store_true", help="Return confidence scores (0.0–1.0)")
    parser.add_argument("--provider", default="gemini",   choices=["openai", "anthropic", "gemini"])
    parser.add_argument("--model",    default=None,       help="Override model name")
    args = parser.parse_args()

    # Build categories dict
    categories = {}
    if args.categories_file:
        with open(args.categories_file, "r", encoding="utf-8") as f:
            categories = json.load(f)
    elif args.categories:
        for cat in args.categories.split(","):
            cat = cat.strip()
            if cat:
                categories[cat] = cat.replace("_", " ")
    else:
        parser.error("Either --categories or --categories-file is required.")

    # Collect texts
    if args.text:
        texts = [args.text]
    else:
        if not os.path.exists(args.input):
            print(f"Error: '{args.input}' not found."); sys.exit(1)
        with open(args.input, "r", encoding="utf-8") as f:
            texts = [line.strip() for line in f if line.strip()]

    results = []
    for i, text in enumerate(texts, 1):
        label = classify_one(text, categories, args.score, args.provider, args.model)
        results.append({"index": i, "text": text[:80] + ("..." if len(text) > 80 else ""),
                        "label" if not args.score else "scores": label})
        icon = "✅" if not args.score else "📊"
        print(f"{icon} [{i}/{len(texts)}] {label}")

    output = json.dumps(results, indent=2, ensure_ascii=False)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(output + "\n")
        print(f"\nSaved: {args.output}")
    elif len(results) > 1:
        print(f"\n{output}")


if __name__ == "__main__":
    main()

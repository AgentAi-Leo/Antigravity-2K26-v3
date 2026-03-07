import os
import sys
import base64
import json
import argparse
import urllib.request
import urllib.error


SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}

DEFAULT_PROMPTS = {
    "openai":    "Describe this image in detail.",
    "anthropic": "Describe this image in detail.",
}


def _encode_image(path: str) -> tuple[str, str]:
    """Return (base64_data, media_type)."""
    ext = os.path.splitext(path)[1].lower()
    media_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                 ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp"}
    media_type = media_map.get(ext, "image/jpeg")
    with open(path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode("utf-8")
    return data, media_type


def _http_post(url: str, headers: dict, body: dict) -> dict:
    payload = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {err[:300]}")
        sys.exit(1)


def caption_openai(image_path: str, prompt: str, model: str, api_key: str) -> str:
    b64, media = _encode_image(image_path)
    body = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:{media};base64,{b64}"}},
                {"type": "text", "text": prompt},
            ]
        }],
        "max_tokens": 1024,
    }
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    resp = _http_post("https://api.openai.com/v1/chat/completions", headers, body)
    return resp["choices"][0]["message"]["content"].strip()


def caption_anthropic(image_path: str, prompt: str, model: str, api_key: str) -> str:
    b64, media = _encode_image(image_path)
    body = {
        "model": model,
        "max_tokens": 1024,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media, "data": b64}},
                {"type": "text", "text": prompt},
            ]
        }],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json",
    }
    resp = _http_post("https://api.anthropic.com/v1/messages", headers, body)
    return resp["content"][0]["text"].strip()


def caption_image(image_path: str, prompt: str, provider: str, model: str) -> str:
    ext = os.path.splitext(image_path)[1].lower()
    if ext not in SUPPORTED_FORMATS:
        print(f"Warning: '{ext}' may not be supported. Supported: {', '.join(SUPPORTED_FORMATS)}")

    if provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            print("Error: OPENAI_API_KEY not set.")
            sys.exit(1)
        return caption_openai(image_path, prompt, model or "gpt-4o", api_key)
    else:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            print("Error: ANTHROPIC_API_KEY not set.")
            sys.exit(1)
        return caption_anthropic(image_path, prompt, model or "claude-3-5-sonnet-20241022", api_key)


def process_dir(input_dir: str, prompt: str, provider: str, model: str, output_path: str | None) -> None:
    images = [f for f in os.listdir(input_dir)
              if os.path.splitext(f)[1].lower() in SUPPORTED_FORMATS]
    if not images:
        print(f"No supported images found in '{input_dir}'.")
        sys.exit(1)

    lines = ["# Image Captions\n"]
    for img in sorted(images):
        path = os.path.join(input_dir, img)
        print(f"Captioning: {img}")
        caption = caption_image(path, prompt, provider, model)
        lines.append(f"## {img}\n\n{caption}\n")

    output = "\n".join(lines)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(output)
        print(f"Saved: {output_path}")
    else:
        print(output)


def main() -> None:
    parser = argparse.ArgumentParser(description="Caption images using a vision LLM.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--input",     help="Single image file path")
    group.add_argument("--input-dir", help="Directory of images for batch captioning")
    parser.add_argument("--output",   default=None,       help="Output file (default: stdout)")
    parser.add_argument("--prompt",   default=None,       help="Custom prompt")
    parser.add_argument("--provider", default="openai",   choices=["openai", "anthropic"])
    parser.add_argument("--model",    default=None,       help="Override model name")
    args = parser.parse_args()

    prompt = args.prompt or DEFAULT_PROMPTS[args.provider]

    if args.input_dir:
        process_dir(args.input_dir, prompt, args.provider, args.model, args.output)
    else:
        if not os.path.exists(args.input):
            print(f"Error: '{args.input}' not found.")
            sys.exit(1)
        caption = caption_image(args.input, prompt, args.provider, args.model)
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(caption + "\n")
            print(f"Saved: {args.output}")
        else:
            print(caption)


if __name__ == "__main__":
    main()

import os
import sys
import json
import base64
import argparse
import urllib.request
import urllib.error
from datetime import datetime


def _call_imagen(prompt: str, model: str, count: int, api_key: str) -> list:
    """Call Google Imagen 4 API. Returns list of base64 PNG bytes."""
    body = {
        "instances": [{"prompt": prompt}],
        "parameters": {"sampleCount": count}
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:predict?key={api_key}"
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            return [pred["bytesBase64Encoded"] for pred in data.get("predictions", [])]
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"HTTP {e.code}: {err[:400]}")
        sys.exit(1)


def _call_dalle(prompt: str, model: str, count: int, size: str, api_key: str) -> list:
    """Call OpenAI DALL-E API. Returns list of URLs."""
    body = {"model": model, "prompt": prompt, "n": count, "size": size, "response_format": "url"}
    req = urllib.request.Request("https://api.openai.com/v1/images/generations",
                                 data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {api_key}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        data = json.loads(resp.read())
        return [img["url"] for img in data["data"]]


def _download_url(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=60) as resp:
        return resp.read()


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate images from text prompts.")
    parser.add_argument("--prompt",   required=True, help="Text description of image to generate")
    parser.add_argument("--output",   default=None,  help="Output file path (single image)")
    parser.add_argument("--count",    type=int, default=1, help="Number of images (default: 1)")
    parser.add_argument("--provider", default="gemini", choices=["gemini", "openai"])
    parser.add_argument("--model",    default=None,  help="Override model")
    parser.add_argument("--size",     default="1024x1024", help="Image size (OpenAI only)")
    args = parser.parse_args()

    os.makedirs("./output", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    if args.provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key: print("Error: OPENAI_API_KEY not set."); sys.exit(1)
        model = args.model or "dall-e-3"
        print(f"Generating {args.count} image(s) with {model}...")
        urls = _call_dalle(args.prompt, model, args.count, args.size, api_key)
        for i, url in enumerate(urls, 1):
            img_bytes = _download_url(url)
            suffix = f"_{i}" if args.count > 1 else ""
            path = args.output if (args.output and args.count == 1) else f"./output/image_{ts}{suffix}.png"
            with open(path, "wb") as f:
                f.write(img_bytes)
            print(f"Saved: {path}")

    else:  # gemini / Imagen
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key: print("Error: GEMINI_API_KEY not set.\nGet one free at: https://aistudio.google.com"); sys.exit(1)
        model = args.model or "imagen-4.0-generate-001"
        print(f"Generating {args.count} image(s) with {model}...")
        b64_list = _call_imagen(args.prompt, model, args.count, api_key)
        if not b64_list:
            print("No images returned from API."); sys.exit(1)
        for i, b64 in enumerate(b64_list, 1):
            img_bytes = base64.b64decode(b64)
            suffix = f"_{i}" if args.count > 1 else ""
            path = args.output if (args.output and args.count == 1) else f"./output/image_{ts}{suffix}.png"
            with open(path, "wb") as f:
                f.write(img_bytes)
            print(f"Saved: {path}")


if __name__ == "__main__":
    main()

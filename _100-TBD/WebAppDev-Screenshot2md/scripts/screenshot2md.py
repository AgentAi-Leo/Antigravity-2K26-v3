import os
import sys
import base64
import json
import argparse
import tempfile
import urllib.request
import urllib.error

# Locate shared _libs/ for Playwright
_script_dir = os.path.dirname(os.path.abspath(__file__))
for _candidate in [
    os.path.join(_script_dir, "..", "libs"),
    os.path.join(_script_dir, "..", "..", "_libs"),
]:
    if os.path.exists(_candidate):
        sys.path.insert(0, os.path.abspath(_candidate))


def _screenshot(url: str, width: int, wait: int, save_path: str | None) -> str:
    """Take a full-page screenshot using Playwright. Returns path to PNG."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Error: playwright not installed.")
        print("Run: pip install playwright && playwright install chromium")
        sys.exit(1)

    tmp = save_path or tempfile.mktemp(suffix=".png")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": width, "height": 900})
        page.goto(url, wait_until="networkidle", timeout=30000)
        if wait > 0:
            page.wait_for_timeout(wait * 1000)
        page.screenshot(path=tmp, full_page=True)
        browser.close()
    return tmp


def _caption_openai(image_path: str, prompt: str, model: str, api_key: str) -> str:
    with open(image_path, "rb") as f:
        b64 = base64.standard_b64encode(f.read()).decode()
    body = {
        "model": model,
        "messages": [{"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64}"}},
            {"type": "text", "text": prompt},
        ]}],
        "max_tokens": 2048,
    }
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read())["choices"][0]["message"]["content"].strip()


def _caption_anthropic(image_path: str, prompt: str, model: str, api_key: str) -> str:
    with open(image_path, "rb") as f:
        b64 = base64.standard_b64encode(f.read()).decode()
    body = {
        "model": model,
        "max_tokens": 2048,
        "messages": [{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": b64}},
            {"type": "text", "text": prompt},
        ]}],
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Screenshot a URL and convert to Markdown via vision LLM.")
    parser.add_argument("--url",        required=True,  help="URL to screenshot")
    parser.add_argument("--output",     default=None,   help="Save Markdown to file (default: stdout)")
    parser.add_argument("--save-image", default=None,   help="Save screenshot PNG to this path")
    parser.add_argument("--prompt",     default="Describe all content visible on this page. Use Markdown formatting with headings, bullet lists, and code blocks where appropriate.",
                        help="LLM prompt")
    parser.add_argument("--provider",   default="openai", choices=["openai", "anthropic"])
    parser.add_argument("--model",      default=None,   help="Override model name")
    parser.add_argument("--width",      type=int, default=1280, help="Viewport width in px (default: 1280)")
    parser.add_argument("--wait",       type=int, default=2, help="Seconds to wait after page load (default: 2)")
    args = parser.parse_args()

    print(f"Screenshotting: {args.url}")
    img_path = _screenshot(args.url, args.width, args.wait, args.save_image)
    print(f"Screenshot saved: {img_path}")

    if args.provider == "openai":
        api_key = os.environ.get("OPENAI_API_KEY", "")
        if not api_key:
            print("Error: OPENAI_API_KEY not set.")
            sys.exit(1)
        result = _caption_openai(img_path, args.prompt, args.model or "gpt-4o", api_key)
    else:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            print("Error: ANTHROPIC_API_KEY not set.")
            sys.exit(1)
        result = _caption_anthropic(img_path, args.prompt, args.model or "claude-3-5-sonnet-20241022", api_key)

    # Clean up temp image if not explicitly saved
    if not args.save_image and os.path.exists(img_path):
        os.remove(img_path)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(result + "\n")
        print(f"Saved: {args.output}")
    else:
        print(result)


if __name__ == "__main__":
    main()

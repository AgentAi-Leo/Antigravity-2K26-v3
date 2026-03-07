import os
import sys
import re
import argparse
import urllib.request
import urllib.error
from html.parser import HTMLParser


# ---------------------------------------------------------------------------
# Minimal HTML → plain text converter (stdlib)
# ---------------------------------------------------------------------------

SKIP_TAGS = {"script", "style", "head", "noscript", "nav", "footer", "header"}
BLOCK_TAGS = {"p", "div", "article", "section", "main", "li", "h1", "h2", "h3", "h4", "h5", "h6", "br", "tr"}
HEADING_TAGS = {"h1": "#", "h2": "##", "h3": "###", "h4": "####", "h5": "#####", "h6": "######"}


class _HTMLToText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.lines = []
        self._current = []
        self._skip_depth = 0
        self._title = ""
        self._in_title = False
        self._heading = None

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag in SKIP_TAGS:
            self._skip_depth += 1
        if tag == "title":
            self._in_title = True
        if tag in HEADING_TAGS:
            self._heading = HEADING_TAGS[tag]
            self._flush()
        elif tag in BLOCK_TAGS:
            self._flush()

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag in SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)
        if tag == "title":
            self._in_title = False
        if tag in HEADING_TAGS or tag in BLOCK_TAGS:
            self._flush()
            self._heading = None

    def handle_data(self, data):
        if self._skip_depth:
            return
        if self._in_title:
            self._title = data.strip()
        text = data.strip()
        if text:
            self._current.append(text)

    def _flush(self):
        text = " ".join(self._current).strip()
        if text:
            if self._heading:
                self.lines.append(f"{self._heading} {text}")
            else:
                self.lines.append(text)
        self._current = []

    def get_text(self) -> str:
        self._flush()
        raw = "\n".join(self.lines)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()


def _bs4_extract(html: str, selector: str) -> str:
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()
    target = soup.select_one(selector) if selector != "body" else soup.body
    if target is None:
        target = soup
    lines = []
    for el in target.find_all(True):
        t = el.name.lower()
        txt = el.get_text(" ", strip=True)
        if not txt:
            continue
        if t in ("h1", "h2", "h3", "h4", "h5", "h6"):
            level = int(t[1])
            lines.append(f"\n{'#' * level} {txt}\n")
        elif t in ("li",):
            lines.append(f"- {txt}")
        elif t in ("p", "article"):
            lines.append(f"\n{txt}\n")
    return re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip()


def scrape(url: str, selector: str, include_title: bool, timeout: int, user_agent: str) -> tuple[str, str]:
    req = urllib.request.Request(url, headers={"User-Agent": user_agent})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            html = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        print(f"HTTP {e.code}: {e.reason}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Error: {e.reason}")
        sys.exit(1)

    # Try bs4 first; fall back to stdlib
    try:
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "_libs")))
        text = _bs4_extract(html, selector)
    except ImportError:
        parser = _HTMLToText()
        parser.feed(html)
        text = parser.get_text()

    title = ""
    if include_title:
        p = _HTMLToText()
        p.feed(html)
        title = p._title or url
        text = f"# {title}\n\n{text}"

    return text, title


def main() -> None:
    parser = argparse.ArgumentParser(description="Scrape a URL and output clean text/Markdown.")
    parser.add_argument("--url",           required=True,  help="URL to fetch")
    parser.add_argument("--output",        default=None,   help="Save to file (default: stdout)")
    parser.add_argument("--selector",      default="body", help="CSS selector (requires beautifulsoup4)")
    parser.add_argument("--include-title", action="store_true", help="Prepend page title as H1")
    parser.add_argument("--timeout",       type=int, default=30, help="Request timeout in seconds")
    parser.add_argument("--user-agent",    default="Mozilla/5.0 (compatible; Antigravity/1.0)",
                        help="Override User-Agent")
    args = parser.parse_args()

    text, _ = scrape(args.url, args.selector, args.include_title, args.timeout, args.user_agent)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(text + "\n")
        print(f"Saved: {args.output}")
    else:
        print(text)


if __name__ == "__main__":
    main()

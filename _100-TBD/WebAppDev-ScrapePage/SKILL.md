---
name: scraping-web-pages
description: Fetches a URL and extracts clean readable text or Markdown from the HTML. Use when the user asks to scrape a page, extract text from a URL, fetch web content, or convert a webpage to Markdown for LLM ingestion.
---

# WebAppDev-ScrapePage Skill

## When to Use This Skill
- User says "scrape this URL", "get text from this page", "fetch web content", or "webpage to Markdown"
- Feeding live web content into an LLM pipeline
- Extracting documentation from public web pages

---

## Workflow
- [ ] 1. Confirm the URL is publicly accessible (no auth required)
- [ ] 2. Run `scripts/scrape_page.py --url "https://..."`
- [ ] 3. Review the output — check for noise or unwanted boilerplate

---

## Commands

```bash
# Basic — prints clean text
python3 scripts/scrape_page.py --url "https://example.com"

# Output as Markdown file
python3 scripts/scrape_page.py --url "https://docs.example.com" --output page.md

# Extract only a specific CSS selector
python3 scripts/scrape_page.py --url "https://example.com" --selector "article"

# Include page title as H1 heading
python3 scripts/scrape_page.py --url "https://example.com" --include-title

# Full options
python3 scripts/scrape_page.py --help
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--url` | *(required)* | URL to fetch |
| `--output` | stdout | Save to `.md` or `.txt` file |
| `--selector` | `body` | CSS selector to extract (requires `beautifulsoup4`) |
| `--include-title` | off | Prepend page `<title>` as H1 |
| `--timeout` | `30` | Request timeout in seconds |
| `--user-agent` | Chrome-like | Override User-Agent header |

---

## Dependencies

- **Stdlib only** for basic text extraction (`urllib`, `html.parser`)
- **Optional — richer extraction:** `python3 -m pip install beautifulsoup4 --target ../../_libs/`

---

## Resources
- `scripts/scrape_page.py` — core scraping script

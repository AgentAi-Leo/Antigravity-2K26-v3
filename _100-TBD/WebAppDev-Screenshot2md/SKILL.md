---
name: screenshot-to-markdown
description: Takes a full-page screenshot of a URL using Playwright and converts the visual content to Markdown via a vision LLM. Use when the user asks to screenshot a page, capture a URL visually, convert a webpage screenshot to text, or extract content from a JavaScript-rendered page.
---

# WebAppDev-Screenshot2md Skill

## When to Use This Skill
- User says "screenshot this URL", "capture this page visually", or "JS-rendered page to Markdown"
- Page content is only visible after JavaScript runs (SPAs, dashboards)
- Need a visual snapshot with text extraction for docs or auditing

---

## Prerequisites

```bash
# Install Playwright (one-time)
pip install playwright --target ../../_libs/
playwright install chromium
```

Set your LLM API key:
```bash
export OPENAI_API_KEY="sk-..."        # default
# OR
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## Workflow
- [ ] 1. Install Playwright (see Prerequisites)
- [ ] 2. Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
- [ ] 3. Run `scripts/screenshot2md.py --url "https://..."`
- [ ] 4. Review the output Markdown

---

## Commands

```bash
# Full-page screenshot → Markdown caption
python3 scripts/screenshot2md.py --url "https://example.com"

# Save screenshot and Markdown
python3 scripts/screenshot2md.py --url "https://app.example.com" \
  --save-image screenshot.png --output page.md

# Custom extraction prompt
python3 scripts/screenshot2md.py --url "https://dashboard.example.com" \
  --prompt "List all data metrics visible on this dashboard."

# Use Anthropic
python3 scripts/screenshot2md.py --url "https://example.com" --provider anthropic
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--url` | *(required)* | URL to screenshot |
| `--output` | stdout | Save Markdown output to file |
| `--save-image` | (deleted after use) | Save the screenshot PNG |
| `--prompt` | "Describe all content on this page as Markdown." | LLM prompt |
| `--provider` | `openai` | `openai` or `anthropic` |
| `--width` | `1280` | Viewport width in px |
| `--wait` | `2` | Seconds to wait after load |

---

## Resources
- `scripts/screenshot2md.py` — core script
- Requires: Playwright + `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`

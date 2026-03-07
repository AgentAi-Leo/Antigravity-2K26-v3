---
name: classifying-content-with-llm
description: Uses an LLM to classify, tag, route, or score text content against a user-defined set of categories or labels. Use when the user asks to classify, label, tag, categorize, route, or score content using AI.
---

# AI-LLM-ClassifyContent Skill

## When to Use This Skill
- User says "classify this", "label these docs", "route this message", "tag content", or "score sentiment"
- Building content moderation, routing, or tagging pipelines
- Categorizing support tickets, emails, feedback, or documents

---

## Prerequisites

```bash
export OPENAI_API_KEY="sk-..."         # default
# OR
export ANTHROPIC_API_KEY="sk-ant-..."
```

---

## Workflow
- [ ] 1. Define your categories (inline or in a JSON file)
- [ ] 2. Run `scripts/classify_content.py`
- [ ] 3. Review classifications — adjust prompt if needed

---

## Commands

```bash
# Classify a single text against categories
python3 scripts/classify_content.py \
  --text "My order hasn't arrived after 2 weeks" \
  --categories "shipping,billing,returns,product_quality,other"

# Classify all lines in a file
python3 scripts/classify_content.py \
  --input feedback.txt \
  --categories "positive,negative,neutral" \
  --output results.json

# Classify with detailed labels from a JSON file
python3 scripts/classify_content.py \
  --input emails.txt \
  --categories-file categories.json

# Score content (0.0-1.0) instead of single label
python3 scripts/classify_content.py \
  --text "This product is amazing!" \
  --categories "positive,negative" --score

# Use Anthropic
python3 scripts/classify_content.py --text "..." \
  --categories "spam,ham" --provider anthropic
```

---

## Categories File Format (`categories.json`)

```json
{
  "shipping": "Issues related to delivery, tracking, or shipping delays",
  "billing": "Payment, invoice, or charge-related questions",
  "returns": "Return, refund, or exchange requests",
  "other": "Anything that doesn't fit the above"
}
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--text` | — | Single text to classify |
| `--input` | — | File with one text per line |
| `--categories` | *(required)* | Comma-separated category list |
| `--categories-file` | — | JSON file with category descriptions |
| `--output` | stdout | Save results JSON to file |
| `--score` | off | Return confidence scores instead of single label |
| `--provider` | `openai` | `openai` or `anthropic` |
| `--model` | `gpt-4o` | Override model |

---

## Resources
- `scripts/classify_content.py` — core script (stdlib urllib, no pip required)

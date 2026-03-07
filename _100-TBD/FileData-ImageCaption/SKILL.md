---
name: captioning-images-with-ai
description: Sends an image file to a vision-capable LLM (OpenAI GPT-4o or Anthropic Claude) and returns a text caption or detailed description. Use when the user asks to describe an image, caption a photo, extract text from an image, or generate alt-text.
---

# FileData-ImageCaption Skill

## When to Use This Skill
- User asks to "describe this image", "caption a photo", "generate alt-text", or "what's in this image"
- Extracting text or content from screenshots for accessibility or documentation
- Batch describing images for a knowledge base or dataset

---

## Prerequisites

Configure your LLM API key via environment variable:

```bash
export OPENAI_API_KEY="sk-..."        # for OpenAI GPT-4o (default)
# OR
export ANTHROPIC_API_KEY="sk-ant-..." # for Anthropic Claude
```

---

## Workflow
- [ ] 1. Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` in environment
- [ ] 2. Run `scripts/image_caption.py --input image.png`
- [ ] 3. Caption is printed to stdout or saved to file

---

## Commands

```bash
# Basic caption (uses OpenAI by default)
python3 scripts/image_caption.py --input "photo.jpg"

# Use Anthropic Claude instead
python3 scripts/image_caption.py --input "photo.jpg" --provider anthropic

# Custom prompt
python3 scripts/image_caption.py --input "screenshot.png" --prompt "Extract all text visible in this image."

# Batch — caption all images in a folder
python3 scripts/image_caption.py --input-dir ./images --output captions.md

# Save single caption to file
python3 scripts/image_caption.py --input "diagram.png" --output caption.md
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--input` | — | Path to single image file |
| `--input-dir` | — | Directory of images to batch-caption |
| `--output` | stdout | Output file path |
| `--prompt` | "Describe this image in detail." | Custom LLM prompt |
| `--provider` | `openai` | `openai` or `anthropic` |
| `--model` | `gpt-4o` / `claude-3-5-sonnet-20241022` | Override model name |

---

## Supported Formats
`.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`

---

## Resources
- `scripts/image_caption.py` — core captioning script
- Requires: `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` environment variable

---
name: generating-images-with-ai
description: Generates images from text prompts using Google Imagen 4 or DALL-E. Saves output as PNG files. Use when the user asks to generate an image, create artwork, make a logo, or produce visual content from a description.
---

# AI-LLM-ImageGenerate Skill

## When to Use This Skill
- User says "generate an image", "create artwork", "make a logo", or "visualize this"
- Generating UI mockups, icons, or placeholder images for web apps
- Creating documentation illustrations or blog post images

---

## Prerequisites

```bash
export GEMINI_API_KEY="..."    # for Imagen 4 (default)
# OR: OPENAI_API_KEY            # for DALL-E 3
```

---

## Workflow
- [ ] 1. Set API key
- [ ] 2. Run `scripts/image_generate.py --prompt "..."`
- [ ] 3. Find the output PNG in `./output/` or specified path

---

## Commands

```bash
# Generate an image from a prompt
python3 scripts/image_generate.py --prompt "A futuristic AI robot coding at a desk, neon lighting"

# Save to a specific path
python3 scripts/image_generate.py --prompt "Minimalist logo for a tech startup" --output logo.png

# High quality (Imagen 4 Ultra)
python3 scripts/image_generate.py --prompt "Photorealistic mountain landscape" \
  --model imagen-4.0-ultra-generate-001

# Fast mode
python3 scripts/image_generate.py --prompt "Simple icon of a cloud" \
  --model imagen-4.0-fast-generate-001

# Use DALL-E 3 instead
python3 scripts/image_generate.py --prompt "Abstract art" --provider openai

# Generate multiple images
python3 scripts/image_generate.py --prompt "App screenshot mockup" --count 3
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--prompt` | *(required)* | Text description of image to generate |
| `--output` | `./output/image_<timestamp>.png` | Output file path |
| `--count` | `1` | Number of images to generate |
| `--provider` | `gemini` | `gemini` (Imagen 4) or `openai` (DALL-E 3) |
| `--model` | `imagen-4.0-generate-001` | Override model |
| `--size` | `1024x1024` | Image size (DALL-E: `1024x1024`, `1792x1024`, `1024x1792`) |

---

## Resources
- `scripts/image_generate.py` — core script (stdlib urllib + base64, no pip required)

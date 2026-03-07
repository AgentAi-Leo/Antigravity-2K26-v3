---
name: generating-code-documentation
description: Generates docstrings, JSDoc comments, or README sections for any code file using an LLM. Use when the user asks to document code, add docstrings, generate JSDoc, write a README, or auto-comment a function or class.
---

# AI-LLM-DocGenerator Skill

## When to Use This Skill
- User says "document this code", "add docstrings", "generate JSDoc", or "write comments"
- Onboarding new codebases — add missing documentation in bulk
- Generate README.md sections from source code

---

## Prerequisites

```bash
export GEMINI_API_KEY="..."    # default
# OR: OPENAI_API_KEY / ANTHROPIC_API_KEY
```

---

## Workflow
- [ ] 1. Set API key
- [ ] 2. Run `scripts/doc_generator.py --input file.py`
- [ ] 3. Review and save the documented output

---

## Commands

```bash
# Add docstrings to a Python file
python3 scripts/doc_generator.py --input utils.py

# Generate JSDoc for JavaScript
python3 scripts/doc_generator.py --input api.js --lang javascript

# Write a README from source code
python3 scripts/doc_generator.py --input app.py --mode readme --output README.md

# Save documented file
python3 scripts/doc_generator.py --input utils.py --output utils_documented.py

# Document all .py files in a directory
python3 scripts/doc_generator.py --input-dir ./src/ --lang python
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--input` | — | Source file to document |
| `--input-dir` | — | Directory of files to document |
| `--lang` | auto-detect | `python`, `javascript`, `typescript`, `go`, `rust` |
| `--mode` | `docstrings` | `docstrings`, `readme`, `comments` |
| `--output` | stdout | Save output to file |
| `--provider` | `gemini` | `gemini`, `openai`, `anthropic` |
| `--model` | `gemini-3.1-pro-preview` | Override model |

---

## Resources
- `scripts/doc_generator.py` — core script (stdlib urllib, no pip required)

---
name: reviewing-code-with-ai
description: Performs an AI code review on a file or git diff, identifying bugs, security issues, style problems, and improvements. Use when the user asks to review code, audit a file, check for bugs, or get AI feedback on code quality.
---

# AI-LLM-CodeReviewer Skill

## When to Use This Skill
- User says "review this code", "audit this file", "find bugs", or "check code quality"
- Pre-PR review to catch issues before human review
- Security audit for authentication, input validation, or data handling code

---

## Prerequisites

```bash
export GEMINI_API_KEY="..."    # default provider
# OR: OPENAI_API_KEY / ANTHROPIC_API_KEY
```

---

## Workflow
- [ ] 1. Set API key
- [ ] 2. Run `scripts/code_reviewer.py --input file.py`
- [ ] 3. Review the Markdown output — address flagged issues

---

## Commands

```bash
# Review a single file
python3 scripts/code_reviewer.py --input app.py

# Review a git diff (staged changes)
python3 scripts/code_reviewer.py --diff

# Review a specific commit
python3 scripts/code_reviewer.py --diff --commit abc1234

# Focus on security only
python3 scripts/code_reviewer.py --input auth.py --focus security

# Save report
python3 scripts/code_reviewer.py --input app.py --output review.md

# Use a different provider
python3 scripts/code_reviewer.py --input app.py --provider openai --model gpt-4o
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--input` | — | Source file to review |
| `--diff` | off | Review current `git diff --staged` |
| `--commit` | — | Review diff of specific commit hash |
| `--focus` | `all` | `all`, `security`, `bugs`, `style`, `performance` |
| `--output` | stdout | Save Markdown report to file |
| `--provider` | `gemini` | `gemini`, `openai`, `anthropic` |
| `--model` | `gemini-3.1-pro-preview` | Override model |

---

## Resources
- `scripts/code_reviewer.py` — core script (stdlib urllib, no pip required)

---
name: building-llm-prompts
description: Builds structured LLM prompts from named templates with variable substitution. Supports system/user/assistant message blocks and saves ready-to-use JSON payloads. Use when the user asks to build a prompt, create an LLM message, fill a prompt template, or construct a system/user prompt.
---

# AI-LLM-PromptBuilder Skill

## When to Use This Skill
- User says "build a prompt", "fill this template", "create a system prompt", or "format messages for LLM"
- Constructing reusable, parameterized prompts for pipelines
- Generating JSON-ready message arrays for OpenAI/Anthropic API calls

---

## Template Format

Templates are Markdown files with YAML frontmatter and `{{variable}}` placeholders:

```markdown
---
name: summarizer
system: "You are a concise summarizer. Respond in {{language}}."
---
Summarize the following text in {{max_words}} words or fewer:

{{text}}
```

---

## Workflow
- [ ] 1. Create a template file (or use a built-in one)
- [ ] 2. Run `scripts/prompt_builder.py` with variables
- [ ] 3. Use the output JSON directly in an API call

---

## Commands

```bash
# Fill a template with variables
python3 scripts/prompt_builder.py --template templates/summarizer.md \
  --var language=English --var max_words=100 --var text="$(cat doc.txt)"

# Output as OpenAI messages JSON
python3 scripts/prompt_builder.py --template templates/summarizer.md \
  --var text="Hello world" --format openai

# Output as Anthropic messages JSON
python3 scripts/prompt_builder.py --template templates/summarizer.md \
  --var text="Hello world" --format anthropic

# List available templates
python3 scripts/prompt_builder.py --list

# Save output to file
python3 scripts/prompt_builder.py --template templates/summarizer.md \
  --var text="..." --output prompt.json
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--template` | — | Path to `.md` template file |
| `--var` | — | `key=value` pairs (repeatable) |
| `--format` | `openai` | `openai`, `anthropic`, or `raw` |
| `--output` | stdout | Save JSON to file |
| `--list` | — | List templates in `templates/` directory |

---

## Resources
- `scripts/prompt_builder.py` — core script (stdlib only)
- `templates/` — built-in prompt templates

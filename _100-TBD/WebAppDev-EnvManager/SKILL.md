---
name: managing-env-files
description: Creates, validates, and documents .env files from a schema template. Checks that all required keys are present and optionally generates a .env.example with descriptions. Use when the user asks to manage env files, validate environment variables, create a .env from a template, or document env config.
---

# WebAppDev-EnvManager Skill

## When to Use This Skill
- User says "validate my .env", "create a .env template", or "document environment variables"
- Onboarding new developers — generate a `.env.example` from a schema
- CI/CD pre-flight checks — verify all required env vars are present

---

## Schema File Format (`.env.schema.json`)

```json
{
  "OPENAI_API_KEY": {
    "required": true,
    "description": "OpenAI API key for LLM calls",
    "example": "sk-..."
  },
  "PORT": {
    "required": false,
    "default": "3000",
    "description": "HTTP server port"
  },
  "DEBUG": {
    "required": false,
    "default": "false",
    "description": "Enable debug logging"
  }
}
```

---

## Workflow
- [ ] 1. Create or locate a `.env.schema.json` for your project
- [ ] 2. Run `scripts/env_manager.py` with desired mode
- [ ] 3. Fill in missing values or share `.env.example` with team

---

## Commands

```bash
# Validate .env against schema
python3 scripts/env_manager.py --schema .env.schema.json --validate --env .env

# Generate .env.example from schema
python3 scripts/env_manager.py --schema .env.schema.json --generate-example

# Generate a blank .env from schema (with defaults filled in)
python3 scripts/env_manager.py --schema .env.schema.json --generate-env

# Document schema as Markdown
python3 scripts/env_manager.py --schema .env.schema.json --docs --output env_docs.md
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--schema` | *(required)* | Path to `.env.schema.json` |
| `--env` | `.env` | Path to `.env` file to validate |
| `--validate` | off | Validate `.env` against schema |
| `--generate-example` | off | Write `.env.example` |
| `--generate-env` | off | Write `.env` with defaults |
| `--docs` | off | Output Markdown documentation |
| `--output` | stdout | File path for output |

---

## Resources
- `scripts/env_manager.py` — core manager (stdlib only)
- `examples/sample.env.schema.json` — sample schema

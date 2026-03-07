---
name: generating-api-documentation
description: Generates Markdown API documentation from an OpenAPI/Swagger JSON or YAML spec file. Use when the user asks to document an API, generate API docs, convert OpenAPI to Markdown, or create reference documentation from a spec.
---

# WebAppDev-DocGen Skill

## When to Use This Skill
- User says "generate API docs", "document this OpenAPI spec", or "convert Swagger to Markdown"
- Publishing human-readable API reference from a machine-readable spec
- Generating docs for GitBook, MkDocs, or a GitHub wiki

---

## Workflow
- [ ] 1. Obtain your OpenAPI spec (`openapi.json` or `openapi.yaml`)
- [ ] 2. Run `scripts/doc_gen.py --spec openapi.json`
- [ ] 3. Use the Markdown output directly in your docs system

---

## Commands

```bash
# Generate docs from JSON spec
python3 scripts/doc_gen.py --spec openapi.json

# From YAML spec
python3 scripts/doc_gen.py --spec openapi.yaml

# Save to file
python3 scripts/doc_gen.py --spec openapi.json --output API_REFERENCE.md

# Include request/response examples
python3 scripts/doc_gen.py --spec openapi.json --examples

# Filter to specific tag/group
python3 scripts/doc_gen.py --spec openapi.json --tag "Users"
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--spec` | *(required)* | Path to OpenAPI JSON or YAML spec |
| `--output` | stdout | Save Markdown to file |
| `--examples` | off | Include request/response body examples |
| `--tag` | all | Filter to a specific tag/group only |

---

## Supported Spec Versions
- OpenAPI 3.x (JSON and YAML)
- Swagger 2.x (JSON)

---

## Resources
- `scripts/doc_gen.py` — core generator (stdlib only; YAML requires `pyyaml` for `.yaml` inputs)

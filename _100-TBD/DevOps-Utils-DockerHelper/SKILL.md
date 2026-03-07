---
name: generating-dockerfiles
description: Analyzes a project directory and generates a Dockerfile and docker-compose.yml tailored to the detected stack. Use when the user asks to dockerize a project, generate a Dockerfile, containerize an app, or create docker-compose config.
---

# UTILS-DevOps-DockerHelper Skill

## When to Use This Skill
- User says "dockerize this", "generate a Dockerfile", "containerize my app", or "create docker-compose"
- Taking an existing project from local-only to containerized in one step
- Standardizing container configs across a team

---

## Workflow
- [ ] 1. Run `scripts/docker_helper.py --dir .` from your project root
- [ ] 2. Review generated `Dockerfile` and `docker-compose.yml`
- [ ] 3. Adjust as needed and run `docker-compose up`

---

## Commands

```bash
# Auto-detect stack and generate Dockerfile
python3 scripts/docker_helper.py --dir .

# Save to project
python3 scripts/docker_helper.py --dir ./my-app --output ./my-app

# Generate docker-compose.yml as well
python3 scripts/docker_helper.py --dir . --compose

# Override detected language
python3 scripts/docker_helper.py --dir . --lang python

# Show what would be generated (dry run)
python3 scripts/docker_helper.py --dir . --dry-run
```

---

## Detected Stacks

| Indicator file | Stack |
|---|---|
| `requirements.txt` / `pyproject.toml` | Python |
| `package.json` | Node.js |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `pom.xml` / `build.gradle` | Java |
| `Gemfile` | Ruby |

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--dir` | `.` | Project directory to analyze |
| `--output` | stdout | Directory to write Dockerfile/compose |
| `--lang` | auto-detect | Override language detection |
| `--compose` | off | Also generate `docker-compose.yml` |
| `--dry-run` | off | Print output without saving |

---

## Resources
- `scripts/docker_helper.py` — core generator (stdlib only)

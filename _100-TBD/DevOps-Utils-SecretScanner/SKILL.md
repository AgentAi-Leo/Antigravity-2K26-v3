---
name: scanning-for-secrets
description: Scans source code directories for accidentally committed secrets, API keys, tokens, and private keys using pattern matching. Use when the user asks to scan for secrets, check for exposed keys, find leaked credentials, or audit code for sensitive data.
---

# SecretScanner Skill

## When to Use This Skill
- User says "scan for secrets", "check for API keys in code", "find leaked credentials"
- Before pushing to a public repository
- During security audits or code reviews
- Post-incident investigation

---

## What It Detects

| Category | Examples |
|---|---|
| Cloud keys | AWS `AKIA...`, GCP service accounts |
| AI/API keys | OpenAI `sk-...`, Anthropic `sk-ant-...` |
| Auth tokens | Bearer tokens, JWT secrets, GitHub PATs |
| Private keys | `-----BEGIN RSA/EC/PRIVATE KEY-----` |
| Passwords | `password=`, `passwd=`, `secret=` in code |
| `.env` contents | Unredacted values in committed `.env` files |
| High-entropy strings | Strings >20 chars that look like random tokens |

---

## Workflow

- [ ] 1. Run `scripts/secret_scanner.py` on the target directory
- [ ] 2. Review findings — check for false positives
- [ ] 3. Rotate any confirmed leaked secrets immediately
- [ ] 4. Add confirmed patterns to `.gitignore` or secret management

---

## Commands

```bash
# Scan current directory
python3 scripts/secret_scanner.py --dir .

# Scan specific path, save report
python3 scripts/secret_scanner.py --dir ./src --output secrets_report.md

# Exclude directories (e.g. node_modules, .git)
python3 scripts/secret_scanner.py --dir . --exclude node_modules .git dist

# Increase entropy threshold (fewer false positives)
python3 scripts/secret_scanner.py --dir . --entropy 4.2
```

```bash
python3 scripts/secret_scanner.py --help
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--dir` | `.` | Directory to scan |
| `--output` | stdout | Save Markdown report to file |
| `--exclude` | `['.git', 'node_modules', '__pycache__', '_libs']` | Directories to skip |
| `--entropy` | `3.8` | Shannon entropy threshold for random-string detection |
| `--extensions` | common code files | Limit scan to specific extensions |

> **Rule:** If a secret is confirmed, rotate it immediately — scanning does not automatically remediate.

---

## Resources
- `scripts/secret_scanner.py` — core scanner

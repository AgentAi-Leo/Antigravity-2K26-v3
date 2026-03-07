---
name: managing-cloud-secrets
description: Securely fetches, sets, and lists secrets using Google Cloud Secret Manager. Includes an injector mode to securely pass secrets into other scripts without writing them to disk. Use when the user asks to manage secrets, fetch an API key safely, update a secret in GCP, or inject a secret into a process.
---

# 000C-SKILL_SECURITY-GCSecrtMgr (Secret Manager)

## When to Use This Skill
- User says "get the dev-test-1 secret", "update my API key in GCP", "list my secrets", or "run this safely"
- Fetching production or development secrets without hardcoding them
- Passing sensitive API keys to AI skills dynamically

---

## Prerequisites

1. Active Google Cloud account and billing-enabled project
2. `gcloud` CLI installed and authenticated (`gcloud auth login`)
3. GCP Secret Manager API enabled

*Note: This skill wraps the `gcloud` command-line tool, meaning no extra Python dependencies (`pip`) are required.*

---

## Workflow

- [ ] 1. Run `scripts/secret_manager.py --list` to view your secrets
- [ ] 2. Fetch a specific secret: `scripts/secret_manager.py --get dev-test-1`
- [ ] 3. Run a command securely: `scripts/secret_manager.py --inject dev-test-1:GEMINI_API_KEY --run "python3 script.py"`

---

## Commands

```bash
# List all secrets in your active GCP project
python3 scripts/secret_manager.py --list

# Read a secret's latest value
python3 scripts/secret_manager.py --get dev-test-1

# Create a new secret (or update an existing one)
python3 scripts/secret_manager.py --set new-api-key --value "AIzaSy..."

# Create a new secret from a file
python3 scripts/secret_manager.py --set cert-key --file ./cert.pem

# 🔐 INJECTION MODE (Maximum Security)
# Fetches dev-test-1, puts it in $GEMINI_API_KEY memory, runs the command, and exits safely
python3 scripts/secret_manager.py \
  --inject dev-test-1:GEMINI_API_KEY \
  --run "python3 ../AI-LLM-SummarizeDoc/scripts/summarize_doc.py --input report.txt"

# Inject multiple secrets at once
python3 scripts/secret_manager.py \
  --inject db-pass:DB_PASSWORD --inject api-token:API_KEY \
  --run "npm start"
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--list` | — | List all secrets in the GCP project |
| `--get` | — | Secret name to read |
| `--reveal` | off | Force display unmasked secret in terminal |
| `--set` | — | Secret name to create or update |
| `--value` | — | Value for the new secret version |
| `--file` | — | Path to file containing the new secret value |
| `--inject` | — | Format `SecretName:ENV_VAR_NAME`. Pulls secret into `ENV_VAR_NAME` memory |
| `--run` | — | Command to run securely (only valid with `--inject`) |

---

## Security Guarantees
- **Terminal Redaction:** Secrets fetched via `--get` directly in the terminal are automatically masked to prevent logging leaks. They are only printed raw if you pipe the output (`|` or `>`) or explicitly pass `--reveal`.
- **Memory Context:** Secrets injected via `--inject` are held strictly in child-process memory and destroyed immediately after the command finishes.
- Never writes secrets to `.env`, `/tmp`, or the hard drive.

---

## Resources
- `scripts/secret_manager.py` — core manager (stdlib subprocess, no pip required)

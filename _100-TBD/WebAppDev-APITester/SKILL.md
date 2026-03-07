---
name: testing-apis
description: Runs a suite of HTTP requests from a JSON or YAML test file and reports status codes, response times, and assertion results as a Markdown table. Use when the user asks to test an API, run API tests, check endpoints, validate HTTP responses, or benchmark request latency.
---

# WebAppDev-APITester Skill

## When to Use This Skill
- User says "test this API", "check my endpoints", "run these HTTP requests", or "validate API responses"
- Pre-deployment endpoint verification
- Monitoring API health from the command line

---

## Test File Format (JSON)

```json
[
  {
    "name": "Health check",
    "method": "GET",
    "url": "https://api.example.com/health",
    "expect_status": 200
  },
  {
    "name": "Create item",
    "method": "POST",
    "url": "https://api.example.com/items",
    "headers": {"Authorization": "Bearer $API_TOKEN"},
    "body": {"name": "Widget", "price": 9.99},
    "expect_status": 201,
    "expect_body_contains": "Widget"
  }
]
```

> Use `$VAR_NAME` in headers/URLs — the script expands them from environment variables.

---

## Workflow
- [ ] 1. Create a test file (JSON array of requests)
- [ ] 2. Set any required env vars (`export API_TOKEN=...`)
- [ ] 3. Run `scripts/api_tester.py --tests tests.json`
- [ ] 4. Review the Markdown report

---

## Commands

```bash
# Run all tests
python3 scripts/api_tester.py --tests tests.json

# Save report
python3 scripts/api_tester.py --tests tests.json --output report.md

# Run with verbose response bodies
python3 scripts/api_tester.py --tests tests.json --verbose

# Set global timeout
python3 scripts/api_tester.py --tests tests.json --timeout 10
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--tests` | *(required)* | Path to JSON test suite file |
| `--output` | stdout | Save Markdown report to file |
| `--timeout` | `30` | Request timeout per call (seconds) |
| `--verbose` | off | Include response body in report |
| `--fail-fast` | off | Stop on first failure |

---

## Resources
- `scripts/api_tester.py` — core tester (stdlib only)
- `examples/sample_tests.json` — sample test suite

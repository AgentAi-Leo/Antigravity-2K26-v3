---
name: running-mock-api-server
description: Spins up a lightweight local HTTP mock REST API server from a JSON spec file. Returns configured responses for any route. Use when the user asks to mock an API, create a fake server, run a mock endpoint, or test frontend without a real backend.
---

# WebAppDev-MockAPI Skill

## When to Use This Skill
- User says "mock this API", "fake server", "run a local endpoint", or "test without backend"
- Frontend development — stub out API responses while backend is being built
- Integration testing against predictable fixed responses

---

## Spec File Format (`mock_api.json`)

```json
{
  "port": 3000,
  "routes": [
    {
      "method": "GET",
      "path": "/api/users",
      "status": 200,
      "body": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    },
    {
      "method": "POST",
      "path": "/api/users",
      "status": 201,
      "body": {"id": 3, "name": "New User", "created": true}
    },
    {
      "method": "GET",
      "path": "/api/health",
      "status": 200,
      "body": {"status": "ok"}
    }
  ]
}
```

---

## Workflow
- [ ] 1. Create a `mock_api.json` spec file with your routes
- [ ] 2. Run `scripts/mock_api.py --spec mock_api.json`
- [ ] 3. Make requests to `http://localhost:3000/...`

---

## Commands

```bash
# Start mock server
python3 scripts/mock_api.py --spec mock_api.json

# Custom port
python3 scripts/mock_api.py --spec mock_api.json --port 8080

# With CORS headers (for browser requests)
python3 scripts/mock_api.py --spec mock_api.json --cors

# Log all incoming requests
python3 scripts/mock_api.py --spec mock_api.json --verbose
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--spec` | *(required)* | Path to JSON spec file |
| `--port` | `3000` | Port to listen on |
| `--cors` | off | Add CORS headers to all responses |
| `--verbose` | off | Log request method, path, response status |

---

## Resources
- `scripts/mock_api.py` — core server (stdlib `http.server`, no pip required)
- `examples/sample_mock_api.json` — sample spec

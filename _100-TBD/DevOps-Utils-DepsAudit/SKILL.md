---
name: auditing-dependencies
description: Audits Python and Node.js project dependencies for outdated packages and known security vulnerabilities. Use when the user asks to check dependencies, audit packages, find outdated libraries, or scan for vulnerable packages.
---

# DepsAudit Skill

## When to Use This Skill
- User says "check my dependencies", "audit packages", "find outdated libraries"
- Before a release or deployment — verify no critical vulnerabilities exist
- Routine project health checks

---

## Supported Project Types

| Type | Detection | Tools Used |
|---|---|---|
| Python | `requirements.txt`, `pyproject.toml`, `setup.py` | `pip list --outdated`, `pip-audit` |
| Node.js | `package.json` | `npm outdated`, `npm audit` |

---

## Workflow

- [ ] 1. Run `scripts/deps_audit.py` from the project root
- [ ] 2. Review the outdated packages table
- [ ] 3. Review any security findings
- [ ] 4. Update or pin packages as needed

---

## Commands

```bash
# Auto-detect project type in current directory
python3 scripts/deps_audit.py --dir .

# Specific project directory
python3 scripts/deps_audit.py --dir /path/to/project

# Output report to file
python3 scripts/deps_audit.py --dir . --output audit_report.md

# Skip security check (faster)
python3 scripts/deps_audit.py --dir . --no-security
```

```bash
python3 scripts/deps_audit.py --help
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--dir` | `.` | Project root directory |
| `--output` | stdout | Save Markdown report to file |
| `--no-security` | off | Skip security vulnerability scan |

---

## Resources
- `scripts/deps_audit.py` — core audit script

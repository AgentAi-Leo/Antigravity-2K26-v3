---
name: analyzing-log-files
description: Parses and summarizes log files — counting errors, extracting patterns, identifying top issues, and optionally generating a Markdown report. Use when the user asks to analyze logs, find errors in a log file, summarize application logs, or monitor log output.
---

# UTILS-DevOps-LogAnalyzer Skill

## When to Use This Skill
- User says "analyze these logs", "find errors in this log", "what's failing", or "summarize logs"
- Incident response — quickly identify top errors from application/server logs
- CI/CD pipelines — extract test failures or build errors from output logs

---

## Workflow
- [ ] 1. Run `scripts/log_analyzer.py --input app.log`
- [ ] 2. Review the summary — top errors, patterns, timeline

---

## Commands

```bash
# Analyze a log file
python3 scripts/log_analyzer.py --input app.log

# Filter to errors only
python3 scripts/log_analyzer.py --input app.log --level error

# Show top N most frequent messages
python3 scripts/log_analyzer.py --input app.log --top 20

# Filter by time range
python3 scripts/log_analyzer.py --input app.log --since "2026-02-23 10:00"

# Search for a pattern
python3 scripts/log_analyzer.py --input app.log --grep "TimeoutError"

# Save Markdown report
python3 scripts/log_analyzer.py --input app.log --output report.md

# Read from stdin (pipe)
cat app.log | python3 scripts/log_analyzer.py --stdin
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--input` | — | Log file path |
| `--stdin` | off | Read from stdin |
| `--level` | all | `error`, `warn`, `info`, `debug` |
| `--top` | `10` | Show top N most frequent messages |
| `--since` | — | Filter entries after this datetime |
| `--grep` | — | Filter to lines matching this pattern |
| `--output` | stdout | Save Markdown report to file |

---

## Supported Log Formats
- JSON logs (auto-detected)
- Common log format (nginx/apache)
- Python/Node.js/generic timestamped logs

---

## Resources
- `scripts/log_analyzer.py` — core analyzer (stdlib only)

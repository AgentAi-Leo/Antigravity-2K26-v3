---
name: running-scripts-safely
description: Executes any shell script or Python script with a configurable timeout, captures stdout/stderr, logs the run, and reports success or failure cleanly. Use when the user asks to run a script safely, execute with logging, run with timeout, or capture script output.
---

# RunScript Skill

## When to Use This Skill
- User says "run this script safely", "execute with logging", or "run with a timeout"
- Automating script execution where output capture and error handling matter
- CI/CD-style script runs where exit codes and logs need to be preserved

---

## Workflow

- [ ] 1. Confirm the script path exists and is executable
- [ ] 2. Run `scripts/run_script.py` with target script and options
- [ ] 3. Check the exit code and review the log

---

## Commands

```bash
# Run any script with default 60s timeout
python3 scripts/run_script.py --cmd "python3 myscript.py --arg value"

# Custom timeout and log file
python3 scripts/run_script.py --cmd "bash deploy.sh" --timeout 120 --log runs/deploy.log

# Dry run (print command without executing)
python3 scripts/run_script.py --cmd "rm -rf /tmp/old" --dry-run
```

```bash
python3 scripts/run_script.py --help
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--cmd` | *(required)* | Command string to execute |
| `--timeout` | `60` | Seconds before kill (0 = no limit) |
| `--log` | `None` | Path to append log output |
| `--dry-run` | off | Print command without running |
| `--cwd` | current dir | Working directory for the command |

---

## Output Format

```
[2026-02-23 12:00:00] CMD: python3 myscript.py
[2026-02-23 12:00:01] EXIT: 0 (success) | elapsed: 1.2s
STDOUT:
  ...
STDERR:
  (none)
```

---

## Resources
- `scripts/run_script.py` — core runner

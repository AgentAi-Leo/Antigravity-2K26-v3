---
name: managing-cron-jobs
description: Lists, adds, and removes macOS/Linux cron jobs from the command line. Use when the user asks to schedule a task, add a cron job, list cron jobs, remove a scheduled task, or manage crontab.
---

# UTILS-DevOps-CronManager Skill

## When to Use This Skill
- User says "schedule this to run daily", "add a cron job", "list my cron jobs", or "remove a scheduled task"
- Scheduling backups, log rotation, or automated scripts
- Managing recurring automation tasks

---

## Workflow
- [ ] 1. Run `scripts/cron_manager.py --list` to see current jobs
- [ ] 2. Add or remove jobs as needed
- [ ] 3. Verify with `--list` again

---

## Commands

```bash
# List all current cron jobs
python3 scripts/cron_manager.py --list

# Add a cron job (cron expression + command)
python3 scripts/cron_manager.py --add "0 9 * * *" "python3 /path/to/backup.py"

# Add with a label (comment in crontab)
python3 scripts/cron_manager.py --add "0 9 * * *" "python3 /path/to/backup.py" \
  --label "Daily backup"

# Remove a job by label
python3 scripts/cron_manager.py --remove --label "Daily backup"

# Remove a job by matching command substring
python3 scripts/cron_manager.py --remove --match "backup.py"

# Translate human-readable schedule to cron expression
python3 scripts/cron_manager.py --translate "every day at 9am"
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--list` | — | Show all current cron jobs |
| `--add` | — | `"<cron_expr>" "<command>"` |
| `--label` | — | Comment/tag for the cron job |
| `--remove` | — | Remove mode |
| `--match` | — | Remove jobs matching this string in command |
| `--translate` | — | Convert plain English to cron expression via LLM |

---

## Common Cron Expressions

| Schedule | Expression |
|---|---|
| Every minute | `* * * * *` |
| Every hour | `0 * * * *` |
| Daily at 9am | `0 9 * * *` |
| Weekly Monday 8am | `0 8 * * 1` |
| Monthly 1st at midnight | `0 0 1 * *` |

---

## Resources
- `scripts/cron_manager.py` — core manager (stdlib subprocess, no pip required)

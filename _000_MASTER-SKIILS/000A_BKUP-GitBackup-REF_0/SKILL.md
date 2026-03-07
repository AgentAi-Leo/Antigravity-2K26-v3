---
name: milestone-git-backup-ref0
description: Processes a full project milestone by staging all changes, committing with a "REF_0" prefix, and force-updating the "REF_0" tag on GitHub. Use when you have completed a major project phase and want to lock in a new "REF_0" baseline across local and remote.
---

# 000A_BKUP-GitBackup-REF_0 Skill

## When to Use This Skill
- You have finished a major feature set and want to mark it as the new baseline.
- You want to sync your local work to GitHub and ensure the `REF_0` tag points to the absolute latest version.
- You want to "lock in" a milestone for other agents or developers to reference.

---

## Configured Remote
Default target:
```
https://github.com/AgentAi-Leo/Antigravity-2K26.git
```

---

## Workflow

- [ ] 1. Ensure `GITHUB_TOKEN` is set or SSH keys are loaded.
- [ ] 2. Run `scripts/milestone_backup.py` from the skill root.
- [ ] 3. Verify the updated tag at: https://github.com/AgentAi-Leo/Antigravity-2K26/tree/REF_0

---

## Commands

```bash
# Update the REF_0 milestone with an auto-message
python3 scripts/milestone_backup.py --dir .

# Update REF_0 with a specific milestone description
python3 scripts/milestone_backup.py --dir . --message "Dashboard UI Finalized"

# Preview what will happen without pushing
python3 scripts/milestone_backup.py --dir . --dry-run
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--dir` | `.` | Directory containing the git repository |
| `--remote` | `https://github.com/AgentAi-Leo/Antigravity-2K26.git` | GitHub remote URL |
| `--branch` | `main` | Target branch |
| `--message` | `Release YYYY-MM-DD HH:MM` | Commit description (will be prefixed with REF_0:) |
| `--dry-run` | off | Run logic and print commands without applying |

---

## Resources
- `scripts/milestone_backup.py` — handles staging, committing, local tag deletion/creation, and force-pushing.

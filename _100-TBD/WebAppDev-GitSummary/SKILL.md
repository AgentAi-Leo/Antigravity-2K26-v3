---
name: summarizing-git-history
description: Generates a readable Markdown changelog or commit summary from recent git history using git log and git diff. Use when the user asks for a git summary, changelog, commit log, release notes, or recent changes summary.
---

# WebAppDev-GitSummary Skill

## When to Use This Skill
- User says "summarize recent commits", "generate a changelog", or "what changed in the last N commits"
- Pre-release changelog generation
- Code review prep — get a quick overview of changes in a branch

---

## Workflow
- [ ] 1. Run from inside a git repository (or pass `--dir`)
- [ ] 2. Adjust `--count` or `--since` to scope the history
- [ ] 3. Review the output Markdown

---

## Commands

```bash
# Last 10 commits in current repo
python3 scripts/git_summary.py

# Last 20 commits, save to file
python3 scripts/git_summary.py --count 20 --output CHANGELOG.md

# Commits since a date
python3 scripts/git_summary.py --since "2026-01-01"

# Commits since a tag
python3 scripts/git_summary.py --since-tag "v1.0.0"

# Show full diffs (for code review)
python3 scripts/git_summary.py --count 5 --diff

# Run against a different repo
python3 scripts/git_summary.py --dir /path/to/repo --count 15
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--dir` | `.` (current dir) | Path to git repository |
| `--count` | `10` | Number of commits to include |
| `--since` | — | Commits after this date (`YYYY-MM-DD`) |
| `--since-tag` | — | Commits after this git tag |
| `--branch` | current | Branch to summarize |
| `--diff` | off | Include file diffs |
| `--output` | stdout | Save Markdown to file |
| `--group-by-type` | off | Group commits by conventional type (feat/fix/chore) |

---

## Output Format

```markdown
# Git Summary — main (last 10 commits)

## 2026-02-23

- **abc1234** feat: add PDF2md skill — Jack Roberts
- **def5678** fix: bullet encoding in md2pdf — Jack Roberts

## 2026-02-22

- **ghi9012** chore: rename skills with Convtr- prefix — Jack Roberts
```

---

## Resources
- `scripts/git_summary.py` — core script (subprocess + git, stdlib only)

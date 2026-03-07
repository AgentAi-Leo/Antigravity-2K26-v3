---
name: batch-renaming-files
description: Renames files in bulk using prefix, suffix, regex find-and-replace, sequential numbering, or date prepending. Includes a dry-run preview mode. Use when the user asks to rename files in bulk, batch rename, add a prefix or suffix, number files sequentially, or clean up filenames.
---

# FileData-BatchRename Skill

## When to Use This Skill
- User says "rename all files in this folder", "add a prefix to these files", "number these files"
- Organising exports, screenshots, or downloads with consistent naming
- Cleaning up filenames (lowercase, remove spaces, strip special chars)

---

## Workflow
- [ ] 1. Always run with `--dry-run` first to preview changes
- [ ] 2. Confirm the preview looks correct
- [ ] 3. Re-run without `--dry-run` to apply

---

## Commands

```bash
# Preview renames (always do this first)
python3 scripts/batch_rename.py --dir ./photos --prefix "2026_" --dry-run

# Add prefix
python3 scripts/batch_rename.py --dir ./exports --prefix "EXPORT_"

# Add suffix (before extension)
python3 scripts/batch_rename.py --dir ./reports --suffix "_FINAL"

# Regex find & replace
python3 scripts/batch_rename.py --dir ./files --find "Draft" --replace "Final"

# Number sequentially (001, 002, ...)
python3 scripts/batch_rename.py --dir ./slides --number --pad 3

# Prepend today's date
python3 scripts/batch_rename.py --dir ./logs --date-prefix

# Lowercase all filenames
python3 scripts/batch_rename.py --dir ./downloads --lowercase

# Remove spaces (replace with underscore)
python3 scripts/batch_rename.py --dir ./docs --no-spaces

# Limit to specific extensions
python3 scripts/batch_rename.py --dir ./mixed --prefix "IMG_" --ext .jpg .png
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--dir` | *(required)* | Directory containing files to rename |
| `--prefix` | — | Prepend string to filename |
| `--suffix` | — | Append string before extension |
| `--find` | — | Regex pattern to find |
| `--replace` | — | Replacement string (used with `--find`) |
| `--number` | off | Add sequential number to filename |
| `--pad` | `3` | Zero-pad width for numbering |
| `--start` | `1` | Starting number |
| `--date-prefix` | off | Prepend `YYYY-MM-DD_` |
| `--lowercase` | off | Convert filename to lowercase |
| `--no-spaces` | off | Replace spaces with underscores |
| `--ext` | all files | Limit to specific extensions |
| `--dry-run` | off | Preview changes without renaming |
| `--recursive` | off | Recurse into subdirectories |

> **Rule:** Always preview with `--dry-run` before applying. Renames cannot be auto-undone.

---

## Resources
- `scripts/batch_rename.py` — core rename script (stdlib only, no pip install)

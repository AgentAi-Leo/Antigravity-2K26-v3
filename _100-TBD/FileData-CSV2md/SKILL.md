---
name: converting-csv-to-markdown
description: Converts CSV and TSV files into formatted Markdown tables. Use when the user mentions CSV to Markdown, tabular data to Markdown, spreadsheet to Markdown, or wants to display CSV data as a readable table.
---

# FileData-CSV2md Skill

## When to Use This Skill
- User wants to convert a `.csv` or `.tsv` file to a Markdown table
- User says "turn this CSV into a table", "format CSV for docs", or "CSV to Markdown"
- Preparing tabular data for documentation, LLM input, or reports

---

## Workflow
- [ ] 1. Confirm `--input` exists and is `.csv` or `.tsv`
- [ ] 2. Run `scripts/csv2md.py`
- [ ] 3. Review the output — check header alignment and row count

---

## Commands

```bash
# Basic — auto-detects delimiter
python3 scripts/csv2md.py --input "data.csv"

# TSV input, custom output
python3 scripts/csv2md.py --input "data.tsv" --output "table.md"

# Limit rows, right-align numbers
python3 scripts/csv2md.py --input "data.csv" --max-rows 50 --align right

# No header row in file
python3 scripts/csv2md.py --input "data.csv" --no-header
```

---

## Options

| Flag | Default | Description |
|---|---|---|
| `--input` | *(required)* | Input `.csv` / `.tsv` file |
| `--output` | stdout | Output `.md` file path |
| `--delimiter` | auto | Force `,` or `\t` |
| `--max-rows` | all | Limit number of data rows |
| `--align` | `left` | Column alignment: `left`, `right`, `center` |
| `--no-header` | off | Treat first row as data, not header |

---

## Resources
- `scripts/csv2md.py` — core conversion (stdlib only, no pip install)

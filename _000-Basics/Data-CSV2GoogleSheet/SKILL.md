---
name: csv-to-google-sheet
description: Converts an uploaded CSV file into a brand new Google Sheet on your Google account. Use when the user wants to turn a CSV, comma separated values, or spreadsheet file into a live Google Sheet.
script: scripts/csv_to_sheet.py
---

# Data-CSV2GoogleSheet Skill

## When to Use This Skill
- User uploads a `.csv` file and asks to convert it to a Google Sheet.
- User wants to import data into a new Google Spreadsheet.

---

## Prerequisites
To interact with the actual Google account, this script requires authentication.
It uses the exact same authentication mechanism as `Data-GoogleSheet` (looks for Secret Manager `DEV-TEST4-GSHEETS` or a local `credentials.json`).

---

## Workflow
- [x] 1. Upload a CSV file through the dashboard.
- [ ] 2. Ensure Google API credentials exist.
- [ ] 3. Run `scripts/csv_to_sheet.py` with the file.
- [ ] 4. Return the generated live Google Sheets URL to the user.

---

## Instructions

When the user uploads a CSV:
1. The dashboard will automatically pass it as `--file [path]`.
2. The script extracts the CSV contents.
3. A new Google Sheet is created with the filename as the title (unless overridden).
4. All rows are injected into the sheet.
5. The sheet is opened in the browser automatically.

---

## Commands

**Basic usage:**
```bash
python3 scripts/csv_to_sheet.py --file "{FILE_1}"
```

---
name: generating-google-sheets
description: Generates a new live Google Spreadsheet on your Google account containing user-defined fields as column headers. Use when the user asks to create an excel sheet, make a google sheet, build a spreadsheet template, or generate spreadsheet columns.
script: scripts/generate_sheet.py
---

# Data-GoogleSheet Skill

## When to Use This Skill
- User wants to create a brand new Google Sheet on their account.
- User provides a list of fields or column names (e.g., "Name, Email, Phone") and wants them turned into a spreadsheet template.
- User says "create a google sheet for...", "build a spreadsheet with these columns", or "make an excel sheet".

---

## Prerequisites
To interact with the actual Google account, this script requires authentication.
You must have a `credentials.json` file from Google Cloud (Desktop App OAuth) or a Service Account JSON located at the project root or passed via `--credentials`.

---

## Workflow
- [x] 1. Gather the list of desired fields/columns from the user.
- [ ] 2. Ensure Google API credentials (`credentials.json` or service account) exist.
- [ ] 3. Run `scripts/generate_sheet.py` with the title and fields.
- [ ] 4. Return the generated live Google Sheets URL to the user.

---

## Instructions

When the user asks to create a sheet:
1. Extract the title of the sheet (or generate a sensible one).
2. Extract the list of columns.
3. Run the python script to create it.
4. The script will output the URL of the created sheet. Display this URL prominently.

First-time execution might open a browser window to authenticate if using Desktop OAuth. Warn the user that they may need to click 'Allow' in their browser.

---

## Commands

**Basic usage:**
```bash
python3 scripts/generate_sheet.py --title "Client Tracker" --fields "First Name" "Last Name" "Email" "Phone Number" "Status"
```

**Using an explicit credentials file:**
```bash
python3 scripts/generate_sheet.py --credentials "my_google_creds.json" --title "Inventory" --fields "SKU" "Item" "Qty" "Price"
```

---

## Resources
- `scripts/generate_sheet.py` — The core script that utilizes the Google Sheets API to create the document and inject the header row.

---

## Dependencies

This script requires the official Google API python client libraries:
```bash
python3 -m pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

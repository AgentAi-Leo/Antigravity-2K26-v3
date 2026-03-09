---
name: managing-google-drive-files
description: Uploads, categorizes, and manages files on Google Drive using the Google Drive API. Includes recursive folder creation and provides sharable web links for easy retrieval. Use when the user asks to save files to the cloud, upload audio to Drive, or organize documents in Google Drive folders.
---

# Data-GoogleDrive Skill

## When to Use This Skill
- User says "upload this file to Google Drive", "save my audio to the cloud", or "organize these in a [category] folder"
- You need to store generated assets (like ElevenLabs audio) and get a permanent link for follow-up actions (like saving to a spreadsheet)
- Creating categorized folder structures for project organization

---

## Workflow
- [ ] 1. Ensure `GCP_PROJECT_ID` and `GCP_SECRET_ID` (default: `DEV-TEST4-GSHEETS`) are available to fetch credentials.
- [ ] 2. Identify the file to upload and the destination folder path (e.g., `AI-Audio/Podcasts/March`).
- [ ] 3. Run `scripts/upload_to_drive.py --file [path] --folder [folder/path]`.
- [ ] 4. Capture the returned Google Drive URL for verification or storage in a database.

---

## Instructions

### Authentication
This skill uses Google Secret Manager to fetch OAuth2 or Service Account credentials. It shares the same secret as the Google Sheets skills (`DEV-TEST4-GSHEETS`) but requires the **Drive scope** (`https://www.googleapis.com/auth/drive.file`).

### Key Rules
- Use `/` for all paths, never `\`.
- If a folder path is provided (e.g., `Folder/Subfolder`), the script will create all missing parents automatically.
- Always return the `webViewLink` so the user can immediately access the file.

---

## Commands

**Upload a file to a specific folder:**
```bash
python3 scripts/upload_to_drive.py --file "output.mp3" --folder "AI-Project/Audio"
```

**Upload to the root directory (no folder):**
```bash
python3 scripts/upload_to_drive.py --file "report.pdf"
```

---

## Resources
- `scripts/upload_to_drive.py` — Core upload logic with recursive folder handling.
- `_output/` — Recommended local staging area before upload.

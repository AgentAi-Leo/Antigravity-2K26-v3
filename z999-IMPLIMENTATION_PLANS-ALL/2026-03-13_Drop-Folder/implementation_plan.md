# Watch Folder Auto-Processing for Convtr-PlainTxt2PDF

Add a toggle-enabled "watch folder" feature to the `Convtr-PlainTxt2PDF` skill. When enabled, the user specifies any folder path on their machine. Any supported files (`.txt`, `.rtf`, `.doc`, `.docx`) placed inside are automatically converted to PDF on a user-selected polling interval, with results stored in a dated subfolder and originals purged.

## Proposed Changes

### Dashboard UI
#### [MODIFY] [app.py](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS-v3/__000-DASHBOARD-TEST1/app.py)

Add a new section when `Convtr-PlainTxt2PDF` is the selected skill:

1. **Toggle switch** — "📂 Watch Folder Auto-Process" (`st.toggle`)
2. **Folder path input** — Text input for any absolute path on the user's machine (e.g., `~/Desktop/MyWatchFolder`). Validates the path exists, creates it if not. **Label styled in orange** (`#FF8C00`) to visually distinguish it.
3. **Polling interval dropdown** — `st.selectbox` with 3 choices:
   - `Every 15 minutes` (900s)
   - `Every 1 minute` (60s)
   - `Every :05` (5s)
4. **Status indicator** — Shows watch folder path + pending file count
5. **Auto-refresh** — Uses `streamlit-autorefresh` (or JS timer) at the selected interval while toggle is ON
6. **Processing logic** — On each rerun while active:
   - Scan watch folder for supported files (top-level only)
   - Process each via `plain_txt2pdf.py`
   - Move output PDF to `<folder>/zProcessed/YYYY-MM-DD/`
   - Purge original from watch folder
   - Show toast with what was processed

---

### Skill SKILL.md
#### [MODIFY] [SKILL.md](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS-v3/_000-Basics/Convtr-PlainTxt2PDF/SKILL.md)

Add `## Watch Folder Mode` section documenting toggle, folder path input, polling options, and auto-purge behavior. Per [Skill Creator](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS-v3/_000_MASTER-SKIILS/000B-SKILL_CREATOR_JackRoberts/SKILL.md) standards: YAML frontmatter maintained, body under 500 lines, forward slashes, `--help` reference for new script.

---

### Watch Folder Processor Script
#### [NEW] [watch_folder_processor.py](file:///Users/jb3/__JB3_ADDs/004_DOCS/__JB3_DOCs/2025_JB3/___000-AI-AGENTS/___ANTIGRAVITY-AI/___000A-ANTIGRAVITY-SKILLS-v3/_000-Basics/Convtr-PlainTxt2PDF/scripts/watch_folder_processor.py)

Standalone CLI script (also callable from dashboard):
- `--folder <path>` — any absolute path to scan
- Scans top-level for `.txt`, `.rtf`, `.doc`, `.docx`
- Calls `plain_txt2pdf.py --input <file> --output <zProcessed/YYYY-MM-DD/file.pdf>`
- Purges originals after successful conversion
- Outputs: `Processed: <file> -> <output>` / `Purged: <file>`

---

### Output Folder Structure

When user points to `/Users/jb3/Desktop/InvoiceWatch`:
```
/Users/jb3/Desktop/InvoiceWatch/
├── newfile.txt                    ← Dropped by watch folder (auto-detected)
└── zProcessed/
    └── 2026-03-13/                ← Dated output folder
        ├── oldfile.pdf            ← Previously processed
        └── earlier.pdf
```

## Verification Plan

### Manual Verification
1. Enable toggle, enter folder path, select polling interval → verify folder is validated/created
2. Drop a `.txt` file into the folder via Finder
3. Within the selected interval, dashboard auto-processes the file
4. Check `<folder>/zProcessed/2026-03-13/` contains the PDF
5. Verify original is purged from watch folder root
6. Disable toggle → confirm polling stops
7. Test `.rtf`, `.doc`, `.docx` all convert correctly
8. Run `watch_folder_processor.py --help` → verify CLI docs
